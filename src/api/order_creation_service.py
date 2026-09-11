"""Persist canonical orders from already-authoritative confirmation inputs."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping

from api.confirmed_order_context_service import ADMIN_EXTERNAL_SOURCE, persist_confirmed_order_context
from api.customer_snapshot import CustomerSnapshotValidationError, extract_manual_customer_snapshot
from api.design_service import SERVICE_LINE_TYPE
from api.models import ManualOrderDraft, OrderDetails, Orders
from api.utils import DEFAULT_CONFIGURATOR_SCREW_OPTION, resolve_screw_configuration


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrderCreationResult:
    """Values needed for source-specific work before the shared commit."""

    order: object
    customer_context: Mapping[str, object]
    is_design_service_checkout: bool
    design_request_id: int | None
    design_item_order_detail_ids: Mapping[int, int]


def create_order_from_confirmed_input(
    *,
    db_session,
    user,
    quote_snapshot,
    customer_snapshot,
    confirmation=None,
    estimated_delivery_at=None,
    estimated_delivery_note=None,
):
    """Create an Order, details and optional context without committing."""
    if not quote_snapshot or not quote_snapshot.get("lines"):
        raise ValueError("Checkout snapshot not available for this payment intent.")

    order_details = build_order_details_from_checkout_quote(quote_snapshot)
    is_design_service_checkout = quote_snapshot.get("checkout_kind") == SERVICE_LINE_TYPE
    contains_design_service_line = any(
        detail.get("line_type") == SERVICE_LINE_TYPE for detail in order_details
    )
    if contains_design_service_line and not is_design_service_checkout:
        raise ValueError("Las líneas de diseño previo requieren un checkout exclusivo de diseño.")
    if is_design_service_checkout and (
        not order_details
        or any(detail.get("line_type") != SERVICE_LINE_TYPE for detail in order_details)
        or len({detail.get("design_request_id") for detail in order_details}) != 1
    ):
        raise ValueError("El checkout de diseño previo debe contener únicamente sus líneas de servicio.")

    order_user_id, customer_snapshot = _resolve_order_customer_identity(
        db_session=db_session,
        user=user,
        customer_snapshot=customer_snapshot,
        confirmation=confirmation,
    )
    customer_context = build_customer_context({}, customer_snapshot)
    new_order = Orders(
        user_id=order_user_id,
        total_amount=0,
        locator=Orders.generate_locator(),
        order_status="pendiente",
        estimated_delivery_at=estimated_delivery_at,
        estimated_delivery_note=estimated_delivery_note,
    )
    db_session.add(new_order)
    db_session.flush()

    subtotal = 0.0
    discount_code = quote_snapshot.get("discount_code") or None
    design_item_order_details = {}
    for detail in order_details:
        precio_recalculado = float(detail.get("precio_total") or 0.0)
        existing_detail = None
        if detail.get("line_type") == "physical":
            existing_detail = db_session.query(OrderDetails).filter_by(
                order_id=new_order.id,
                product_id=detail["producto_id"],
                alto=detail.get("alto"),
                ancho=detail.get("ancho"),
                anclaje=detail.get("anclaje"),
                color=detail.get("color"),
                screw_option=detail.get("screw_option") or DEFAULT_CONFIGURATOR_SCREW_OPTION,
                line_type="physical",
            ).first()

        if existing_detail:
            logger.info("Detalle ya existente: %s", existing_detail.serialize())
            existing_detail.quantity += detail["quantity"]
            existing_detail.precio_total = precio_recalculado
            subtotal += precio_recalculado * detail["quantity"]
            continue

        new_detail = OrderDetails(
            order_id=new_order.id,
            product_id=detail["producto_id"],
            quantity=detail["quantity"],
            line_type=detail.get("line_type") or "physical",
            alto=detail.get("alto"),
            ancho=detail.get("ancho"),
            anclaje=detail.get("anclaje"),
            color=detail.get("color"),
            screw_option=detail.get("screw_option") or DEFAULT_CONFIGURATOR_SCREW_OPTION,
            screw_length_mm=detail.get("screw_length_mm"),
            screw_supplement=detail.get("screw_supplement", 0.0),
            precio_total=precio_recalculado,
            firstname=customer_context["firstname"],
            lastname=customer_context["lastname"],
            shipping_address=(
                customer_context["shipping_address"]
                if detail.get("line_type") == "physical"
                else None
            ),
            shipping_city=(
                customer_context["shipping_city"]
                if detail.get("line_type") == "physical"
                else None
            ),
            shipping_postal_code=(
                customer_context["shipping_postal_code"]
                if detail.get("line_type") == "physical"
                else None
            ),
            billing_address=customer_context["billing_address"],
            billing_city=customer_context["billing_city"],
            billing_postal_code=customer_context["billing_postal_code"],
            CIF=customer_context["CIF"],
            shipping_type=detail.get("shipping_type"),
            shipping_cost=detail.get("shipping_cost"),
        )
        db_session.add(new_detail)
        db_session.flush()
        if detail.get("line_type") == SERVICE_LINE_TYPE:
            design_item_order_details[detail["design_request_item_id"]] = new_detail.id
        subtotal += precio_recalculado * detail.get("quantity", 1)

    shipping_cost = float(quote_snapshot["shipping_cost"])
    backend_total = float(quote_snapshot["total_amount"])
    gross_sum = subtotal + float(shipping_cost or 0.0)
    discount_value_iva = round(float(quote_snapshot["discount_amount"]), 2)

    new_order.discount_code = discount_code
    new_order.discount_value = discount_value_iva
    new_order.shipping_cost = round(float(shipping_cost or 0.0), 2)
    new_order.total_amount = round(backend_total, 2)

    if confirmation is not None:
        persist_confirmed_order_context(
            db_session=db_session,
            order=new_order,
            quote_snapshot=quote_snapshot,
            customer_snapshot=customer_snapshot,
            confirmation=confirmation,
        )

    logger.info(
        "Cálculo final autoritativo backend -> Bruto: %.2f EUR | Descuento: %.2f EUR | "
        "Envío: %.2f EUR | Total guardado: %.2f EUR",
        gross_sum,
        discount_value_iva,
        shipping_cost,
        backend_total,
    )

    design_request_id = (
        order_details[0]["design_request_id"] if is_design_service_checkout else None
    )
    return OrderCreationResult(
        order=new_order,
        customer_context=customer_context,
        is_design_service_checkout=is_design_service_checkout,
        design_request_id=design_request_id,
        design_item_order_detail_ids=design_item_order_details,
    )


def _resolve_order_customer_identity(*, db_session, user, customer_snapshot, confirmation):
    """Allow an accountless customer only through the locked manual-order flow."""
    if user is not None:
        user_id = getattr(user, "id", None)
        if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id < 1:
            raise ValueError("El usuario del pedido confirmado no es válido.")
        return user_id, customer_snapshot or {}

    if confirmation is None or getattr(confirmation, "source", None) != ADMIN_EXTERNAL_SOURCE:
        raise ValueError("Los pedidos web confirmados requieren un usuario existente.")

    draft_id = getattr(confirmation, "source_manual_draft_id", None)
    if isinstance(draft_id, bool) or not isinstance(draft_id, int) or draft_id < 1:
        raise ValueError("El pedido manual sin cuenta debe conservar su borrador de origen.")

    manual_draft = (
        db_session.query(ManualOrderDraft)
        .filter(ManualOrderDraft.id == draft_id)
        .with_for_update()
        .one_or_none()
    )
    if (
        manual_draft is None
        or manual_draft.status != ManualOrderDraft.STATUS_DRAFT
        or manual_draft.issued_order_id is not None
        or manual_draft.customer_mode != ManualOrderDraft.CUSTOMER_MODE_MANUAL_CUSTOMER
        or manual_draft.user_id is not None
    ):
        raise ValueError("El contexto del cliente sin cuenta no procede de un borrador manual válido.")

    try:
        draft_customer_snapshot = extract_manual_customer_snapshot(manual_draft.customer_draft)
        supplied_customer_snapshot = extract_manual_customer_snapshot(customer_snapshot)
    except CustomerSnapshotValidationError as exc:
        raise ValueError("El cliente sin cuenta no tiene un snapshot completo válido.") from exc
    if draft_customer_snapshot != supplied_customer_snapshot:
        raise ValueError("El snapshot del cliente no coincide con el borrador manual validado.")
    return None, supplied_customer_snapshot


def build_order_details_from_checkout_quote(checkout_quote):
    """Map frozen quote lines to the legacy OrderDetails persistence contract."""
    order_details = []
    for line in (checkout_quote.get("lines") or []):
        line_type = line.get("line_type") or "physical"
        if line_type not in {"physical", SERVICE_LINE_TYPE}:
            raise ValueError("El tipo de línea del pedido no es válido.")
        if line_type == SERVICE_LINE_TYPE:
            design_request_id = line.get("design_request_id") or checkout_quote.get("design_request_id")
            design_request_item_id = line.get("design_request_item_id")
            if design_request_id is None or design_request_item_id is None:
                raise ValueError("La solicitud de diseño es obligatoria para finalizar el pago.")
            order_details.append({
                "line_type": SERVICE_LINE_TYPE,
                "design_request_id": design_request_id,
                "design_request_item_id": design_request_item_id,
                "producto_id": line["product_id"],
                "quantity": 1,
                "alto": line["alto"],
                "ancho": line["ancho"],
                "anclaje": None,
                "color": None,
                "screw_option": "not_applicable",
                "screw_length_mm": None,
                "screw_supplement": 0.0,
                "precio_total": line["unit_price"],
                "shipping_type": None,
                "shipping_cost": 0.0,
            })
            continue

        screw_option = line.get("screw_option") or DEFAULT_CONFIGURATOR_SCREW_OPTION
        resolved_screws = resolve_screw_configuration(line.get("anclaje"), screw_option) or {}
        order_details.append({
            "line_type": "physical",
            "producto_id": line["product_id"],
            "quantity": line["quantity"],
            "alto": line["alto"],
            "ancho": line["ancho"],
            "anclaje": line.get("anclaje"),
            "color": line.get("color"),
            "screw_option": screw_option,
            "screw_length_mm": line.get("screw_length_mm") or resolved_screws.get("screw_length_mm"),
            "screw_supplement": line.get("screw_supplement", resolved_screws.get("screw_supplement", 0.0)),
            "precio_total": line["unit_price"],
            "shipping_type": line.get("shipping_type"),
            "shipping_cost": line.get("shipping_cost"),
        })
    assert_homogeneous_order_details(order_details)
    return order_details


def assert_homogeneous_order_details(order_details):
    line_types = {detail.get("line_type") or "physical" for detail in order_details}
    if len(line_types) > 1:
        raise ValueError("Un pedido no puede mezclar productos físicos y diseños previos.")


def get_customer_value(request_data, customer_snapshot, field_name):
    request_value = request_data.get(field_name)
    if request_value is not None and request_value != "":
        return request_value
    return (customer_snapshot or {}).get(field_name)


def build_customer_context(request_data, customer_snapshot):
    return {
        "firstname": get_customer_value(request_data, customer_snapshot, "firstname"),
        "lastname": get_customer_value(request_data, customer_snapshot, "lastname"),
        "phone": get_customer_value(request_data, customer_snapshot, "phone"),
        "shipping_address": get_customer_value(request_data, customer_snapshot, "shipping_address"),
        "shipping_city": get_customer_value(request_data, customer_snapshot, "shipping_city"),
        "shipping_postal_code": get_customer_value(request_data, customer_snapshot, "shipping_postal_code"),
        "billing_address": get_customer_value(request_data, customer_snapshot, "billing_address"),
        "billing_city": get_customer_value(request_data, customer_snapshot, "billing_city"),
        "billing_postal_code": get_customer_value(request_data, customer_snapshot, "billing_postal_code"),
        "CIF": get_customer_value(request_data, customer_snapshot, "CIF"),
    }

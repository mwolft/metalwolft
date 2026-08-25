"""Authoritative domain services for the paid design-preview product."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import secrets

from api.invoice_snapshot_builder import SUPPORTED_TAX_RATE
from api.models import CheckoutSessions, DesignRequest, DesignRequestItem, DesignServiceConfig, Products
from api.product_lifecycle import ensure_product_available_for_sale
from api.utils import (
    CONFIGURATOR_MAX_DIMENSION_CM,
    CONFIGURATOR_MAX_DIMENSION_SUM_CM,
    CONFIGURATOR_MIN_DIMENSION_CM,
)


SERVICE_LINE_TYPE = "design_service"
SERVICE_CURRENCY = "EUR"


class DesignServiceError(ValueError):
    pass


class DesignServiceUnavailable(DesignServiceError):
    pass


class DesignServiceValidationError(DesignServiceError):
    pass


@dataclass(frozen=True)
class DesignRequestResult:
    design_request: object
    created: bool


def get_design_service_config(db_session):
    config = db_session.get(DesignServiceConfig, 1)
    if config is None:
        raise DesignServiceUnavailable("La configuración del diseño previo no está disponible.")
    return config


def build_design_service_quote(*, db_session, items):
    """Quote real models and dimensions without physical product options."""
    config = get_design_service_config(db_session)
    if not config.is_active:
        raise DesignServiceUnavailable("El servicio de diseño previo no está disponible actualmente.")

    validated_items = _validate_request_items(db_session=db_session, items=items)
    return _build_quote(
        items=validated_items,
        base_unit_price=_money(config.base_price_gross, "config.base_price_gross"),
        lead_time_hours=_lead_time(config.lead_time_hours),
        price_tiers=tuple(getattr(config, "price_tiers", ()) or ()),
    )


def create_design_request(*, db_session, user_id, items, creation_key):
    normalized_key = _required_text(creation_key, "creation_key")
    existing = (
        db_session.query(DesignRequest)
        .filter_by(user_id=user_id, creation_key=normalized_key)
        .one_or_none()
    )
    if existing is not None:
        return DesignRequestResult(design_request=existing, created=False)

    quote = build_design_service_quote(db_session=db_session, items=items)
    design_request = DesignRequest(
        reference=_new_reference(),
        creation_key=normalized_key,
        user_id=user_id,
        subtotal_gross=_decimal(quote["subtotal"], "subtotal_gross"),
        price_gross=_decimal(quote["total_amount"], "price_gross"),
        discount_amount=_decimal(quote["discount_amount"], "discount_amount"),
        pricing_tier_min_design_count=quote["pricing_tier_min_design_count"],
        currency=quote["currency"],
        lead_time_hours=quote["lead_time_hours"],
        status=DesignRequest.STATUS_PENDING_PAYMENT,
    )
    db_session.add(design_request)
    db_session.flush()
    for item in quote["items"]:
        db_session.add(DesignRequestItem(
            design_request_id=design_request.id,
            product_id=item["product_id"],
            product_name=item["product_name"],
            width_cm=_decimal(item["width_cm"], "width_cm"),
            height_cm=_decimal(item["height_cm"], "height_cm"),
        ))
    db_session.flush()
    return DesignRequestResult(design_request=design_request, created=True)


def build_design_checkout_quote(*, design_request, user_id):
    if design_request is None or design_request.user_id != user_id:
        raise DesignServiceValidationError("La solicitud de diseño no está disponible.")
    if design_request.status != DesignRequest.STATUS_PENDING_PAYMENT:
        raise DesignServiceValidationError("La solicitud de diseño ya no está pendiente de pago.")
    if not design_request.items:
        raise DesignServiceValidationError("La solicitud de diseño no contiene modelos.")

    frozen_items = [
        {
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "width_cm": _measurement_string(item.width_cm),
            "height_cm": _measurement_string(item.height_cm),
        }
        for item in design_request.items
    ]
    return _build_quote(
        items=frozen_items,
        base_unit_price=_money(design_request.subtotal_gross, "design_request.subtotal_gross") /
        Decimal(len(frozen_items)),
        lead_time_hours=_lead_time(design_request.lead_time_hours),
        price_tiers=(),
        design_request_id=design_request.id,
        frozen_total=_money(design_request.price_gross, "design_request.price_gross"),
        frozen_discount=_nonnegative_money(design_request.discount_amount, "design_request.discount_amount"),
        pricing_tier_min_design_count=design_request.pricing_tier_min_design_count,
    )


def prepare_design_checkout_session(
    *, db_session, design_request, user_id, payment_provider, idempotency_key, customer_snapshot=None
):
    """Persist the canonical quote; Phase 2 will attach the provider payment."""
    normalized_key = _required_text(idempotency_key, "idempotency_key")
    quote = build_design_checkout_quote(design_request=design_request, user_id=user_id)
    existing = (
        db_session.query(CheckoutSessions)
        .filter_by(user_id=user_id, design_request_id=design_request.id, idempotency_key=normalized_key)
        .one_or_none()
    )
    if existing is not None:
        return existing, False

    checkout_session = CheckoutSessions(
        user_id=user_id,
        design_request_id=design_request.id,
        payment_provider=_required_text(payment_provider, "payment_provider"),
        public_checkout_token=CheckoutSessions.generate_public_checkout_token(),
        idempotency_key=normalized_key,
        status="pending_payment",
        subtotal=float(_decimal(quote["subtotal"], "subtotal")),
        shipping_cost=0.0,
        discount_percent=0.0,
        discount_amount=float(_decimal(quote["discount_amount"], "discount_amount")),
        total_amount=float(_decimal(quote["total_amount"], "total_amount")),
        quote_snapshot=quote,
        customer_snapshot=customer_snapshot,
    )
    db_session.add(checkout_session)
    db_session.flush()
    return checkout_session, True


def mark_design_request_paid(*, db_session, design_request_id, order_id, item_order_detail_ids):
    design_request = (
        db_session.query(DesignRequest)
        .filter_by(id=design_request_id)
        .with_for_update()
        .one_or_none()
    )
    if design_request is None:
        raise DesignServiceValidationError("La solicitud de diseño no existe.")
    if design_request.order_id not in (None, order_id):
        raise DesignServiceValidationError("La solicitud de diseño ya está asociada a otro pedido.")
    if design_request.status == DesignRequest.STATUS_PENDING_PAYMENT:
        design_request.status = DesignRequest.STATUS_PENDING
        design_request.paid_at = datetime.now(timezone.utc)
    if design_request.status != DesignRequest.STATUS_PENDING:
        raise DesignServiceValidationError("La solicitud de diseño no se puede confirmar como pagada.")

    expected_ids = {item.id for item in design_request.items}
    if set(item_order_detail_ids) != expected_ids:
        raise DesignServiceValidationError("Las líneas del pedido no coinciden con la solicitud de diseño.")
    for item in design_request.items:
        detail_id = item_order_detail_ids[item.id]
        if item.order_detail_id not in (None, detail_id):
            raise DesignServiceValidationError("Un diseño ya está asociado a otra línea de pedido.")
        item.order_detail_id = detail_id
    design_request.order_id = order_id
    return design_request


def transition_design_request_status(*, design_request, new_status):
    """Cancellation is deliberately excluded until refund policy exists."""
    allowed = {
        DesignRequest.STATUS_PENDING: {DesignRequest.STATUS_IN_PROGRESS},
        DesignRequest.STATUS_IN_PROGRESS: {DesignRequest.STATUS_DELIVERED},
    }
    normalized_status = _required_text(new_status, "status")
    if normalized_status not in allowed.get(design_request.status, set()):
        raise DesignServiceValidationError("La transición de estado de la solicitud no está permitida.")
    if normalized_status == DesignRequest.STATUS_DELIVERED and not design_request.result_storage_key:
        raise DesignServiceValidationError("No se puede marcar como entregada una solicitud sin resultado asociado.")

    now = datetime.now(timezone.utc)
    design_request.status = normalized_status
    if normalized_status == DesignRequest.STATUS_IN_PROGRESS:
        design_request.started_at = now
    else:
        design_request.delivered_at = now
    return design_request


def order_contains_design_service(order):
    return any(
        getattr(detail, "line_type", "physical") == SERVICE_LINE_TYPE
        for detail in (getattr(order, "order_details", ()) or ())
    )


def assert_order_accepts_physical_detail(order):
    if order_contains_design_service(order) or getattr(order, "design_request", None):
        raise DesignServiceValidationError("No se pueden añadir líneas físicas a un pedido de diseño previo.")


def is_design_service_only_order(order):
    details = tuple(getattr(order, "order_details", ()) or ())
    return bool(details) and all(
        getattr(detail, "line_type", "physical") == SERVICE_LINE_TYPE for detail in details
    )


def _build_quote(
    *, items, base_unit_price, lead_time_hours, price_tiers, design_request_id=None,
    frozen_total=None, frozen_discount=None, pricing_tier_min_design_count=None,
):
    item_count = len(items)
    if item_count <= 0:
        raise DesignServiceValidationError("Incluye al menos un diseño.")

    base_unit = _money(base_unit_price, "base_unit_price")
    tier = _matching_tier(price_tiers, item_count)
    effective_unit = _money(tier.unit_price_gross, "tier.unit_price_gross") if tier else base_unit
    if effective_unit > base_unit:
        raise DesignServiceValidationError("Un tramo de diseño no puede superar el precio base.")

    subtotal = (base_unit * item_count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    calculated_total = (effective_unit * item_count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    calculated_discount = (subtotal - calculated_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = frozen_total if frozen_total is not None else calculated_total
    discount = frozen_discount if frozen_discount is not None else calculated_discount
    if subtotal - discount != total:
        raise DesignServiceValidationError("El precio congelado de la solicitud no es coherente.")

    tax_base, tax_amount = _tax_from_gross(total)
    quote_items = []
    lines = []
    for item in items:
        quote_item = {
            "id": item.get("id"),
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "width_cm": _measurement_string(item["width_cm"]),
            "height_cm": _measurement_string(item["height_cm"]),
        }
        quote_items.append(quote_item)
        line = {
            "line_type": SERVICE_LINE_TYPE,
            "product_id": quote_item["product_id"],
            "product_name": quote_item["product_name"],
            "quantity": 1,
            "alto": quote_item["height_cm"],
            "ancho": quote_item["width_cm"],
            "unit_price": _money_string(base_unit),
            "line_total": _money_string(base_unit),
            "shipping_type": None,
            "shipping_cost": "0.00",
        }
        if design_request_id is not None:
            line["design_request_id"] = design_request_id
            line["design_request_item_id"] = quote_item["id"]
        lines.append(line)

    applied_tier = pricing_tier_min_design_count if pricing_tier_min_design_count is not None else (
        tier.min_design_count if tier else None
    )
    quote = {
        "checkout_kind": SERVICE_LINE_TYPE,
        "currency": SERVICE_CURRENCY,
        "requires_shipping": False,
        "shipping_cost": "0.00",
        "subtotal": _money_string(subtotal),
        "base_price_gross": _money_string(subtotal),
        "discount_amount": _money_string(discount),
        "discount_percent": 0,
        "total_amount": _money_string(total),
        "tax_rate": _money_string(SUPPORTED_TAX_RATE),
        "tax_base": _money_string(tax_base),
        "tax_amount": _money_string(tax_amount),
        "lead_time_hours": lead_time_hours,
        "pricing_tier_min_design_count": applied_tier,
        "items": quote_items,
        "lines": lines,
    }
    if design_request_id is not None:
        quote["design_request_id"] = design_request_id
    return quote


def _validate_request_items(*, db_session, items):
    if not isinstance(items, list) or not items:
        raise DesignServiceValidationError("Incluye al menos un diseño.")
    validated = []
    seen = set()
    for index, raw_item in enumerate(items, start=1):
        if not isinstance(raw_item, dict):
            raise DesignServiceValidationError(f"El diseño {index} no es válido.")
        product = db_session.get(Products, _product_id(raw_item.get("product_id")))
        if product is None:
            raise DesignServiceValidationError("El modelo seleccionado no existe.")
        try:
            ensure_product_available_for_sale(product)
        except ValueError as exc:
            raise DesignServiceValidationError(str(exc)) from exc
        width = _valid_dimension(raw_item.get("width_cm"), "width_cm")
        height = _valid_dimension(raw_item.get("height_cm"), "height_cm")
        if width + height > Decimal(str(CONFIGURATOR_MAX_DIMENSION_SUM_CM)):
            raise DesignServiceValidationError("La suma de las medidas supera el máximo permitido.")
        key = (product.id, width, height)
        # A repeated model with the same normalized dimensions is one design, not two billable items.
        if key in seen:
            continue
        seen.add(key)
        validated.append({
            "product_id": int(product.id),
            "product_name": _product_name(product.nombre),
            "width_cm": _measurement_string(width),
            "height_cm": _measurement_string(height),
        })
    return validated


def _matching_tier(tiers, item_count):
    matches = [tier for tier in tiers if int(tier.min_design_count) <= item_count]
    return max(matches, key=lambda tier: int(tier.min_design_count)) if matches else None


def _product_id(value):
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise DesignServiceValidationError("El modelo seleccionado no es válido.") from exc


def _required_text(value, field):
    text = str(value or "").strip()
    if not text or len(text) > 64:
        raise DesignServiceValidationError(f"{field} no es válido.")
    return text


def _product_name(value):
    text = str(value or "").strip()
    if not text or len(text) > 255:
        raise DesignServiceValidationError("product_name no es válido.")
    return text


def _lead_time(value):
    try:
        hours = int(value)
    except (TypeError, ValueError) as exc:
        raise DesignServiceValidationError("lead_time_hours no es válido.") from exc
    if hours <= 0:
        raise DesignServiceValidationError("lead_time_hours no es válido.")
    return hours


def _decimal(value, field):
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise DesignServiceValidationError(f"{field} no es válido.") from exc
    if not parsed.is_finite():
        raise DesignServiceValidationError(f"{field} no es válido.")
    return parsed


def _money(value, field):
    amount = _decimal(value, field).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise DesignServiceValidationError(f"{field} debe ser mayor que cero.")
    return amount


def _nonnegative_money(value, field):
    amount = _decimal(value, field).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount < 0:
        raise DesignServiceValidationError(f"{field} no puede ser negativo.")
    return amount


def _valid_dimension(value, field):
    measurement = _decimal(value, field)
    minimum = Decimal(str(CONFIGURATOR_MIN_DIMENSION_CM))
    maximum = Decimal(str(CONFIGURATOR_MAX_DIMENSION_CM))
    if measurement < minimum or measurement > maximum:
        raise DesignServiceValidationError(
            f"{field} debe estar entre {_measurement_string(minimum)} y {_measurement_string(maximum)} cm."
        )
    return measurement


def _money_string(value):
    return f"{Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def _measurement_string(value):
    normalized = _decimal(value, "measurement")
    if normalized <= 0:
        raise DesignServiceValidationError("Las medidas deben ser mayores que cero.")
    normalized = normalized.normalize()
    return str(int(normalized)) if normalized == normalized.to_integral() else format(normalized, "f")


def _tax_from_gross(gross):
    base = (gross / (Decimal("1") + (SUPPORTED_TAX_RATE / Decimal("100")))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return base, (gross - base).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _new_reference():
    return f"DP-{secrets.token_hex(5).upper()}"

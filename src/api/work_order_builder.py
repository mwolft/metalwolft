"""Build and read immutable, non-economic manufacturing work-order snapshots."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping
from urllib.parse import urlparse

from api.order_shipping import (
    shipping_address_from_customer_snapshot,
    shipping_address_from_order_details,
    shipping_address_lines,
)
from api.order_confirmation_context import get_order_customer_snapshot
from api.utils import CONFIGURATOR_ANCHORAGES, CONFIGURATOR_COLORS


WORK_ORDER_SCHEMA_VERSION = 1
WORK_ORDER_IMAGE_HOSTS = frozenset({"res.cloudinary.com"})
_FORBIDDEN_ECONOMIC_KEYS = frozenset(
    {
        "price",
        "precio",
        "subtotal",
        "discount",
        "descuento",
        "iva",
        "tax",
        "shipping_cost",
        "porte",
        "total",
        "stripe",
        "paypal",
        "invoice",
        "factura",
    }
)


class WorkOrderValidationError(ValueError):
    """Raised when an order cannot safely produce a manufacturing work order."""


@dataclass(frozen=True)
class WorkOrderData:
    """The only data contract exposed to HTML now and PDF rendering later."""

    schema_version: int
    order: Mapping[str, Any]
    customer: Mapping[str, Any]
    lines: tuple[Mapping[str, Any], ...]
    generated_at: str | None
    internal_notes: str | None
    manufactured_at: str | None
    manufactured_by: str | None

    def to_template_context(self):
        return {
            "schema_version": self.schema_version,
            "order": deepcopy(dict(self.order)),
            "customer": deepcopy(dict(self.customer)),
            "lines": tuple(deepcopy(dict(line)) for line in self.lines),
            "generated_at": self.generated_at,
            "internal_notes": self.internal_notes,
            "manufactured_at": self.manufactured_at,
            "manufactured_by": self.manufactured_by,
        }


class WorkOrderBuilder:
    """Creates a stable v1 snapshot once, then reads only that snapshot."""

    @classmethod
    def build_snapshot(cls, order):
        details = tuple(getattr(order, "order_details", ()) or ())
        if not details:
            raise WorkOrderValidationError("El pedido no contiene líneas físicas para fabricar.")
        if any((getattr(detail, "line_type", "physical") or "physical") != "physical" for detail in details):
            raise WorkOrderValidationError(
                "Los servicios de diseño previo no generan parte de fabricación."
            )

        customer_snapshot = get_order_customer_snapshot(order)
        return {
            "schema_version": WORK_ORDER_SCHEMA_VERSION,
            "order": {
                "id": _integer(getattr(order, "id", None)),
                "locator": _text(getattr(order, "locator", None)) or "No consta",
                "ordered_at": _date_text(getattr(order, "order_date", None)),
            },
            "customer": _build_customer(customer_snapshot, details),
            "lines": [
                cls._build_line(detail, position)
                for position, detail in enumerate(details, start=1)
            ],
        }

    @classmethod
    def _build_line(cls, detail, position):
        product = getattr(detail, "product", None)
        product_id = _integer(getattr(detail, "product_id", None))
        color_code = _text(getattr(detail, "color", None))
        color_rule = CONFIGURATOR_COLORS.get(color_code) if color_code else None
        anchorage_value = _text(getattr(detail, "anclaje", None))
        anchorage_rule = (
            CONFIGURATOR_ANCHORAGES.get(anchorage_value) if anchorage_value else None
        )
        opening_code = _text(getattr(product, "opening_type", None))

        return {
            "line_number": position,
            "product_id": product_id,
            "model_name": _text(getattr(product, "nombre", None))
            or (f"Producto #{product_id}" if product_id is not None else "Producto no identificado"),
            "product_slug": _text(getattr(product, "slug", None)),
            "quantity": _positive_integer(getattr(detail, "quantity", None)),
            "dimensions": {
                "unit": "cm",
                "height": _normalized_dimension(getattr(detail, "alto", None)),
                "width": _normalized_dimension(getattr(detail, "ancho", None)),
            },
            "anchorage": {
                "value": anchorage_value,
                "label": _text((anchorage_rule or {}).get("name")) or anchorage_value,
            },
            "color": {
                "code": color_code,
                "label": _text((color_rule or {}).get("label")) or _humanize(color_code),
                "finish_label": _text((color_rule or {}).get("finish_label")),
            },
            "screws": _build_screws(detail, anchorage_rule),
            "opening_type": {
                "code": opening_code,
                "label": _opening_label(opening_code),
            },
            "image_url": _safe_image_url(product),
        }

    @classmethod
    def from_work_order(cls, work_order):
        snapshot = getattr(work_order, "snapshot", None)
        if not isinstance(snapshot, Mapping):
            raise WorkOrderValidationError("El parte de fabricación no contiene un snapshot válido.")
        schema_version = snapshot.get("schema_version")
        if schema_version != WORK_ORDER_SCHEMA_VERSION:
            raise WorkOrderValidationError("La versión del parte de fabricación no es compatible.")
        assert_snapshot_has_no_economic_data(snapshot)

        order = snapshot.get("order")
        customer = snapshot.get("customer")
        lines = snapshot.get("lines")
        if not isinstance(order, Mapping) or not isinstance(customer, Mapping) or not isinstance(lines, list):
            raise WorkOrderValidationError("El snapshot del parte de fabricación está incompleto.")

        return WorkOrderData(
            schema_version=schema_version,
            order=deepcopy(dict(order)),
            customer=deepcopy(dict(customer)),
            lines=tuple(deepcopy(dict(line)) for line in lines if isinstance(line, Mapping)),
            generated_at=_date_text(getattr(work_order, "created_at", None)),
            internal_notes=_text(getattr(work_order, "internal_notes", None)),
            manufactured_at=_datetime_text(getattr(work_order, "manufactured_at", None)),
            manufactured_by=_text(getattr(work_order, "manufactured_by", None)),
        )


def get_or_create_work_order(*, db_session, order, created_by):
    """Persist the first manufacturing snapshot and return it unchanged thereafter."""
    from api.models import WorkOrder

    existing = db_session.query(WorkOrder).filter_by(order_id=order.id).one_or_none()
    if existing is not None:
        return existing, False

    actor = _text(created_by)
    if not actor:
        raise WorkOrderValidationError("No se ha podido identificar al administrador que genera el parte.")

    work_order = WorkOrder(
        order_id=order.id,
        schema_version=WORK_ORDER_SCHEMA_VERSION,
        snapshot=WorkOrderBuilder.build_snapshot(order),
        created_by=actor,
    )
    assert_snapshot_has_no_economic_data(work_order.snapshot)
    db_session.add(work_order)
    db_session.flush()
    return work_order, True


def assert_snapshot_has_no_economic_data(value):
    """Reject economic fields before they can leak into an internal work-order renderer."""
    _assert_no_economic_keys(value)


def _assert_no_economic_keys(value):
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_ECONOMIC_KEYS:
                raise WorkOrderValidationError(
                    "El snapshot del parte no puede contener datos económicos o fiscales."
                )
            _assert_no_economic_keys(nested_value)
    elif isinstance(value, (list, tuple)):
        for nested_value in value:
            _assert_no_economic_keys(nested_value)


def _build_customer(customer_snapshot, details):
    snapshot = customer_snapshot if isinstance(customer_snapshot, Mapping) else {}
    name = _name(snapshot.get("firstname"), snapshot.get("lastname"))
    if not name:
        first_detail = details[0] if details else None
        name = _name(
            getattr(first_detail, "firstname", None),
            getattr(first_detail, "lastname", None),
        )

    shipping_address = shipping_address_from_customer_snapshot(snapshot)
    if not shipping_address.is_available:
        shipping_address = shipping_address_from_order_details(details)

    return {
        "name": name,
        "phone": _text(snapshot.get("phone")),
        "delivery_address": list(shipping_address_lines(shipping_address)),
    }


def _build_screws(detail, anchorage_rule):
    length = _integer(getattr(detail, "screw_length_mm", None))
    if length is not None:
        return {"length_mm": length, "display": f"{length} mm"}
    if anchorage_rule and not anchorage_rule.get("screw_required", True):
        return {"length_mm": None, "display": "No aplica"}
    return {"length_mm": None, "display": "No consta"}


def _safe_image_url(product):
    if product is None:
        return None
    candidates = [_text(getattr(product, "imagen", None))]
    candidates.extend(_text(getattr(image, "image_url", None)) for image in (getattr(product, "images", None) or ()))
    for candidate in candidates:
        if not candidate:
            continue
        parsed = urlparse(candidate)
        if (
            parsed.scheme == "https"
            and parsed.hostname in WORK_ORDER_IMAGE_HOSTS
        ):
            return candidate
    return None


def _normalized_dimension(value):
    if value is None:
        return None
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not decimal_value.is_finite() or decimal_value <= 0:
        return None
    normalized = decimal_value.quantize(Decimal("0.01")).normalize()
    return format(normalized, "f").rstrip("0").rstrip(".") if "." in format(normalized, "f") else format(normalized, "f")


def _date_text(value):
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return None


def _datetime_text(value):
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M UTC")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return None


def _integer(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _positive_integer(value):
    normalized = _integer(value)
    return normalized if normalized is not None and normalized > 0 else None


def _text(value):
    normalized = str(value or "").strip()
    return normalized or None


def _name(firstname, lastname):
    return " ".join(part for part in (_text(firstname), _text(lastname)) if part) or None


def _humanize(value):
    return value.replace("_", " ") if value else None


def _opening_label(value):
    return {"fixed": "Fija", "hinged": "Abatible"}.get(value, "No consta")

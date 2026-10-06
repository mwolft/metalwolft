"""Build a delivery receipt from an order without persisting anything."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping

from api.order_confirmation_context import get_order_customer_snapshot, get_order_quote_snapshot
from api.order_shipping import shipping_address_from_order, shipping_address_lines
from api.work_order_builder import WorkOrderBuilder, WorkOrderValidationError


class DeliveryReceiptValidationError(ValueError):
    """The order cannot produce a physical delivery receipt."""


@dataclass(frozen=True)
class DeliveryReceiptData:
    locator: str
    ordered_at: str
    customer_name: str
    phone: str
    email: str
    delivery_address: tuple[str, ...]
    lines: tuple[Mapping[str, object], ...]


def build_delivery_receipt(order) -> DeliveryReceiptData:
    """Read live order data using the existing work-order normalization and fallbacks."""
    try:
        data = WorkOrderBuilder.build_snapshot(order)
    except WorkOrderValidationError as exc:
        raise DeliveryReceiptValidationError(str(exc)) from exc

    customer_snapshot = get_order_customer_snapshot(order)
    quote_snapshot = get_order_quote_snapshot(order)
    customer = data["customer"]
    details = tuple(order.order_details or ())
    address = shipping_address_from_order(order)

    lines = []
    for detail, line in zip(details, data["lines"], strict=True):
        lines.append({
            "quantity": line["quantity"],
            "model_name": (
                _frozen_model_name(quote_snapshot, detail)
                or _work_order_model_name(getattr(order, "work_order", None), detail)
                or line["model_name"]
            ),
            "dimensions": line["dimensions"],
            "anchorage": line["anchorage"]["label"],
            "color": line["color"]["label"],
            "finish": line["color"]["finish_label"],
            "screws": line["screws"]["display"],
            "opening_type": line["opening_type"]["label"],
        })

    return DeliveryReceiptData(
        locator=data["order"]["locator"],
        ordered_at=data["order"]["ordered_at"] or "No consta",
        customer_name=_text(customer_snapshot.get("legal_name")) or customer["name"] or "No consta",
        phone=customer["phone"] or "No consta",
        email=customer["email"] or "No consta",
        delivery_address=tuple(shipping_address_lines(address, include_recipient=False)),
        lines=tuple(lines),
    )


def _frozen_model_name(quote_snapshot, detail):
    """Accept a quoted name only for an exact, unambiguous configuration match."""
    quote_lines = quote_snapshot.get("lines") if isinstance(quote_snapshot, Mapping) else None
    if not isinstance(quote_lines, list):
        return None

    matching_names = set()
    for line in quote_lines:
        if not isinstance(line, Mapping) or line.get("line_type", "physical") != "physical":
            continue
        if str(line.get("product_id", line.get("producto_id"))) != str(detail.product_id):
            continue
        if not all(_same_dimension(line.get(field), getattr(detail, field, None)) for field in ("alto", "ancho")):
            continue
        if any(_text(line.get(field)) != _text(getattr(detail, field, None)) for field in ("anclaje", "color")):
            continue
        name = _text(line.get("product_name"))
        if name:
            matching_names.add(name)

    return next(iter(matching_names)) if len(matching_names) == 1 else None


def _work_order_model_name(work_order, detail):
    snapshot = getattr(work_order, "snapshot", None)
    lines = snapshot.get("lines") if isinstance(snapshot, Mapping) else None
    if not isinstance(lines, list):
        return None

    matching_names = set()
    for line in lines:
        if not isinstance(line, Mapping) or str(line.get("product_id")) != str(detail.product_id):
            continue
        dimensions = line.get("dimensions")
        anchorage = line.get("anchorage")
        color = line.get("color")
        if not all(isinstance(value, Mapping) for value in (dimensions, anchorage, color)):
            continue
        if not all(
            _same_dimension(dimensions.get(key), getattr(detail, field, None))
            for key, field in (("height", "alto"), ("width", "ancho"))
        ):
            continue
        if _text(anchorage.get("value")) != _text(detail.anclaje):
            continue
        if _text(color.get("code")) != _text(detail.color):
            continue
        name = _text(line.get("model_name"))
        if name:
            matching_names.add(name)

    return next(iter(matching_names)) if len(matching_names) == 1 else None


def _same_dimension(first, second):
    if first is None or second is None:
        return first is None and second is None
    try:
        return Decimal(str(first)) == Decimal(str(second))
    except (InvalidOperation, TypeError, ValueError):
        return False


def _text(value):
    normalized = str(value or "").strip()
    return normalized or None

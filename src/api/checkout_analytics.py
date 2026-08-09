from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class CheckoutAnalyticsSnapshotError(ValueError):
    """Raised when a confirmed checkout does not retain a usable quote snapshot."""


def build_confirmed_purchase_payload(*, order, checkout_session):
    """Build the GTM purchase contract from the frozen checkout quote only."""
    quote_snapshot = getattr(checkout_session, "quote_snapshot", None)
    if not isinstance(quote_snapshot, dict):
        raise CheckoutAnalyticsSnapshotError("checkout_session.quote_snapshot is required")

    transaction_id = str(getattr(order, "locator", "") or getattr(order, "id", "")).strip()
    if not transaction_id:
        raise CheckoutAnalyticsSnapshotError("order.id or order.locator is required")

    lines = quote_snapshot.get("lines")
    if not isinstance(lines, list) or not lines:
        raise CheckoutAnalyticsSnapshotError("quote_snapshot.lines is required")

    return {
        "transaction_id": transaction_id,
        "value": _amount(quote_snapshot.get("total_amount"), "quote_snapshot.total_amount"),
        "currency": "EUR",
        "shipping": _amount(quote_snapshot.get("shipping_cost"), "quote_snapshot.shipping_cost"),
        "coupon": quote_snapshot.get("discount_code") or None,
        "items": [_build_item(line, index) for index, line in enumerate(lines, start=1)],
    }


def _build_item(line, index):
    if not isinstance(line, dict):
        raise CheckoutAnalyticsSnapshotError(f"quote_snapshot.lines[{index}] is invalid")

    item_id = line.get("product_id", line.get("producto_id"))
    item_name = line.get("product_name")
    if item_id is None or not str(item_name or "").strip():
        raise CheckoutAnalyticsSnapshotError(f"quote_snapshot.lines[{index}] is missing product data")

    quantity = line.get("quantity")
    if not isinstance(quantity, int) or quantity < 1:
        raise CheckoutAnalyticsSnapshotError(f"quote_snapshot.lines[{index}].quantity is invalid")

    return {
        "item_id": item_id,
        "item_name": str(item_name),
        "price": _amount(line.get("unit_price"), f"quote_snapshot.lines[{index}].unit_price"),
        "quantity": quantity,
    }


def _amount(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise CheckoutAnalyticsSnapshotError(f"{field} is invalid") from error

    if not amount.is_finite() or amount < 0:
        raise CheckoutAnalyticsSnapshotError(f"{field} is invalid")

    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

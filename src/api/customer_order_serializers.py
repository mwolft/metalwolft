from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


PUBLIC_ORDER_STATUS = {
    "pendiente": {"code": "pendiente", "label": "Pendiente"},
    "fabricacion": {"code": "fabricacion", "label": "En fabricación"},
    "pintura": {"code": "pintura", "label": "En pintura"},
    "embalaje": {"code": "embalaje", "label": "En embalaje"},
    "enviado": {"code": "enviado", "label": "Enviado"},
    "entregado": {"code": "entregado", "label": "Entregado"},
}

UNKNOWN_PUBLIC_ORDER_STATUS = {"code": "revision", "label": "En revisión"}


def public_order_status(order_status):
    status_code = str(order_status or "").strip().lower()
    return PUBLIC_ORDER_STATUS.get(status_code, UNKNOWN_PUBLIC_ORDER_STATUS).copy()


def serialize_customer_order_summary(order):
    return {
        "id": order.id,
        "reference": order.locator,
        "created_at": order.order_date.isoformat() if order.order_date else None,
        "total": _format_decimal_amount(order.total_amount),
        "currency": "EUR",
        "status": public_order_status(order.order_status),
    }


def _format_decimal_amount(value):
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        decimal_value = Decimal("0")

    return str(decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

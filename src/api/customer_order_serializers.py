from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from api.utils import DEFAULT_CONFIGURATOR_SCREW_OPTION, resolve_screw_configuration
from api.order_shipping import shipping_address_from_order_details


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
        "estimated_delivery_at": (
            order.estimated_delivery_at.isoformat()
            if order.estimated_delivery_at
            else None
        ),
    }


def serialize_customer_order_detail(order, invoice=None, *, invoice_pdf_available=False):
    return {
        **serialize_customer_order_summary(order),
        "shipping_address": _serialize_shipping_address(order.order_details),
        "lines": [
            _serialize_customer_order_line(detail)
            for detail in sorted(order.order_details, key=lambda item: item.id or 0)
        ],
        "invoice": _serialize_customer_order_invoice(invoice, invoice_pdf_available),
    }


def _serialize_shipping_address(order_details):
    address = shipping_address_from_order_details(order_details)
    return {
        "recipient": address.recipient,
        "address": address.address,
        "postal_code": address.postal_code,
        "city": address.city,
    }


def _serialize_customer_order_line(detail):
    screw_option = getattr(detail, "screw_option", None) or DEFAULT_CONFIGURATOR_SCREW_OPTION
    screw_length_mm = getattr(detail, "screw_length_mm", None)
    screw_supplement = getattr(detail, "screw_supplement", 0.0)
    if screw_length_mm is None:
        resolved_screws = resolve_screw_configuration(detail.anclaje, screw_option)
        if resolved_screws:
            screw_option = resolved_screws["screw_option"]
            screw_length_mm = resolved_screws["screw_length_mm"]
            screw_supplement = resolved_screws["screw_supplement"]

    return {
        "id": detail.id,
        "product_name": detail.product.nombre if detail.product else None,
        "quantity": detail.quantity,
        "configuration": {
            "alto": _format_optional_number(detail.alto),
            "ancho": _format_optional_number(detail.ancho),
            "color": detail.color,
            "anclaje": detail.anclaje,
            "screw_option": screw_option,
            "screw_length_mm": screw_length_mm,
            "screw_supplement": _format_decimal_amount(screw_supplement),
        },
    }


def _serialize_customer_order_invoice(invoice, invoice_pdf_available):
    if not invoice or not invoice_pdf_available:
        return {
            "available": False,
            "number": None,
            "issued_at": None,
        }

    return {
        "available": True,
        "number": invoice.invoice_number,
        "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
    }


def _format_decimal_amount(value):
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        decimal_value = Decimal("0")

    return str(decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _format_optional_number(value):
    if value is None:
        return None

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None

    normalized = decimal_value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f")

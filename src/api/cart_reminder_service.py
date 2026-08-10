from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from api.models import Cart, Orders
from api.transactional_email_renderer import (
    OrderEmailLine,
    TransactionalEmailRenderError,
    render_cart_reminder_email,
)
from api.utils import CONFIGURATOR_ANCHORAGES, CONFIGURATOR_COLORS, format_screw_configuration


class CartReminderIneligibleError(ValueError):
    """Raised when a manual cart reminder cannot safely be sent."""


class CartReminderDeliveryError(RuntimeError):
    """Raised when the mail transport does not accept a reminder."""


@dataclass(frozen=True)
class CartReminderEligibility:
    eligible: bool
    reason: str | None
    cart_items: tuple
    latest_cart_added_at: object | None
    later_order: object | None


def get_cart_reminder_eligibility(*, db_session, user):
    cart_items = tuple(
        db_session.query(Cart)
        .filter_by(usuario_id=user.id)
        .order_by(Cart.added_at.desc(), Cart.id.desc())
        .all()
    )
    latest_cart_added_at = next((item.added_at for item in cart_items if item.added_at), None)
    later_order = None
    if latest_cart_added_at:
        later_order = (
            db_session.query(Orders)
            .filter(Orders.user_id == user.id, Orders.order_date > latest_cart_added_at)
            .order_by(Orders.order_date.desc())
            .first()
        )

    return evaluate_cart_reminder_eligibility(
        user=user,
        cart_items=cart_items,
        latest_cart_added_at=latest_cart_added_at,
        later_order=later_order,
    )


def evaluate_cart_reminder_eligibility(*, user, cart_items, latest_cart_added_at, later_order):
    normalized_items = tuple(cart_items or ())
    if getattr(user, "is_admin", False):
        return CartReminderEligibility(False, "Los usuarios administradores no son elegibles.", (), None, None)
    if not str(getattr(user, "email", "") or "").strip():
        return CartReminderEligibility(False, "El usuario no tiene email registrado.", (), None, None)
    if not normalized_items:
        return CartReminderEligibility(False, "El usuario no tiene productos en el carrito.", (), None, None)
    if later_order is not None:
        return CartReminderEligibility(
            False,
            "El usuario ya tiene un pedido posterior al \u00faltimo movimiento del carrito.",
            normalized_items,
            latest_cart_added_at,
            later_order,
        )
    return CartReminderEligibility(True, None, normalized_items, latest_cart_added_at, None)


def send_manual_cart_reminder(*, db_session, user, cart_url, logger, send_email_func=None):
    eligibility = get_cart_reminder_eligibility(db_session=db_session, user=user)
    if not eligibility.eligible:
        raise CartReminderIneligibleError(eligibility.reason or "El carrito no es elegible.")

    if send_email_func is None:
        from api.email_routes import send_email

        send_email_func = send_email

    try:
        rendered_email = render_cart_reminder_email(
            customer_firstname=getattr(user, "firstname", None),
            lines=tuple(_build_cart_line(item) for item in eligibility.cart_items),
            subtotal=_cart_subtotal(eligibility.cart_items),
            cart_url=cart_url,
        )
    except TransactionalEmailRenderError as exc:
        raise CartReminderIneligibleError("El carrito no contiene datos v\u00e1lidos para el recordatorio.") from exc

    if not send_email_func(
        subject="Tu carrito sigue listo | MetalWolft",
        recipients=[user.email],
        body=rendered_email.text,
        html=rendered_email.html,
    ):
        raise CartReminderDeliveryError("No se pudo enviar el recordatorio del carrito.")

    logger.info(
        "Manual cart reminder sent user_id=%s line_count=%s",
        user.id,
        len(eligibility.cart_items),
    )
    return eligibility


def _build_cart_line(item):
    product = getattr(item, "product", None)
    product_name = getattr(product, "nombre", None) or f"Producto {item.producto_id}"
    screw_configuration = format_screw_configuration(
        getattr(item, "screw_length_mm", None),
        getattr(item, "screw_supplement", None),
    )
    return OrderEmailLine(
        product_name=str(product_name).strip(),
        quantity=_positive_quantity(getattr(item, "quantity", None)),
        measurements=_format_measurements(getattr(item, "alto", None), getattr(item, "ancho", None)),
        anchorage=_humanize_anchorage(getattr(item, "anclaje", None)),
        color=_humanize_color(getattr(item, "color", None)),
        screw_configuration=screw_configuration,
        line_total=_cart_line_total(item),
        image_url=_product_image_url(product),
        total_label="Total",
    )


def _cart_subtotal(cart_items):
    return sum((_cart_line_total(item) for item in cart_items), Decimal("0.00"))


def _cart_line_total(item):
    unit_amount = _money(getattr(item, "precio_total", None), "precio_total")
    return unit_amount * _positive_quantity(getattr(item, "quantity", None))


def _positive_quantity(value):
    if isinstance(value, bool):
        raise CartReminderIneligibleError("El carrito contiene una cantidad inv\u00e1lida.")
    try:
        quantity = int(value)
    except (TypeError, ValueError) as exc:
        raise CartReminderIneligibleError("El carrito contiene una cantidad inv\u00e1lida.") from exc
    if quantity < 1:
        raise CartReminderIneligibleError("El carrito contiene una cantidad inv\u00e1lida.")
    return quantity


def _money(value, field_name):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CartReminderIneligibleError(f"El carrito contiene {field_name} inv\u00e1lido.") from exc
    if not amount.is_finite() or amount < 0:
        raise CartReminderIneligibleError(f"El carrito contiene {field_name} inv\u00e1lido.")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _format_measurements(alto, ancho):
    if alto is None or ancho is None:
        return "-"
    return f"{_format_measurement(alto)} \u00d7 {_format_measurement(ancho)} cm"


def _format_measurement(value):
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value).strip()
    return format(normalized.normalize(), "f") if normalized.is_finite() else str(value).strip()


def _humanize_anchorage(value):
    normalized = str(value or "").strip()
    rule = CONFIGURATOR_ANCHORAGES.get(normalized)
    return str(rule.get("name") or rule.get("label") or normalized).strip() if rule else (normalized or "-")


def _humanize_color(value):
    normalized = str(value or "").strip()
    rule = CONFIGURATOR_COLORS.get(normalized)
    return str(rule.get("label") or rule.get("name") or normalized).strip() if rule else (normalized or "-")


def _product_image_url(product):
    image_url = str(getattr(product, "imagen", "") or "").strip()
    return image_url if image_url.startswith(("https://", "http://")) else None

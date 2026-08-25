from decimal import Decimal, InvalidOperation

from api.transactional_email_renderer import (
    OrderEmailLine,
    render_order_confirmation_email,
)
from api.order_shipping import shipping_address_from_customer_snapshot
from api.utils import (
    CONFIGURATOR_ANCHORAGES,
    CONFIGURATOR_COLORS,
    format_screw_configuration,
)


def _format_measurements(line):
    alto = line.get("alto")
    ancho = line.get("ancho")
    if alto is None or ancho is None:
        return "-"
    return f"{_format_measurement(alto)} × {_format_measurement(ancho)} cm"


def _format_measurement(value):
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value).strip()
    if not normalized.is_finite():
        return str(value).strip()
    return format(normalized.normalize(), "f")


def _humanize_anchorage(value):
    normalized = str(value or "").strip()
    if not normalized:
        return "-"
    rule = CONFIGURATOR_ANCHORAGES.get(normalized)
    if not rule:
        return normalized
    return str(rule.get("name") or rule.get("label") or normalized).strip()


def _humanize_color(value):
    normalized = str(value or "").strip()
    if not normalized:
        return "-"
    rule = CONFIGURATOR_COLORS.get(normalized)
    if not rule:
        return normalized
    return str(rule.get("label") or rule.get("name") or normalized).strip()


def _format_color_with_finish(value):
    color = _humanize_color(value)
    return f"{color} · Esmalte sintético" if color != "-" else color


def _build_order_line(line):
    product_name = (
        line.get("product_name")
        or line.get("nombre")
        or f"Producto {line.get('product_id') or line.get('producto_id')}"
    )
    screw_configuration = format_screw_configuration(
        line.get("screw_length_mm"),
        line.get("screw_supplement"),
    )

    return OrderEmailLine(
        product_name=str(product_name).strip(),
        quantity=line.get("quantity", 1),
        measurements=_format_measurements(line),
        anchorage=(
            "" if (line.get("line_type") or "physical") == "design_service"
            else _humanize_anchorage(line.get("anclaje"))
        ),
        color=_format_color_with_finish(line.get("color")),
        screw_configuration=screw_configuration,
        line_total=line.get("line_total"),
        line_type=line.get("line_type") or "physical",
    )


def _build_order_confirmation_email(
    *, order, checkout_quote, customer_firstname, customer_snapshot=None
):
    lines = tuple(
        _build_order_line(line)
        for line in (checkout_quote.get("lines") or [])
    )
    is_design_service = bool(lines) and all(line.line_type == "design_service" for line in lines)
    return render_order_confirmation_email(
        order_reference=order.locator,
        customer_firstname=customer_firstname,
        lines=lines,
        subtotal=checkout_quote.get("subtotal"),
        shipping_cost=checkout_quote.get("shipping_cost"),
        discount_amount=checkout_quote.get("discount_amount"),
        total_amount=order.total_amount,
        shipping_address=None if is_design_service else shipping_address_from_customer_snapshot(customer_snapshot),
        is_design_service=is_design_service,
    )


def send_order_confirmation_email(
    *,
    user,
    order,
    checkout_quote,
    customer_firstname,
    customer_snapshot=None,
    mail_username,
    logger,
    send_email_func=None,
):
    if send_email_func is None:
        from api.email_routes import send_email

        send_email_func = send_email

    try:
        logger.info(
            "Enviando correo de confirmación para el pedido %s.",
            order.locator,
        )
        rendered_email = _build_order_confirmation_email(
            order=order,
            checkout_quote=checkout_quote,
            customer_firstname=customer_firstname,
            customer_snapshot=customer_snapshot,
        )
        email_sent = send_email_func(
            subject=f"Hemos recibido tu pedido {order.locator}",
            recipients=[user.email, mail_username],
            body=rendered_email.text,
            html=rendered_email.html,
        )
        if not email_sent:
            logger.error(
                "Error al enviar el correo de confirmación del pedido %s.",
                order.locator,
            )
        else:
            logger.info(
                "Correo de confirmación enviado correctamente para el pedido %s.",
                order.locator,
            )
    except Exception as exc:
        logger.error(
            "Error al preparar o enviar el correo de confirmación del pedido %s "
            "(tipo=%s).",
            order.locator,
            type(exc).__name__,
        )

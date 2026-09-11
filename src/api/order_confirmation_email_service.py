from decimal import Decimal, InvalidOperation

from flask import has_app_context
from sqlalchemy.orm import selectinload

from api.models import Products

from api.transactional_email_renderer import (
    OrderEmailLine,
    render_order_confirmation_email,
)
from api.order_confirmation_context import (
    get_order_confirmation_customer_firstname,
    get_order_confirmation_recipient_email,
    get_order_customer_snapshot,
    get_order_quote_snapshot,
)
from api.order_shipping import shipping_address_from_customer_snapshot
from api.utils import (
    CONFIGURATOR_ANCHORAGES,
    CONFIGURATOR_COLORS,
    format_screw_configuration,
)


def _format_measurements(line, *, include_labels=False):
    alto = line.get("alto")
    ancho = line.get("ancho")
    if alto is None or ancho is None:
        return "-"
    formatted_alto = _format_measurement(alto)
    formatted_ancho = _format_measurement(ancho)
    if include_labels:
        return f"Alto: {formatted_alto} cm · Ancho: {formatted_ancho} cm"
    return f"{formatted_alto} × {formatted_ancho} cm"


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


def _build_order_line(line, *, image_url=None):
    product_name = (
        line.get("product_name")
        or line.get("nombre")
        or f"Producto {line.get('product_id') or line.get('producto_id')}"
    )
    screw_configuration = format_screw_configuration(
        line.get("screw_length_mm"),
        line.get("screw_supplement"),
    )

    line_type = line.get("line_type") or "physical"
    return OrderEmailLine(
        product_name=str(product_name).strip(),
        quantity=line.get("quantity", 1),
        measurements=_format_measurements(
            line,
            include_labels=line_type == "physical",
        ),
        anchorage=(
            "" if line_type == "design_service"
            else _humanize_anchorage(line.get("anclaje"))
        ),
        color=_format_color_with_finish(line.get("color")),
        screw_configuration=screw_configuration,
        line_total=line.get("line_total"),
        image_url=image_url,
        image_width=96 if image_url else None,
        line_type=line_type,
    )


def _build_order_confirmation_email(
    *, order, checkout_quote, customer_firstname, customer_snapshot=None
):
    quote_lines = tuple(checkout_quote.get("lines") or [])
    image_urls = _order_line_image_urls(quote_lines)
    lines = tuple(
        _build_order_line(line, image_url=image_urls.get(index))
        for index, line in enumerate(quote_lines)
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


def _order_line_image_urls(lines):
    """Resolve frozen image URLs first, then the current stable product image."""
    resolved = {}
    product_ids = set()

    for index, line in enumerate(lines):
        image_url = _frozen_line_image_url(line)
        if image_url:
            resolved[index] = image_url
            continue
        product_id = _line_product_id(line)
        if product_id is not None:
            product_ids.add(product_id)

    if not product_ids or not has_app_context():
        return resolved

    products = (
        Products.query.options(selectinload(Products.images))
        .filter(Products.id.in_(product_ids))
        .all()
    )
    product_image_urls = {
        product.id: _product_image_url(product)
        for product in products
    }
    for index, line in enumerate(lines):
        if index in resolved:
            continue
        image_url = product_image_urls.get(_line_product_id(line))
        if image_url:
            resolved[index] = image_url
    return resolved


def _frozen_line_image_url(line):
    for field_name in ("image_url", "product_image_url", "imagen"):
        image_url = _valid_image_url(line.get(field_name))
        if image_url:
            return image_url
    return None


def _line_product_id(line):
    value = line.get("product_id", line.get("producto_id"))
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _product_image_url(product):
    image_url = _valid_image_url(getattr(product, "imagen", None))
    if image_url:
        return image_url
    for image in getattr(product, "images", ()) or ():
        image_url = _valid_image_url(getattr(image, "image_url", None))
        if image_url:
            return image_url
    return None


def _valid_image_url(value):
    normalized = str(value or "").strip()
    return normalized if normalized.startswith(("https://", "http://")) else None


def send_order_confirmation_email(
    *,
    user=None,
    order,
    checkout_quote=None,
    customer_firstname=None,
    customer_snapshot=None,
    mail_username,
    logger,
    send_email_func=None,
):
    if send_email_func is None:
        from api.email_routes import send_email

        send_email_func = send_email

    try:
        resolved_quote = get_order_quote_snapshot(order) or checkout_quote or {}
        resolved_customer_snapshot = (
            get_order_customer_snapshot(order) or customer_snapshot or {}
        )
        recipient_email = (
            get_order_confirmation_recipient_email(order)
            or _normalized_text(getattr(user, "email", None))
        )
        resolved_customer_firstname = (
            get_order_confirmation_customer_firstname(order)
            or _normalized_text(customer_firstname)
        )
        if not recipient_email:
            raise ValueError("No hay un email de destinatario para el pedido confirmado.")

        logger.info(
            "Enviando correo de confirmación para el pedido %s.",
            order.locator,
        )
        rendered_email = _build_order_confirmation_email(
            order=order,
            checkout_quote=resolved_quote,
            customer_firstname=resolved_customer_firstname,
            customer_snapshot=resolved_customer_snapshot,
        )
        is_design_service = bool(resolved_quote.get("lines")) and all(
            (line.get("line_type") or "physical") == "design_service"
            for line in resolved_quote["lines"]
        )
        email_sent = send_email_func(
            subject=(
                f"Hemos recibido tu solicitud de diseño {order.locator}"
                if is_design_service
                else f"Hemos recibido tu pedido {order.locator}"
            ),
            recipients=[recipient_email, mail_username],
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


def _normalized_text(value):
    return str(value or "").strip()

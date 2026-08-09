from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from html import escape


BRAND_NAME = "MetalWolft"
BRAND_TAGLINE = "Rejas para ventanas a medida"
COLOR_TEXT = "#1f2937"
COLOR_MUTED = "#6b7280"
COLOR_BORDER = "#e5e7eb"
COLOR_SURFACE_ALT = "#fff6f7"
COLOR_ACCENT = "#cf1c35"


class TransactionalEmailRenderError(ValueError):
    """Raised when required presentation data is missing or invalid."""


@dataclass(frozen=True)
class RenderedEmail:
    text: str
    html: str


@dataclass(frozen=True)
class OrderEmailLine:
    product_name: str
    quantity: object
    measurements: str
    anchorage: str
    color: str
    screw_configuration: str
    line_total: object
    image_url: str | None = None
    total_label: str | None = None


def render_order_confirmation_email(
    *,
    order_reference,
    customer_firstname,
    lines,
    subtotal,
    shipping_cost,
    discount_amount,
    total_amount,
):
    order_reference_text = _required_text(order_reference, "order_reference")
    customer_name = _text(customer_firstname)
    normalized_lines = tuple(lines or ())

    subtotal_text = _format_money(subtotal, "subtotal")
    shipping_value = _required_decimal(shipping_cost, "shipping_cost")
    shipping_text = "GRATIS" if shipping_value == 0 else _format_decimal_money(shipping_value)
    discount_value = _optional_decimal(discount_amount, "discount_amount")
    discount_text = _format_decimal_money(discount_value)
    total_text = _format_money(total_amount, "total_amount")

    rendered_lines = tuple(_render_order_line(line) for line in normalized_lines)
    greeting = f"Hola {customer_name}," if customer_name else "Hola,"

    plain_lines = "\n\n".join(line[0] for line in rendered_lines)
    if not plain_lines:
        plain_lines = "Pedido sin líneas disponibles."

    totals = [
        f"Subtotal: {subtotal_text}",
        f"Envío: {shipping_text}",
    ]
    if discount_value > 0:
        totals.append(f"Descuento: −{discount_text}")
    totals.append(f"TOTAL: {total_text}")
    totals_text = "\n".join(totals)

    text_body = (
        "METALWOLFT\n"
        f"{BRAND_TAGLINE}\n\n"
        f"{greeting}\n\n"
        "¡Gracias por tu pedido!\n\n"
        f"Hemos recibido correctamente tu pedido {order_reference_text}.\n\n"
        f"Pedido: {order_reference_text}\n"
        "Estado del pago: confirmado\n\n"
        "RESUMEN DEL PEDIDO\n\n"
        f"{plain_lines}\n\n"
        f"{totals_text}\n\n"
        "Ahora comenzaremos a preparar y fabricar tu pedido.\n"
        "Te informaremos cuando avance su estado.\n\n"
        "Gracias por confiar en MetalWolft.\n\n"
        "MetalWolft\n"
        "Fabricación de rejas a medida"
    )

    lines_html = "".join(line[1] for line in rendered_lines)
    if not lines_html:
        lines_html = (
            '<p style="margin:0;color:#6b7280;font-size:14px;line-height:1.6;">'
            "Pedido sin líneas disponibles."
            "</p>"
        )

    discount_row = ""
    if discount_value > 0:
        discount_row = _render_total_row("Descuento", f"−{discount_text}")

    content_html = (
        f'<p style="margin:0 0 18px;color:{COLOR_MUTED};font-size:15px;line-height:1.6;">'
        f"{_html(greeting)}"
        "</p>"
        f'<h1 style="margin:0 0 10px;color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;'
        'font-size:28px;line-height:1.2;font-weight:700;">¡Gracias por tu pedido!</h1>'
        f'<p style="margin:0 0 22px;color:{COLOR_TEXT};font-size:16px;line-height:1.6;">'
        f"Hemos recibido correctamente tu pedido <strong>{_html(order_reference_text)}</strong>."
        "</p>"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="width:100%;margin:0 0 28px;border-collapse:separate;">'
        "<tr>"
        f'<td style="padding:10px 12px;background:{COLOR_SURFACE_ALT};border:1px solid {COLOR_BORDER};'
        f'color:{COLOR_TEXT};font-size:14px;line-height:1.3;font-weight:600;">'
        f"Pedido {_html(order_reference_text)}</td>"
        '<td width="10" style="width:10px;font-size:0;line-height:0;">&nbsp;</td>'
        f'<td style="padding:10px 12px;background:{COLOR_SURFACE_ALT};border:1px solid {COLOR_BORDER};'
        f'color:{COLOR_TEXT};font-size:14px;line-height:1.3;font-weight:600;">Pago confirmado</td>'
        "</tr></table>"
        f'<h2 style="margin:0 0 12px;color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;'
        'font-size:14px;line-height:1.4;font-weight:700;letter-spacing:0.08em;">RESUMEN DEL PEDIDO</h2>'
        f"{lines_html}"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;margin:20px 0 24px;border-top:1px solid {COLOR_BORDER};border-collapse:collapse;">'
        f"{_render_total_row('Subtotal', subtotal_text)}"
        f"{_render_total_row('Envío', shipping_text)}"
        f"{discount_row}"
        f"{_render_total_row('TOTAL', total_text, emphasized=True)}"
        "</table>"
        f'<div style="padding:18px;background:{COLOR_SURFACE_ALT};border-left:3px solid {COLOR_ACCENT};">'
        f'<p style="margin:0 0 5px;color:{COLOR_TEXT};font-size:15px;line-height:1.5;font-weight:600;">'
        "Ahora comenzaremos a preparar y fabricar tu pedido.</p>"
        f'<p style="margin:0;color:{COLOR_MUTED};font-size:14px;line-height:1.5;">'
        "Te informaremos cuando avance su estado.</p>"
        "</div>"
    )

    return RenderedEmail(
        text=text_body,
        html=_render_shell(
            preheader=f"Hemos recibido correctamente tu pedido {order_reference_text}.",
            content_html=content_html,
        ),
    )


def render_cart_reminder_email(*, customer_firstname, lines, subtotal, cart_url):
    customer_name = _text(customer_firstname)
    cart_url_text = _required_text(cart_url, "cart_url")
    subtotal_text = _format_money(subtotal, "subtotal")
    rendered_lines = tuple(_render_order_line(line) for line in tuple(lines or ()))
    if not rendered_lines:
        raise TransactionalEmailRenderError("El carrito no contiene l\u00edneas disponibles.")

    greeting = f"Hola {customer_name}," if customer_name else "Hola,"
    plain_lines = "\n\n".join(line[0] for line in rendered_lines)
    lines_html = "".join(line[1] for line in rendered_lines)

    text_body = (
        "METALWOLFT\n"
        f"{BRAND_TAGLINE}\n\n"
        f"{greeting}\n\n"
        "Tu carrito sigue listo.\n\n"
        "Hemos guardado la configuraci\u00f3n de los productos que a\u00f1adiste.\n\n"
        "RESUMEN DEL CARRITO\n\n"
        f"{plain_lines}\n\n"
        f"Subtotal de productos guardados: {subtotal_text}\n\n"
        f"Volver a mi carrito: {cart_url_text}\n\n"
        "Si necesitas revisar las medidas o la instalaci\u00f3n, estaremos encantados de ayudarte.\n\n"
        "MetalWolft\n"
        "Fabricaci\u00f3n de rejas a medida"
    )

    content_html = (
        f'<p style="margin:0 0 18px;color:{COLOR_MUTED};font-size:15px;line-height:1.6;">'
        f"{_html(greeting)}"
        "</p>"
        f'<h1 style="margin:0 0 12px;color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;'
        'font-size:27px;line-height:1.2;font-weight:700;">Tu carrito sigue listo</h1>'
        f'<p style="margin:0 0 24px;color:{COLOR_TEXT};font-size:16px;line-height:1.6;">'
        "Hemos guardado la configuraci\u00f3n de los productos que a\u00f1adiste."
        "</p>"
        f'<h2 style="margin:0 0 12px;color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;'
        'font-size:14px;line-height:1.4;font-weight:700;letter-spacing:0.08em;">RESUMEN DEL CARRITO</h2>'
        f"{lines_html}"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;margin:20px 0 24px;border-top:1px solid {COLOR_BORDER};border-collapse:collapse;">'
        f"{_render_total_row('Subtotal de productos guardados', subtotal_text, emphasized=True)}"
        "</table>"
        f'<a href="{_html(cart_url_text)}" '
        f'style="display:inline-block;background:{COLOR_ACCENT};color:#ffffff;text-decoration:none;font-size:16px;'
        'font-weight:700;padding:13px 22px;border-radius:999px;">Volver a mi carrito</a>'
        f'<p style="margin:22px 0 0;color:{COLOR_MUTED};font-size:14px;line-height:1.6;">'
        "Si necesitas revisar las medidas o la instalaci\u00f3n, estaremos encantados de ayudarte."
        "</p>"
    )

    return RenderedEmail(
        text=text_body,
        html=_render_shell(
            preheader="Tu carrito sigue listo para cuando quieras continuar.",
            content_html=content_html,
        ),
    )


def render_invoice_delivery_email(
    *,
    invoice_number,
    order_reference,
    trade_name,
    customer_name=None,
    original_invoice_number=None,
):
    invoice_number_text = _required_text(invoice_number, "invoice_number")
    order_reference_text = _text(order_reference)
    trade_name_text = _text(trade_name) or BRAND_NAME
    customer_name_text = _text(customer_name)
    original_invoice_number_text = _text(original_invoice_number)
    greeting = f"Hola {customer_name_text}," if customer_name_text else "Hola,"

    if order_reference_text:
        attachment_sentence = (
            f"Adjuntamos la factura correspondiente a tu pedido {order_reference_text}."
        )
        order_plain = f"Pedido: {order_reference_text}\n"
        order_html = _render_invoice_detail_row("Pedido", order_reference_text)
    else:
        attachment_sentence = "Adjuntamos tu factura en formato PDF."
        order_plain = ""
        order_html = ""

    is_rectification = bool(original_invoice_number_text)
    invoice_label = "Factura rectificativa" if is_rectification else "Factura"
    if is_rectification:
        attachment_sentence = "Adjuntamos la factura rectificativa en formato PDF."
    original_plain = (
        f"Factura original rectificada: {original_invoice_number_text}\n"
        if is_rectification
        else ""
    )
    original_html = (
        _render_invoice_detail_row(
            "Factura original rectificada",
            original_invoice_number_text,
        )
        if is_rectification
        else ""
    )

    text_body = (
        "METALWOLFT\n"
        f"{BRAND_TAGLINE}\n\n"
        f"{greeting}\n\n"
        f"Tu {invoice_label.lower()} {invoice_number_text}\n\n"
        f"{attachment_sentence}\n\n"
        f"{invoice_label}: {invoice_number_text}\n"
        f"{original_plain}"
        f"{order_plain}"
        "Documento: PDF adjunto\n\n"
        f"Gracias por confiar en {trade_name_text}.\n\n"
        "MetalWolft\n"
        "Fabricación de rejas a medida"
    )

    content_html = (
        f'<p style="margin:0 0 18px;color:{COLOR_MUTED};font-size:15px;line-height:1.6;">'
        f"{_html(greeting)}"
        "</p>"
        f'<h1 style="margin:0 0 12px;color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;'
        f'font-size:27px;line-height:1.2;font-weight:700;">Tu {_html(invoice_label.lower())} {_html(invoice_number_text)}</h1>'
        f'<p style="margin:0 0 24px;color:{COLOR_TEXT};font-size:16px;line-height:1.6;">'
        f"{_html(attachment_sentence)}"
        "</p>"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;margin:0 0 24px;background:{COLOR_SURFACE_ALT};border:1px solid {COLOR_BORDER};'
        'border-collapse:collapse;">'
        f"{_render_invoice_detail_row(invoice_label, invoice_number_text)}"
        f"{original_html}"
        f"{order_html}"
        f"{_render_invoice_detail_row('Documento', 'PDF adjunto')}"
        "</table>"
        f'<p style="margin:0;color:{COLOR_TEXT};font-size:15px;line-height:1.6;">'
        f"Gracias por confiar en {_html(trade_name_text)}."
        "</p>"
    )

    return RenderedEmail(
        text=text_body,
        html=_render_shell(
            preheader=(
                f"Tu factura rectificativa {invoice_number_text} está adjunta en formato PDF."
                if is_rectification
                else f"Tu factura {invoice_number_text} está adjunta en formato PDF."
            ),
            content_html=content_html,
        ),
    )


def _render_order_line(line):
    if not isinstance(line, OrderEmailLine):
        raise TransactionalEmailRenderError("Línea de pedido no válida.")

    product_name = _required_text(line.product_name, "product_name")
    quantity = _text(line.quantity) or "1"
    measurements = _text(line.measurements) or "-"
    anchorage = _text(line.anchorage) or "-"
    color = _text(line.color) or "-"
    screw_configuration = _text(line.screw_configuration) or "-"
    line_total = _format_money(line.line_total, "line_total")
    image_url = _email_image_url(line.image_url)
    total_label = _text(line.total_label)
    text_total_label = total_label or "Importe"
    html_total_label = total_label or "Importe de línea"

    plain = (
        f"{product_name} ×{quantity}\n"
        f"Medidas: {measurements}\n"
        f"Instalación: {anchorage}\n"
        f"Color: {color}\n"
        f"Tornillos: {screw_configuration}\n"
        f"Cantidad: {quantity}\n"
        f"{text_total_label}: {line_total}"
    )

    image_cell = ""
    if image_url:
        image_cell = (
            f'<td valign="top" width="64" style="width:64px;padding:16px 12px 4px 0;">'
            f'<img src="{_html(image_url)}" alt="" width="56" height="56" '
            'style="display:block;width:56px;height:56px;border:0;border-radius:6px;object-fit:cover;" '
            'loading="lazy"></td>'
        )

    html = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;border-top:1px solid {COLOR_BORDER};border-collapse:collapse;">'
        "<tr>"
        f"{image_cell}"
        f'<td style="padding:16px 0 4px;color:{COLOR_TEXT};font-size:16px;line-height:1.4;font-weight:700;'
        'word-break:break-word;">'
        f"{_html(product_name)}</td>"
        f'<td align="right" valign="top" style="padding:16px 0 4px 12px;color:{COLOR_TEXT};'
        f'font-size:15px;line-height:1.4;font-weight:600;white-space:nowrap;">×{_html(quantity)}</td>'
        "</tr><tr>"
        f'<td colspan="{3 if image_cell else 2}" style="padding:0 0 5px;color:{COLOR_MUTED};font-size:14px;line-height:1.55;">'
        f"{_html(measurements)} · {_html(anchorage)}<br>"
        f"{_html(color)}<br>"
        f"Tornillos {_html(screw_configuration)}"
        "</td></tr><tr>"
        f'<td colspan="{2 if image_cell else 1}" style="padding:4px 0 16px;color:{COLOR_MUTED};font-size:13px;line-height:1.4;">'
        f"{_html(html_total_label)}</td>"
        f'<td align="right" style="padding:4px 0 16px 12px;color:{COLOR_TEXT};font-size:15px;'
        f'line-height:1.4;font-weight:700;white-space:nowrap;">{_html(line_total)}</td>'
        "</tr></table>"
    )
    return plain, html


def _render_total_row(label, value, emphasized=False):
    if emphasized:
        return (
            "<tr>"
            f'<td style="padding:16px 0 4px;border-top:2px solid {COLOR_TEXT};color:{COLOR_TEXT};'
            'font-size:17px;line-height:1.4;font-weight:700;">TOTAL</td>'
            f'<td align="right" style="padding:16px 0 4px;border-top:2px solid {COLOR_TEXT};'
            f'color:{COLOR_ACCENT};font-size:20px;line-height:1.4;font-weight:700;white-space:nowrap;">'
            f"{_html(value)}</td>"
            "</tr>"
        )
    return (
        "<tr>"
        f'<td style="padding:9px 0;color:{COLOR_MUTED};font-size:14px;line-height:1.4;">'
        f"{_html(label)}</td>"
        f'<td align="right" style="padding:9px 0;color:{COLOR_TEXT};font-size:14px;line-height:1.4;'
        f'font-weight:600;white-space:nowrap;">{_html(value)}</td>'
        "</tr>"
    )


def _render_invoice_detail_row(label, value):
    return (
        "<tr>"
        f'<td valign="top" style="width:34%;padding:13px 16px;border-bottom:1px solid {COLOR_BORDER};'
        f'color:{COLOR_MUTED};font-size:13px;line-height:1.4;">{_html(label)}</td>'
        f'<td valign="top" style="padding:13px 16px;border-bottom:1px solid {COLOR_BORDER};'
        f'color:{COLOR_TEXT};font-size:14px;line-height:1.4;font-weight:600;word-break:break-word;">'
        f"{_html(value)}</td>"
        "</tr>"
    )


def _render_shell(*, preheader, content_html):
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{_html(BRAND_NAME)}</title></head>'
        f'<body style="margin:0;padding:0;background:{COLOR_SURFACE_ALT};color:{COLOR_TEXT};'
        'font-family:Arial,Helvetica,sans-serif;-webkit-text-size-adjust:100%;">'
        f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">'
        f"{_html(preheader)}&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;</div>"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;background:{COLOR_SURFACE_ALT};border-collapse:collapse;">'
        '<tr><td align="center" style="padding:24px 12px;">'
        '<table role="presentation" width="620" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;max-width:620px;background:#ffffff;border:1px solid {COLOR_BORDER};'
        'border-radius:12px;overflow:hidden;border-collapse:separate;">'
        f'<tr><td style="height:4px;background:{COLOR_ACCENT};font-size:0;line-height:0;">&nbsp;</td></tr>'
        '<tr><td style="padding:24px 28px 20px;">'
        f'<div style="color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;font-size:22px;'
        'line-height:1.1;font-weight:800;letter-spacing:0.04em;">METAL'
        f'<span style="color:{COLOR_ACCENT};">WOLFT</span></div>'
        f'<div style="margin-top:5px;color:{COLOR_MUTED};font-size:12px;line-height:1.4;">'
        f"{_html(BRAND_TAGLINE)}</div>"
        "</td></tr>"
        f'<tr><td style="padding:4px 28px 30px;">{content_html}</td></tr>'
        f'<tr><td style="padding:20px 28px;background:{COLOR_SURFACE_ALT};border-top:1px solid {COLOR_BORDER};">'
        f'<p style="margin:0 0 4px;color:{COLOR_TEXT};font-size:13px;line-height:1.4;font-weight:700;">'
        "MetalWolft</p>"
        f'<p style="margin:0;color:{COLOR_MUTED};font-size:12px;line-height:1.5;">'
        "Fabricación de rejas a medida</p>"
        "</td></tr></table>"
        "</td></tr></table>"
        "</body></html>"
    )


def _format_money(value, field_name):
    return _format_decimal_money(_required_decimal(value, field_name))


def _format_decimal_money(value):
    sign = "−" if value < 0 else ""
    raw = f"{abs(value):,.2f}"
    localized = raw.replace(",", "\0").replace(".", ",").replace("\0", ".")
    return f"{sign}{localized} €"


def _required_decimal(value, field_name):
    if value is None or isinstance(value, bool):
        raise TransactionalEmailRenderError(f"Falta el importe requerido: {field_name}.")
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise TransactionalEmailRenderError(
            f"Importe no válido para {field_name}."
        ) from exc
    if not normalized.is_finite():
        raise TransactionalEmailRenderError(f"Importe no válido para {field_name}.")
    return normalized


def _optional_decimal(value, field_name):
    if value is None:
        return Decimal("0")
    return _required_decimal(value, field_name)


def _required_text(value, field_name):
    normalized = _text(value)
    if not normalized:
        raise TransactionalEmailRenderError(f"Falta el texto requerido: {field_name}.")
    return normalized


def _email_image_url(value):
    normalized = _text(value)
    return normalized if normalized.startswith(("https://", "http://")) else ""


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _html(value):
    return escape(_text(value), quote=True)

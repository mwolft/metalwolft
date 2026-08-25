from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from html import escape

from api.order_shipping import ShippingAddress, shipping_address_lines


BRAND_NAME = "MetalWolft"
BRAND_TAGLINE = "Rejas para ventanas a medida"
COLOR_TEXT = "#1f2937"
COLOR_MUTED = "#6b7280"
COLOR_BORDER = "#e5e7eb"
COLOR_SURFACE_ALT = "#fff6f7"
COLOR_ACCENT = "#cf1c35"
INSTALLATION_GUIDE_URL = "https://www.metalwolft.com/instalation-rejas-para-ventanas"
MAINTENANCE_GUIDE_URL = "https://www.metalwolft.com/mantenimiento-acabado-rejas-metalicas"
RECEIPT_GUIDE_URL = "https://www.metalwolft.com/recepcion-pedidos-revisar-antes-firmar"
INCIDENT_FORM_URL = "https://www.metalwolft.com/formulario-incidencias"


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
    screw_configuration: str | None
    line_total: object
    image_url: str | None = None
    total_label: str | None = None
    line_type: str = "physical"


def render_order_confirmation_email(
    *,
    order_reference,
    customer_firstname,
    lines,
    subtotal,
    shipping_cost,
    discount_amount,
    total_amount,
    shipping_address=None,
    is_design_service=False,
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

    totals = [f"Subtotal: {subtotal_text}"]
    if not is_design_service:
        totals.append(f"Envío: {shipping_text}")
    if discount_value > 0:
        totals.append(f"Descuento: −{discount_text}")
    totals.append(f"TOTAL: {total_text}")
    totals_text = "\n".join(totals)
    shipping_text_body = "" if is_design_service else _render_order_shipping_text(shipping_address)
    confirmation_title = "Hemos recibido tu solicitud de diseño" if is_design_service else "¡Gracias por tu pedido!"
    confirmation_message = (
        "Hemos recibido correctamente tu solicitud de diseño previo. "
        "Te avisaremos cuando esté preparada."
        if is_design_service
        else "Ahora comenzaremos a preparar y fabricar tu pedido.\nTe informaremos cuando avance su estado."
    )

    text_body = (
        "METALWOLFT\n"
        f"{BRAND_TAGLINE}\n\n"
        f"{greeting}\n\n"
        f"{confirmation_title}\n\n"
        f"Hemos recibido correctamente tu pedido {order_reference_text}.\n\n"
        f"Pedido: {order_reference_text}\n"
        "Estado del pago: confirmado\n\n"
        "RESUMEN DEL PEDIDO\n\n"
        f"{plain_lines}\n\n"
        f"{totals_text}\n\n"
        f"{shipping_text_body}"
        f"{confirmation_message}\n\n"
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

    shipping_html = "" if is_design_service else _render_order_shipping_html(shipping_address)
    shipping_total_row = "" if is_design_service else _render_total_row("Envío", shipping_text)
    html_title = "Hemos recibido tu solicitud de diseño" if is_design_service else "¡Gracias por tu pedido!"
    html_confirmation = (
        "Hemos recibido correctamente tu solicitud de diseño previo. Te avisaremos cuando esté preparada."
        if is_design_service
        else "Hemos recibido correctamente tu pedido"
    )
    html_next_step = (
        "Revisaremos la configuración solicitada y te avisaremos cuando el diseño esté preparado."
        if is_design_service
        else "Ahora comenzaremos a preparar y fabricar tu pedido."
    )
    html_next_detail = "" if is_design_service else "Te informaremos cuando avance su estado."

    content_html = (
        f'<p style="margin:0 0 18px;color:{COLOR_MUTED};font-size:15px;line-height:1.6;">'
        f"{_html(greeting)}"
        "</p>"
        f'<h1 style="margin:0 0 10px;color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;'
        f'font-size:28px;line-height:1.2;font-weight:700;">{_html(html_title)}</h1>'
        f'<p style="margin:0 0 22px;color:{COLOR_TEXT};font-size:16px;line-height:1.6;">'
        f"{_html(html_confirmation)} <strong>{_html(order_reference_text)}</strong>."
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
        f"{shipping_total_row}"
        f"{discount_row}"
        f"{_render_total_row('TOTAL', total_text, emphasized=True)}"
        "</table>"
        f"{shipping_html}"
        f'<div style="padding:18px;background:{COLOR_SURFACE_ALT};border-left:3px solid {COLOR_ACCENT};">'
        f'<p style="margin:0 0 5px;color:{COLOR_TEXT};font-size:15px;line-height:1.5;font-weight:600;">'
        f"{_html(html_next_step)}</p>"
        f'<p style="margin:0;color:{COLOR_MUTED};font-size:14px;line-height:1.5;">'
        f"{_html(html_next_detail)}</p>"
        "</div>"
    )

    return RenderedEmail(
        text=text_body,
        html=_render_shell(
            preheader=f"Hemos recibido correctamente tu pedido {order_reference_text}.",
            content_html=content_html,
        ),
    )


def _render_order_shipping_text(shipping_address):
    if not isinstance(shipping_address, ShippingAddress) or not shipping_address.is_available:
        return ""
    if shipping_address.same_as_billing:
        return "DIRECCI\u00d3N DE ENV\u00cdO\nMisma que la direcci\u00f3n de facturaci\u00f3n.\n\n"
    return "DIRECCI\u00d3N DE ENV\u00cdO\n" + "\n".join(shipping_address_lines(shipping_address)) + "\n\n"


def _render_order_shipping_html(shipping_address):
    if not isinstance(shipping_address, ShippingAddress) or not shipping_address.is_available:
        return ""
    if shipping_address.same_as_billing:
        details = "Misma que la direcci\u00f3n de facturaci\u00f3n."
    else:
        details = "<br>".join(_html(line) for line in shipping_address_lines(shipping_address))
    return (
        f'<div style="margin:0 0 24px;padding:16px;background:{COLOR_SURFACE_ALT};border:1px solid {COLOR_BORDER};">'
        f'<p style="margin:0 0 6px;color:{COLOR_TEXT};font-size:13px;line-height:1.4;font-weight:700;letter-spacing:0.08em;">DIRECCI\u00d3N DE ENV\u00cdO</p>'
        f'<p style="margin:0;color:{COLOR_TEXT};font-size:14px;line-height:1.55;">{details}</p>'
        "</div>"
    )


def render_order_status_update_email(
    *,
    order_reference,
    current_status,
    statuses,
    estimated_delivery_date=None,
    estimated_delivery_note=None,
    include_receipt_guide=False,
    include_installation_guide=True,
    include_incident_form=False,
    include_maintenance_guide=True,
):
    order_reference_text = _required_text(order_reference, "order_reference")
    current_status_text = _required_text(current_status, "current_status")
    normalized_statuses = tuple(statuses or ())
    current_index = next(
        (
            index
            for index, status in enumerate(normalized_statuses)
            if isinstance(status, tuple) and len(status) == 2 and status[0] == current_status_text
        ),
        None,
    )
    if current_index is None:
        raise TransactionalEmailRenderError("El estado actual del pedido no es v\u00e1lido.")

    current_label = _required_text(normalized_statuses[current_index][1], "current_status_label")
    delivery_date = _text(estimated_delivery_date)
    delivery_note = _text(estimated_delivery_note)
    delivery_text = _render_status_delivery_text(delivery_date, delivery_note)
    progress_text = "\n".join(
        f"{'Completado' if index < current_index else 'Actual' if index == current_index else 'Pendiente'}: {label}"
        for index, (_, label) in enumerate(normalized_statuses)
    )
    guidance_text, guidance_html = _render_order_status_guidance(
        current_status_text,
        include_receipt_guide=include_receipt_guide,
        include_installation_guide=include_installation_guide,
        include_incident_form=include_incident_form,
        include_maintenance_guide=include_maintenance_guide,
    )

    text_body = (
        "METALWOLFT\n"
        f"{BRAND_TAGLINE}\n\n"
        "ESTADO DE TU PEDIDO\n\n"
        f"Tu pedido ha cambiado de estado y ahora se encuentra en la fase: {current_label}.\n\n"
        f"Localizador: {order_reference_text}\n"
        f"{delivery_text}"
        "\nPROGRESO DEL PEDIDO\n"
        f"{progress_text}\n\n"
        f"{guidance_text}"
        "Si tienes cualquier duda, puedes responder directamente a este correo.\n\n"
        "MetalWolft\n"
        "Fabricaci\u00f3n de rejas a medida"
    )

    detail_rows = _render_invoice_detail_row("Localizador", order_reference_text)
    if delivery_date:
        detail_rows += _render_invoice_detail_row("Fecha estimada de entrega", delivery_date)
    if delivery_note:
        detail_rows += _render_invoice_detail_row("Nota", delivery_note)

    progress_rows = "".join(
        _render_status_progress_row(label, index, current_index)
        for index, (_, label) in enumerate(normalized_statuses)
    )
    content_html = (
        f'<h1 style="margin:0 0 12px;color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;'
        'font-size:28px;line-height:1.2;font-weight:700;">Estado de tu pedido</h1>'
        f'<p style="margin:0 0 18px;color:{COLOR_TEXT};font-size:16px;line-height:1.6;">'
        f'Tu pedido ha cambiado de estado y ahora se encuentra en la fase: '
        f'<strong style="color:{COLOR_ACCENT};">{_html(current_label)}</strong>.'
        "</p>"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;margin:0 0 24px;background:{COLOR_SURFACE_ALT};border:1px solid {COLOR_BORDER};'
        'border-collapse:collapse;">'
        f"{detail_rows}"
        "</table>"
        f'<h2 style="margin:0 0 12px;color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;'
        'font-size:14px;line-height:1.4;font-weight:700;letter-spacing:0.08em;">PROGRESO DEL PEDIDO</h2>'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;margin:0 0 24px;border:1px solid {COLOR_BORDER};border-collapse:collapse;">'
        f"{progress_rows}"
        "</table>"
        f"{guidance_html}"
        f'<p style="margin:0;color:{COLOR_MUTED};font-size:14px;line-height:1.6;">'
        "Si tienes cualquier duda, puedes responder directamente a este correo."
        "</p>"
    )

    return RenderedEmail(
        text=text_body,
        html=_render_shell(
            preheader=f"Tu pedido {order_reference_text} est\u00e1 ahora en {current_label}.",
            content_html=content_html,
        ),
    )


def _render_order_status_guidance(
    current_status,
    *,
    include_receipt_guide=False,
    include_installation_guide=True,
    include_incident_form=False,
    include_maintenance_guide=True,
):
    if current_status == "enviado":
        guidance_links = []
        if include_receipt_guide:
            guidance_links.append(("Guía de recepción del pedido", RECEIPT_GUIDE_URL))
        if include_installation_guide:
            guidance_links.append(("Ver guía de instalación", INSTALLATION_GUIDE_URL))
        if include_incident_form:
            guidance_links.append(("Formulario de incidencias", INCIDENT_FORM_URL))

        if not guidance_links:
            return "", ""

        if include_installation_guide:
            title = "Prepárate para la instalación"
            description = (
                "Antes de instalar tu reja, consulta nuestra guía de instalación y manipulación. "
                "Encontrarás cómo desembalarla, proteger el acabado y realizar correctamente la fijación."
            )
        else:
            title = "Información útil para tu pedido"
            description = "Consulta los recursos seleccionados para la recepción y el cuidado de tu reja."

        links_text = "".join(f"{label}: {url}\n" for label, url in guidance_links)
        links_html = "<br>".join(
            f'<a href="{url}" style="color:{COLOR_ACCENT};font-size:14px;line-height:1.4;font-weight:700;">{label}</a>'
            for label, url in guidance_links
        )
        return (
            f"{title}\n{description}\n{links_text}\n",
            f'<div style="margin:0 0 24px;padding:16px;background:{COLOR_SURFACE_ALT};border-left:3px solid {COLOR_ACCENT};">'
            f'<p style="margin:0 0 6px;color:{COLOR_TEXT};font-size:15px;line-height:1.45;font-weight:700;">'
            f"{title}</p>"
            f'<p style="margin:0 0 9px;color:{COLOR_MUTED};font-size:14px;line-height:1.55;">'
            f"{description}</p>"
            f"{links_html}</div>",
        )

    if current_status == "entregado":
        guidance_links = []
        if include_installation_guide:
            guidance_links.append(("Guía de instalación", INSTALLATION_GUIDE_URL))
        if include_maintenance_guide:
            guidance_links.append(("Mantenimiento y acabado", MAINTENANCE_GUIDE_URL))

        if not guidance_links:
            return "", ""

        if include_installation_guide and include_maintenance_guide:
            description = (
                "Consulta la guía de instalación antes de montarla y guarda la guía de mantenimiento para la limpieza "
                "y conservación del acabado."
            )
        elif include_installation_guide:
            description = "Consulta la guía de instalación antes de montar tu reja."
        else:
            description = "Guarda la guía de mantenimiento para la limpieza y conservación del acabado."

        links_text = "".join(f"{label}: {url}\n" for label, url in guidance_links)
        links_html = f'<span style="color:{COLOR_MUTED};font-size:14px;">&nbsp;·&nbsp;</span>'.join(
            f'<a href="{url}" style="color:{COLOR_ACCENT};font-size:14px;line-height:1.4;font-weight:700;">{label}</a>'
            for label, url in guidance_links
        )
        return (
            "Ya tienes tu reja\n"
            f"{description}\n"
            f"{links_text}\n",
            f'<div style="margin:0 0 24px;padding:16px;background:{COLOR_SURFACE_ALT};border-left:3px solid {COLOR_ACCENT};">'
            f'<p style="margin:0 0 6px;color:{COLOR_TEXT};font-size:15px;line-height:1.45;font-weight:700;">'
            "Ya tienes tu reja</p>"
            f'<p style="margin:0 0 9px;color:{COLOR_MUTED};font-size:14px;line-height:1.55;">'
            f"{description}</p>"
            f"{links_html}</div>",
        )

    return "", ""


def _render_status_delivery_text(delivery_date, delivery_note):
    details = []
    if delivery_date:
        details.append(f"Fecha estimada de entrega: {delivery_date}")
    if delivery_note:
        details.append(f"Nota: {delivery_note}")
    return "\n".join(details) + ("\n" if details else "")


def _render_status_progress_row(label, index, current_index):
    if index < current_index:
        state_label = "Completado"
        state_color = "#15803d"
    elif index == current_index:
        state_label = "Estado actual"
        state_color = COLOR_ACCENT
    else:
        state_label = "Pendiente"
        state_color = COLOR_MUTED
    return (
        "<tr>"
        f'<td style="padding:11px 14px;border-bottom:1px solid {COLOR_BORDER};color:{COLOR_TEXT};font-size:14px;line-height:1.4;font-weight:600;">'
        f"{_html(label)}</td>"
        f'<td align="right" style="padding:11px 14px;border-bottom:1px solid {COLOR_BORDER};color:{state_color};font-size:13px;line-height:1.4;font-weight:700;white-space:nowrap;">'
        f"{state_label}</td>"
        "</tr>"
    )


def render_order_delivery_estimate_update_email(
    *, order_reference, estimated_delivery_date=None, estimated_delivery_note=None
):
    order_reference_text = _required_text(order_reference, "order_reference")
    delivery_date = _text(estimated_delivery_date)
    delivery_note = _text(estimated_delivery_note)

    plain_details = [f"Localizador: {order_reference_text}"]
    if delivery_date:
        plain_details.insert(0, f"Fecha estimada de entrega: {delivery_date}")
    if delivery_note:
        plain_details.append(f"Nota: {delivery_note}")

    introduction = (
        "Hemos actualizado la fecha estimada de entrega de tu pedido."
        if delivery_date
        else "Hemos actualizado la informaci\u00f3n de entrega de tu pedido."
    )
    text_body = (
        "METALWOLFT\n"
        f"{BRAND_TAGLINE}\n\n"
        "ACTUALIZACI\u00d3N DE ENTREGA\n\n"
        f"{introduction}\n\n"
        + "\n".join(plain_details)
        + "\n\nSi tienes cualquier duda, puedes responder directamente a este correo.\n\n"
        "MetalWolft\n"
        "Fabricaci\u00f3n de rejas a medida"
    )

    detail_rows = _render_invoice_detail_row("Localizador", order_reference_text)
    if delivery_date:
        detail_rows += _render_invoice_detail_row("Fecha estimada de entrega", delivery_date)
    if delivery_note:
        detail_rows += _render_invoice_detail_row("Nota", delivery_note)
    content_html = (
        f'<h1 style="margin:0 0 12px;color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;'
        'font-size:28px;line-height:1.2;font-weight:700;">Actualizaci\u00f3n de entrega</h1>'
        f'<p style="margin:0 0 18px;color:{COLOR_TEXT};font-size:16px;line-height:1.6;">'
        f"{_html(introduction)}"
        "</p>"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;margin:0 0 24px;background:{COLOR_SURFACE_ALT};border:1px solid {COLOR_BORDER};'
        'border-collapse:collapse;">'
        f"{detail_rows}"
        "</table>"
        f'<p style="margin:0;color:{COLOR_MUTED};font-size:14px;line-height:1.6;">'
        "Si tienes cualquier duda, puedes responder directamente a este correo."
        "</p>"
    )
    return RenderedEmail(
        text=text_body,
        html=_render_shell(
            preheader=(
                f"Nueva fecha estimada de entrega: {delivery_date}."
                if delivery_date
                else f"Actualizaci\u00f3n de entrega para tu pedido {order_reference_text}."
            ),
            content_html=content_html,
        ),
    )


def render_account_welcome_email(*, customer_firstname=None, login_url):
    login_url_text = _required_text(login_url, "login_url")
    customer_name = _text(customer_firstname)
    greeting = f"Hola, {customer_name}," if customer_name else "Hola,"
    introduction = (
        "Tu cuenta ha sido creada correctamente. Ya puedes iniciar sesi\u00f3n, explorar nuestros modelos "
        "y consultar tus pedidos desde tu cuenta."
    )
    closing = (
        "Gracias por registrarte en MetalWolft. Si necesitas ayuda, puedes responder "
        "directamente a este correo."
    )
    text_body = (
        "METALWOLFT\n"
        f"{BRAND_TAGLINE}\n\n"
        "\u00a1Bienvenido a MetalWolft!\n\n"
        f"{greeting}\n\n"
        f"{introduction}\n\n"
        f"Iniciar sesi\u00f3n: {login_url_text}\n\n"
        f"{closing}\n\n"
        "MetalWolft\n"
        "Fabricaci\u00f3n de rejas a medida"
    )
    content_html = (
        f'<p style="margin:0 0 18px;color:{COLOR_MUTED};font-size:15px;line-height:1.6;">'
        f"{_html(greeting)}"
        "</p>"
        f'<h1 style="margin:0 0 12px;color:{COLOR_TEXT};font-family:Arial,Helvetica,sans-serif;'
        'font-size:28px;line-height:1.2;font-weight:700;">\u00a1Bienvenido a MetalWolft!</h1>'
        f'<p style="margin:0 0 24px;color:{COLOR_TEXT};font-size:16px;line-height:1.6;">'
        f"{_html(introduction)}"
        "</p>"
        f'<a href="{_html(login_url_text)}" '
        f'style="display:inline-block;background:{COLOR_ACCENT};color:#ffffff;text-decoration:none;font-size:16px;'
        'font-weight:700;padding:13px 22px;border-radius:999px;">Iniciar sesi\u00f3n</a>'
        f'<p style="margin:22px 0 0;color:{COLOR_MUTED};font-size:14px;line-height:1.6;">'
        f"{_html(closing)}"
        "</p>"
    )
    return RenderedEmail(
        text=text_body,
        html=_render_shell(
            preheader="Tu cuenta de MetalWolft ha sido creada correctamente.",
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
    screw_configuration = _text(line.screw_configuration)
    line_total = _format_money(line.line_total, "line_total")
    image_url = _email_image_url(line.image_url)
    total_label = _text(line.total_label)
    text_total_label = total_label or "Importe"
    html_total_label = total_label or "Importe de línea"

    if line.line_type == "design_service":
        plain = (
            f"{product_name} ×{quantity}\n"
            f"Medidas: {measurements}\n"
            f"{text_total_label}: {line_total}"
        )
        html_details = _html(measurements)
    else:
        plain = (
        f"{product_name} ×{quantity}\n"
        f"Medidas: {measurements}\n"
        f"Instalación: {anchorage}\n"
        f"Color: {color}\n"
        + (f"Tornillos: {screw_configuration}\n" if screw_configuration else "")
        + f"Cantidad: {quantity}\n"
        + f"{text_total_label}: {line_total}"
    )
        html_details = (
            f"{_html(measurements)} · {_html(anchorage)}<br>{_html(color)}"
            + (f"<br>Tornillos {_html(screw_configuration)}" if screw_configuration else "")
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
        (
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
        f"{html_details}"
        )
        + (
        "</td></tr><tr>"
        f'<td colspan="{2 if image_cell else 1}" style="padding:4px 0 16px;color:{COLOR_MUTED};font-size:13px;line-height:1.4;">'
        f"{_html(html_total_label)}</td>"
        f'<td align="right" style="padding:4px 0 16px 12px;color:{COLOR_TEXT};font-size:15px;'
        f'line-height:1.4;font-weight:700;white-space:nowrap;">{_html(line_total)}</td>'
        "</tr></table>"
        )
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
        f'<tr><td style="padding:20px 28px;background:#ffffff;border-top:1px solid {COLOR_BORDER};">'
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

from api.utils import format_screw_configuration


def _format_money(value):
    try:
        return f"{float(value or 0):.2f} €"
    except (TypeError, ValueError):
        return "0.00 €"


def _format_measurements(line):
    alto = line.get("alto")
    ancho = line.get("ancho")
    if alto is None or ancho is None:
        return "-"
    return f"{alto} x {ancho} cm"


def _build_line_summary(line):
    product_name = line.get("product_name") or line.get("nombre") or f"Producto {line.get('product_id') or line.get('producto_id')}"
    quantity = line.get("quantity", 1)
    line_total = line.get("line_total")
    if line_total is None:
        line_total = float(line.get("unit_price") or line.get("precio_total") or 0) * int(quantity or 1)
    screw_configuration = format_screw_configuration(
        line.get("screw_length_mm"),
        line.get("screw_supplement"),
    ) or "-"

    return (
        f"- {product_name} | "
        f"Medidas: {_format_measurements(line)} | "
        f"Anclaje: {line.get('anclaje') or '-'} | "
        f"Color: {line.get('color') or '-'} | "
        f"Tornillos: {screw_configuration} | "
        f"Cantidad: {quantity} | "
        f"Importe: {_format_money(line_total)}"
    )


def _build_order_confirmation_body(*, order, checkout_quote, customer_firstname):
    lines = checkout_quote.get("lines") or []
    line_summaries = "\n".join(_build_line_summary(line) for line in lines) or "- Pedido sin líneas disponibles"
    discount_amount = float(checkout_quote.get("discount_amount") or 0.0)
    discount_line = (
        f"- Descuento: -{_format_money(discount_amount)}\n"
        if discount_amount > 0
        else ""
    )

    greeting_name = (customer_firstname or "").strip()
    greeting = f"Hola {greeting_name}," if greeting_name else "Hola,"

    return (
        f"{greeting}\n\n"
        "Hemos recibido correctamente tu pedido en MetalWolft.\n\n"
        f"Pedido: {order.locator}\n"
        "Estado del pago: confirmado\n\n"
        "Resumen:\n"
        f"{line_summaries}\n\n"
        f"- Subtotal: {_format_money(checkout_quote.get('subtotal'))}\n"
        f"- Envío: {_format_money(checkout_quote.get('shipping_cost'))}\n"
        f"{discount_line}"
        f"- Total: {_format_money(order.total_amount)}\n\n"
        "Comenzaremos a preparar y fabricar tu pedido.\n\n"
        "Te informaremos cuando avance su estado.\n\n"
        "Gracias por confiar en MetalWolft."
    )


def send_order_confirmation_email(
    *,
    user,
    order,
    checkout_quote,
    customer_firstname,
    mail_username,
    logger,
    send_email_func=None,
):
    if send_email_func is None:
        from api.email_routes import send_email

        send_email_func = send_email

    try:
        logger.info("Enviando correo de confirmación para el pedido %s.", order.locator)
        email_sent = send_email_func(
            subject=f"Hemos recibido tu pedido {order.locator}",
            recipients=[user.email, mail_username],
            body=_build_order_confirmation_body(
                order=order,
                checkout_quote=checkout_quote,
                customer_firstname=customer_firstname,
            ),
        )
        if not email_sent:
            logger.error("Error al enviar el correo de confirmación del pedido %s.", order.locator)
        else:
            logger.info("Correo de confirmación enviado correctamente para el pedido %s.", order.locator)
    except Exception as e:
        logger.error("Error al enviar el correo de confirmación del pedido %s: %s", order.locator, str(e))

def send_invoice_email(
    *,
    user,
    invoice_result,
    customer_firstname,
    customer_lastname,
    mail_username,
    logger,
    send_email_func=None,
):
    if send_email_func is None:
        from api.email_routes import send_email

        send_email_func = send_email

    try:
        email_sent = send_email_func(
            subject=f"Factura de tu pedido #{invoice_result.invoice_number}",
            recipients=[user.email, mail_username],
            body=(
                f"Hola {(customer_firstname or '').strip()} {(customer_lastname or '').strip()},\n\n"
                f"Adjuntamos la factura {invoice_result.invoice_number} de tu compra.\n\n"
                "Gracias por tu confianza."
            ),
            attachment_path=invoice_result.file_path,
        )
        if not email_sent:
            logger.error("Error al enviar el correo con la factura %s.", invoice_result.invoice_number)
        else:
            logger.info("Correo enviado correctamente con la factura %s.", invoice_result.invoice_number)
    except Exception as e:
        logger.error("Error al enviar el correo con la factura %s: %s", invoice_result.invoice_number, str(e))

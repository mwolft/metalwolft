"""Post-commit notification for a delivered design-preview result."""

from decimal import Decimal, InvalidOperation

from api.order_confirmation_context import (
    get_order_confirmation_customer_firstname,
    get_order_confirmation_recipient_email,
)
from api.transactional_email_renderer import render_design_result_ready_email


def send_design_result_ready_email(
    *,
    design_request,
    frontend_url,
    mail_username,
    logger,
    send_email_func=None,
):
    """Attempt delivery notice without changing the already committed request."""
    if send_email_func is None:
        from api.email_routes import send_email

        send_email_func = send_email

    try:
        order = getattr(design_request, "order", None)
        if order is None or not getattr(order, "id", None):
            raise ValueError("La solicitud entregada no está vinculada a un pedido.")

        recipient_email = get_order_confirmation_recipient_email(order)
        if not recipient_email:
            raise ValueError("No hay un email de destinatario para el resultado entregado.")

        rendered_email = render_design_result_ready_email(
            design_reference=design_request.reference,
            customer_firstname=get_order_confirmation_customer_firstname(order),
            items=[
                {
                    "product_name": item.product_name,
                    "measurements": _format_item_measurements(item),
                }
                for item in (getattr(design_request, "items", ()) or ())
            ],
            account_url=_design_result_account_url(frontend_url, order.id),
        )
        logger.info("Enviando aviso de resultado listo para la solicitud %s.", design_request.reference)
        email_sent = send_email_func(
            subject=f"Tu diseño previo {design_request.reference} está listo",
            recipients=[recipient_email, mail_username],
            body=rendered_email.text,
            html=rendered_email.html,
        )
        if not email_sent:
            logger.error(
                "No se ha podido enviar el aviso de resultado listo para la solicitud %s.",
                design_request.reference,
            )
        return bool(email_sent)
    except Exception as exc:
        logger.error(
            "Error al preparar o enviar el aviso de resultado listo para la solicitud %s "
            "(tipo=%s).",
            getattr(design_request, "reference", "desconocida"),
            type(exc).__name__,
        )
        return False


def _format_item_measurements(item):
    return (
        f"Alto {_format_measurement(getattr(item, 'height_cm', None))} cm × "
        f"Ancho {_format_measurement(getattr(item, 'width_cm', None))} cm"
    )


def _format_measurement(value):
    if value is None:
        return "-"
    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value).strip() or "-"
    if not normalized.is_finite():
        return str(value).strip() or "-"
    return format(normalized.normalize(), "f")


def _design_result_account_url(frontend_url, order_id):
    normalized_frontend_url = str(frontend_url or "").strip().rstrip("/")
    if not normalized_frontend_url.startswith(("https://", "http://")):
        raise ValueError("La URL pública del frontend no es válida.")
    return f"{normalized_frontend_url}/mi-cuenta/pedidos/{order_id}"

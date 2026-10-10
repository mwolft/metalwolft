"""Send validated customer photos directly to the private administration mailbox."""

from email import policy
from email.message import EmailMessage
import smtplib
import ssl

from api.transactional_email_renderer import render_customer_photo_confirmation_email


PHOTO_MAIL_RECIPIENT = "admin@metalwolft.com"
MAX_MIME_BYTES = 12 * 1024 * 1024


class PhotoMailRejected(Exception):
    """The relay definitively did not accept this message."""


class PhotoMailUncertain(Exception):
    """Relay acceptance could not be established; never retry automatically."""


def build_photo_message(*, app, order_reference, request_id, attempt_id, date, consent, photos, is_simulation=False):
    message = EmailMessage()
    message["Subject"] = f"Fotografías de cliente - pedido {order_reference} - solicitud {request_id}"
    message["From"] = app.config.get("MAIL_DEFAULT_SENDER") or ""
    message["To"] = PHOTO_MAIL_RECIPIENT
    message["Message-ID"] = f"<customer-photos-{attempt_id}@metalwolft.com>"
    simulation_notice = "SIMULACIÓN — SIN REEMBOLSO\n" if is_simulation else ""
    message.set_content(
        f"{simulation_notice}Pedido: {order_reference}\nSolicitud: {request_id}\nFecha: {date.isoformat()}\n"
        f"Fotografías: {len(photos)}\nAutorización comercial: {'Sí' if consent else 'No'}\n"
        "Las fotografías están adjuntas; no se guardan en el panel de administración.\n"
    )
    for index, (mime, content, _digest, extension) in enumerate(photos, 1):
        major, minor = mime.split("/", 1)
        message.add_attachment(content, maintype=major, subtype=minor, filename=f"fotografia-{index}{extension}")
    if len(message.as_bytes(policy=policy.SMTP)) > MAX_MIME_BYTES:
        raise PhotoMailRejected("Las fotografías generan un correo demasiado grande. Selecciona imágenes más pequeñas.")
    return message


def build_photo_confirmation_message(*, app, recipient, order_reference, request_id, mode, terms_url=None, is_simulation=False):
    message = EmailMessage()
    message["Subject"] = "¡Hemos recibido tus fotos! 📸 | MetalWolft"
    message["From"] = app.config.get("MAIL_DEFAULT_SENDER") or ""
    message["To"] = recipient
    message["Reply-To"] = PHOTO_MAIL_RECIPIENT
    rendered = render_customer_photo_confirmation_email(
        mode=mode, order_reference=order_reference, request_id=request_id,
        terms_url=terms_url, is_simulation=is_simulation,
    )
    message.set_content(rendered.text)
    message.add_alternative(rendered.html, subtype="html")
    return message


def send_photo_message(*, app, message):
    host = app.config.get("MAIL_SERVER")
    port = app.config.get("MAIL_PORT")
    if not host or not port or not message["From"]:
        raise PhotoMailRejected("El envío de fotografías no está configurado.")
    smtp_type = smtplib.SMTP_SSL if app.config.get("MAIL_USE_SSL") else smtplib.SMTP
    try:
        with smtp_type(host=host, port=int(port), timeout=20) as smtp:
            if app.config.get("MAIL_USE_TLS") and not app.config.get("MAIL_USE_SSL"):
                smtp.starttls(context=ssl.create_default_context())
            username = app.config.get("MAIL_USERNAME")
            if username:
                smtp.login(username, app.config.get("MAIL_PASSWORD") or "")
            smtp.send_message(message)
    except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused) as exc:
        raise PhotoMailRejected("El servidor de correo rechazó el envío.") from exc
    except smtplib.SMTPDataError as exc:
        if 500 <= exc.smtp_code < 600:
            raise PhotoMailRejected("El servidor de correo rechazó el envío.") from exc
        raise PhotoMailUncertain("No se pudo confirmar la entrega al servidor de correo.") from exc
    except (OSError, TimeoutError, smtplib.SMTPException) as exc:
        raise PhotoMailUncertain("No se pudo confirmar la entrega al servidor de correo.") from exc

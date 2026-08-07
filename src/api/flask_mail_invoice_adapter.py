from pathlib import Path

from flask_mail import Message


class FlaskMailInvoiceAdapterError(Exception):
    """Raised when an InvoiceEmailMessage cannot be sent through Flask-Mail."""


class FlaskMailInvoiceAdapter:
    def __init__(self, mail):
        self.mail = mail

    def send(self, invoice_email_message):
        message = _validated_message(invoice_email_message)
        flask_message = Message(
            subject=message.subject,
            recipients=list(message.recipients),
            body=message.body,
            html=message.html,
        )

        for attachment in message.attachments:
            flask_message.attach(
                filename=attachment.filename,
                content_type=attachment.content_type,
                data=attachment.data,
            )

        try:
            self.mail.send(flask_message)
        except Exception as exc:
            raise FlaskMailInvoiceAdapterError("No se pudo enviar el email de factura.") from exc


def _validated_message(message):
    if message is None:
        raise FlaskMailInvoiceAdapterError("El mensaje de factura es obligatorio.")

    subject = str(getattr(message, "subject", "") or "").strip()
    if not subject:
        raise FlaskMailInvoiceAdapterError("El asunto del email de factura es obligatorio.")

    recipients = tuple(getattr(message, "recipients", None) or ())
    if not recipients or any(not str(recipient or "").strip() for recipient in recipients):
        raise FlaskMailInvoiceAdapterError("El email de factura debe tener destinatarios.")

    body = str(getattr(message, "body", "") or "").strip()
    html = str(getattr(message, "html", "") or "").strip()
    if not body or not html:
        raise FlaskMailInvoiceAdapterError(
            "El email de factura debe incluir texto y HTML."
        )

    attachments = tuple(getattr(message, "attachments", None) or ())
    if len(attachments) != 1:
        raise FlaskMailInvoiceAdapterError(
            "El email de factura debe tener un único adjunto PDF."
        )

    for attachment in attachments:
        _validate_attachment(attachment)

    return message


def _validate_attachment(attachment):
    if attachment is None:
        raise FlaskMailInvoiceAdapterError("Adjunto de factura no valido.")

    filename = str(getattr(attachment, "filename", "") or "").strip()
    if not _is_safe_filename(filename):
        raise FlaskMailInvoiceAdapterError("Nombre de adjunto de factura no valido.")

    content_type = str(getattr(attachment, "content_type", "") or "").strip()
    if content_type.lower() != "application/pdf":
        raise FlaskMailInvoiceAdapterError("El adjunto de factura no tiene MIME PDF.")

    data = getattr(attachment, "data", None)
    if not isinstance(data, bytes) or not data:
        raise FlaskMailInvoiceAdapterError("El adjunto de factura no contiene bytes validos.")


def _is_safe_filename(filename):
    if not filename or "\x00" in filename:
        return False
    if "/" in filename or "\\" in filename:
        return False
    if filename != Path(filename).name:
        return False
    return filename.lower().endswith(".pdf")

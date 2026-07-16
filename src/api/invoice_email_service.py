import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash


SUPPORTED_SCHEMA_VERSION = 1
EMAIL_STATUS_PENDING = "pending"
EMAIL_STATUS_SENT = "sent"
EMAIL_STATUS_FAILED = "failed"
PDF_MIME_TYPE = "application/pdf"


class InvoiceEmailError(Exception):
    """Base error for InvoiceSnapshot-based invoice email delivery."""


class InvoiceEmailSnapshotMissing(InvoiceEmailError):
    """Raised when the invoice does not contain a usable InvoiceSnapshot v1."""


class InvoiceEmailIntegrityError(InvoiceEmailError):
    """Raised when the persisted snapshot hash does not match the snapshot."""


class InvoiceEmailRecipientMissing(InvoiceEmailError):
    """Raised when the invoice snapshot does not contain a customer email."""


class InvoiceEmailPdfMissing(InvoiceEmailError):
    """Raised when the invoice PDF is missing or unsafe."""


class InvoiceEmailSendError(InvoiceEmailError):
    """Raised when the mailer cannot send the message."""


class InvoiceEmailUnsupportedSchema(InvoiceEmailError):
    """Raised when the invoice snapshot schema is not supported."""


@dataclass(frozen=True)
class InvoiceEmailResult:
    recipient: str
    sent_at: datetime | None
    invoice_number: str
    attachment_filename: str
    already_sent: bool


@dataclass(frozen=True)
class InvoiceEmailAttachment:
    filename: str
    content_type: str
    data: bytes


@dataclass(frozen=True)
class InvoiceEmailMessage:
    subject: str
    recipients: tuple[str, ...]
    body: str
    attachments: tuple[InvoiceEmailAttachment, ...]


def send_invoice_email(invoice, *, mailer=None):
    """Send an issued invoice PDF using only the persisted InvoiceSnapshot v1.

    The service deliberately does not commit or rollback. It only updates email
    delivery fields on the invoice object so the caller can control the
    surrounding transaction.
    """
    invoice_number = _required_invoice_number(invoice)
    _required_issued_at(invoice)
    snapshot = _validated_snapshot(invoice)
    _validate_snapshot_hash(invoice, snapshot)

    customer = _required_mapping(snapshot, "customer")
    issuer = _required_mapping(snapshot, "issuer")
    operation = _required_mapping(snapshot, "operation")
    recipient = _required_email(customer)
    attachment_path, attachment_filename = _validated_pdf_path(invoice, invoice_number)

    sent_at = getattr(invoice, "email_sent_at", None)
    if getattr(invoice, "email_status", None) == EMAIL_STATUS_SENT:
        return InvoiceEmailResult(
            recipient=recipient,
            sent_at=sent_at,
            invoice_number=invoice_number,
            attachment_filename=attachment_filename,
            already_sent=True,
        )

    trade_name = _text(issuer.get("trade_name") or issuer.get("legal_name") or "MetalWolft")
    customer_name = _text(customer.get("legal_name") or "cliente")
    order_reference = _text(operation.get("order_locator") or operation.get("order_id") or "")
    subject = f"Factura {invoice_number} - {trade_name}"
    body = _email_body(
        customer_name=customer_name,
        invoice_number=invoice_number,
        order_reference=order_reference,
        trade_name=trade_name,
    )

    message = _build_message(
        subject=subject,
        recipient=recipient,
        body=body,
        attachment_path=attachment_path,
        attachment_filename=attachment_filename,
    )

    invoice.email_attempts = int(getattr(invoice, "email_attempts", None) or 0) + 1

    try:
        _resolved_mailer(mailer).send(message)
    except Exception as exc:
        invoice.email_status = EMAIL_STATUS_FAILED
        invoice.email_last_error = "No se pudo enviar el email de factura."
        raise InvoiceEmailSendError("No se pudo enviar el email de factura.") from exc

    sent_at = datetime.now(timezone.utc)
    invoice.email_status = EMAIL_STATUS_SENT
    invoice.email_sent_at = sent_at
    invoice.email_last_error = None
    return InvoiceEmailResult(
        recipient=recipient,
        sent_at=sent_at,
        invoice_number=invoice_number,
        attachment_filename=attachment_filename,
        already_sent=False,
    )


def _required_invoice_number(invoice):
    if invoice is None:
        raise InvoiceEmailSnapshotMissing("La factura es obligatoria.")

    invoice_number = getattr(invoice, "invoice_number", None)
    if not invoice_number:
        raise InvoiceEmailSnapshotMissing("La factura no tiene numero fiscal.")
    return str(invoice_number)


def _required_issued_at(invoice):
    if not getattr(invoice, "issued_at", None):
        raise InvoiceEmailSnapshotMissing("La factura debe estar emitida para enviarse por email.")


def _validated_snapshot(invoice):
    snapshot = getattr(invoice, "invoice_snapshot", None)
    if not isinstance(snapshot, dict):
        raise InvoiceEmailSnapshotMissing("La factura no tiene snapshot fiscal.")

    if snapshot.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise InvoiceEmailUnsupportedSchema("Version de snapshot no soportada.")
    return snapshot


def _validate_snapshot_hash(invoice, snapshot):
    stored_hash = getattr(invoice, "invoice_snapshot_hash", None)
    if not stored_hash:
        raise InvoiceEmailIntegrityError("La factura no tiene hash fiscal.")

    calculated_hash = calculate_invoice_snapshot_hash(snapshot)
    if calculated_hash != stored_hash:
        raise InvoiceEmailIntegrityError("El hash fiscal de la factura no coincide.")


def _required_mapping(snapshot, key):
    value = snapshot.get(key)
    if not isinstance(value, dict):
        raise InvoiceEmailSnapshotMissing(f"El snapshot no contiene {key}.")
    return value


def _required_email(customer):
    email = _text(customer.get("email"))
    if not email:
        raise InvoiceEmailRecipientMissing("El cliente no tiene email en el snapshot.")
    return email


def _validated_pdf_path(invoice, invoice_number):
    stored_pdf_path = getattr(invoice, "pdf_path", None)
    if not stored_pdf_path:
        raise InvoiceEmailPdfMissing("La factura no tiene PDF generado.")

    filename = _safe_pdf_filename(stored_pdf_path)
    expected_filename = _invoice_pdf_filename(invoice_number)
    if filename != expected_filename:
        raise InvoiceEmailPdfMissing("El PDF no corresponde a la factura.")

    base_dir = _invoice_pdf_base_dir()
    output_path = (base_dir / filename).resolve()
    if output_path.parent != base_dir:
        raise InvoiceEmailPdfMissing("Ruta de PDF no permitida.")
    if not output_path.exists() or not output_path.is_file():
        raise InvoiceEmailPdfMissing("El archivo PDF no existe.")
    return output_path, filename


def _safe_pdf_filename(stored_pdf_path):
    normalized = str(stored_pdf_path).replace("\\", "/")
    if "\x00" in normalized:
        raise InvoiceEmailPdfMissing("Nombre de PDF no valido.")

    parts = [part for part in normalized.split("/") if part]
    if not parts or any(part == ".." for part in parts):
        raise InvoiceEmailPdfMissing("Nombre de PDF no valido.")

    filename = parts[-1]
    if filename != Path(filename).name or not filename.lower().endswith(".pdf"):
        raise InvoiceEmailPdfMissing("Nombre de PDF no valido.")
    return filename


def _invoice_pdf_base_dir():
    configured_folder = os.getenv("INVOICE_FOLDER")
    return Path(configured_folder or os.path.join(os.getcwd(), "invoices")).resolve()


def _invoice_pdf_filename(invoice_number):
    safe_number = re.sub(r"[^A-Za-z0-9._-]+", "_", str(invoice_number)).strip("._-")
    if not safe_number:
        raise InvoiceEmailPdfMissing("Numero de factura no valido para nombre de PDF.")
    return f"invoice_{safe_number}.pdf"


def _build_message(*, subject, recipient, body, attachment_path, attachment_filename):
    attachment = InvoiceEmailAttachment(
        filename=attachment_filename,
        content_type=PDF_MIME_TYPE,
        data=attachment_path.read_bytes(),
    )
    return InvoiceEmailMessage(
        subject=subject,
        recipients=(recipient,),
        body=body,
        attachments=(attachment,),
    )


def _resolved_mailer(mailer):
    if mailer is not None:
        return mailer

    raise InvoiceEmailSendError("No hay adaptador de email configurado.")


def _email_body(*, customer_name, invoice_number, order_reference, trade_name):
    order_line = f"Referencia del pedido: {order_reference}\n" if order_reference else ""
    return (
        f"Hola {customer_name},\n\n"
        f"Adjuntamos la factura {invoice_number} correspondiente a tu pedido.\n"
        f"{order_line}"
        "Encontraras el documento en PDF adjunto a este correo.\n\n"
        f"Gracias por confiar en {trade_name}.\n\n"
        "Un saludo,\n"
        "MetalWolft"
    )


def _text(value):
    if value is None:
        return ""
    return str(value).strip()

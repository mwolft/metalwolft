import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from api.invoice_pdf_download_service import InvoicePdfDownloadError, resolve_invoice_pdf_download
from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash
from api.transactional_email_renderer import render_invoice_delivery_email


SUPPORTED_SCHEMA_VERSIONS = {1, 2}
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
    html: str | None = None


def send_invoice_email(invoice, *, mailer=None, invoice_folder=None, allow_resend=False):
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
    attachment_path, attachment_filename = _validated_pdf_path(invoice, invoice_number, invoice_folder)

    sent_at = getattr(invoice, "email_sent_at", None)
    if not allow_resend and getattr(invoice, "email_status", None) == EMAIL_STATUS_SENT:
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
    rendered_email = render_invoice_delivery_email(
        customer_name=customer_name,
        invoice_number=invoice_number,
        order_reference=order_reference,
        trade_name=trade_name,
    )

    message = _build_message(
        subject=subject,
        recipient=recipient,
        body=rendered_email.text,
        html=rendered_email.html,
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

    if snapshot.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
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


def _validated_pdf_path(invoice, invoice_number, invoice_folder):
    try:
        resolved_pdf = resolve_invoice_pdf_download(invoice, invoice_folder)
    except InvoicePdfDownloadError as exc:
        raise InvoiceEmailPdfMissing("La factura no tiene un PDF disponible para enviar.") from exc

    filename = resolved_pdf.filename
    expected_filename = _invoice_pdf_filename(invoice_number)
    if filename != expected_filename:
        raise InvoiceEmailPdfMissing("El PDF no corresponde a la factura.")
    return Path(resolved_pdf.file_path), filename


def _invoice_pdf_filename(invoice_number):
    safe_number = re.sub(r"[^A-Za-z0-9._-]+", "_", str(invoice_number)).strip("._-")
    if not safe_number:
        raise InvoiceEmailPdfMissing("Numero de factura no valido para nombre de PDF.")
    return f"invoice_{safe_number}.pdf"


def _build_message(*, subject, recipient, body, html, attachment_path, attachment_filename):
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
        html=html,
    )


def _resolved_mailer(mailer):
    if mailer is not None:
        return mailer

    raise InvoiceEmailSendError("No hay adaptador de email configurado.")


def _text(value):
    if value is None:
        return ""
    return str(value).strip()

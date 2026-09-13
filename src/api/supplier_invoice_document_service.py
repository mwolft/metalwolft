"""Domain service for immutable private source documents of supplier invoices."""

from dataclasses import dataclass
from pathlib import Path

from flask import current_app

from api.models import SupplierInvoice, SupplierInvoiceDocument, SupplierInvoiceExtraction, db
from api.private_document_validation import (
    ALLOWED_PRIVATE_DOCUMENT_TYPES,
    MAX_PRIVATE_DOCUMENT_BYTES,
    PrivateDocumentValidationError,
    ValidatedPrivateDocument,
    build_private_document_storage_key,
    validate_private_document_upload,
)
from api.supplier_invoice_document_storage import get_supplier_invoice_document_storage


MAX_DOCUMENT_BYTES = MAX_PRIVATE_DOCUMENT_BYTES
ALLOWED_DOCUMENT_TYPES = ALLOWED_PRIVATE_DOCUMENT_TYPES


class SupplierInvoiceDocumentError(Exception):
    """Base error for supplier invoice document operations."""


class SupplierInvoiceDocumentValidationError(SupplierInvoiceDocumentError):
    """Raised when an uploaded source document is unsafe or invalid."""


class SupplierInvoiceDocumentImmutabilityError(SupplierInvoiceDocumentError):
    """Raised when a registered supplier invoice would be altered."""


class SupplierInvoiceDocumentPersistenceError(SupplierInvoiceDocumentError):
    """Raised when metadata cannot be persisted after a successful upload."""


class SupplierInvoiceDocumentDeletionError(SupplierInvoiceDocumentError):
    """Raised when a private source document cannot be removed safely."""


class SupplierInvoiceDocumentDeletionBlockedError(SupplierInvoiceDocumentDeletionError):
    """Raised when fiscal or extraction state prevents document deletion."""


class SupplierInvoiceDocumentDeletionStorageError(SupplierInvoiceDocumentDeletionError):
    """Raised when R2 deletion fails and the document is retained for retry."""


class SupplierInvoiceDocumentDeletionPersistenceError(SupplierInvoiceDocumentDeletionError):
    """Raised when metadata cleanup fails after the object deletion attempt."""


ValidatedSupplierInvoiceDocument = ValidatedPrivateDocument


@dataclass(frozen=True)
class SupplierInvoiceDocumentUploadResult:
    document: SupplierInvoiceDocument
    duplicate_count: int


def validate_supplier_invoice_document_upload(
    file_storage,
    *,
    max_bytes=MAX_DOCUMENT_BYTES,
    allowed_mime_types=None,
):
    try:
        return validate_private_document_upload(
            file_storage,
            max_bytes=max_bytes,
            allowed_mime_types=allowed_mime_types,
        )
    except PrivateDocumentValidationError as exc:
        raise SupplierInvoiceDocumentValidationError(str(exc)) from exc


def build_supplier_invoice_document_storage_key(*, now=None, extension):
    try:
        return build_private_document_storage_key(
            namespace="supplier-invoices",
            now=now,
            extension=extension,
        )
    except PrivateDocumentValidationError as exc:
        raise SupplierInvoiceDocumentValidationError(str(exc)) from exc


def upload_supplier_invoice_document(
    file_storage,
    *,
    supplier_invoice=None,
    actor=None,
    db_session=None,
    storage=None,
    now=None,
    allowed_mime_types=None,
):
    """Validate, upload and persist a document; compensate R2 if DB persistence fails."""
    if supplier_invoice and supplier_invoice.status == SupplierInvoice.STATUS_REGISTERED:
        raise SupplierInvoiceDocumentImmutabilityError(
            "No se pueden añadir documentos a una factura recibida registrada."
        )

    session = db_session or db.session
    max_bytes = int(current_app.config.get("SUPPLIER_DOCUMENT_MAX_BYTES", MAX_DOCUMENT_BYTES))
    validated = validate_supplier_invoice_document_upload(
        file_storage,
        max_bytes=max_bytes,
        allowed_mime_types=allowed_mime_types,
    )
    extension = Path(validated.original_filename).suffix.lower()
    storage_key = build_supplier_invoice_document_storage_key(now=now, extension=extension)
    storage = storage or get_supplier_invoice_document_storage(current_app)
    duplicate_count = (
        session.query(SupplierInvoiceDocument)
        .filter(SupplierInvoiceDocument.sha256 == validated.sha256)
        .count()
    )

    storage.put_document(
        storage_key=storage_key,
        content=validated.content,
        mime_type=validated.mime_type,
    )
    document = SupplierInvoiceDocument(
        supplier_invoice=supplier_invoice,
        storage_provider="r2",
        storage_key=storage_key,
        original_filename=validated.original_filename,
        mime_type=validated.mime_type,
        file_size=validated.file_size,
        sha256=validated.sha256,
        uploaded_by=_normalized_actor(actor),
        processing_status=SupplierInvoiceDocument.STATUS_UPLOADED,
    )
    try:
        session.add(document)
        session.flush()
    except Exception as exc:
        try:
            storage.delete_document(storage_key=storage_key)
        except Exception:
            pass
        raise SupplierInvoiceDocumentPersistenceError(
            "No se ha podido guardar la referencia del documento privado."
        ) from exc

    return SupplierInvoiceDocumentUploadResult(
        document=document,
        duplicate_count=duplicate_count,
    )


_DELETABLE_INVOICE_STATUSES = {
    SupplierInvoice.STATUS_DRAFT,
    SupplierInvoice.STATUS_NEEDS_REVIEW,
}
_DELETABLE_EXTRACTION_STATUSES = {
    SupplierInvoiceExtraction.STATUS_FAILED,
    SupplierInvoiceExtraction.STATUS_EXTRACTED,
    SupplierInvoiceExtraction.STATUS_NEEDS_REVIEW,
}


def can_delete_supplier_invoice_document(document):
    """Return whether an individual source document is safe to remove."""
    try:
        _validate_supplier_invoice_document_deletion(document)
    except SupplierInvoiceDocumentDeletionBlockedError:
        return False
    return True


def delete_supplier_invoice_document(document, *, db_session=None, storage=None):
    """Delete an eligible document and its non-fiscal extraction attempts.

    R2 and PostgreSQL do not share a transaction. A committed ``deleting`` state
    makes interrupted cleanup traceable; failures become ``delete_failed`` and
    can be retried without database cascades.
    """
    session = db_session or db.session
    _validate_supplier_invoice_document_deletion(document)
    document_id = document.id
    storage_key = document.storage_key

    document.processing_status = SupplierInvoiceDocument.STATUS_DELETING
    try:
        session.commit()
    except Exception as exc:
        session.rollback()
        raise SupplierInvoiceDocumentDeletionPersistenceError(
            "No se ha podido preparar la eliminación del documento."
        ) from exc

    try:
        (storage or get_supplier_invoice_document_storage(current_app)).delete_document(
            storage_key=storage_key
        )
    except Exception as exc:
        _mark_supplier_invoice_document_delete_failed(session, document_id)
        raise SupplierInvoiceDocumentDeletionStorageError(
            "No se ha podido eliminar el documento privado. Puedes reintentarlo."
        ) from exc

    try:
        persisted_document = session.get(SupplierInvoiceDocument, document_id)
        if persisted_document is None:
            return
        for extraction in list(persisted_document.extractions):
            session.delete(extraction)
        session.flush()
        session.delete(persisted_document)
        session.commit()
    except Exception as exc:
        session.rollback()
        _mark_supplier_invoice_document_delete_failed(session, document_id)
        raise SupplierInvoiceDocumentDeletionPersistenceError(
            "El documento se ha marcado para reintento de eliminación."
        ) from exc


def _validate_supplier_invoice_document_deletion(document):
    if not isinstance(document, SupplierInvoiceDocument) or not getattr(document, "id", None):
        raise SupplierInvoiceDocumentDeletionBlockedError("El documento recibido no existe.")
    invoice = document.supplier_invoice
    if invoice is None or invoice.status not in _DELETABLE_INVOICE_STATUSES:
        raise SupplierInvoiceDocumentDeletionBlockedError(
            "Solo se pueden eliminar documentos de facturas recibidas en borrador o revisión."
        )
    if document.processing_status == SupplierInvoiceDocument.STATUS_DELETING:
        raise SupplierInvoiceDocumentDeletionBlockedError(
            "El documento ya se está eliminando. Espera antes de reintentar."
        )
    if document.processing_status in {
        SupplierInvoiceDocument.STATUS_EXTRACTING,
        SupplierInvoiceDocument.STATUS_APPLIED,
    }:
        raise SupplierInvoiceDocumentDeletionBlockedError(
            "No se puede eliminar un documento con una extracción aplicada o en curso."
        )
    for extraction in document.extractions:
        if extraction.status not in _DELETABLE_EXTRACTION_STATUSES:
            raise SupplierInvoiceDocumentDeletionBlockedError(
                "No se puede eliminar un documento con una extracción aplicada o en curso."
            )


def _mark_supplier_invoice_document_delete_failed(session, document_id):
    try:
        session.rollback()
        document = session.get(SupplierInvoiceDocument, document_id)
        if document is not None:
            document.processing_status = SupplierInvoiceDocument.STATUS_DELETE_FAILED
            session.commit()
    except Exception:
        session.rollback()


def _normalized_actor(actor):
    value = str(actor or "").strip()
    return value or None

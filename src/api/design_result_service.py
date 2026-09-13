"""Private final-result delivery for manually prepared design previews."""

from dataclasses import dataclass
import logging
from pathlib import Path
import re

from flask import current_app
from werkzeug.utils import secure_filename

from api.design_service import transition_design_request_status
from api.models import DesignRequest, db
from api.private_document_validation import (
    ALLOWED_PRIVATE_DOCUMENT_TYPES,
    MAX_PRIVATE_DOCUMENT_BYTES,
    PrivateDocumentValidationError,
    build_private_document_storage_key,
    validate_private_document_upload,
)
from api.private_object_storage import get_private_object_storage


DESIGN_RESULT_MAX_BYTES = MAX_PRIVATE_DOCUMENT_BYTES
DESIGN_RESULT_NAMESPACE = "design-results"
_RESULT_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_RESULT_METADATA_FIELDS = (
    "result_storage_key",
    "result_filename",
    "result_mime",
    "result_size",
    "result_sha256",
)


class DesignResultError(Exception):
    """Base error for design-result delivery operations."""


class DesignResultNotFoundError(DesignResultError):
    """Raised when the requested design preview does not exist."""


class DesignResultStateError(DesignResultError):
    """Raised when a request cannot safely receive a result."""


class DesignResultValidationError(DesignResultError):
    """Raised when the selected final file is unsafe or invalid."""


class DesignResultPersistenceError(DesignResultError):
    """Raised after R2 upload when result metadata cannot be persisted."""


@dataclass(frozen=True)
class DesignResultUploadResult:
    design_request: object
    storage_key: str
    storage: object


def result_metadata_state(design_request):
    """Return empty, partial, or complete without looking up private storage."""
    values = tuple(getattr(design_request, field, None) for field in _RESULT_METADATA_FIELDS)
    if not any(value is not None for value in values):
        return "empty"
    return "complete" if has_complete_result_metadata(design_request) else "partial"


def has_complete_result_metadata(design_request):
    storage_key = _normalized_text(getattr(design_request, "result_storage_key", None))
    filename = _normalized_text(getattr(design_request, "result_filename", None))
    mime_type = _normalized_text(getattr(design_request, "result_mime", None)).lower()
    sha256_value = _normalized_text(getattr(design_request, "result_sha256", None)).lower()
    file_size = getattr(design_request, "result_size", None)
    extension = Path(filename).suffix.lower()

    return bool(
        storage_key
        and filename
        and ALLOWED_PRIVATE_DOCUMENT_TYPES.get(extension) == mime_type
        and isinstance(file_size, int)
        and not isinstance(file_size, bool)
        and file_size > 0
        and _RESULT_SHA256_PATTERN.fullmatch(sha256_value)
    )


def is_design_result_available(design_request):
    return bool(
        design_request
        and getattr(design_request, "status", None) == DesignRequest.STATUS_DELIVERED
        and has_complete_result_metadata(design_request)
    )


def design_result_download_filename(design_request):
    """Return a safe attachment name from validated metadata only."""
    filename = secure_filename(_normalized_text(getattr(design_request, "result_filename", None)))
    if filename:
        return filename

    mime_type = _normalized_text(getattr(design_request, "result_mime", None)).lower()
    extension = next(
        (
            candidate
            for candidate, candidate_mime in ALLOWED_PRIVATE_DOCUMENT_TYPES.items()
            if candidate_mime == mime_type
        ),
        ".pdf",
    )
    reference = secure_filename(_normalized_text(getattr(design_request, "reference", None)))
    return f"diseno-previo-{reference or getattr(design_request, 'id', 'resultado')}{extension}"


def upload_design_result(
    *,
    design_request_id,
    file_storage,
    db_session=None,
    storage=None,
    now=None,
):
    """Upload one final file and transition an in-progress request to delivered.

    The caller owns the final commit. If flushing the metadata fails, this
    function compensates the private object before surfacing the error.
    """
    session = db_session or db.session
    design_request = (
        session.query(DesignRequest)
        .filter(DesignRequest.id == design_request_id)
        .with_for_update()
        .one_or_none()
    )
    if design_request is None:
        raise DesignResultNotFoundError("La solicitud de diseño no existe.")

    _assert_uploadable(design_request)
    try:
        validated = validate_private_document_upload(
            file_storage,
            max_bytes=int(current_app.config.get("DESIGN_RESULT_MAX_BYTES", DESIGN_RESULT_MAX_BYTES)),
        )
    except PrivateDocumentValidationError as exc:
        raise DesignResultValidationError(str(exc)) from exc

    extension = Path(validated.original_filename).suffix.lower()
    storage_key = build_private_document_storage_key(
        namespace=DESIGN_RESULT_NAMESPACE,
        extension=extension,
        now=now,
    )
    resolved_storage = storage or get_private_object_storage(current_app)
    resolved_storage.put_object(
        storage_key=storage_key,
        content=validated.content,
        mime_type=validated.mime_type,
    )

    try:
        design_request.result_storage_key = storage_key
        design_request.result_filename = validated.original_filename
        design_request.result_mime = validated.mime_type
        design_request.result_size = validated.file_size
        design_request.result_sha256 = validated.sha256
        transition_design_request_status(
            design_request=design_request,
            new_status=DesignRequest.STATUS_DELIVERED,
        )
        session.flush()
    except Exception as exc:
        _delete_uploaded_object(resolved_storage, storage_key)
        raise DesignResultPersistenceError(
            "No se ha podido guardar la referencia del resultado privado."
        ) from exc

    return DesignResultUploadResult(
        design_request=design_request,
        storage_key=storage_key,
        storage=resolved_storage,
    )


def compensate_design_result_upload(result, *, logger=None):
    """Best-effort cleanup after the caller's final database commit fails."""
    if result is None:
        return True
    try:
        result.storage.delete_object(storage_key=result.storage_key)
    except Exception:
        (logger or logging.getLogger(__name__)).exception(
            "Could not compensate private design result after database failure key=%s",
            result.storage_key,
        )
        return False
    return True


def _assert_uploadable(design_request):
    if design_request.status != DesignRequest.STATUS_IN_PROGRESS:
        if design_request.status == DesignRequest.STATUS_DELIVERED:
            raise DesignResultStateError("La solicitud ya tiene una entrega cerrada.")
        raise DesignResultStateError(
            "Solo se puede subir el resultado de una solicitud que está en curso."
        )

    metadata_state = result_metadata_state(design_request)
    if metadata_state == "complete":
        raise DesignResultStateError("La solicitud ya tiene un resultado asociado.")
    if metadata_state == "partial":
        raise DesignResultStateError(
            "La solicitud tiene metadatos de resultado incompletos y requiere revisión."
        )
    if not getattr(design_request, "order_id", None):
        raise DesignResultStateError(
            "La solicitud no está vinculada a un pedido confirmado."
        )


def _delete_uploaded_object(storage, storage_key):
    try:
        storage.delete_object(storage_key=storage_key)
    except Exception:
        logging.getLogger(__name__).exception(
            "Could not compensate private design result after metadata persistence failure key=%s",
            storage_key,
        )


def _normalized_text(value):
    return str(value or "").strip()

"""Validation primitives for private PDF and image uploads."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from werkzeug.utils import secure_filename


MAX_PRIVATE_DOCUMENT_BYTES = 15 * 1024 * 1024
ALLOWED_PRIVATE_DOCUMENT_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


class PrivateDocumentValidationError(ValueError):
    """Raised when a private upload is unsafe or invalid."""


@dataclass(frozen=True)
class ValidatedPrivateDocument:
    original_filename: str
    mime_type: str
    file_size: int
    sha256: str
    content: bytes


def validate_private_document_upload(
    file_storage,
    *,
    max_bytes=MAX_PRIVATE_DOCUMENT_BYTES,
    allowed_mime_types=None,
):
    if file_storage is None or not getattr(file_storage, "filename", None):
        raise PrivateDocumentValidationError("Selecciona un PDF, JPEG o PNG para subir.")

    original_filename = secure_filename(str(file_storage.filename))
    extension = Path(original_filename).suffix.lower()
    expected_mime_type = ALLOWED_PRIVATE_DOCUMENT_TYPES.get(extension)
    if not original_filename or expected_mime_type is None:
        raise PrivateDocumentValidationError("Solo se admiten archivos PDF, JPEG o PNG.")

    if allowed_mime_types is not None and expected_mime_type not in set(allowed_mime_types):
        raise PrivateDocumentValidationError("Solo se admiten archivos PDF.")

    declared_mime_type = str(getattr(file_storage, "mimetype", "") or "").lower().strip()
    if declared_mime_type != expected_mime_type:
        raise PrivateDocumentValidationError(
            "El tipo declarado del archivo no coincide con su extensión."
        )

    content = file_storage.stream.read(max_bytes + 1)
    if not content:
        raise PrivateDocumentValidationError("El archivo está vacío.")
    if len(content) > max_bytes:
        raise PrivateDocumentValidationError(
            "El archivo supera el tamaño máximo permitido de 15 MB."
        )

    detected_mime_type = _detect_private_document_mime_type(content)
    if detected_mime_type != expected_mime_type:
        raise PrivateDocumentValidationError(
            "El contenido del archivo no coincide con su tipo declarado."
        )

    return ValidatedPrivateDocument(
        original_filename=original_filename,
        mime_type=detected_mime_type,
        file_size=len(content),
        sha256=sha256(content).hexdigest(),
        content=content,
    )


def build_private_document_storage_key(*, namespace, extension, now=None):
    normalized_namespace = str(namespace or "").strip().strip("/")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", normalized_namespace):
        raise PrivateDocumentValidationError("El espacio privado del documento no es válido.")

    normalized_extension = str(extension or "").lower()
    if normalized_extension not in ALLOWED_PRIVATE_DOCUMENT_TYPES:
        raise PrivateDocumentValidationError("La extensión del documento no está permitida.")

    timestamp = now or datetime.now(timezone.utc)
    return f"{normalized_namespace}/{timestamp:%Y}/{timestamp:%m}/{uuid4().hex}{normalized_extension}"


def _detect_private_document_mime_type(content):
    if content.startswith(b"%PDF-"):
        try:
            PdfReader(BytesIO(content), strict=True)
        except (PdfReadError, ValueError, OSError) as exc:
            raise PrivateDocumentValidationError("El PDF no es legible.") from exc
        return "application/pdf"

    try:
        image = Image.open(BytesIO(content))
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise PrivateDocumentValidationError("La imagen no es válida.") from exc

    image_format = image.format.upper()
    if image_format == "JPEG":
        return "image/jpeg"
    if image_format == "PNG":
        return "image/png"
    raise PrivateDocumentValidationError("Solo se admiten imágenes JPEG o PNG.")

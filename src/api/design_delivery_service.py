"""Private, versioned deliverables for each design in a request."""

import json
import re
import struct
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from flask import current_app
from werkzeug.utils import secure_filename

from api.design_service import transition_design_request_status
from api.models import DesignDeliverable, DesignRequest
from api.private_document_validation import (
    PrivateDocumentValidationError,
    validate_private_document_upload,
)


MAX_GLB_BYTES = 25 * 1024 * 1024
MAX_REQUEST_BYTES = 60 * 1024 * 1024
MAX_MESSAGE_LENGTH = 2000
_GLB_JSON_CHUNK = 0x4E4F534A
_GLB_BINARY_CHUNK = 0x004E4942
_MIME_BY_KIND = {"glb": "model/gltf-binary", "image": None, "pdf": "application/pdf"}


class DesignDeliveryError(ValueError):
    pass


@dataclass
class DeliveryChanges:
    design_request: DesignRequest
    uploaded_keys: list[str]
    changed: bool


def validate_glb(file_storage):
    if not file_storage or Path(str(file_storage.filename or "")).suffix.lower() != ".glb":
        raise DesignDeliveryError("Selecciona un archivo GLB.")
    content = file_storage.stream.read(MAX_GLB_BYTES + 1)
    if len(content) > MAX_GLB_BYTES or len(content) < 20:
        raise DesignDeliveryError("El GLB está vacío, incompleto o supera 25 MB.")
    magic, version, declared_length = struct.unpack_from("<4sII", content)
    if magic != b"glTF" or version != 2 or declared_length != len(content):
        raise DesignDeliveryError("La cabecera del GLB no es válida.")
    offset = 12
    chunks = []
    while offset + 8 <= len(content):
        chunk_length, chunk_type = struct.unpack_from("<II", content, offset)
        offset += 8
        if chunk_length % 4 or offset + chunk_length > len(content):
            raise DesignDeliveryError("La estructura del GLB no es válida.")
        chunks.append((chunk_type, content[offset:offset + chunk_length]))
        offset += chunk_length
    if offset != len(content) or not chunks or chunks[0][0] != _GLB_JSON_CHUNK:
        raise DesignDeliveryError("El GLB no contiene una escena válida.")
    if any(kind not in {_GLB_JSON_CHUNK, _GLB_BINARY_CHUNK} for kind, _ in chunks[1:]):
        raise DesignDeliveryError("El GLB contiene bloques no admitidos.")
    try:
        scene = json.loads(chunks[0][1].decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise DesignDeliveryError("El JSON del GLB no es válido.") from exc
    if not isinstance(scene, dict) or not isinstance(scene.get("asset"), dict):
        raise DesignDeliveryError("El GLB no contiene una escena glTF 2.0.")
    if scene["asset"].get("version") != "2.0" or not isinstance(scene.get("scenes"), list) or not scene["scenes"]:
        raise DesignDeliveryError("El GLB no contiene una escena glTF 2.0.")
    if len(chunks) > 2 or (len(chunks) == 2 and chunks[1][0] != _GLB_BINARY_CHUNK):
        raise DesignDeliveryError("La estructura del GLB no es válida.")
    for group in ("buffers", "images"):
        resources = scene.get(group, [])
        if not isinstance(resources, list) or any(not isinstance(resource, dict) for resource in resources):
            raise DesignDeliveryError("La estructura del GLB no es válida.")
        for resource in resources:
            uri = resource.get("uri")
            if uri is not None and (not isinstance(uri, str) or not uri.startswith("data:")):
                raise DesignDeliveryError("El GLB no puede depender de recursos externos.")
            if group == "buffers" and uri is None and len(chunks) != 2:
                raise DesignDeliveryError("El GLB no contiene sus datos binarios.")
            if group == "images" and uri is None and "bufferView" not in resource:
                raise DesignDeliveryError("El GLB no contiene todas sus imágenes.")
    return content


def validate_delivery_file(kind, file_storage):
    if kind not in _MIME_BY_KIND:
        raise DesignDeliveryError("Tipo de entregable no permitido.")
    if kind == "glb":
        content = validate_glb(file_storage)
        return content, "model/gltf-binary", secure_filename(file_storage.filename) or "modelo.glb", ".glb"
    try:
        validated = validate_private_document_upload(file_storage)
    except PrivateDocumentValidationError as exc:
        raise DesignDeliveryError(str(exc)) from exc
    if kind == "pdf" and validated.mime_type != "application/pdf":
        raise DesignDeliveryError("El documento debe ser PDF.")
    if kind == "image" and validated.mime_type not in {"image/jpeg", "image/png"}:
        raise DesignDeliveryError("La imagen debe ser JPEG o PNG.")
    return validated.content, validated.mime_type, validated.original_filename, Path(validated.original_filename).suffix.lower()


def active_deliverables(design_request):
    return [file for item in design_request.items for file in item.deliverables if file.active]


def has_complete_delivery(design_request):
    items = getattr(design_request, "items", ()) or ()
    return bool(items) and all(
        any(file.active for file in (getattr(item, "deliverables", ()) or ())) for item in items
    )


def apply_delivery_changes(*, db_session, request_id, additions, retire_ids, message, deliver, storage):
    design_request = (
        db_session.query(DesignRequest).filter_by(id=request_id).with_for_update().one_or_none()
    )
    if design_request is None or design_request.status not in {
        DesignRequest.STATUS_IN_PROGRESS, DesignRequest.STATUS_DELIVERED
    }:
        raise DesignDeliveryError("La solicitud debe estar en curso o entregada.")
    if not design_request.order_id:
        raise DesignDeliveryError("La solicitud no tiene un pedido confirmado.")
    if not isinstance(message, str) or len(message) > MAX_MESSAGE_LENGTH:
        raise DesignDeliveryError("El mensaje supera el límite de 2000 caracteres.")
    if len(additions) > 30:
        raise DesignDeliveryError("No se pueden subir más de 30 archivos en una entrega.")
    item_ids = {item.id for item in design_request.items}
    files_by_id = {file.id: file for item in design_request.items for file in item.deliverables}
    retire_ids = set(retire_ids)
    if not retire_ids <= files_by_id.keys():
        raise DesignDeliveryError("Hay archivos que no pertenecen a esta solicitud.")
    for item_id, kind, _file in additions:
        if item_id not in item_ids or kind not in _MIME_BY_KIND:
            raise DesignDeliveryError("El archivo no pertenece a un diseño válido.")

    validated = [(item_id, kind, *validate_delivery_file(kind, file))
                 for item_id, kind, file in additions]
    existing_bytes = sum(
        file.size_bytes for file in files_by_id.values() if file.active and file.id not in retire_ids
    )
    if existing_bytes + sum(len(content) for _, _, content, *_ in validated) > MAX_REQUEST_BYTES:
        raise DesignDeliveryError("La entrega completa supera el límite de 60 MB.")
    active_glb = {file.item.id for file in files_by_id.values()
                  if file.active and file.kind == "glb" and file.id not in retire_ids}
    for item_id, kind, *_ in validated:
        if kind == "glb":
            if item_id in active_glb:
                raise DesignDeliveryError("Sustituye o retira primero el GLB activo de ese diseño.")
            active_glb.add(item_id)

    uploaded_keys = []
    try:
        for item_id, kind, content, mime_type, filename, extension in validated:
            key = f"design-results/{uuid.uuid4().hex}{extension}"
            uploaded_keys.append(key)
            storage.put_object(storage_key=key, content=content, mime_type=mime_type)
            db_session.add(DesignDeliverable(
                design_request_item_id=item_id, kind=kind, storage_key=key,
                filename=filename, mime_type=mime_type, size_bytes=len(content),
                sha256=sha256(content).hexdigest(),
            ))
        for file_id in retire_ids:
            files_by_id[file_id].active = False
            files_by_id[file_id].retired_at = datetime.now(timezone.utc)
        message_changed = (design_request.customer_message or "") != message.strip()
        design_request.customer_message = message.strip() or None
        db_session.flush()
        for item in design_request.items:
            db_session.expire(item, ["deliverables"])
        if deliver:
            if not has_complete_delivery(design_request) and not (
                design_request.status == DesignRequest.STATUS_DELIVERED
                and design_request.result_storage_key
            ):
                raise DesignDeliveryError("Cada diseño necesita al menos un entregable activo.")
            if design_request.status == DesignRequest.STATUS_IN_PROGRESS:
                transition_design_request_status(
                    design_request=design_request, new_status=DesignRequest.STATUS_DELIVERED
                )
        elif design_request.status == DesignRequest.STATUS_DELIVERED and not (
            has_complete_delivery(design_request) or design_request.result_storage_key
        ):
            raise DesignDeliveryError("No puedes dejar una entrega cerrada sin archivos para cada diseño.")
        db_session.flush()
        return DeliveryChanges(design_request, uploaded_keys, bool(validated or retire_ids or message_changed))
    except Exception:
        for key in uploaded_keys:
            try:
                storage.delete_object(storage_key=key)
            except Exception:
                current_app.logger.warning("Could not compensate private design upload")
        raise

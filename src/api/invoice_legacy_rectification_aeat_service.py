"""Controlled AEAT classification for rectificative v3 snapshots issued before R1/R4 existed."""

from datetime import datetime, timezone
from typing import Mapping

from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash


CORRECTIVE_INVOICE_TYPE = "corrective"
SUPPORTED_LEGACY_AEAT_TYPES = {"R1", "R4"}


class LegacyRectificationAeatClassificationError(Exception):
    """Raised when a legacy rectification cannot be manually classified safely."""


def is_legacy_rectification_eligible_for_manual_classification(invoice):
    """Return whether an issued legacy v3 rectification still needs an audited R1/R4 decision."""
    try:
        _validate_legacy_rectification_structure(invoice)
    except LegacyRectificationAeatClassificationError:
        return False

    aeat_type = _optional_text(getattr(invoice, "rectification_aeat_type", None))
    classified_at = getattr(invoice, "rectification_aeat_classified_at", None)
    classified_by = _optional_text(getattr(invoice, "rectification_aeat_classified_by", None))
    if classified_at or classified_by:
        return False
    return aeat_type is None or aeat_type in SUPPORTED_LEGACY_AEAT_TYPES


def classify_legacy_total_rectification_aeat(invoice, *, aeat_type, actor, classified_at=None):
    """Persist a human-confirmed R1/R4 decision without changing the frozen snapshot."""
    if not is_legacy_rectification_eligible_for_manual_classification(invoice):
        raise LegacyRectificationAeatClassificationError(
            "La rectificativa no es elegible para clasificación AEAT manual legacy."
        )

    normalized_type = _optional_text(aeat_type)
    if normalized_type not in SUPPORTED_LEGACY_AEAT_TYPES:
        raise LegacyRectificationAeatClassificationError(
            "La clasificación AEAT manual legacy solo admite R1 o R4."
        )
    existing_type = _optional_text(getattr(invoice, "rectification_aeat_type", None))
    if existing_type and existing_type != normalized_type:
        raise LegacyRectificationAeatClassificationError(
            "La clasificación AEAT legacy ya elegida debe confirmarse sin modificar su tipo fiscal."
        )
    normalized_actor = _optional_text(actor)
    if not normalized_actor:
        raise LegacyRectificationAeatClassificationError(
            "La clasificación AEAT manual legacy requiere identificar al administrador."
        )

    invoice.rectification_aeat_type = normalized_type
    invoice.rectification_aeat_classified_at = classified_at or datetime.now(timezone.utc).replace(tzinfo=None)
    invoice.rectification_aeat_classified_by = normalized_actor
    return invoice


def legacy_manual_aeat_type_for_export(invoice, snapshot):
    """Return a persisted manual R1/R4 only for an identifiable pre-AEAT v3 snapshot."""
    _validate_legacy_rectification_structure(invoice, snapshot=snapshot)

    aeat_type = _optional_text(getattr(invoice, "rectification_aeat_type", None))
    classified_at = getattr(invoice, "rectification_aeat_classified_at", None)
    classified_by = _optional_text(getattr(invoice, "rectification_aeat_classified_by", None))
    number = _optional_text(getattr(invoice, "invoice_number", None)) or "?"
    if not aeat_type or not classified_at or not classified_by:
        raise LegacyRectificationAeatClassificationError(
            f"La factura rectificativa {number} es histórica y requiere clasificación AEAT manual R1/R4 antes de exportar."
        )
    if aeat_type not in SUPPORTED_LEGACY_AEAT_TYPES:
        raise LegacyRectificationAeatClassificationError(
            f"La factura rectificativa {number} usa un tipo AEAT fuera del alcance actual."
        )
    return aeat_type


def legacy_rectification_details(invoice):
    """Expose frozen data needed by the Admin confirmation page, after eligibility checks."""
    snapshot = _validate_legacy_rectification_structure(invoice)
    rectification = snapshot["operation"]["rectification"]
    return {
        "original_invoice_number": rectification.get("original_invoice_number"),
        "original_invoice_issued_at": rectification.get("original_invoice_issued_at"),
        "reason": rectification.get("rectification_reason"),
        "reason_text": rectification.get("rectification_reason_text"),
        "tax_base": snapshot["totals"].get("tax_base"),
        "tax_amount": snapshot["totals"].get("tax_amount"),
        "total_amount": snapshot["totals"].get("total_amount"),
    }


def _validate_legacy_rectification_structure(invoice, *, snapshot=None):
    if getattr(invoice, "invoice_type", None) != CORRECTIVE_INVOICE_TYPE:
        raise LegacyRectificationAeatClassificationError("La factura no es rectificativa.")
    number = _optional_text(getattr(invoice, "invoice_number", None))
    if not number or not number.startswith("R"):
        raise LegacyRectificationAeatClassificationError("La rectificativa no pertenece a la serie R.")
    if getattr(invoice, "issued_at", None) is None:
        raise LegacyRectificationAeatClassificationError("La rectificativa debe estar emitida.")

    snapshot = snapshot if snapshot is not None else getattr(invoice, "invoice_snapshot", None)
    if not isinstance(snapshot, Mapping) or snapshot.get("schema_version") != 3:
        raise LegacyRectificationAeatClassificationError("La rectificativa legacy requiere un snapshot v3.")
    stored_hash = _optional_text(getattr(invoice, "invoice_snapshot_hash", None))
    if not stored_hash or calculate_invoice_snapshot_hash(snapshot) != stored_hash:
        raise LegacyRectificationAeatClassificationError("La integridad del snapshot fiscal no coincide.")

    operation = snapshot.get("operation")
    rectification = operation.get("rectification") if isinstance(operation, Mapping) else None
    if not isinstance(operation, Mapping) or operation.get("invoice_type") != CORRECTIVE_INVOICE_TYPE or not isinstance(rectification, Mapping):
        raise LegacyRectificationAeatClassificationError("El snapshot no describe una rectificativa válida.")
    if rectification.get("rectification_scope") != "total":
        raise LegacyRectificationAeatClassificationError("La clasificación legacy no admite rectificativas parciales.")
    if "aeat_type" in rectification:
        raise LegacyRectificationAeatClassificationError("La rectificativa ya usa el contrato AEAT actual.")
    if not isinstance(snapshot.get("totals"), Mapping):
        raise LegacyRectificationAeatClassificationError("La rectificativa no contiene totales fiscales congelados.")

    original = getattr(invoice, "original_invoice", None)
    original_id = rectification.get("original_invoice_id")
    if original is None or original_id != getattr(invoice, "original_invoice_id", None):
        raise LegacyRectificationAeatClassificationError("La rectificativa no coincide con su factura original persistida.")
    if original_id != getattr(original, "id", None):
        raise LegacyRectificationAeatClassificationError("La rectificativa tiene una referencia original incoherente.")
    if rectification.get("original_invoice_number") != getattr(original, "invoice_number", None):
        raise LegacyRectificationAeatClassificationError("La rectificativa no coincide con el número congelado de la original.")
    original_issued_at = getattr(original, "issued_at", None)
    if not original_issued_at or rectification.get("original_invoice_issued_at") != original_issued_at.isoformat():
        raise LegacyRectificationAeatClassificationError("La rectificativa no coincide con la fecha congelada de la original.")
    return snapshot


def _optional_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None

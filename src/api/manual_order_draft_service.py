"""Review mutable manual-order drafts with the canonical checkout quote engine."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
import math

from api.checkout_service import build_checkout_quote
from api.customer_snapshot import (
    CustomerSnapshotValidationError,
    extract_customer_snapshot,
)
from api.models import Users


class ManualOrderDraftError(ValueError):
    """Base error for manual-order draft review operations."""


class ManualOrderDraftNotEditableError(ManualOrderDraftError):
    """Raised when a non-draft order is submitted for review."""


class ManualOrderDraftValidationError(ManualOrderDraftError):
    """Raised when mutable draft data is incomplete or inconsistent."""


class ManualOrderDraftQuoteError(ManualOrderDraftError):
    """Raised when the canonical physical-product quote rejects the draft."""


def review_manual_order_draft(*, db_session, draft):
    """Persist a fresh authoritative quote on one editable draft without committing."""
    _require_editable_draft(draft)
    user = _resolve_draft_user(db_session, draft)
    customer_snapshot = normalize_manual_order_draft_customer(draft=draft, user=user)
    quote_snapshot = calculate_manual_order_draft_quote(draft)
    draft.customer_draft = customer_snapshot
    draft.discount_code = _normalize_discount_code(getattr(draft, "discount_code", None))
    draft.last_quote_snapshot = quote_snapshot
    draft.quote_fingerprint = build_manual_order_draft_fingerprint(
        draft,
        customer_snapshot=customer_snapshot,
        quote_snapshot=quote_snapshot,
    )
    db_session.flush()
    return quote_snapshot


def calculate_manual_order_draft_quote(draft):
    """Build one fresh quote without mutating the draft or its reviewed snapshot."""
    raw_products = build_manual_order_draft_quote_input(draft)
    discount_code = _normalize_discount_code(getattr(draft, "discount_code", None))

    try:
        quote_snapshot = build_checkout_quote(
            raw_products=raw_products,
            discount_code=discount_code,
        )
    except ValueError as exc:
        raise ManualOrderDraftQuoteError(str(exc)) from exc

    if discount_code and not quote_snapshot.get("discount_code_valid"):
        raise ManualOrderDraftQuoteError("El código de descuento no es válido.")
    return deepcopy(quote_snapshot)


def manual_order_draft_quote_snapshots_match(reviewed_quote, current_quote):
    """Compare two quote snapshots independently from JSON key ordering."""
    return _canonical_quote_snapshot(reviewed_quote) == _canonical_quote_snapshot(current_quote)


def normalize_manual_order_draft_customer(*, draft, user):
    """Normalize a complete customer snapshot without mutating the User profile."""
    customer_draft = getattr(draft, "customer_draft", None)
    if not isinstance(customer_draft, Mapping):
        raise ManualOrderDraftValidationError(
            "El borrador debe incluir los datos de cliente y facturación."
        )

    try:
        customer_snapshot = extract_customer_snapshot(
            customer_draft,
            require_checkout_fields=True,
        )
    except CustomerSnapshotValidationError as exc:
        raise ManualOrderDraftValidationError(str(exc)) from exc

    user_email = _canonical_email(getattr(user, "email", None))
    customer_email = _canonical_email(customer_snapshot.get("email"))
    if user_email is None:
        raise ManualOrderDraftValidationError(
            "El usuario del borrador no tiene un email válido."
        )
    if customer_email != user_email:
        raise ManualOrderDraftValidationError(
            "El email del cliente debe coincidir con el email del usuario asociado."
        )
    return customer_snapshot


def build_manual_order_draft_quote_input(draft):
    """Adapt ordered draft lines to the exact physical checkout quote contract."""
    draft_lines = tuple(getattr(draft, "lines", ()) or ())
    if not draft_lines:
        raise ManualOrderDraftValidationError(
            "El borrador debe contener al menos una configuración."
        )

    ordered_lines = []
    seen_positions = set()
    for line in draft_lines:
        position = getattr(line, "position", None)
        if isinstance(position, bool) or not isinstance(position, int) or position < 0:
            raise ManualOrderDraftValidationError(
                "La posición de una configuración no es válida."
            )
        if position in seen_positions:
            raise ManualOrderDraftValidationError(
                "Las posiciones de las configuraciones no pueden repetirse."
            )
        seen_positions.add(position)
        ordered_lines.append((position, getattr(line, "id", None), line))

    raw_products = []
    for _position, _line_id, line in sorted(
        ordered_lines,
        key=lambda value: (value[0], value[1] if value[1] is not None else -1),
    ):
        raw_products.append({
            "product_id": getattr(line, "product_id", None),
            "quantity": getattr(line, "quantity", None),
            "alto": getattr(line, "alto", None),
            "ancho": getattr(line, "ancho", None),
            "anclaje": getattr(line, "anclaje", None),
            "color": getattr(line, "color", None),
            "screw_option": getattr(line, "screw_option", None),
        })
    return raw_products


def build_manual_order_draft_fingerprint(
    draft,
    *,
    customer_snapshot=None,
    quote_snapshot=None,
):
    """Hash the reviewed commercial identity deterministically with SHA-256."""
    _require_editable_draft(draft)
    if customer_snapshot is None:
        user = getattr(draft, "user", None)
        if user is None:
            raise ManualOrderDraftValidationError("El usuario del borrador no es válido.")
        customer_snapshot = normalize_manual_order_draft_customer(draft=draft, user=user)
    if quote_snapshot is None:
        quote_snapshot = getattr(draft, "last_quote_snapshot", None)
    if not isinstance(quote_snapshot, Mapping):
        raise ManualOrderDraftValidationError(
            "El borrador no tiene una revisión de presupuesto válida."
        )

    payload = {
        "version": 1,
        "user_id": getattr(draft, "user_id", None),
        "customer_draft": customer_snapshot,
        "discount_code": _normalize_discount_code(getattr(draft, "discount_code", None)),
        "lines": build_manual_order_draft_quote_input(draft),
        "estimated_delivery_at": _validated_delivery_date(
            getattr(draft, "estimated_delivery_at", None)
        ),
        "estimated_delivery_note": _normalized_optional_text(
            getattr(draft, "estimated_delivery_note", None),
            "estimated_delivery_note",
        ),
        "quote_snapshot": quote_snapshot,
    }
    canonical_payload = _canonicalize_fingerprint_value(payload)
    serialized = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def is_manual_order_draft_review_current(draft):
    """Return whether editable data still matches its stored review fingerprint."""
    stored_fingerprint = getattr(draft, "quote_fingerprint", None)
    quote_snapshot = getattr(draft, "last_quote_snapshot", None)
    if not isinstance(stored_fingerprint, str) or not stored_fingerprint:
        return False
    if not isinstance(quote_snapshot, Mapping):
        return False

    try:
        current_fingerprint = build_manual_order_draft_fingerprint(
            draft,
            quote_snapshot=quote_snapshot,
        )
    except ManualOrderDraftError:
        return False
    return current_fingerprint == stored_fingerprint


def invalidate_manual_order_draft_review(draft):
    """Clear derived review data after a future draft-editing operation."""
    draft.last_quote_snapshot = None
    draft.quote_fingerprint = None


def _canonical_quote_snapshot(quote_snapshot):
    if not isinstance(quote_snapshot, Mapping):
        raise ManualOrderDraftValidationError(
            "El borrador no tiene una revisión de presupuesto válida."
        )
    return _canonicalize_fingerprint_value(quote_snapshot)


def _require_editable_draft(draft):
    if draft is None:
        raise ManualOrderDraftValidationError("El borrador manual no es válido.")
    if getattr(draft, "status", None) != "draft" or getattr(
        draft,
        "issued_order_id",
        None,
    ) is not None:
        raise ManualOrderDraftNotEditableError(
            "Solo se pueden revisar borradores manuales en estado draft."
        )


def _resolve_draft_user(db_session, draft):
    user_id = getattr(draft, "user_id", None)
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id < 1:
        raise ManualOrderDraftValidationError("El usuario del borrador no es válido.")

    user = getattr(draft, "user", None)
    if getattr(user, "id", None) != user_id:
        user = db_session.get(Users, user_id)
    if user is None or getattr(user, "id", None) != user_id:
        raise ManualOrderDraftValidationError("El usuario del borrador no existe.")
    return user


def _normalize_discount_code(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ManualOrderDraftValidationError("El código de descuento no es válido.")
    normalized = value.strip().upper()
    return normalized or None


def _canonical_email(value):
    if not isinstance(value, str):
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _normalized_optional_text(value, field_name):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ManualOrderDraftValidationError(f"El campo '{field_name}' debe ser texto.")
    normalized = value.strip()
    return normalized or None


def _validated_delivery_date(value):
    if value is None:
        return None
    if isinstance(value, datetime) or not isinstance(value, date):
        raise ManualOrderDraftValidationError(
            "La fecha estimada de entrega no es válida."
        )
    return value


def _canonicalize_fingerprint_value(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Decimal):
        return {
            "__manual_order_draft_type__": "decimal",
            "value": _decimal_text(value),
        }
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ManualOrderDraftValidationError(
                "El borrador contiene un número no válido."
            )
        return {
            "__manual_order_draft_type__": "float",
            "value": format(value, ".17g"),
        }
    if isinstance(value, datetime):
        return {
            "__manual_order_draft_type__": "datetime",
            "value": value.isoformat(),
        }
    if isinstance(value, date):
        return {
            "__manual_order_draft_type__": "date",
            "value": value.isoformat(),
        }
    if isinstance(value, Mapping):
        normalized = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ManualOrderDraftValidationError(
                    "El borrador contiene una clave de datos no válida."
                )
            normalized[key] = _canonicalize_fingerprint_value(item)
        return normalized
    if isinstance(value, (list, tuple)):
        return [_canonicalize_fingerprint_value(item) for item in value]
    raise ManualOrderDraftValidationError(
        "El borrador contiene un valor no serializable."
    )


def _decimal_text(value):
    if not value.is_finite():
        raise ManualOrderDraftValidationError("El borrador contiene un número no válido.")
    return format(value.normalize(), "f")

"""Emit reviewed manual-order drafts through the canonical Order creation path."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import uuid4

from api.confirmed_order_context_service import (
    ADMIN_EXTERNAL_SOURCE,
    CONFIRMED_PAYMENT_STATUS,
    ConfirmedOrderContextError,
    ConfirmedOrderInput,
    confirmation_currency_from_quote,
    confirmation_payment_amount_from_quote,
    validate_admin_external_payment_evidence,
)
from api.manual_order_draft_service import (
    ManualOrderDraftError,
    ManualOrderDraftQuoteError,
    ManualOrderDraftValidationError,
    calculate_manual_order_draft_quote,
    is_manual_order_draft_review_current,
    manual_order_draft_quote_snapshots_match,
    normalize_manual_order_draft_customer,
    resolve_manual_order_draft_user,
)
from api.models import ConfirmedOrderContext, ManualOrderDraft, Orders
from api.order_creation_service import create_order_from_confirmed_input


SUPPORTED_MANUAL_PAYMENT_METHODS = frozenset(
    {"bank_transfer", "cash", "external_other"}
)


class ManualOrderDraftIssueError(ManualOrderDraftError):
    """Base error for a failed manual-order emission."""


class ManualOrderDraftNotFoundError(ManualOrderDraftIssueError):
    """Raised when the requested draft does not exist."""


class ManualOrderDraftCancelledError(ManualOrderDraftIssueError):
    """Raised when a cancelled draft is submitted for issuance."""


class ManualOrderDraftIssuedIntegrityError(ManualOrderDraftIssueError):
    """Raised when a draft's issued state cannot be trusted safely."""


class ManualOrderDraftReviewRequiredError(ManualOrderDraftIssueError):
    """Raised when no complete reviewed quote is available."""


class ManualOrderDraftReviewStaleError(ManualOrderDraftIssueError):
    """Raised when editable data no longer matches the reviewed fingerprint."""


class ManualOrderDraftQuoteChangedError(ManualOrderDraftIssueError):
    """Raised when a fresh authoritative quote differs from the reviewed quote."""


class ManualOrderDraftPaymentEvidenceError(ManualOrderDraftIssueError):
    """Raised when external-payment evidence is incomplete or inconsistent."""


class ManualOrderDraftCustomerError(ManualOrderDraftIssueError):
    """Raised when the frozen customer input is no longer valid for its user."""


class ManualOrderDraftOrderCreationError(ManualOrderDraftIssueError):
    """Raised when canonical Order creation rejects an otherwise reviewed draft."""


@dataclass(frozen=True)
class ManualOrderDraftIssueResult:
    """Describe whether this call created the canonical order or reused it."""

    order: Orders
    created: bool


def issue_manual_order_draft(*, db_session, draft_id, actor):
    """Convert one reviewed, externally paid draft into its canonical Order.

    The caller owns the surrounding transaction. This service intentionally never
    commits, rolls back, creates a CheckoutSession, or triggers external effects.
    """
    draft = _load_draft_for_issue(db_session=db_session, draft_id=draft_id)
    existing_order = _existing_issued_order_or_error(db_session=db_session, draft=draft)
    if existing_order is not None:
        return ManualOrderDraftIssueResult(order=existing_order, created=False)

    if draft.status == ManualOrderDraft.STATUS_CANCELLED:
        raise ManualOrderDraftCancelledError("El borrador manual está cancelado.")
    if draft.status != ManualOrderDraft.STATUS_DRAFT or draft.issued_order_id is not None:
        raise ManualOrderDraftIssuedIntegrityError(
            "El estado del borrador manual no es coherente para emitirlo."
        )

    user = _resolve_draft_user(db_session=db_session, draft=draft)
    customer_snapshot = _normalize_customer_snapshot(draft=draft, user=user)
    _require_complete_current_review(draft)

    try:
        current_quote = calculate_manual_order_draft_quote(draft)
    except ManualOrderDraftQuoteError as exc:
        raise ManualOrderDraftQuoteChangedError(
            "El presupuesto revisado ya no es válido; vuelve a revisarlo antes de emitir."
        ) from exc

    try:
        quote_matches_review = manual_order_draft_quote_snapshots_match(
            draft.last_quote_snapshot,
            current_quote,
        )
    except ManualOrderDraftValidationError as exc:
        raise ManualOrderDraftReviewRequiredError(
            "El borrador no tiene una revisión de presupuesto válida."
        ) from exc
    if not quote_matches_review:
        raise ManualOrderDraftQuoteChangedError(
            "El presupuesto ha cambiado desde la última revisión; revísalo de nuevo."
        )

    confirmation = _build_manual_confirmation(
        draft=draft,
        actor=actor,
        quote_snapshot=current_quote,
    )
    _ensure_issuance_key(draft)
    _ensure_no_conflicting_confirmation_context(db_session=db_session, draft=draft)

    try:
        creation = create_order_from_confirmed_input(
            db_session=db_session,
            user=user,
            quote_snapshot=current_quote,
            customer_snapshot=customer_snapshot,
            confirmation=confirmation,
            estimated_delivery_at=draft.estimated_delivery_at,
            estimated_delivery_note=draft.estimated_delivery_note,
        )
    except (ConfirmedOrderContextError, ValueError) as exc:
        raise ManualOrderDraftOrderCreationError(
            "No se pudo crear el pedido manual con el contexto confirmado."
        ) from exc

    order = creation.order
    draft.status = ManualOrderDraft.STATUS_ISSUED
    draft.issued_order_id = order.id
    db_session.flush()
    return ManualOrderDraftIssueResult(order=order, created=True)


def _load_draft_for_issue(*, db_session, draft_id):
    normalized_draft_id = _required_positive_integer(draft_id, "El identificador del borrador")
    draft = (
        db_session.query(ManualOrderDraft)
        .filter(ManualOrderDraft.id == normalized_draft_id)
        .with_for_update()
        .one_or_none()
    )
    if draft is None:
        raise ManualOrderDraftNotFoundError("El borrador manual no existe.")
    return draft


def _existing_issued_order_or_error(*, db_session, draft):
    if draft.status != ManualOrderDraft.STATUS_ISSUED:
        return None
    if draft.issued_order_id is None:
        raise ManualOrderDraftIssuedIntegrityError(
            "El borrador emitido no conserva su pedido asociado."
        )

    order = db_session.get(Orders, draft.issued_order_id)
    if order is None:
        raise ManualOrderDraftIssuedIntegrityError(
            "El borrador emitido apunta a un pedido inexistente."
        )
    return order


def _require_complete_current_review(draft):
    reviewed_quote = getattr(draft, "last_quote_snapshot", None)
    fingerprint = getattr(draft, "quote_fingerprint", None)
    if not isinstance(reviewed_quote, Mapping) or not reviewed_quote:
        raise ManualOrderDraftReviewRequiredError(
            "El borrador debe revisarse antes de emitirlo."
        )
    if not isinstance(fingerprint, str) or not fingerprint.strip():
        raise ManualOrderDraftReviewRequiredError(
            "El borrador debe revisarse antes de emitirlo."
        )
    if not is_manual_order_draft_review_current(draft):
        raise ManualOrderDraftReviewStaleError(
            "El borrador ha cambiado desde la última revisión."
        )


def _resolve_draft_user(*, db_session, draft):
    try:
        return resolve_manual_order_draft_user(db_session, draft)
    except ManualOrderDraftValidationError as exc:
        raise ManualOrderDraftCustomerError(
            "Los datos de cliente del borrador no son válidos."
        ) from exc


def _normalize_customer_snapshot(*, draft, user):
    try:
        return normalize_manual_order_draft_customer(draft=draft, user=user)
    except ManualOrderDraftValidationError as exc:
        raise ManualOrderDraftCustomerError(
            "Los datos del cliente del borrador no son válidos."
        ) from exc


def _build_manual_confirmation(*, draft, actor, quote_snapshot):
    payment_method = _normalized_payment_method(getattr(draft, "payment_method", None))
    payment_reference = _normalized_optional_text(
        getattr(draft, "payment_reference", None),
        "La referencia de pago no es válida.",
    )
    confirmed_by = _normalized_required_text(
        actor,
        "Debe indicarse quién confirmó el pago externo.",
    )
    internal_note = _payment_evidence_note(draft)
    payment_confirmed_at = getattr(draft, "payment_confirmed_at", None)

    try:
        validate_admin_external_payment_evidence(
            payment_method=payment_method,
            payment_reference=payment_reference,
            payment_confirmed_at=payment_confirmed_at,
            confirmed_by=confirmed_by,
            internal_note=internal_note,
            source_checkout_session_id=None,
        )
    except ConfirmedOrderContextError as exc:
        raise ManualOrderDraftPaymentEvidenceError(str(exc)) from exc

    return ConfirmedOrderInput(
        source=ADMIN_EXTERNAL_SOURCE,
        payment_method=payment_method,
        payment_reference=payment_reference,
        payment_confirmed_at=payment_confirmed_at,
        payment_amount=confirmation_payment_amount_from_quote(quote_snapshot),
        currency=confirmation_currency_from_quote(quote_snapshot),
        payment_status=CONFIRMED_PAYMENT_STATUS,
        provider_identifiers=None,
        confirmed_by=confirmed_by,
        source_manual_draft_id=draft.id,
        internal_note=internal_note,
    )


def _payment_evidence_note(draft):
    internal_note = _normalized_optional_text(
        getattr(draft, "internal_note", None),
        "La nota interna del pago no es válida.",
    )
    if internal_note is not None:
        return internal_note
    return _normalized_optional_text(
        getattr(draft, "payment_note", None),
        "La evidencia del pago no es válida.",
    )


def _normalized_payment_method(value):
    payment_method = _normalized_required_text(
        value,
        "Debe indicarse el método de pago externo.",
    ).lower()
    if payment_method not in SUPPORTED_MANUAL_PAYMENT_METHODS:
        raise ManualOrderDraftPaymentEvidenceError(
            "El método de pago externo no es compatible con un pedido manual."
        )
    return payment_method


def _normalized_required_text(value, error_message):
    normalized = _normalized_optional_text(value, error_message)
    if normalized is None:
        raise ManualOrderDraftPaymentEvidenceError(error_message)
    return normalized


def _normalized_optional_text(value, error_message):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ManualOrderDraftPaymentEvidenceError(error_message)
    normalized = value.strip()
    return normalized or None


def _ensure_issuance_key(draft):
    issuance_key = getattr(draft, "issuance_key", None)
    if issuance_key is None or (isinstance(issuance_key, str) and not issuance_key.strip()):
        draft.issuance_key = str(uuid4())
        return
    if not isinstance(issuance_key, str):
        raise ManualOrderDraftIssuedIntegrityError(
            "La clave de emisión del borrador no es válida."
        )


def _ensure_no_conflicting_confirmation_context(*, db_session, draft):
    existing_context = (
        db_session.query(ConfirmedOrderContext)
        .filter(ConfirmedOrderContext.source_manual_draft_id == draft.id)
        .one_or_none()
    )
    if existing_context is not None:
        raise ManualOrderDraftIssuedIntegrityError(
            "El borrador ya está vinculado a otro contexto de pedido confirmado."
        )


def _required_positive_integer(value, error_message):
    if isinstance(value, bool):
        raise ManualOrderDraftNotFoundError(f"{error_message} no es válido.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ManualOrderDraftNotFoundError(f"{error_message} no es válido.") from exc
    if parsed < 1:
        raise ManualOrderDraftNotFoundError(f"{error_message} no es válido.")
    return parsed

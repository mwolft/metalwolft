"""Persist immutable order-confirmation contexts from validated inputs."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from api.models import ConfirmedOrderContext


WEB_CHECKOUT_SOURCE = "web_checkout"
ADMIN_EXTERNAL_SOURCE = "admin_external"
CONFIRMED_PAYMENT_STATUS = "confirmed"
SUPPORTED_CONFIRMATION_SOURCES = frozenset(
    {WEB_CHECKOUT_SOURCE, ADMIN_EXTERNAL_SOURCE}
)
SUPPORTED_PAYMENT_STATUSES = frozenset({CONFIRMED_PAYMENT_STATUS})
SUPPORTED_PAYMENT_METHODS = frozenset(
    {"stripe", "paypal", "bank_transfer", "cash", "external_other"}
)
SUPPORTED_WEB_PAYMENT_METHODS = frozenset({"stripe", "paypal"})
SUPPORTED_CURRENCY = "EUR"
MONEY_QUANTUM = Decimal("0.01")


class ConfirmedOrderContextError(ValueError):
    """Raised when a confirmation cannot produce a canonical order context."""


@dataclass(frozen=True)
class ConfirmedOrderInput:
    """Validated, source-neutral data required to persist a confirmation record."""

    source: str
    payment_method: str
    payment_reference: str | None
    payment_confirmed_at: datetime | None
    payment_amount: Decimal
    currency: str
    payment_status: str = CONFIRMED_PAYMENT_STATUS
    provider_identifiers: Mapping[str, str] | None = None
    confirmed_by: str | None = None
    source_checkout_session_id: int | None = None
    source_manual_draft_id: int | None = None
    internal_note: str | None = None


@dataclass(frozen=True)
class _ValidatedConfirmation:
    payment_reference: str | None
    provider_identifiers: dict[str, str] | None
    confirmed_by: str | None
    internal_note: str | None


def build_web_checkout_confirmation_input(checkout_session):
    """Adapt a paid CheckoutSession into source-neutral confirmation data."""
    checkout_session_id = getattr(checkout_session, "id", None)
    if checkout_session_id is None:
        raise ConfirmedOrderContextError("La sesión de checkout confirmada es obligatoria.")
    if getattr(checkout_session, "status", None) not in {"paid", "order_created"}:
        raise ConfirmedOrderContextError("La sesión de checkout debe estar confirmada antes de crear el contexto.")

    quote_snapshot = _required_snapshot(
        getattr(checkout_session, "quote_snapshot", None),
        "quote_snapshot",
    )
    _required_snapshot(
        getattr(checkout_session, "customer_snapshot", None),
        "customer_snapshot",
    )
    payment_method = _payment_method(checkout_session)

    return ConfirmedOrderInput(
        source=WEB_CHECKOUT_SOURCE,
        payment_method=payment_method,
        payment_reference=_payment_reference(checkout_session, payment_method),
        provider_identifiers=_web_provider_identifiers(checkout_session, payment_method),
        # CheckoutSessions does not persist an exact provider payment timestamp yet.
        payment_confirmed_at=None,
        payment_amount=_payment_amount(quote_snapshot),
        currency=_currency(quote_snapshot),
        payment_status=CONFIRMED_PAYMENT_STATUS,
        confirmed_by=None,
        source_checkout_session_id=checkout_session_id,
    )


def persist_confirmed_order_context(
    *,
    db_session,
    order,
    quote_snapshot,
    customer_snapshot,
    confirmation,
):
    """Persist one immutable context inside the caller-owned transaction."""
    order_id = getattr(order, "id", None)
    if order_id is None:
        raise ConfirmedOrderContextError("El pedido debe persistirse antes de crear su contexto confirmado.")
    if not isinstance(confirmation, ConfirmedOrderInput):
        raise ConfirmedOrderContextError("El contexto de confirmación no es válido.")

    quote_snapshot = _required_snapshot(quote_snapshot, "quote_snapshot")
    customer_snapshot = _required_snapshot(customer_snapshot, "customer_snapshot")
    validated_confirmation = _validate_confirmation_against_quote(
        confirmation,
        quote_snapshot,
    )

    existing_context = db_session.query(ConfirmedOrderContext).filter_by(order_id=order_id).one_or_none()
    if existing_context is not None:
        return existing_context, False

    _ensure_source_is_available(
        db_session=db_session,
        order_id=order_id,
        field_name="source_checkout_session_id",
        source_id=confirmation.source_checkout_session_id,
        already_linked_message="La sesión de checkout ya pertenece a otro pedido confirmado.",
    )
    _ensure_source_is_available(
        db_session=db_session,
        order_id=order_id,
        field_name="source_manual_draft_id",
        source_id=confirmation.source_manual_draft_id,
        already_linked_message="El borrador manual ya pertenece a otro pedido confirmado.",
    )

    context = ConfirmedOrderContext(
        order_id=order_id,
        source=confirmation.source,
        quote_snapshot=deepcopy(dict(quote_snapshot)),
        customer_snapshot=deepcopy(dict(customer_snapshot)),
        payment_method=confirmation.payment_method,
        payment_status=confirmation.payment_status,
        payment_reference=validated_confirmation.payment_reference,
        provider_identifiers=deepcopy(validated_confirmation.provider_identifiers),
        payment_confirmed_at=confirmation.payment_confirmed_at,
        payment_amount=confirmation.payment_amount,
        currency=confirmation.currency,
        confirmed_by=validated_confirmation.confirmed_by,
        source_checkout_session_id=confirmation.source_checkout_session_id,
        source_manual_draft_id=confirmation.source_manual_draft_id,
        internal_note=validated_confirmation.internal_note,
    )
    db_session.add(context)
    db_session.flush()
    return context, True


def create_web_checkout_confirmed_order_context(*, db_session, order, checkout_session):
    """Backward-compatible convenience wrapper for existing callers."""
    source_order_id = getattr(checkout_session, "order_id", None)
    order_id = getattr(order, "id", None)
    if source_order_id not in (None, order_id):
        raise ConfirmedOrderContextError("La sesión de checkout pertenece a otro pedido.")

    confirmation = build_web_checkout_confirmation_input(checkout_session)
    return persist_confirmed_order_context(
        db_session=db_session,
        order=order,
        quote_snapshot=getattr(checkout_session, "quote_snapshot", None),
        customer_snapshot=getattr(checkout_session, "customer_snapshot", None),
        confirmation=confirmation,
    )


def _required_snapshot(value, field_name):
    if not isinstance(value, Mapping):
        raise ConfirmedOrderContextError(f"{field_name} debe ser un objeto válido.")
    return value


def _ensure_source_is_available(*, db_session, order_id, field_name, source_id, already_linked_message):
    if source_id is None:
        return

    source_context = (
        db_session.query(ConfirmedOrderContext)
        .filter(getattr(ConfirmedOrderContext, field_name) == source_id)
        .one_or_none()
    )
    if source_context is not None:
        if source_context.order_id == order_id:
            return
        raise ConfirmedOrderContextError(already_linked_message)


def _validate_confirmation_against_quote(confirmation, quote_snapshot):
    _require_allowed_value(
        confirmation.source,
        SUPPORTED_CONFIRMATION_SOURCES,
        "El origen de confirmación no es válido.",
    )
    _require_allowed_value(
        confirmation.payment_method,
        SUPPORTED_PAYMENT_METHODS,
        "El método de pago confirmado no es válido.",
    )
    _require_allowed_value(
        confirmation.payment_status,
        SUPPORTED_PAYMENT_STATUSES,
        "El estado de pago confirmado no es válido.",
    )
    if confirmation.payment_confirmed_at is not None and not isinstance(
        confirmation.payment_confirmed_at,
        datetime,
    ):
        raise ConfirmedOrderContextError("La fecha de confirmación del pago no es válida.")

    payment_amount = _payment_amount(quote_snapshot)
    if confirmation.payment_amount != payment_amount:
        raise ConfirmedOrderContextError("El importe confirmado no coincide con el total congelado.")

    currency = _currency(quote_snapshot)
    if confirmation.currency != currency:
        raise ConfirmedOrderContextError("La moneda confirmada no coincide con el checkout congelado.")

    payment_reference = _optional_payment_reference(confirmation.payment_reference)
    provider_identifiers = _normalized_provider_identifiers(confirmation.provider_identifiers)
    confirmed_by = _optional_text(confirmation.confirmed_by, "La persona que confirmó el pago no es válida.")
    internal_note = _optional_text(confirmation.internal_note, "La nota interna del pago no es válida.")

    if confirmation.source == WEB_CHECKOUT_SOURCE:
        _validate_web_checkout_confirmation(
            confirmation,
            payment_reference,
            provider_identifiers,
        )
    else:
        validate_admin_external_payment_evidence(
            payment_method=confirmation.payment_method,
            payment_reference=payment_reference,
            payment_confirmed_at=confirmation.payment_confirmed_at,
            confirmed_by=confirmed_by,
            internal_note=internal_note,
            source_checkout_session_id=confirmation.source_checkout_session_id,
        )

    return _ValidatedConfirmation(
        payment_reference=payment_reference,
        provider_identifiers=provider_identifiers,
        confirmed_by=confirmed_by,
        internal_note=internal_note,
    )


def _require_allowed_value(value, allowed_values, error_message):
    if value not in allowed_values:
        raise ConfirmedOrderContextError(error_message)


def _validate_web_checkout_confirmation(
    confirmation,
    payment_reference,
    provider_identifiers,
):
    if confirmation.payment_method not in SUPPORTED_WEB_PAYMENT_METHODS:
        raise ConfirmedOrderContextError("El método de pago web confirmado no es compatible.")
    if confirmation.source_checkout_session_id is None:
        raise ConfirmedOrderContextError("El checkout web confirmado debe conservar su sesión de origen.")
    if payment_reference is None:
        raise ConfirmedOrderContextError("La sesión de checkout pagada no tiene una referencia de pago válida.")
    if not provider_identifiers:
        raise ConfirmedOrderContextError("El checkout web debe conservar los identificadores reales del proveedor.")

    if confirmation.payment_method == "stripe":
        if provider_identifiers.get("payment_intent_id") != payment_reference:
            raise ConfirmedOrderContextError("El contexto Stripe no conserva el payment_intent_id real.")
        return

    paypal_identifiers = {
        value
        for key, value in provider_identifiers.items()
        if key in {"provider_order_id", "provider_capture_id"}
    }
    if not paypal_identifiers or payment_reference not in paypal_identifiers:
        raise ConfirmedOrderContextError("El contexto PayPal no conserva la referencia real del proveedor.")


def validate_admin_external_payment_evidence(
    *,
    payment_method,
    payment_reference,
    payment_confirmed_at,
    confirmed_by,
    internal_note,
    source_checkout_session_id=None,
):
    """Validate the durable evidence required for any admin-external payment.

    This is intentionally shared by confirmation persistence and invoice-context
    validation so an issued order cannot pass one boundary and fail the other.
    """
    if source_checkout_session_id is not None:
        raise ConfirmedOrderContextError("Un contexto administrativo no puede reutilizar una CheckoutSession.")
    if not isinstance(payment_confirmed_at, datetime):
        raise ConfirmedOrderContextError(
            "Un pago administrativo requiere la fecha real de confirmación."
        )
    if not _has_nonempty_text(confirmed_by):
        raise ConfirmedOrderContextError(
            "Un pago administrativo requiere quién lo confirmó."
        )

    if payment_method == "bank_transfer":
        if payment_reference is None:
            raise ConfirmedOrderContextError(
                "Una transferencia requiere una referencia bancaria real."
            )
        return

    if payment_method == "cash":
        if not _has_nonempty_text(internal_note):
            raise ConfirmedOrderContextError(
                "Un pago en efectivo requiere una nota interna."
            )
        return

    if payment_method == "external_other":
        if payment_reference is None and not _has_nonempty_text(internal_note):
            raise ConfirmedOrderContextError(
                "Un pago externo requiere referencia o nota interna de evidencia."
            )
        return

    if payment_method in SUPPORTED_WEB_PAYMENT_METHODS and payment_reference is None:
        raise ConfirmedOrderContextError("Stripe y PayPal requieren una referencia de pago real.")


def confirmation_payment_amount_from_quote(quote_snapshot):
    """Return the canonical, cent-quantized payment amount from a frozen quote."""
    return _payment_amount(quote_snapshot)


def confirmation_currency_from_quote(quote_snapshot):
    """Return the supported canonical currency from a frozen quote."""
    return _currency(quote_snapshot)


def _optional_payment_reference(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfirmedOrderContextError("La referencia de pago no es válida.")
    reference = value.strip()
    return reference or None


def _optional_text(value, error_message):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfirmedOrderContextError(error_message)
    normalized = value.strip()
    return normalized or None


def _normalized_provider_identifiers(value):
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ConfirmedOrderContextError("Los identificadores del proveedor no son válidos.")

    identifiers = {}
    for key, identifier in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ConfirmedOrderContextError("El nombre de un identificador del proveedor no es válido.")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ConfirmedOrderContextError("El valor de un identificador del proveedor no es válido.")
        identifiers[key.strip()] = identifier.strip()
    return identifiers or None


def _has_nonempty_text(value):
    return isinstance(value, str) and bool(value.strip())


def _payment_method(checkout_session):
    method = str(getattr(checkout_session, "payment_provider", "") or "").strip().lower()
    if method not in SUPPORTED_WEB_PAYMENT_METHODS:
        raise ConfirmedOrderContextError("El método de pago web confirmado no es compatible.")
    return method


def _payment_reference(checkout_session, payment_method):
    if payment_method == "stripe":
        reference = getattr(checkout_session, "payment_intent_id", None)
    else:
        reference = (
            getattr(checkout_session, "provider_capture_id", None)
            or getattr(checkout_session, "provider_order_id", None)
        )

    reference = str(reference or "").strip()
    if not reference:
        raise ConfirmedOrderContextError("La sesión de checkout pagada no tiene una referencia de pago válida.")
    return reference


def _web_provider_identifiers(checkout_session, payment_method):
    if payment_method == "stripe":
        payment_intent_id = str(getattr(checkout_session, "payment_intent_id", "") or "").strip()
        return {"payment_intent_id": payment_intent_id} if payment_intent_id else None

    identifiers = {}
    for field_name in ("provider_order_id", "provider_capture_id"):
        identifier = str(getattr(checkout_session, field_name, "") or "").strip()
        if identifier:
            identifiers[field_name] = identifier
    return identifiers or None


def _payment_amount(quote_snapshot):
    value = quote_snapshot.get("total_amount")
    try:
        return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise ConfirmedOrderContextError("El total congelado del checkout no es válido.") from None


def _currency(quote_snapshot):
    currency = str(quote_snapshot.get("currency") or SUPPORTED_CURRENCY).upper()
    if currency != SUPPORTED_CURRENCY:
        raise ConfirmedOrderContextError("La moneda del checkout confirmado no es compatible.")
    return currency

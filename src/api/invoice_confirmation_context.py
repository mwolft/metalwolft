"""Normalize the immutable confirmation evidence required for invoice issuance."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


FINAL_CHECKOUT_STATUSES = frozenset({"paid", "order_created"})
SUPPORTED_CURRENCY = "EUR"
CONFIRMED_PAYMENT_STATUS = "confirmed"
WEB_CHECKOUT_SOURCE = "web_checkout"
ADMIN_EXTERNAL_SOURCE = "admin_external"
SUPPORTED_CONFIRMATION_SOURCES = frozenset(
    {WEB_CHECKOUT_SOURCE, ADMIN_EXTERNAL_SOURCE}
)
SUPPORTED_PAYMENT_METHODS = frozenset(
    {"stripe", "paypal", "bank_transfer", "cash", "external_other"}
)
MONEY_QUANTUM = Decimal("0.01")


class InvoiceConfirmationContextError(ValueError):
    """Raised when confirmation evidence cannot safely support an invoice."""

    def __init__(self, message, *, field=None):
        self.field = field
        super().__init__(message)


@dataclass(frozen=True)
class InvoiceConfirmationContext:
    """Immutable, source-neutral input consumed by ordinary invoice issuance."""

    order_id: int
    quote_snapshot: Mapping
    customer_snapshot: Mapping
    payment_method: str
    payment_reference: str | None
    payment_status: str
    payment_amount: Decimal
    currency: str
    payment_confirmed_at: datetime | None
    source: str
    confirmed_by: str | None
    provider_identifiers: Mapping | None
    confirmation_context_id: int | None
    source_checkout_session_id: int | None
    source_manual_draft_id: int | None
    internal_note: str | None


def build_invoice_confirmation_context_from_confirmed_order_context(
    *,
    order,
    confirmed_order_context,
):
    """Adapt a persisted ConfirmedOrderContext without consulting checkout."""
    if confirmed_order_context is None:
        raise InvoiceConfirmationContextError("El contexto confirmado es obligatorio.")

    context = InvoiceConfirmationContext(
        order_id=_required_integer(getattr(confirmed_order_context, "order_id", None), "context.order_id"),
        quote_snapshot=_copy_mapping(
            getattr(confirmed_order_context, "quote_snapshot", None),
            "context.quote_snapshot",
        ),
        customer_snapshot=_copy_mapping(
            getattr(confirmed_order_context, "customer_snapshot", None),
            "context.customer_snapshot",
        ),
        payment_method=_required_text(
            getattr(confirmed_order_context, "payment_method", None),
            "context.payment_method",
        ),
        payment_reference=_optional_text(getattr(confirmed_order_context, "payment_reference", None)),
        payment_status=_required_text(
            getattr(confirmed_order_context, "payment_status", None),
            "context.payment_status",
        ),
        payment_amount=_money(
            getattr(confirmed_order_context, "payment_amount", None),
            "context.payment_amount",
        ),
        currency=_currency(getattr(confirmed_order_context, "currency", None), "context.currency"),
        payment_confirmed_at=_optional_datetime(
            getattr(confirmed_order_context, "payment_confirmed_at", None),
            "context.payment_confirmed_at",
        ),
        source=_required_text(getattr(confirmed_order_context, "source", None), "context.source"),
        confirmed_by=_optional_text(getattr(confirmed_order_context, "confirmed_by", None)),
        provider_identifiers=_copy_optional_mapping(
            getattr(confirmed_order_context, "provider_identifiers", None),
            "context.provider_identifiers",
        ),
        confirmation_context_id=_required_integer(
            getattr(confirmed_order_context, "id", None),
            "context.id",
        ),
        source_checkout_session_id=_optional_integer(
            getattr(confirmed_order_context, "source_checkout_session_id", None),
            "context.source_checkout_session_id",
        ),
        source_manual_draft_id=_optional_integer(
            getattr(confirmed_order_context, "source_manual_draft_id", None),
            "context.source_manual_draft_id",
        ),
        internal_note=_optional_text(getattr(confirmed_order_context, "internal_note", None)),
    )
    validate_invoice_confirmation_context(context, order=order)
    return context


def build_invoice_confirmation_context_from_checkout_session(*, order, checkout_session):
    """Adapt a legacy paid CheckoutSession into the normalized invoice input."""
    if checkout_session is None:
        raise InvoiceConfirmationContextError("La sesion de checkout es obligatoria.")

    order_id = _required_order_id(order)
    checkout_order_id = _required_integer(
        getattr(checkout_session, "order_id", None),
        "checkout_session.order_id",
    )
    if checkout_order_id != order_id:
        raise InvoiceConfirmationContextError(
            "La sesion de checkout no pertenece al pedido.",
            field="checkout_session.order_id",
        )

    status = _required_text(getattr(checkout_session, "status", None), "checkout_session.status")
    if status not in FINAL_CHECKOUT_STATUSES:
        raise InvoiceConfirmationContextError(
            "La sesion de checkout no esta finalizada ni pagada.",
            field="checkout_session.status",
        )

    payment_method = _required_text(
        getattr(checkout_session, "payment_provider", None),
        "checkout_session.payment_provider",
    )
    payment_reference, provider_identifiers = _legacy_payment_evidence(
        checkout_session,
        payment_method,
    )
    quote_snapshot = _copy_mapping(
        getattr(checkout_session, "quote_snapshot", None),
        "checkout_session.quote_snapshot",
    )
    customer_snapshot = _copy_mapping(
        getattr(checkout_session, "customer_snapshot", None),
        "checkout_session.customer_snapshot",
    )

    context = InvoiceConfirmationContext(
        order_id=order_id,
        quote_snapshot=quote_snapshot,
        customer_snapshot=customer_snapshot,
        payment_method=payment_method,
        payment_reference=payment_reference,
        payment_status=CONFIRMED_PAYMENT_STATUS,
        payment_amount=_quote_total(quote_snapshot),
        currency=_quote_currency(quote_snapshot),
        payment_confirmed_at=None,
        source=WEB_CHECKOUT_SOURCE,
        confirmed_by=None,
        provider_identifiers=provider_identifiers,
        confirmation_context_id=None,
        source_checkout_session_id=_required_integer(
            getattr(checkout_session, "id", None),
            "checkout_session.id",
        ),
        source_manual_draft_id=None,
        internal_note=None,
    )
    validate_invoice_confirmation_context(context, order=order)
    return context


def coerce_invoice_confirmation_context(*, order, confirmation_context):
    """Accept the normalized context or one legacy checkout object for compatibility."""
    if isinstance(confirmation_context, InvoiceConfirmationContext):
        validate_invoice_confirmation_context(confirmation_context, order=order)
        return confirmation_context
    return build_invoice_confirmation_context_from_checkout_session(
        order=order,
        checkout_session=confirmation_context,
    )


def validate_invoice_confirmation_context(context, *, order):
    """Validate invoice-critical confirmation evidence without mutating its source."""
    if not isinstance(context, InvoiceConfirmationContext):
        raise InvoiceConfirmationContextError("El contexto de confirmacion no es valido.")

    order_id = _required_order_id(order)
    if context.order_id != order_id:
        raise InvoiceConfirmationContextError("El contexto confirmado no pertenece al pedido.")
    if context.payment_status != CONFIRMED_PAYMENT_STATUS:
        raise InvoiceConfirmationContextError("El pago del pedido no esta confirmado.")

    quote_snapshot = _copy_mapping(context.quote_snapshot, "context.quote_snapshot")
    _copy_mapping(context.customer_snapshot, "context.customer_snapshot")
    quote_total = _quote_total(quote_snapshot)
    if context.payment_amount != quote_total:
        raise InvoiceConfirmationContextError(
            "El importe confirmado no coincide con el total congelado."
        )

    quote_currency = _quote_currency(quote_snapshot)
    if context.currency != quote_currency:
        raise InvoiceConfirmationContextError(
            "La moneda confirmada no coincide con el checkout congelado."
        )
    if context.currency != SUPPORTED_CURRENCY:
        raise InvoiceConfirmationContextError("La moneda confirmada no es compatible.")

    if context.source not in SUPPORTED_CONFIRMATION_SOURCES:
        raise InvoiceConfirmationContextError("El origen de confirmacion no es valido.")
    if context.payment_method not in SUPPORTED_PAYMENT_METHODS:
        raise InvoiceConfirmationContextError("El metodo de pago confirmado no es valido.")
    if context.payment_confirmed_at is not None and not isinstance(
        context.payment_confirmed_at,
        datetime,
    ):
        raise InvoiceConfirmationContextError("La fecha de confirmacion del pago no es valida.")

    if context.source == WEB_CHECKOUT_SOURCE:
        _validate_web_checkout_context(context)
    else:
        _validate_admin_external_context(context)


def _validate_web_checkout_context(context):
    if context.source_checkout_session_id is None:
        raise InvoiceConfirmationContextError(
            "El checkout web confirmado debe conservar su sesion de origen."
        )
    if context.payment_reference is None:
        raise InvoiceConfirmationContextError(
            "El checkout web confirmado no tiene una referencia de pago valida."
        )

    identifiers = context.provider_identifiers or {}
    if context.payment_method == "stripe":
        if identifiers.get("payment_intent_id") != context.payment_reference:
            raise InvoiceConfirmationContextError(
                "El contexto Stripe no conserva el payment_intent_id real."
            )
    elif context.payment_method == "paypal":
        paypal_identifiers = {
            value
            for key, value in identifiers.items()
            if key in {"provider_order_id", "provider_capture_id"}
        }
        if context.payment_reference not in paypal_identifiers:
            raise InvoiceConfirmationContextError(
                "El contexto PayPal no conserva la referencia real del proveedor."
            )


def _validate_admin_external_context(context):
    if context.source_checkout_session_id is not None:
        raise InvoiceConfirmationContextError(
            "Un contexto administrativo no puede reutilizar una sesion de checkout."
        )
    if context.payment_confirmed_at is None:
        raise InvoiceConfirmationContextError(
            "Un pago administrativo requiere la fecha real de confirmacion."
        )
    if not context.confirmed_by:
        raise InvoiceConfirmationContextError(
            "Un pago administrativo requiere quien lo confirmo."
        )

    if context.payment_method == "bank_transfer":
        if context.payment_reference is None:
            raise InvoiceConfirmationContextError(
                "Una transferencia requiere una referencia bancaria real."
            )
        return

    if context.payment_method == "cash":
        if not context.internal_note:
            raise InvoiceConfirmationContextError(
                "Un pago en efectivo requiere una nota interna."
            )
        return

    if context.payment_method == "external_other":
        if context.payment_reference is None and not context.internal_note:
            raise InvoiceConfirmationContextError(
                "Un pago externo requiere referencia o nota interna de evidencia."
            )
        return

    if context.payment_method in {"stripe", "paypal"} and context.payment_reference is None:
        raise InvoiceConfirmationContextError(
            "Stripe y PayPal requieren una referencia de pago real."
        )


def _legacy_payment_evidence(checkout_session, payment_method):
    payment_intent_id = _optional_text(getattr(checkout_session, "payment_intent_id", None))
    provider_order_id = _optional_text(getattr(checkout_session, "provider_order_id", None))
    provider_capture_id = _optional_text(getattr(checkout_session, "provider_capture_id", None))

    if payment_method == "stripe":
        if payment_intent_id is None:
            raise InvoiceConfirmationContextError(
                "La sesion Stripe no tiene una referencia de pago valida."
            )
        return payment_intent_id, {"payment_intent_id": payment_intent_id}

    if payment_method == "paypal":
        payment_reference = provider_capture_id or provider_order_id
        if payment_reference is None:
            raise InvoiceConfirmationContextError(
                "La sesion PayPal no tiene una referencia de pago valida."
            )
        identifiers = {}
        if provider_order_id is not None:
            identifiers["provider_order_id"] = provider_order_id
        if provider_capture_id is not None:
            identifiers["provider_capture_id"] = provider_capture_id
        return payment_reference, identifiers

    payment_reference = provider_capture_id or provider_order_id or payment_intent_id
    if payment_reference is None:
        raise InvoiceConfirmationContextError(
            "La sesion de checkout no tiene una referencia de pago valida."
        )
    identifiers = {
        key: value
        for key, value in (
            ("payment_intent_id", payment_intent_id),
            ("provider_order_id", provider_order_id),
            ("provider_capture_id", provider_capture_id),
        )
        if value is not None
    }
    return payment_reference, identifiers or None


def _required_order_id(order):
    return _required_integer(getattr(order, "id", None), "order.id")


def _required_integer(value, field):
    if isinstance(value, bool):
        raise InvoiceConfirmationContextError(f"{field} debe ser un entero valido.", field=field)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise InvoiceConfirmationContextError(f"{field} debe ser un entero valido.", field=field) from exc
    if parsed <= 0:
        raise InvoiceConfirmationContextError(f"{field} debe ser un entero valido.", field=field)
    return parsed


def _optional_integer(value, field):
    if value is None:
        return None
    return _required_integer(value, field)


def _required_text(value, field):
    normalized = _optional_text(value)
    if normalized is None:
        raise InvoiceConfirmationContextError(f"{field} es obligatorio.", field=field)
    return normalized


def _optional_text(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvoiceConfirmationContextError("El texto de confirmacion no es valido.")
    normalized = value.strip()
    return normalized or None


def _optional_datetime(value, field):
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise InvoiceConfirmationContextError(f"{field} no es valida.")
    return value


def _copy_mapping(value, field):
    if not isinstance(value, Mapping):
        raise InvoiceConfirmationContextError(f"{field} debe ser un objeto valido.", field=field)
    return deepcopy(dict(value))


def _copy_optional_mapping(value, field):
    if value is None:
        return None
    mapping = _copy_mapping(value, field)
    normalized = {}
    for key, identifier in mapping.items():
        if not isinstance(key, str) or not key.strip():
            raise InvoiceConfirmationContextError("El nombre de identificador del proveedor no es valido.")
        if not isinstance(identifier, str) or not identifier.strip():
            raise InvoiceConfirmationContextError("El identificador del proveedor no es valido.")
        normalized[key.strip()] = identifier.strip()
    return normalized or None


def _quote_total(quote_snapshot):
    return _money(quote_snapshot.get("total_amount"), "quote_snapshot.total_amount")


def _quote_currency(quote_snapshot):
    return _currency(quote_snapshot.get("currency") or SUPPORTED_CURRENCY, "quote_snapshot.currency")


def _currency(value, field):
    currency = _required_text(value, field).upper()
    return currency


def _money(value, field):
    try:
        return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise InvoiceConfirmationContextError(f"{field} no es valido.") from exc

"""Authoritative registration flow for manually entered supplier invoices."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from api.models import (
    SupplierInvoice,
    SupplierInvoiceReceptionSequence,
    SupplierInvoiceTaxBreakdown,
    db,
)
from api.supplier_invoice_snapshot_integrity import calculate_supplier_invoice_snapshot_hash


SNAPSHOT_SCHEMA_VERSION = 1
SNAPSHOT_GENERATOR = "supplier_invoice_registration_v1"
SUPPORTED_CURRENCY = "EUR"
SUPPORTED_COUNTRY_CODE = "ES"
SUPPORTED_TAX_ID_TYPE = "NIF"
SUPPORTED_FISCAL_INVOICE_TYPE = "F1"
SUPPORTED_TAX_TREATMENT = "domestic_standard"
SUPPORTED_SOURCE = "manual"
EDITABLE_STATUSES = {SupplierInvoice.STATUS_DRAFT, SupplierInvoice.STATUS_NEEDS_REVIEW}


class SupplierInvoiceRegistrationError(Exception):
    """Base error for the supplier invoice registration workflow."""


class SupplierInvoiceRegistrationValidationError(SupplierInvoiceRegistrationError):
    """Raised when a draft cannot be registered under the v1 fiscal scope."""


class SupplierInvoiceDuplicateError(SupplierInvoiceRegistrationError):
    """Raised when a possible supplier document duplicate requires confirmation."""


@dataclass(frozen=True)
class SupplierInvoiceRegistrationResult:
    invoice: SupplierInvoice
    registered: bool
    duplicate_override_used: bool


def register_supplier_invoice(
    supplier_invoice,
    *,
    db_session=None,
    actor=None,
    allow_duplicate=False,
    registered_at=None,
):
    """Freeze a validated draft and assign its next internal receipt number.

    This function never commits or rolls back. The receipt sequence increment,
    snapshot and state transition share the caller's database transaction.
    """
    session = db_session or db.session
    invoice_id = _required_positive_id(getattr(supplier_invoice, "id", None), "La factura recibida no existe.")

    if getattr(supplier_invoice, "status", None) == SupplierInvoice.STATUS_REGISTERED:
        return SupplierInvoiceRegistrationResult(
            invoice=supplier_invoice,
            registered=False,
            duplicate_override_used=False,
        )
    if getattr(supplier_invoice, "status", None) == SupplierInvoice.STATUS_CANCELLED:
        raise SupplierInvoiceRegistrationValidationError("Una factura recibida cancelada no puede registrarse.")
    if getattr(supplier_invoice, "status", None) not in EDITABLE_STATUSES:
        raise SupplierInvoiceRegistrationValidationError("El estado de la factura recibida no permite registrarla.")
    if getattr(supplier_invoice, "reception_number", None) is not None:
        raise SupplierInvoiceRegistrationValidationError("El número de recepción solo se asigna al registrar.")

    validated = _validate_registration_input(supplier_invoice)
    duplicates = find_possible_supplier_invoice_duplicates(supplier_invoice, db_session=session)
    if duplicates and not allow_duplicate:
        raise SupplierInvoiceDuplicateError(
            "Existe una posible factura recibida duplicada. Confirma expresamente para registrarla."
        )

    sequence = (
        session.query(SupplierInvoiceReceptionSequence)
        .filter_by(id=1)
        .with_for_update()
        .one_or_none()
    )
    if sequence is None:
        raise SupplierInvoiceRegistrationValidationError("La secuencia de recepción no está inicializada.")

    registered_at_value = _normalized_datetime(registered_at or datetime.now(timezone.utc))
    sequence.last_number = int(sequence.last_number or 0) + 1
    supplier_invoice.reception_number = sequence.last_number
    supplier_invoice.registered_at = registered_at_value
    supplier_invoice.registered_by = _optional_text(actor)
    snapshot = build_supplier_invoice_snapshot(
        supplier_invoice,
        breakdowns=validated["breakdowns"],
        total_amount=validated["total_amount"],
        registered_at=registered_at_value,
        duplicate_override_used=bool(allow_duplicate and duplicates),
    )
    supplier_invoice.fiscal_snapshot = snapshot
    supplier_invoice.snapshot_schema_version = SNAPSHOT_SCHEMA_VERSION
    supplier_invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(snapshot)
    supplier_invoice.status = SupplierInvoice.STATUS_REGISTERED
    session.flush()

    return SupplierInvoiceRegistrationResult(
        invoice=supplier_invoice,
        registered=True,
        duplicate_override_used=bool(allow_duplicate and duplicates),
    )


def find_possible_supplier_invoice_duplicates(supplier_invoice, *, db_session=None):
    """Return matching supplier/NIF document numbers without making a policy decision."""
    session = db_session or db.session
    supplier_tax_id = _optional_text(getattr(supplier_invoice, "supplier_tax_id", None))
    invoice_number = _optional_text(getattr(supplier_invoice, "supplier_invoice_number", None))
    if not supplier_tax_id or not invoice_number:
        return []

    query = session.query(SupplierInvoice).filter(
        SupplierInvoice.supplier_tax_id == supplier_tax_id,
        SupplierInvoice.supplier_invoice_number == invoice_number,
        SupplierInvoice.status != SupplierInvoice.STATUS_CANCELLED,
    )
    if getattr(supplier_invoice, "id", None):
        query = query.filter(SupplierInvoice.id != supplier_invoice.id)
    return query.order_by(SupplierInvoice.id.asc()).all()


def build_supplier_invoice_snapshot(
    supplier_invoice,
    *,
    breakdowns,
    total_amount,
    registered_at,
    duplicate_override_used=False,
):
    """Build a deterministic v1 snapshot from validated persisted draft fields."""
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "metadata": {
            "generator": SNAPSHOT_GENERATOR,
        },
        "supplier": {
            "legal_name": _required_text(supplier_invoice.supplier_legal_name, "supplier_legal_name"),
            "tax_id": _required_text(supplier_invoice.supplier_tax_id, "supplier_tax_id"),
            "country_code": _required_text(supplier_invoice.supplier_country_code, "supplier_country_code"),
            "tax_id_type": _required_text(supplier_invoice.supplier_tax_id_type, "supplier_tax_id_type"),
        },
        "document": {
            "supplier_invoice_number": _required_text(
                supplier_invoice.supplier_invoice_number,
                "supplier_invoice_number",
            ),
            "reception_number": _required_positive_id(
                supplier_invoice.reception_number,
                "reception_number",
            ),
            "issue_date": _date_string(supplier_invoice.issue_date, "issue_date"),
            "operation_date": _optional_date_string(supplier_invoice.operation_date, "operation_date"),
            "concept": _required_text(supplier_invoice.concept, "concept"),
            "currency": _required_text(supplier_invoice.currency, "currency"),
            "fiscal_invoice_type": _required_text(
                supplier_invoice.fiscal_invoice_type,
                "fiscal_invoice_type",
            ),
            "tax_treatment": _required_text(supplier_invoice.tax_treatment, "tax_treatment"),
            "special_regime_key": _optional_text(supplier_invoice.special_regime_key),
        },
        "tax_breakdowns": [
            {
                "position": breakdown["position"],
                "tax_base": _money_string(breakdown["tax_base"]),
                "tax_rate": _money_string(breakdown["tax_rate"]),
                "tax_amount": _money_string(breakdown["tax_amount"]),
                "deductible_tax_amount": _money_string(breakdown["deductible_tax_amount"]),
            }
            for breakdown in breakdowns
        ],
        "totals": {
            "tax_base": _money_string(sum(item["tax_base"] for item in breakdowns)),
            "tax_amount": _money_string(sum(item["tax_amount"] for item in breakdowns)),
            "deductible_tax_amount": _money_string(
                sum(item["deductible_tax_amount"] for item in breakdowns)
            ),
            "total_amount": _money_string(total_amount),
        },
        "registration": {
            "registered_at": _timestamp_string(registered_at),
            "registered_by": _optional_text(supplier_invoice.registered_by),
            "source": _required_text(supplier_invoice.source, "source"),
            "duplicate_override_used": bool(duplicate_override_used),
        },
    }


def _validate_registration_input(supplier_invoice):
    _required_text(supplier_invoice.supplier_legal_name, "supplier_legal_name")
    _required_text(supplier_invoice.supplier_tax_id, "supplier_tax_id")
    _required_text(supplier_invoice.supplier_invoice_number, "supplier_invoice_number")
    _required_text(supplier_invoice.concept, "concept")
    _date_string(supplier_invoice.issue_date, "issue_date")
    _optional_date_string(supplier_invoice.operation_date, "operation_date")

    _require_exact(supplier_invoice.currency, SUPPORTED_CURRENCY, "currency")
    _require_exact(supplier_invoice.supplier_country_code, SUPPORTED_COUNTRY_CODE, "supplier_country_code")
    _require_exact(supplier_invoice.supplier_tax_id_type, SUPPORTED_TAX_ID_TYPE, "supplier_tax_id_type")
    _require_exact(supplier_invoice.fiscal_invoice_type, SUPPORTED_FISCAL_INVOICE_TYPE, "fiscal_invoice_type")
    _require_exact(supplier_invoice.tax_treatment, SUPPORTED_TAX_TREATMENT, "tax_treatment")
    _require_exact(supplier_invoice.source, SUPPORTED_SOURCE, "source")
    if _optional_text(supplier_invoice.special_regime_key):
        raise SupplierInvoiceRegistrationValidationError("No se admiten regímenes especiales en el alcance actual.")

    breakdowns = _validated_breakdowns(getattr(supplier_invoice, "tax_breakdowns", None))
    total_amount = _money(supplier_invoice.total_amount, "total_amount")
    expected_total = sum(
        (breakdown["tax_base"] + breakdown["tax_amount"] for breakdown in breakdowns),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if total_amount != expected_total:
        raise SupplierInvoiceRegistrationValidationError(
            "El total no coincide con la suma de las bases y cuotas de IVA."
        )
    return {"breakdowns": breakdowns, "total_amount": total_amount}


def _validated_breakdowns(breakdowns):
    if not isinstance(breakdowns, (list, tuple)) or not breakdowns:
        raise SupplierInvoiceRegistrationValidationError("Debe existir al menos un desglose de IVA.")

    validated = []
    positions = set()
    for item in breakdowns:
        position = _required_positive_id(getattr(item, "position", None), "La posición del desglose no es válida.")
        if position in positions:
            raise SupplierInvoiceRegistrationValidationError("Las posiciones de desglose no pueden repetirse.")
        positions.add(position)
        tax_base = _money(getattr(item, "tax_base", None), "tax_base")
        tax_rate = _money(getattr(item, "tax_rate", None), "tax_rate")
        tax_amount = _money(getattr(item, "tax_amount", None), "tax_amount")
        deductible_tax_amount = _money(
            getattr(item, "deductible_tax_amount", None),
            "deductible_tax_amount",
        )
        if any(amount < Decimal("0.00") for amount in (tax_base, tax_rate, tax_amount, deductible_tax_amount)):
            raise SupplierInvoiceRegistrationValidationError("Los importes de IVA no pueden ser negativos.")
        if deductible_tax_amount > tax_amount:
            raise SupplierInvoiceRegistrationValidationError(
                "La cuota deducible no puede superar la cuota soportada."
            )
        validated.append(
            {
                "position": position,
                "tax_base": tax_base,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "deductible_tax_amount": deductible_tax_amount,
            }
        )
    return sorted(validated, key=lambda item: item["position"])


def _require_exact(value, expected, field):
    if _optional_text(value) != expected:
        raise SupplierInvoiceRegistrationValidationError(
            f"El campo {field} no está soportado en el alcance fiscal actual."
        )


def _required_positive_id(value, message):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise SupplierInvoiceRegistrationValidationError(message) from exc
    if number <= 0 or str(number) != str(value).strip():
        raise SupplierInvoiceRegistrationValidationError(message)
    return number


def _money(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise SupplierInvoiceRegistrationValidationError(f"Importe no válido: {field}.") from exc
    if not amount.is_finite():
        raise SupplierInvoiceRegistrationValidationError(f"Importe no válido: {field}.")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _money_string(value):
    return f"{_money(value, 'snapshot'):.2f}"


def _required_text(value, field):
    normalized = _optional_text(value)
    if not normalized:
        raise SupplierInvoiceRegistrationValidationError(f"Campo obligatorio ausente: {field}.")
    return normalized


def _optional_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _date_string(value, field):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError as exc:
            raise SupplierInvoiceRegistrationValidationError(f"Fecha no válida: {field}.") from exc
    raise SupplierInvoiceRegistrationValidationError(f"Campo obligatorio ausente: {field}.")


def _optional_date_string(value, field):
    return None if value is None else _date_string(value, field)


def _normalized_datetime(value):
    if not isinstance(value, datetime):
        raise SupplierInvoiceRegistrationValidationError("La fecha de registro no es válida.")
    return value.replace(tzinfo=None)


def _timestamp_string(value):
    if not isinstance(value, datetime):
        raise SupplierInvoiceRegistrationValidationError("La fecha de registro no es válida.")
    return value.isoformat()

"""Pure preparation of AEAT ``RECIBIDAS_GASTOS`` rows from frozen snapshots.

This module deliberately does not create workbooks.  It validates the
registered SupplierInvoice snapshot and exposes one normalized row per VAT
breakdown so a future XLSX writer has no fiscal decisions left to make.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from api.supplier_invoice_snapshot_integrity import (
    SupplierInvoiceSnapshotIntegrityError,
    calculate_supplier_invoice_snapshot_hash,
)


SUPPORTED_SCHEMA_VERSION = 2
SUPPORTED_CURRENCY = "EUR"
SUPPORTED_COUNTRY_CODE = "ES"
SUPPORTED_TAX_ID_TYPE = "NIF"
SUPPORTED_FISCAL_INVOICE_TYPE = "F1"
SUPPORTED_TAX_TREATMENT = "domestic_standard"
SUPPORTED_EXPENSE_CONCEPT_CODES = {"G01", "G03"}
REGISTERED_STATUS = "registered"

BUSINESS_ACTIVITY_CODE = "A"
BUSINESS_ACTIVITY_TYPE = "3"
IAE_CODE = "3141"
AEAT_OPERATION_KEY = "01"

# Ordered A:AP contract for the future RECIBIDAS_GASTOS worksheet writer.
AEAT_RECEIVED_EXPENSE_LEDGER_COLUMN_KEYS = (
    "exercise", "period", "activity_code", "activity_type", "iae_code",
    "invoice_type", "expense_concept_code", "deductible_expense_amount",
    "issue_date", "operation_date", "supplier_invoice_number",
    "supplier_invoice_number_final", "received_date", "reception_number",
    "reception_number_final", "tax_id_type", "country_code", "supplier_tax_id",
    "supplier_legal_name", "operation_key", "investment_good", "reverse_charge",
    "deductible_later", "deduction_exercise", "deduction_period", "total_amount",
    "tax_base", "tax_rate", "tax_amount", "deductible_tax_amount",
    "equivalence_surcharge_rate", "equivalence_surcharge_amount", "payment_date",
    "payment_amount", "payment_method", "payment_method_id", "withholding_type",
    "withholding_amount", "billing_agreement", "property_situation",
    "cadastral_reference", "external_reference",
)

# Limits from the AEAT template data contract.  Reject instead of silently
# truncating a frozen fiscal value before it reaches the workbook writer.
MAX_SUPPLIER_INVOICE_NUMBER_LENGTH = 60
MAX_SUPPLIER_TAX_ID_LENGTH = 20
MAX_SUPPLIER_LEGAL_NAME_LENGTH = 120


class AeatReceivedExpenseLedgerError(Exception):
    """Base error for received-expense ledger preparation."""


class AeatReceivedExpenseLedgerValidationError(AeatReceivedExpenseLedgerError):
    """Raised when a registered supplier snapshot is not exportable."""


def prepare_aeat_received_expense_ledger_rows(supplier_invoices, *, allow_empty=False):
    """Return deterministic AEAT rows, one per frozen VAT breakdown.

    ``supplier_invoices`` can be any iterable of registered SupplierInvoice
    objects.  Only their persisted status, snapshot version and hash are read;
    all fiscal output values come exclusively from ``fiscal_snapshot``.
    """
    if supplier_invoices is None:
        raise AeatReceivedExpenseLedgerValidationError(
            "Debe indicarse al menos una factura recibida registrada."
        )

    rows = []
    for supplier_invoice in list(supplier_invoices):
        rows.extend(_prepare_supplier_invoice_rows(supplier_invoice))

    if not rows and not allow_empty:
        raise AeatReceivedExpenseLedgerValidationError(
            "Debe indicarse al menos una factura recibida registrada."
        )

    return sorted(
        rows,
        key=lambda row: (
            row["issue_date"],
            row["supplier_invoice_number"],
            row["reception_number"],
        ),
    )


def _prepare_supplier_invoice_rows(supplier_invoice):
    _validate_registered_invoice(supplier_invoice)
    snapshot = _validated_snapshot(supplier_invoice)
    _validate_snapshot_hash(supplier_invoice, snapshot)
    prepared = _prepare_snapshot(snapshot)

    deductible_expenses = _allocated_deductible_expenses(prepared)
    return [
        _build_row(prepared, breakdown, deductible_expense)
        for breakdown, deductible_expense in zip(
            prepared["tax_breakdowns"],
            deductible_expenses,
            strict=True,
        )
    ]


def _validate_registered_invoice(supplier_invoice):
    if getattr(supplier_invoice, "status", None) != REGISTERED_STATUS:
        raise AeatReceivedExpenseLedgerValidationError(
            "Solo se pueden preparar facturas recibidas registradas."
        )


def _validated_snapshot(supplier_invoice):
    snapshot = getattr(supplier_invoice, "fiscal_snapshot", None)
    reception_number = getattr(supplier_invoice, "reception_number", None)
    if not isinstance(snapshot, dict):
        raise AeatReceivedExpenseLedgerValidationError(
            "La factura recibida no tiene snapshot fiscal."
        )

    schema_version = snapshot.get("schema_version")
    if schema_version == 1:
        raise AeatReceivedExpenseLedgerValidationError(
            "La factura recibida con numero de recepcion "
            f"{reception_number or 'sin asignar'} usa snapshot v1 y no contiene "
            "los datos necesarios para RECIBIDAS_GASTOS."
        )
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise AeatReceivedExpenseLedgerValidationError(
            "Version de snapshot fiscal no soportada para RECIBIDAS_GASTOS."
        )
    if getattr(supplier_invoice, "snapshot_schema_version", None) != SUPPORTED_SCHEMA_VERSION:
        raise AeatReceivedExpenseLedgerValidationError(
            "La version persistida no coincide con el snapshot fiscal de la factura recibida."
        )

    for block in ("supplier", "document", "totals", "expense_classification"):
        if not isinstance(snapshot.get(block), dict):
            raise AeatReceivedExpenseLedgerValidationError(
                f"Bloque de snapshot obligatorio ausente: {block}."
            )
    if not isinstance(snapshot.get("tax_breakdowns"), list):
        raise AeatReceivedExpenseLedgerValidationError(
            "Bloque de snapshot obligatorio ausente: tax_breakdowns."
        )
    return snapshot


def _validate_snapshot_hash(supplier_invoice, snapshot):
    stored_hash = _required_text(
        getattr(supplier_invoice, "snapshot_hash", None), "snapshot_hash"
    )
    try:
        calculated_hash = calculate_supplier_invoice_snapshot_hash(snapshot)
    except SupplierInvoiceSnapshotIntegrityError as exc:
        raise AeatReceivedExpenseLedgerValidationError(
            "No se puede verificar la integridad del snapshot fiscal."
        ) from exc
    if calculated_hash != stored_hash:
        raise AeatReceivedExpenseLedgerValidationError(
            "La integridad del snapshot fiscal de la factura recibida no coincide."
        )


def _prepare_snapshot(snapshot):
    supplier = snapshot["supplier"]
    document = snapshot["document"]
    totals = snapshot["totals"]
    classification = snapshot["expense_classification"]

    _require_exact(document.get("currency"), SUPPORTED_CURRENCY, "document.currency")
    _require_exact(
        supplier.get("country_code"), SUPPORTED_COUNTRY_CODE, "supplier.country_code"
    )
    _require_exact(
        supplier.get("tax_id_type"), SUPPORTED_TAX_ID_TYPE, "supplier.tax_id_type"
    )
    _require_exact(
        document.get("fiscal_invoice_type"),
        SUPPORTED_FISCAL_INVOICE_TYPE,
        "document.fiscal_invoice_type",
    )
    _require_exact(
        document.get("tax_treatment"), SUPPORTED_TAX_TREATMENT, "document.tax_treatment"
    )
    if _optional_text(document.get("special_regime_key")):
        raise AeatReceivedExpenseLedgerValidationError(
            "No se admiten regimenes especiales en RECIBIDAS_GASTOS."
        )

    supplier_invoice_number = _required_text(
        document.get("supplier_invoice_number"), "document.supplier_invoice_number"
    )
    supplier_tax_id = _required_text(supplier.get("tax_id"), "supplier.tax_id")
    supplier_legal_name = _required_text(
        supplier.get("legal_name"), "supplier.legal_name"
    )
    _validate_length(
        supplier_invoice_number,
        MAX_SUPPLIER_INVOICE_NUMBER_LENGTH,
        "document.supplier_invoice_number",
    )
    _validate_length(supplier_tax_id, MAX_SUPPLIER_TAX_ID_LENGTH, "supplier.tax_id")
    _validate_length(
        supplier_legal_name, MAX_SUPPLIER_LEGAL_NAME_LENGTH, "supplier.legal_name"
    )

    expense_code = _required_text(
        classification.get("aeat_expense_concept_code"),
        "expense_classification.aeat_expense_concept_code",
    )
    if expense_code not in SUPPORTED_EXPENSE_CONCEPT_CODES:
        raise AeatReceivedExpenseLedgerValidationError(
            "El concepto de gasto AEAT esta fuera del alcance nacional actual."
        )

    issue_date = _snapshot_date(document.get("issue_date"), "document.issue_date")
    operation_date = _snapshot_date(
        document.get("operation_date") or document.get("issue_date"),
        "document.operation_date",
    )

    return {
        "supplier_invoice_number": supplier_invoice_number,
        "supplier_tax_id": supplier_tax_id,
        "supplier_legal_name": supplier_legal_name,
        "issue_date": issue_date,
        "operation_date": operation_date,
        "received_at": _snapshot_datetime(document.get("received_at"), "document.received_at"),
        "reception_number": _positive_int(
            document.get("reception_number"), "document.reception_number"
        ),
        "expense_concept_code": expense_code,
        "expense_deductible_amount": _money(
            classification.get("expense_deductible_amount"),
            "expense_classification.expense_deductible_amount",
        ),
        "tax_breakdowns": _validated_breakdowns(snapshot.get("tax_breakdowns")),
        "totals": {
            "tax_base": _money(totals.get("tax_base"), "totals.tax_base"),
            "tax_amount": _money(totals.get("tax_amount"), "totals.tax_amount"),
            "deductible_tax_amount": _money(
                totals.get("deductible_tax_amount"), "totals.deductible_tax_amount"
            ),
            "total_amount": _money(totals.get("total_amount"), "totals.total_amount"),
        },
    }


def _validated_breakdowns(raw_breakdowns):
    if not raw_breakdowns:
        raise AeatReceivedExpenseLedgerValidationError(
            "Debe existir al menos un desglose de IVA en el snapshot fiscal."
        )

    breakdowns = []
    positions = set()
    for index, raw in enumerate(raw_breakdowns, start=1):
        if not isinstance(raw, dict):
            raise AeatReceivedExpenseLedgerValidationError(
                f"Desglose de IVA invalido: {index}."
            )
        position = _positive_int(raw.get("position"), f"tax_breakdowns.{index}.position")
        if position in positions:
            raise AeatReceivedExpenseLedgerValidationError(
                "Las posiciones de desglose no pueden repetirse."
            )
        positions.add(position)
        breakdowns.append(
            {
                "position": position,
                "tax_base": _nonnegative_money(
                    raw.get("tax_base"), f"tax_breakdowns.{index}.tax_base"
                ),
                "tax_rate": _nonnegative_money(
                    raw.get("tax_rate"), f"tax_breakdowns.{index}.tax_rate"
                ),
                "tax_amount": _nonnegative_money(
                    raw.get("tax_amount"), f"tax_breakdowns.{index}.tax_amount"
                ),
                "deductible_tax_amount": _nonnegative_money(
                    raw.get("deductible_tax_amount"),
                    f"tax_breakdowns.{index}.deductible_tax_amount",
                ),
            }
        )

    return sorted(breakdowns, key=lambda breakdown: breakdown["position"])


def _allocated_deductible_expenses(prepared):
    breakdowns = prepared["tax_breakdowns"]
    totals = prepared["totals"]
    _reconcile_breakdowns(breakdowns, totals)

    expense_amount = prepared["expense_deductible_amount"]
    if len(breakdowns) == 1:
        return [expense_amount]
    if expense_amount != totals["tax_base"]:
        raise AeatReceivedExpenseLedgerValidationError(
            "No se puede repartir el gasto deducible entre varios desgloses IVA "
            "sin una asignacion fiscal congelada."
        )
    return [breakdown["tax_base"] for breakdown in breakdowns]


def _reconcile_breakdowns(breakdowns, totals):
    tax_base = _sum_money(breakdown["tax_base"] for breakdown in breakdowns)
    tax_amount = _sum_money(breakdown["tax_amount"] for breakdown in breakdowns)
    deductible_tax_amount = _sum_money(
        breakdown["deductible_tax_amount"] for breakdown in breakdowns
    )
    total_amount = _sum_money(
        breakdown["tax_base"] + breakdown["tax_amount"] for breakdown in breakdowns
    )
    expected = {
        "tax_base": tax_base,
        "tax_amount": tax_amount,
        "deductible_tax_amount": deductible_tax_amount,
        "total_amount": total_amount,
    }
    for field, amount in expected.items():
        if totals[field] != amount:
            raise AeatReceivedExpenseLedgerValidationError(
                "Los totales del snapshot fiscal no reconcilian con sus desgloses de IVA."
            )


def _build_row(prepared, breakdown, deductible_expense):
    received_date = prepared["received_at"].date()
    row = {
        "exercise": received_date.year,
        "period": _quarter(received_date),
        "activity_code": BUSINESS_ACTIVITY_CODE,
        "activity_type": BUSINESS_ACTIVITY_TYPE,
        "iae_code": IAE_CODE,
        "invoice_type": SUPPORTED_FISCAL_INVOICE_TYPE,
        "expense_concept_code": prepared["expense_concept_code"],
        "deductible_expense_amount": deductible_expense,
        "issue_date": prepared["issue_date"],
        "operation_date": prepared["operation_date"],
        "supplier_invoice_number": prepared["supplier_invoice_number"],
        "supplier_invoice_number_final": None,
        "received_date": received_date,
        "reception_number": prepared["reception_number"],
        "reception_number_final": None,
        "tax_id_type": None,
        "country_code": None,
        "supplier_tax_id": prepared["supplier_tax_id"],
        "supplier_legal_name": prepared["supplier_legal_name"],
        "operation_key": AEAT_OPERATION_KEY,
        "investment_good": None,
        "reverse_charge": None,
        "deductible_later": None,
        "deduction_exercise": None,
        "deduction_period": None,
        "total_amount": _sum_money((breakdown["tax_base"], breakdown["tax_amount"])),
        "tax_base": breakdown["tax_base"],
        "tax_rate": breakdown["tax_rate"],
        "tax_amount": breakdown["tax_amount"],
        "deductible_tax_amount": breakdown["deductible_tax_amount"],
        "equivalence_surcharge_rate": None,
        "equivalence_surcharge_amount": None,
        "payment_date": None,
        "payment_amount": None,
        "payment_method": None,
        "payment_method_id": None,
        "withholding_type": None,
        "withholding_amount": None,
        "billing_agreement": None,
        "property_situation": None,
        "cadastral_reference": None,
        "external_reference": None,
    }
    if tuple(row) != AEAT_RECEIVED_EXPENSE_LEDGER_COLUMN_KEYS:
        raise RuntimeError("El contrato interno de RECIBIDAS_GASTOS no tiene 42 columnas.")
    return row


def _require_exact(value, expected, field):
    if _optional_text(value) != expected:
        raise AeatReceivedExpenseLedgerValidationError(
            f"El campo {field} esta fuera del alcance nacional actual."
        )


def _required_text(value, field):
    text = _optional_text(value)
    if not text:
        raise AeatReceivedExpenseLedgerValidationError(
            f"Campo obligatorio ausente: {field}."
        )
    return text


def _optional_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validate_length(value, maximum, field):
    if len(value) > maximum:
        raise AeatReceivedExpenseLedgerValidationError(
            f"El campo {field} supera la longitud maxima admitida por AEAT."
        )


def _positive_int(value, field):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise AeatReceivedExpenseLedgerValidationError(
            f"Identificador obligatorio invalido: {field}."
        ) from exc
    if number <= 0 or str(number) != str(value).strip():
        raise AeatReceivedExpenseLedgerValidationError(
            f"Identificador obligatorio invalido: {field}."
        )
    return number


def _snapshot_date(value, field):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date()
        except ValueError as exc:
            raise AeatReceivedExpenseLedgerValidationError(
                f"Fecha invalida en {field}."
            ) from exc
    raise AeatReceivedExpenseLedgerValidationError(f"Fecha obligatoria ausente: {field}.")


def _snapshot_datetime(value, field):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise AeatReceivedExpenseLedgerValidationError(
                f"Fecha invalida en {field}."
            ) from exc
    raise AeatReceivedExpenseLedgerValidationError(f"Fecha obligatoria ausente: {field}.")


def _money(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise AeatReceivedExpenseLedgerValidationError(
            f"Importe no valido en {field}."
        ) from exc
    if not amount.is_finite():
        raise AeatReceivedExpenseLedgerValidationError(f"Importe no valido en {field}.")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _nonnegative_money(value, field):
    amount = _money(value, field)
    if amount < Decimal("0.00"):
        raise AeatReceivedExpenseLedgerValidationError(f"Importe negativo no valido en {field}.")
    return amount


def _sum_money(amounts):
    return sum(amounts, Decimal("0.00")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def _quarter(value):
    return f"{((value.month - 1) // 3) + 1}T"

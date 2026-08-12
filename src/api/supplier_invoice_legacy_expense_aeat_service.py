"""Controlled AEAT completion for registered SupplierInvoice v1 snapshots."""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Mapping

from api.supplier_invoice_snapshot_integrity import calculate_supplier_invoice_snapshot_hash


LEGACY_SCHEMA_VERSION = 1
REGISTERED_STATUS = "registered"
SUPPORTED_EXPENSE_CODES = {"G01", "G03"}
G01_SUPPLIER_TAX_IDS = {"B13559141", "B13019559"}


class LegacySupplierInvoiceExpenseAeatError(Exception):
    """Raised when a v1 supplier invoice cannot use the audited legacy path."""


def is_legacy_supplier_invoice_eligible_for_manual_classification(invoice):
    try:
        _validate_legacy_structure(invoice)
    except LegacySupplierInvoiceExpenseAeatError:
        return False
    return not _has_complete_audit(invoice) and not _has_partial_audit(invoice)


def legacy_supplier_invoice_expense_details(invoice):
    """Return frozen facts and editable proposals for the Admin confirmation page."""
    snapshot = _validate_legacy_structure(invoice)
    supplier = snapshot["supplier"]
    document = snapshot["document"]
    totals = snapshot["totals"]
    breakdowns = _validated_breakdowns(snapshot["tax_breakdowns"])
    issue_date = _required_date(document.get("issue_date"), "document.issue_date")
    return {
        "reception_number": _positive_int(document.get("reception_number"), "document.reception_number"),
        "supplier_legal_name": _required_text(supplier.get("legal_name"), "supplier.legal_name"),
        "supplier_tax_id": _required_text(supplier.get("tax_id"), "supplier.tax_id"),
        "supplier_invoice_number": _required_text(
            document.get("supplier_invoice_number"), "document.supplier_invoice_number"
        ),
        "issue_date": issue_date,
        "operation_date": _optional_date(document.get("operation_date")),
        "tax_base": _money(totals.get("tax_base"), "totals.tax_base"),
        "tax_amount": _money(totals.get("tax_amount"), "totals.tax_amount"),
        "total_amount": _money(totals.get("total_amount"), "totals.total_amount"),
        "breakdowns": breakdowns,
        "proposed_expense_code": _existing_or_proposed_expense_code(invoice, supplier["tax_id"]),
        "proposed_expense_deductible_amount": _existing_or_proposed_amount(invoice, breakdowns),
        # v1 did not freeze a fiscal receipt date. This is a proposal only and
        # must be confirmed by the administrator before it is persisted.
        "proposed_received_at": issue_date,
    }


def classify_legacy_supplier_invoice_expense_aeat(
    invoice,
    *,
    aeat_expense_concept_code,
    expense_deductible_amount,
    legacy_expense_received_at,
    actor,
    classified_at=None,
):
    """Persist a human-confirmed legacy completion without altering v1 JSON/hash."""
    if not is_legacy_supplier_invoice_eligible_for_manual_classification(invoice):
        raise LegacySupplierInvoiceExpenseAeatError(
            "La factura recibida no es elegible para clasificaciÃ³n AEAT legacy."
        )

    snapshot = _validate_legacy_structure(invoice)
    breakdowns = _validated_breakdowns(snapshot["tax_breakdowns"])
    totals = _validated_totals(snapshot["totals"], breakdowns)
    code = _optional_text(aeat_expense_concept_code)
    if code not in SUPPORTED_EXPENSE_CODES:
        raise LegacySupplierInvoiceExpenseAeatError(
            "La clasificaciÃ³n AEAT legacy solo admite G01 o G03."
        )
    amount = _money(expense_deductible_amount, "expense_deductible_amount")
    if amount < Decimal("0.00") or amount > totals["total_amount"]:
        raise LegacySupplierInvoiceExpenseAeatError(
            "El gasto deducible debe estar entre cero y el total de la factura."
        )
    received_at = _required_date(legacy_expense_received_at, "legacy_expense_received_at")
    normalized_actor = _optional_text(actor)
    if not normalized_actor:
        raise LegacySupplierInvoiceExpenseAeatError(
            "La clasificaciÃ³n AEAT legacy requiere identificar al administrador."
        )

    invoice.aeat_expense_concept_code = code
    invoice.expense_deductible_amount = amount
    invoice.legacy_expense_received_at = received_at
    invoice.legacy_expense_classified_at = _normalized_datetime(
        classified_at or datetime.now(timezone.utc)
    )
    invoice.legacy_expense_classified_by = normalized_actor
    return invoice


def legacy_supplier_invoice_expense_data_for_export(invoice, snapshot):
    """Return the sole live-data exception accepted for an identifiable v1."""
    _validate_legacy_structure(invoice, snapshot=snapshot)
    if not _has_complete_audit(invoice):
        number = getattr(invoice, "reception_number", None) or "sin asignar"
        raise LegacySupplierInvoiceExpenseAeatError(
            "La factura recibida con nÃºmero de recepciÃ³n "
            f"{number} es histÃ³rica y requiere clasificaciÃ³n AEAT legacy antes de exportar."
        )
    code = _optional_text(getattr(invoice, "aeat_expense_concept_code", None))
    if code not in SUPPORTED_EXPENSE_CODES:
        raise LegacySupplierInvoiceExpenseAeatError(
            "La factura recibida histÃ³rica usa un concepto de gasto AEAT fuera del alcance actual."
        )
    return {
        "aeat_expense_concept_code": code,
        "expense_deductible_amount": _money(
            getattr(invoice, "expense_deductible_amount", None), "expense_deductible_amount"
        ),
        "received_at": _required_date(
            getattr(invoice, "legacy_expense_received_at", None), "legacy_expense_received_at"
        ),
        "classified_at": getattr(invoice, "legacy_expense_classified_at", None),
        "classified_by": _optional_text(
            getattr(invoice, "legacy_expense_classified_by", None)
        ),
    }


def _validate_legacy_structure(invoice, *, snapshot=None):
    if getattr(invoice, "status", None) != REGISTERED_STATUS:
        raise LegacySupplierInvoiceExpenseAeatError("La factura recibida debe estar registrada.")
    if getattr(invoice, "snapshot_schema_version", None) != LEGACY_SCHEMA_VERSION:
        raise LegacySupplierInvoiceExpenseAeatError("La factura recibida no usa un snapshot v1 legacy.")
    snapshot = snapshot if snapshot is not None else getattr(invoice, "fiscal_snapshot", None)
    if not isinstance(snapshot, Mapping) or snapshot.get("schema_version") != LEGACY_SCHEMA_VERSION:
        raise LegacySupplierInvoiceExpenseAeatError("El snapshot fiscal v1 no es vÃ¡lido.")
    stored_hash = _optional_text(getattr(invoice, "snapshot_hash", None))
    if not stored_hash or calculate_supplier_invoice_snapshot_hash(snapshot) != stored_hash:
        raise LegacySupplierInvoiceExpenseAeatError("La integridad del snapshot fiscal no coincide.")

    supplier = snapshot.get("supplier")
    document = snapshot.get("document")
    totals = snapshot.get("totals")
    breakdowns = snapshot.get("tax_breakdowns")
    if not all(isinstance(block, Mapping) for block in (supplier, document, totals)) or not isinstance(breakdowns, list):
        raise LegacySupplierInvoiceExpenseAeatError("El snapshot v1 no contiene la estructura fiscal necesaria.")
    if _optional_text(supplier.get("country_code")) != "ES" or _optional_text(supplier.get("tax_id_type")) != "NIF":
        raise LegacySupplierInvoiceExpenseAeatError("La factura recibida legacy estÃ¡ fuera del alcance nacional.")
    if _optional_text(document.get("currency")) != "EUR":
        raise LegacySupplierInvoiceExpenseAeatError("La factura recibida legacy no estÃ¡ en EUR.")
    if _optional_text(document.get("fiscal_invoice_type")) != "F1":
        raise LegacySupplierInvoiceExpenseAeatError("La factura recibida legacy no usa tipo fiscal F1.")
    if _optional_text(document.get("tax_treatment")) != "domestic_standard":
        raise LegacySupplierInvoiceExpenseAeatError("La factura recibida legacy no usa tratamiento nacional ordinario.")
    if _optional_text(document.get("special_regime_key")):
        raise LegacySupplierInvoiceExpenseAeatError("La factura recibida legacy usa un rÃ©gimen especial no soportado.")

    _required_text(supplier.get("legal_name"), "supplier.legal_name")
    _required_text(supplier.get("tax_id"), "supplier.tax_id")
    _required_text(document.get("supplier_invoice_number"), "document.supplier_invoice_number")
    snapshot_reception_number = _positive_int(
        document.get("reception_number"), "document.reception_number"
    )
    if snapshot_reception_number != _positive_int(
        getattr(invoice, "reception_number", None), "invoice.reception_number"
    ):
        raise LegacySupplierInvoiceExpenseAeatError(
            "El nÃºmero de recepciÃ³n persistido no coincide con el snapshot v1."
        )
    _required_date(document.get("issue_date"), "document.issue_date")
    _optional_date(document.get("operation_date"))
    parsed_breakdowns = _validated_breakdowns(breakdowns)
    _validated_totals(totals, parsed_breakdowns)
    return snapshot


def _validated_breakdowns(raw_breakdowns):
    if not raw_breakdowns:
        raise LegacySupplierInvoiceExpenseAeatError("El snapshot v1 no contiene desgloses de IVA.")
    positions = set()
    breakdowns = []
    for index, raw in enumerate(raw_breakdowns, start=1):
        if not isinstance(raw, Mapping):
            raise LegacySupplierInvoiceExpenseAeatError(f"Desglose de IVA invÃ¡lido: {index}.")
        position = _positive_int(raw.get("position"), f"tax_breakdowns.{index}.position")
        if position in positions:
            raise LegacySupplierInvoiceExpenseAeatError("Las posiciones de IVA no pueden repetirse.")
        positions.add(position)
        base = _nonnegative_money(raw.get("tax_base"), f"tax_breakdowns.{index}.tax_base")
        tax = _nonnegative_money(raw.get("tax_amount"), f"tax_breakdowns.{index}.tax_amount")
        deductible = _nonnegative_money(
            raw.get("deductible_tax_amount"), f"tax_breakdowns.{index}.deductible_tax_amount"
        )
        if deductible > tax:
            raise LegacySupplierInvoiceExpenseAeatError(
                "La cuota deducible del snapshot v1 supera la cuota soportada."
            )
        breakdowns.append({
            "position": position,
            "tax_base": base,
            "tax_rate": _nonnegative_money(raw.get("tax_rate"), f"tax_breakdowns.{index}.tax_rate"),
            "tax_amount": tax,
            "deductible_tax_amount": deductible,
        })
    return sorted(breakdowns, key=lambda item: item["position"])


def _validated_totals(raw_totals, breakdowns):
    totals = {
        field: _money(raw_totals.get(field), f"totals.{field}")
        for field in ("tax_base", "tax_amount", "deductible_tax_amount", "total_amount")
    }
    expected = {
        "tax_base": _sum(item["tax_base"] for item in breakdowns),
        "tax_amount": _sum(item["tax_amount"] for item in breakdowns),
        "deductible_tax_amount": _sum(item["deductible_tax_amount"] for item in breakdowns),
        "total_amount": _sum(item["tax_base"] + item["tax_amount"] for item in breakdowns),
    }
    if totals != expected:
        raise LegacySupplierInvoiceExpenseAeatError(
            "Los totales del snapshot v1 no reconcilian con sus desgloses de IVA."
        )
    return totals


def _existing_or_proposed_expense_code(invoice, supplier_tax_id):
    existing = _optional_text(getattr(invoice, "aeat_expense_concept_code", None))
    if existing in SUPPORTED_EXPENSE_CODES:
        return existing
    return "G01" if _optional_text(supplier_tax_id).upper() in G01_SUPPLIER_TAX_IDS else "G03"


def _existing_or_proposed_amount(invoice, breakdowns):
    existing = getattr(invoice, "expense_deductible_amount", None)
    if existing is not None:
        try:
            return _money(existing, "expense_deductible_amount")
        except LegacySupplierInvoiceExpenseAeatError:
            pass
    return _sum(item["tax_base"] for item in breakdowns)


def _has_complete_audit(invoice):
    return bool(
        getattr(invoice, "legacy_expense_classified_at", None)
        and _optional_text(getattr(invoice, "legacy_expense_classified_by", None))
        and getattr(invoice, "legacy_expense_received_at", None)
    )


def _has_partial_audit(invoice):
    values = (
        getattr(invoice, "legacy_expense_classified_at", None),
        _optional_text(getattr(invoice, "legacy_expense_classified_by", None)),
        getattr(invoice, "legacy_expense_received_at", None),
    )
    return any(values) and not all(values)


def _required_text(value, field):
    value = _optional_text(value)
    if not value:
        raise LegacySupplierInvoiceExpenseAeatError(f"Campo obligatorio ausente: {field}.")
    return value


def _optional_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _required_date(value, field):
    parsed = _optional_date(value)
    if parsed is None:
        raise LegacySupplierInvoiceExpenseAeatError(f"Fecha obligatoria ausente: {field}.")
    return parsed


def _optional_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date()
        except ValueError as exc:
            raise LegacySupplierInvoiceExpenseAeatError("Fecha fiscal legacy invÃ¡lida.") from exc
    raise LegacySupplierInvoiceExpenseAeatError("Fecha fiscal legacy invÃ¡lida.")


def _positive_int(value, field):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise LegacySupplierInvoiceExpenseAeatError(f"Identificador invÃ¡lido: {field}.") from exc
    if number <= 0 or str(number) != str(value).strip():
        raise LegacySupplierInvoiceExpenseAeatError(f"Identificador invÃ¡lido: {field}.")
    return number


def _money(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LegacySupplierInvoiceExpenseAeatError(f"Importe no vÃ¡lido: {field}.") from exc
    if not amount.is_finite():
        raise LegacySupplierInvoiceExpenseAeatError(f"Importe no vÃ¡lido: {field}.")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _nonnegative_money(value, field):
    amount = _money(value, field)
    if amount < Decimal("0.00"):
        raise LegacySupplierInvoiceExpenseAeatError(f"Importe negativo no vÃ¡lido: {field}.")
    return amount


def _sum(values):
    return sum(values, Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _normalized_datetime(value):
    if not isinstance(value, datetime):
        raise LegacySupplierInvoiceExpenseAeatError("La fecha de clasificaciÃ³n no es vÃ¡lida.")
    return value.replace(tzinfo=None)

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash
from api.manual_invoice_snapshot_builder import MANUAL_CORRECTIVE_SNAPSHOT_GENERATOR
from api.models import AccountingEntry, db


ENTRY_TYPE_SALE = AccountingEntry.ENTRY_TYPE_SALE

STATUS_PENDING = AccountingEntry.STATUS_PENDING
STATUS_RECORDED = AccountingEntry.STATUS_RECORDED
STATUS_FAILED = AccountingEntry.STATUS_FAILED

SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS = {1, 2, 3}


class AccountingEntryError(Exception):
    """Base error for accounting entry creation."""


class AccountingEntryValidationError(AccountingEntryError):
    """Raised when an invoice cannot produce an accounting entry."""


class AccountingEntryIntegrityError(AccountingEntryError):
    """Raised when the stored invoice snapshot hash does not match."""


class AccountingEntryUnsupportedSchema(AccountingEntryError):
    """Raised when the invoice snapshot schema cannot be used."""


def create_accounting_entry(invoice, *, db_session=None):
    """Create the internal sale accounting entry for an emitted invoice.

    This service is intentionally idempotent and does not commit or rollback.
    It copies accounting data from InvoiceSnapshot v1-v3 and never mutates
    fiscal invoice fields such as number, snapshot, hash, or issued_at.
    """
    session = db_session or db.session
    invoice_id = _required_invoice_id(invoice)

    existing_entry = (
        session.query(AccountingEntry)
        .filter_by(invoice_id=invoice_id, entry_type=ENTRY_TYPE_SALE)
        .one_or_none()
    )
    if existing_entry:
        return existing_entry

    snapshot = _validated_snapshot(invoice)
    _validate_snapshot_hash(invoice, snapshot)

    entry = AccountingEntry(
        invoice_id=invoice_id,
        entry_type=ENTRY_TYPE_SALE,
        status=STATUS_PENDING,
        invoice_number=_required_invoice_number(invoice),
        invoice_date=_invoice_date(snapshot),
        customer_name=_customer_name(snapshot),
        customer_tax_id=_customer_tax_id(snapshot),
        taxable_base=_money(snapshot["totals"].get("tax_base"), "totals.tax_base"),
        vat_amount=_money(snapshot["totals"].get("tax_amount"), "totals.tax_amount"),
        total_amount=_money(snapshot["totals"].get("total_amount"), "totals.total_amount"),
        currency=_currency(snapshot),
        payment_provider=_payment_provider(snapshot),
        order_id=_order_id(snapshot),
    )
    session.add(entry)
    session.flush()
    return entry


def _required_invoice_id(invoice):
    invoice_id = getattr(invoice, "id", None)
    if not invoice_id:
        raise AccountingEntryValidationError("Issued invoice id is required.")
    return invoice_id


def _required_invoice_number(invoice):
    invoice_number = getattr(invoice, "invoice_number", None)
    if not invoice_number:
        raise AccountingEntryValidationError("Issued invoice number is required.")
    return str(invoice_number)


def _validated_snapshot(invoice):
    if not getattr(invoice, "issued_at", None):
        raise AccountingEntryValidationError("Invoice must be issued before accounting.")

    snapshot = getattr(invoice, "invoice_snapshot", None)
    if not isinstance(snapshot, dict):
        raise AccountingEntryValidationError("Invoice snapshot is required.")

    schema_version = snapshot.get("schema_version")
    if schema_version not in SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS:
        raise AccountingEntryUnsupportedSchema("Unsupported invoice snapshot schema.")

    for block in ("customer", "operation", "payment", "totals"):
        if not isinstance(snapshot.get(block), dict):
            raise AccountingEntryValidationError(f"Invoice snapshot block {block} is required.")

    if schema_version == 3:
        _validate_rectification_snapshot(invoice, snapshot)

    return snapshot


def _validate_rectification_snapshot(invoice, snapshot):
    operation = snapshot["operation"]
    if operation.get("invoice_type") != "corrective":
        raise AccountingEntryValidationError("Corrective snapshot invoice type is required.")
    if getattr(invoice, "invoice_type", None) != "corrective":
        raise AccountingEntryValidationError("Corrective invoice type is required.")

    rectification = operation.get("rectification")
    if not isinstance(rectification, dict):
        raise AccountingEntryValidationError("Corrective snapshot reference is required.")
    scope = rectification.get("rectification_scope")
    if scope not in {"total", "partial"}:
        raise AccountingEntryValidationError("Corrective rectification scope is required.")
    if scope == "partial":
        _validate_manual_partial_rectification(invoice, snapshot, rectification)
        return

    original_invoice_id = _positive_integer(
        rectification.get("original_invoice_id"),
        "Corrective original invoice id is required.",
    )
    if original_invoice_id != getattr(invoice, "original_invoice_id", None):
        raise AccountingEntryValidationError("Corrective original invoice reference does not match.")

    if not str(rectification.get("original_invoice_number") or "").strip():
        raise AccountingEntryValidationError("Corrective original invoice number is required.")
    _invoice_date_value(
        rectification.get("original_invoice_issued_at"),
        "Corrective original invoice issue date is required.",
    )


def _validate_manual_partial_rectification(invoice, snapshot, rectification):
    metadata = snapshot.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("generator") != MANUAL_CORRECTIVE_SNAPSHOT_GENERATOR:
        raise AccountingEntryValidationError("Only manual partial rectifications are supported.")
    if rectification.get("rectification_type") != "differences":
        raise AccountingEntryValidationError("Manual partial rectifications must use differences.")
    if rectification.get("aeat_type") not in {"R1", "R4"}:
        raise AccountingEntryValidationError("Manual partial rectifications require AEAT type R1 or R4.")
    if getattr(invoice, "rectification_aeat_type", None) != rectification.get("aeat_type"):
        raise AccountingEntryValidationError("Corrective AEAT type does not match the snapshot.")

    reference_type = rectification.get("original_reference_type")
    original_number = str(rectification.get("original_invoice_number") or "").strip()
    original_date = rectification.get("original_invoice_issued_at")
    if not original_number:
        raise AccountingEntryValidationError("Corrective original invoice number is required.")
    _invoice_date_value(original_date, "Corrective original invoice issue date is required.")

    if reference_type == "invoice":
        original_invoice_id = _positive_integer(
            rectification.get("original_invoice_id"),
            "Corrective original invoice id is required.",
        )
        if original_invoice_id != getattr(invoice, "original_invoice_id", None):
            raise AccountingEntryValidationError("Corrective original invoice reference does not match.")
        if getattr(invoice, "external_original_invoice_number", None) or getattr(invoice, "external_original_issue_date", None):
            raise AccountingEntryValidationError("Modern corrective references cannot include an external original.")
        return

    if reference_type == "external":
        if rectification.get("original_invoice_id") is not None or getattr(invoice, "original_invoice_id", None) is not None:
            raise AccountingEntryValidationError("External corrective references cannot include an invoice id.")
        if getattr(invoice, "external_original_invoice_number", None) != original_number:
            raise AccountingEntryValidationError("External corrective invoice number does not match the snapshot.")
        if _invoice_date_value(
            getattr(invoice, "external_original_issue_date", None),
            "External corrective invoice issue date is required.",
        ) != _invoice_date_value(original_date, "Corrective original invoice issue date is required."):
            raise AccountingEntryValidationError("External corrective invoice date does not match the snapshot.")
        return

    raise AccountingEntryValidationError("Corrective original reference type is required.")


def _positive_integer(value, message):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise AccountingEntryValidationError(message) from exc
    if parsed <= 0 or str(parsed) != str(value).strip():
        raise AccountingEntryValidationError(message)
    return parsed


def _validate_snapshot_hash(invoice, snapshot):
    stored_hash = getattr(invoice, "invoice_snapshot_hash", None)
    if not stored_hash:
        raise AccountingEntryIntegrityError("Invoice snapshot hash is required.")

    calculated_hash = calculate_invoice_snapshot_hash(snapshot)
    if calculated_hash != stored_hash:
        raise AccountingEntryIntegrityError("Invoice snapshot hash mismatch.")


def _invoice_date(snapshot):
    return _invoice_date_value(
        snapshot["operation"].get("issue_date"),
        "Invoice issue date is required.",
    )


def _invoice_date_value(issue_date, required_message):
    if isinstance(issue_date, date) and not isinstance(issue_date, datetime):
        return issue_date
    if isinstance(issue_date, datetime):
        return issue_date.date()
    if isinstance(issue_date, str) and issue_date:
        try:
            return datetime.fromisoformat(issue_date).date()
        except ValueError as exc:
            raise AccountingEntryValidationError("Invoice issue date is invalid.") from exc
    raise AccountingEntryValidationError(required_message)


def _customer_name(snapshot):
    customer_name = snapshot["customer"].get("legal_name")
    if not customer_name:
        raise AccountingEntryValidationError("Customer name is required.")
    return str(customer_name)


def _customer_tax_id(snapshot):
    tax_id = snapshot["customer"].get("tax_id")
    return str(tax_id) if tax_id else None


def _currency(snapshot):
    currency = snapshot["operation"].get("currency")
    if not currency:
        raise AccountingEntryValidationError("Currency is required.")
    return str(currency).upper()


def _payment_provider(snapshot):
    provider = snapshot["payment"].get("provider")
    return str(provider) if provider else None


def _order_id(snapshot):
    order_id = snapshot["operation"].get("order_id")
    if order_id in (None, ""):
        return None
    return int(order_id)


def _money(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise AccountingEntryValidationError(f"{field} must be numeric.") from exc
    if not amount.is_finite():
        raise AccountingEntryValidationError(f"{field} must be numeric.")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

"""Issuance service for order-independent manual invoices and credits."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from api.invoice_issue_service import (
    CORRECTIVE_INVOICE_TYPE,
    DEFAULT_INVOICE_SERIES,
    DEFAULT_RECTIFICATION_SERIES,
    InvoiceIssueError,
    ORDINARY_INVOICE_TYPE,
)
from api.invoice_number_service import acquire_next_invoice_number
from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash
from api.manual_invoice_snapshot_builder import build_manual_invoice_snapshot


MANUAL_ISSUANCE_SOURCE = "manual_invoice_admin"


@dataclass(frozen=True)
class ManualIssuedInvoiceResult:
    invoice: object
    invoice_number: str
    created: bool


def issue_manual_invoice(*, db_session, draft_id, issuer, actor=None):
    """Issue a manual ordinary invoice or corrective credit exactly once."""
    draft = None
    try:
        draft = _lock_draft_for_update(db_session, draft_id)
        if draft is None:
            raise InvoiceIssueError("No se ha encontrado el borrador de factura manual.")
        if getattr(draft, "issued_invoice_id", None):
            invoice = getattr(draft, "issued_invoice", None) or _invoice_by_id(
                db_session, draft.issued_invoice_id
            )
            if invoice is None:
                raise InvoiceIssueError("El borrador emitido no tiene una factura asociada.")
            db_session.commit()
            return ManualIssuedInvoiceResult(invoice, invoice.invoice_number, False)
        if getattr(draft, "status", None) != "draft":
            raise InvoiceIssueError("El borrador no está disponible para emitir.")

        document_nature = _document_nature(draft)
        original_invoice = _locked_original_invoice(db_session, draft, document_nature)
        issued_at = _issued_at(getattr(draft, "issue_date", None))
        snapshot = build_manual_invoice_snapshot(
            draft,
            issuer,
            issue_date=issued_at,
            actor=actor,
            original_invoice=original_invoice,
        )
        if document_nature == "corrective" and original_invoice is not None:
            _validate_corrective_amount_within_original(
                db_session,
                original_invoice=original_invoice,
                corrective_snapshot=snapshot,
            )
        snapshot_hash = calculate_invoice_snapshot_hash(snapshot)
        allocation = acquire_next_invoice_number(
            db_session,
            series=DEFAULT_RECTIFICATION_SERIES if document_nature == "corrective" else DEFAULT_INVOICE_SERIES,
            fiscal_year=issued_at.year,
        )
        invoice = (
            _corrective_invoice_record(
                draft,
                invoice_number=allocation.invoice_number,
                snapshot=snapshot,
                snapshot_hash=snapshot_hash,
                issued_at=issued_at,
                actor=actor,
            )
            if document_nature == "corrective"
            else _invoice_record(
                draft,
                invoice_number=allocation.invoice_number,
                snapshot=snapshot,
                snapshot_hash=snapshot_hash,
                issued_at=issued_at,
                actor=actor,
            )
        )
        db_session.add(invoice)
        db_session.flush()
        draft.issued_invoice_id = invoice.id
        draft.status = "issued"
        draft.issued_at = issued_at
        draft.issued_by = _actor(actor)
        db_session.flush()
        db_session.commit()
        return ManualIssuedInvoiceResult(invoice, allocation.invoice_number, True)
    except Exception:
        db_session.rollback()
        raise


def _lock_draft_for_update(db_session, draft_id):
    from api.models import ManualInvoiceDraft
    return db_session.query(ManualInvoiceDraft).filter_by(id=draft_id).with_for_update().one_or_none()


def _invoice_by_id(db_session, invoice_id):
    return db_session.get(_invoice_model(), invoice_id)


def _document_nature(draft):
    nature = getattr(draft, "document_nature", None) or "ordinary"
    if nature not in {"ordinary", "corrective"}:
        raise InvoiceIssueError("La naturaleza de la factura manual no es válida.")
    return nature


def _locked_original_invoice(db_session, draft, document_nature):
    original_invoice_id = getattr(draft, "original_invoice_id", None)
    if document_nature != "corrective":
        if original_invoice_id is not None:
            raise InvoiceIssueError("Una factura ordinaria manual no puede tener factura original.")
        return None
    if original_invoice_id is None:
        return None
    invoice = (
        db_session.query(_invoice_model())
        .filter_by(id=original_invoice_id)
        .with_for_update()
        .one_or_none()
    )
    if invoice is None:
        raise InvoiceIssueError("No se ha encontrado la factura original moderna.")
    return invoice


def _invoice_record(draft, *, invoice_number, snapshot, snapshot_hash, issued_at, actor):
    Invoices = _invoice_model()
    try:
        total = Decimal(str(snapshot["totals"]["total_amount"]))
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise InvoiceIssueError("El snapshot manual no contiene un total válido.") from exc
    if total <= 0:
        raise InvoiceIssueError("La factura manual debe tener un total positivo.")
    customer = snapshot["customer"]
    return Invoices(
        invoice_number=invoice_number,
        order_id=None,
        invoice_type=ORDINARY_INVOICE_TYPE,
        pdf_path=None,
        amount=float(total),  # Legacy display field; the snapshot remains fiscal authority.
        client_name=customer["legal_name"],
        client_address=customer["address"],
        client_cif=customer["tax_id"],
        client_phone=None,
        order_details=list(snapshot["lines"]),
        invoice_snapshot=snapshot,
        invoice_snapshot_schema_version=snapshot["schema_version"],
        invoice_snapshot_hash=snapshot_hash,
        issued_at=issued_at,
        issuance_source=MANUAL_ISSUANCE_SOURCE,
        issued_by=_actor(actor),
    )


def _corrective_invoice_record(draft, *, invoice_number, snapshot, snapshot_hash, issued_at, actor):
    Invoices = _invoice_model()
    rectification = snapshot["operation"]["rectification"]
    customer = snapshot["customer"]
    total = _snapshot_total(snapshot)
    if total >= 0:
        raise InvoiceIssueError("El abono manual debe tener un total negativo.")

    external_reference = rectification.get("original_reference_type") == "external"
    return Invoices(
        invoice_number=invoice_number,
        order_id=None,
        invoice_type=CORRECTIVE_INVOICE_TYPE,
        original_invoice_id=None if external_reference else rectification["original_invoice_id"],
        external_original_invoice_number=rectification["original_invoice_number"] if external_reference else None,
        external_original_issue_date=_date_value(rectification["original_invoice_issued_at"])
        if external_reference else None,
        rectification_type=rectification["rectification_type"],
        rectification_reason=rectification["rectification_reason"],
        rectification_aeat_type=rectification["aeat_type"],
        pdf_path=None,
        amount=float(total),  # Legacy display field; the snapshot remains fiscal authority.
        client_name=customer["legal_name"],
        client_address=customer["address"],
        client_cif=customer["tax_id"],
        client_phone=customer.get("phone"),
        order_details=list(snapshot["lines"]),
        invoice_snapshot=snapshot,
        invoice_snapshot_schema_version=snapshot["schema_version"],
        invoice_snapshot_hash=snapshot_hash,
        issued_at=issued_at,
        issuance_source=MANUAL_ISSUANCE_SOURCE,
        issued_by=_actor(actor),
    )


def _snapshot_total(snapshot):
    try:
        total = Decimal(str(snapshot["totals"]["total_amount"]))
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise InvoiceIssueError("El snapshot manual no contiene un total válido.") from exc
    return total.quantize(Decimal("0.01"))


def _validate_corrective_amount_within_original(db_session, *, original_invoice, corrective_snapshot):
    """Keep manually linked partial credits within the original fiscal amounts."""
    original_snapshot = getattr(original_invoice, "invoice_snapshot", None)
    if not isinstance(original_snapshot, dict):
        raise InvoiceIssueError("La factura original moderna no tiene snapshot fiscal válido.")

    original_totals = _snapshot_amounts(original_snapshot, "La factura original moderna")
    requested_totals = _snapshot_amounts(corrective_snapshot, "El abono manual")
    if any(value >= 0 for value in requested_totals.values()):
        raise InvoiceIssueError("El abono manual debe tener importes fiscales negativos.")

    used = {field: Decimal("0.00") for field in original_totals}
    existing_credits = (
        db_session.query(_invoice_model())
        .filter_by(original_invoice_id=getattr(original_invoice, "id", None), invoice_type=CORRECTIVE_INVOICE_TYPE)
        .all()
    )
    for credit in existing_credits:
        snapshot = getattr(credit, "invoice_snapshot", None)
        if not isinstance(snapshot, dict):
            raise InvoiceIssueError("Una rectificativa previa no tiene snapshot fiscal válido.")
        credit_totals = _snapshot_amounts(snapshot, "Una rectificativa previa")
        if any(value > 0 for value in credit_totals.values()):
            raise InvoiceIssueError("Una rectificativa previa tiene importes fiscales incompatibles.")
        for field, value in credit_totals.items():
            used[field] += abs(value)

    for field, original_amount in original_totals.items():
        if original_amount < 0 or used[field] + abs(requested_totals[field]) > original_amount:
            raise InvoiceIssueError("El abono supera los importes fiscales pendientes de la factura original.")


def _snapshot_amounts(snapshot, subject):
    totals = snapshot.get("totals") if isinstance(snapshot, dict) else None
    if not isinstance(totals, dict):
        raise InvoiceIssueError(f"{subject} no contiene totales fiscales válidos.")
    values = {}
    for field in ("tax_base", "tax_amount", "total_amount"):
        try:
            values[field] = Decimal(str(totals[field])).quantize(Decimal("0.01"))
        except (KeyError, InvalidOperation, TypeError) as exc:
            raise InvoiceIssueError(f"{subject} no contiene {field} válido.") from exc
    return values


def _date_value(value):
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError as exc:
            raise InvoiceIssueError("La fecha de la factura original no es válida.") from exc
    raise InvoiceIssueError("La fecha de la factura original es obligatoria.")


def _issued_at(issue_date):
    if issue_date is None:
        raise InvoiceIssueError("La fecha de expedición es obligatoria.")
    now = datetime.now(timezone.utc)
    return datetime.combine(issue_date, now.timetz())


def _actor(actor):
    if actor is None:
        return None
    if isinstance(actor, dict):
        return actor.get("email") or str(actor.get("id") or "")
    return getattr(actor, "email", None) or str(getattr(actor, "id", "") or actor)


def _invoice_model():
    from api.models import Invoices
    return Invoices

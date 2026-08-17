"""Issuance service for positive, order-independent ordinary invoices."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from api.invoice_issue_service import DEFAULT_INVOICE_SERIES, InvoiceIssueError, ORDINARY_INVOICE_TYPE
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
    """Issue a draft exactly once, reserving an F number only after validation."""
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

        issued_at = _issued_at(getattr(draft, "issue_date", None))
        snapshot = build_manual_invoice_snapshot(draft, issuer, issue_date=issued_at, actor=actor)
        snapshot_hash = calculate_invoice_snapshot_hash(snapshot)
        allocation = acquire_next_invoice_number(
            db_session,
            series=DEFAULT_INVOICE_SERIES,
            fiscal_year=issued_at.year,
        )
        invoice = _invoice_record(
            draft,
            invoice_number=allocation.invoice_number,
            snapshot=snapshot,
            snapshot_hash=snapshot_hash,
            issued_at=issued_at,
            actor=actor,
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

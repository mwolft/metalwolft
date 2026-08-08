from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Mapping

from api.invoice_number_service import InvoiceNumberError, acquire_next_invoice_number
from api.invoice_snapshot_builder import (
    build_invoice_snapshot,
    build_rectification_snapshot_from_invoice,
)
from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash


ORDINARY_INVOICE_TYPE = "ordinary"
DEFAULT_INVOICE_SERIES = "F"
CORRECTIVE_INVOICE_TYPE = "corrective"
DEFAULT_RECTIFICATION_SERIES = "R"
DEFAULT_ISSUANCE_SOURCE = "manual"
_UNSET = object()


class InvoiceIssueError(Exception):
    """Raised when an order cannot be issued as an invoice."""


@dataclass(frozen=True)
class IssuedInvoiceResult:
    invoice: object
    invoice_number: str
    created: bool


def issue_invoice_for_order(
    *,
    db_session,
    checkout_session,
    issuer,
    order=None,
    order_id=None,
    issue_date=None,
    source=DEFAULT_ISSUANCE_SOURCE,
    actor=None,
    series=DEFAULT_INVOICE_SERIES,
):
    """Issue an ordinary fiscal invoice for a paid order.

    The whole operation is intentionally owned by this service: it locks the
    order, checks idempotency, allocates the fiscal number, persists the
    immutable snapshot and commits everything as a single transaction.
    """
    target_order_id = _resolve_order_id(order=order, order_id=order_id)
    issued_at = issue_date or datetime.now(timezone.utc)
    locked_order = None
    previous_order_invoice_number = _UNSET

    try:
        locked_order = _lock_order_for_update(db_session, target_order_id)
        if locked_order is None:
            raise InvoiceIssueError("No se ha encontrado el pedido para facturar.")
        previous_order_invoice_number = getattr(locked_order, "invoice_number", None)

        existing_invoice = _find_existing_ordinary_invoice(db_session, locked_order.id)
        if existing_invoice is not None:
            db_session.commit()
            return IssuedInvoiceResult(
                invoice=existing_invoice,
                invoice_number=existing_invoice.invoice_number,
                created=False,
            )

        allocation = acquire_next_invoice_number(
            db_session,
            series=series,
            fiscal_year=_fiscal_year_from_issue_date(issued_at),
        )
        snapshot = build_invoice_snapshot(
            locked_order,
            checkout_session,
            issuer,
            issue_date=issued_at,
            source=source,
            actor=actor,
        )
        snapshot_hash = calculate_invoice_snapshot_hash(snapshot)

        invoice = _build_invoice_record(
            locked_order,
            checkout_session,
            invoice_number=allocation.invoice_number,
            snapshot=snapshot,
            snapshot_hash=snapshot_hash,
            issued_at=issued_at,
            source=source,
            actor=actor,
        )
        db_session.add(invoice)
        locked_order.invoice_number = allocation.invoice_number
        db_session.flush()
        db_session.commit()

        return IssuedInvoiceResult(
            invoice=invoice,
            invoice_number=allocation.invoice_number,
            created=True,
        )
    except Exception:
        if locked_order is not None and previous_order_invoice_number is not _UNSET:
            locked_order.invoice_number = previous_order_invoice_number
        db_session.rollback()
        raise


def issue_total_rectification_for_invoice(
    *,
    db_session,
    original_invoice_id,
    rectification_type,
    rectification_reason,
    issue_date=None,
    source=DEFAULT_ISSUANCE_SOURCE,
    actor=None,
    rectification_scope="total",
):
    """Issue one total corrective invoice from an emitted invoice snapshot.

    The original invoice is locked before checking for an existing correction so
    a retry cannot allocate a second R-series number for the same total
    rectification. No order, checkout, or live product/customer data is read.
    """
    if original_invoice_id is None:
        raise InvoiceIssueError("El identificador de la factura original es obligatorio.")
    if rectification_scope != "total":
        raise InvoiceIssueError("La rectificacion parcial todavia no esta soportada.")

    issued_at = issue_date or datetime.now(timezone.utc)
    locked_original = None

    try:
        locked_original = _lock_invoice_for_update(db_session, original_invoice_id)
        _validate_original_invoice_for_rectification(locked_original)

        existing_rectification = _find_existing_corrective_invoice(
            db_session,
            locked_original.id,
        )
        if existing_rectification is not None:
            _ensure_matching_total_rectification(
                existing_rectification,
                rectification_type=rectification_type,
                rectification_reason=rectification_reason,
                rectification_scope=rectification_scope,
            )
            db_session.commit()
            return IssuedInvoiceResult(
                invoice=existing_rectification,
                invoice_number=existing_rectification.invoice_number,
                created=False,
            )

        snapshot = build_rectification_snapshot_from_invoice(
            locked_original,
            issue_date=issued_at,
            rectification_type=rectification_type,
            rectification_reason=rectification_reason,
            rectification_scope=rectification_scope,
            source=source,
            actor=actor,
        )
        allocation = acquire_next_invoice_number(
            db_session,
            series=DEFAULT_RECTIFICATION_SERIES,
            fiscal_year=_fiscal_year_from_issue_date(issued_at),
        )
        snapshot_hash = calculate_invoice_snapshot_hash(snapshot)

        invoice = _build_corrective_invoice_record(
            locked_original,
            invoice_number=allocation.invoice_number,
            snapshot=snapshot,
            snapshot_hash=snapshot_hash,
            issued_at=issued_at,
            source=source,
            actor=actor,
            rectification_type=rectification_type,
            rectification_reason=rectification_reason,
        )
        db_session.add(invoice)
        db_session.flush()
        db_session.commit()

        return IssuedInvoiceResult(
            invoice=invoice,
            invoice_number=allocation.invoice_number,
            created=True,
        )
    except Exception:
        db_session.rollback()
        raise


def _resolve_order_id(*, order, order_id):
    if order_id is not None:
        return order_id
    resolved_order_id = getattr(order, "id", None)
    if resolved_order_id is None:
        raise InvoiceIssueError("El identificador del pedido es obligatorio.")
    return resolved_order_id


def _lock_order_for_update(db_session, order_id):
    Orders = _order_model()
    return (
        db_session.query(Orders)
        .filter_by(id=order_id)
        .with_for_update()
        .one_or_none()
    )


def _lock_invoice_for_update(db_session, invoice_id):
    Invoices = _invoice_model()
    return (
        db_session.query(Invoices)
        .filter_by(id=invoice_id)
        .with_for_update()
        .one_or_none()
    )


def _find_existing_ordinary_invoice(db_session, order_id):
    Invoices = _invoice_model()
    return (
        db_session.query(Invoices)
        .filter_by(order_id=order_id, invoice_type=ORDINARY_INVOICE_TYPE)
        .one_or_none()
    )


def _find_existing_corrective_invoice(db_session, original_invoice_id):
    Invoices = _invoice_model()
    return (
        db_session.query(Invoices)
        .filter_by(
            original_invoice_id=original_invoice_id,
            invoice_type=CORRECTIVE_INVOICE_TYPE,
        )
        .order_by(Invoices.id.asc())
        .first()
    )


def _build_invoice_record(
    order,
    checkout_session,
    *,
    invoice_number,
    snapshot,
    snapshot_hash,
    issued_at,
    source,
    actor,
):
    Invoices = _invoice_model()
    customer_snapshot = _customer_snapshot(checkout_session)

    return Invoices(
        invoice_number=invoice_number,
        order_id=order.id,
        invoice_type=ORDINARY_INVOICE_TYPE,
        pdf_path=None,
        amount=getattr(order, "total_amount", 0),
        client_name=_customer_name(customer_snapshot),
        client_address=_customer_address(customer_snapshot),
        client_cif=customer_snapshot.get("CIF") or customer_snapshot.get("tax_id"),
        client_phone=customer_snapshot.get("phone"),
        order_details=_serialize_order_details(order),
        invoice_snapshot=snapshot,
        invoice_snapshot_schema_version=snapshot.get("schema_version"),
        invoice_snapshot_hash=snapshot_hash,
        issued_at=issued_at,
        issuance_source=source,
        issued_by=_serialize_issued_by(actor),
    )


def _build_corrective_invoice_record(
    original_invoice,
    *,
    invoice_number,
    snapshot,
    snapshot_hash,
    issued_at,
    source,
    actor,
    rectification_type,
    rectification_reason,
):
    Invoices = _invoice_model()
    customer = snapshot["customer"]

    return Invoices(
        invoice_number=invoice_number,
        order_id=getattr(original_invoice, "order_id", None),
        invoice_type=CORRECTIVE_INVOICE_TYPE,
        original_invoice_id=original_invoice.id,
        rectification_type=rectification_type,
        rectification_reason=rectification_reason,
        pdf_path=None,
        amount=_snapshot_total_amount(snapshot),
        client_name=customer["legal_name"],
        client_address=customer["address"],
        client_cif=customer.get("tax_id"),
        client_phone=customer.get("phone"),
        # This legacy column is derived from the frozen snapshot, never order data.
        order_details=deepcopy(snapshot["lines"]),
        invoice_snapshot=snapshot,
        invoice_snapshot_schema_version=snapshot.get("schema_version"),
        invoice_snapshot_hash=snapshot_hash,
        issued_at=issued_at,
        issuance_source=source,
        issued_by=_serialize_issued_by(actor),
    )


def _validate_original_invoice_for_rectification(invoice):
    if invoice is None:
        raise InvoiceIssueError("No se ha encontrado la factura original.")
    if getattr(invoice, "invoice_type", None) == CORRECTIVE_INVOICE_TYPE:
        raise InvoiceIssueError("No se puede rectificar una factura rectificativa.")
    if not getattr(invoice, "invoice_number", None) or getattr(invoice, "issued_at", None) is None:
        raise InvoiceIssueError("La factura original debe estar emitida.")
    if not isinstance(getattr(invoice, "invoice_snapshot", None), Mapping):
        raise InvoiceIssueError("La factura original no tiene un snapshot fiscal valido.")


def _ensure_matching_total_rectification(
    invoice,
    *,
    rectification_type,
    rectification_reason,
    rectification_scope,
):
    snapshot = getattr(invoice, "invoice_snapshot", None)
    operation = snapshot.get("operation") if isinstance(snapshot, Mapping) else None
    rectification = operation.get("rectification") if isinstance(operation, Mapping) else None
    if (
        isinstance(rectification, Mapping)
        and rectification.get("rectification_scope") == rectification_scope
        and getattr(invoice, "rectification_type", None) == rectification_type
        and getattr(invoice, "rectification_reason", None) == rectification_reason
    ):
        return
    raise InvoiceIssueError("La factura original ya tiene una rectificacion emitida.")


def _snapshot_total_amount(snapshot):
    try:
        total = Decimal(str(snapshot["totals"]["total_amount"]))
    except (KeyError, TypeError, InvalidOperation) as exc:
        raise InvoiceIssueError("El snapshot rectificativo no contiene un total valido.") from exc
    return float(total)


def _customer_snapshot(checkout_session):
    snapshot = getattr(checkout_session, "customer_snapshot", None)
    return snapshot if isinstance(snapshot, Mapping) else {}


def _customer_name(customer_snapshot):
    legal_name = customer_snapshot.get("legal_name")
    if legal_name:
        return legal_name
    return " ".join(
        part
        for part in (
            customer_snapshot.get("firstname"),
            customer_snapshot.get("lastname"),
        )
        if part
    ).strip()


def _customer_address(customer_snapshot):
    return customer_snapshot.get("billing_address") or customer_snapshot.get("shipping_address") or ""


def _serialize_order_details(order):
    serialized_details = []
    for detail in getattr(order, "order_details", []) or []:
        if hasattr(detail, "serialize"):
            serialized_details.append(detail.serialize())
        elif isinstance(detail, Mapping):
            serialized_details.append(dict(detail))
    return serialized_details


def _serialize_issued_by(actor):
    if actor is None:
        return None
    if isinstance(actor, str):
        return actor
    if isinstance(actor, Mapping):
        return actor.get("email") or _string_or_none(actor.get("id"))
    return (
        getattr(actor, "email", None)
        or _string_or_none(getattr(actor, "id", None))
        or str(actor)
    )


def _string_or_none(value):
    return None if value is None else str(value)


def _fiscal_year_from_issue_date(issue_date):
    return issue_date.year


def _order_model():
    from api.models import Orders

    return Orders


def _invoice_model():
    from api.models import Invoices

    return Invoices

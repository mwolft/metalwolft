import os
from dataclasses import asdict, dataclass

from api.invoice_accounting_service import create_accounting_entry
from api.invoice_email_service import (
    EMAIL_STATUS_FAILED,
    EMAIL_STATUS_SENT,
    send_invoice_email,
)
from api.invoice_fiscal_submission_service import (
    PROVIDER_VERIFACTU,
    STATUS_ACCEPTED,
    STATUS_PENDING,
    STATUS_SENT,
    create_pending_submission,
)
from api.invoice_issue_service import issue_invoice_for_order
from api.invoice_pdf_service import generate_invoice_pdf
from api.models import AccountingEntry, InvoiceFiscalSubmission, Invoices


STEP_INVOICE = "invoice"
STEP_PDF = "pdf"
STEP_ACCOUNTING = "accounting"
STEP_VERIFACTU = "verifactu"
STEP_EMAIL = "email"

STATUS_COMPLETED = "completed"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"

USABLE_FISCAL_SUBMISSION_STATUSES = (
    STATUS_PENDING,
    STATUS_SENT,
    STATUS_ACCEPTED,
)


class InvoiceWorkflowError(Exception):
    """Base error for the invoice document workflow."""


class InvoiceWorkflowConfigurationError(InvoiceWorkflowError):
    """Raised when required infrastructure for the workflow is missing."""


class InvoiceWorkflowStepError(InvoiceWorkflowError):
    """Raised when a workflow step cannot continue."""


@dataclass(frozen=True)
class InvoiceWorkflowStepResult:
    name: str
    status: str
    already_completed: bool = False
    detail: str | None = None

    def to_dict(self):
        data = asdict(self)
        if data["detail"] is None:
            data.pop("detail")
        return data


@dataclass(frozen=True)
class InvoiceWorkflowResult:
    order_id: int
    invoice_id: int | None
    invoice_number: str | None
    completed: bool
    failed_step: str | None
    steps: tuple[InvoiceWorkflowStepResult, ...]

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "completed": self.completed,
            "failed_step": self.failed_step,
            "steps": [step.to_dict() for step in self.steps],
        }


def run_invoice_workflow_for_order(
    order_id,
    *,
    issuer,
    checkout_session,
    actor,
    invoice_output_dir,
    mailer,
    db_session,
):
    """Run the ordinary invoice document workflow with one commit per phase.

    The invoice issuance service owns its own fiscal transaction and commits
    internally. Every following phase commits independently so retries can
    resume from the last confirmed state without consuming another number.
    """
    _validate_workflow_configuration(
        order_id=order_id,
        issuer=issuer,
        checkout_session=checkout_session,
        invoice_output_dir=invoice_output_dir,
        mailer=mailer,
        db_session=db_session,
    )

    steps = []
    invoice = None

    try:
        issued_result = issue_invoice_for_order(
            db_session=db_session,
            order_id=order_id,
            checkout_session=checkout_session,
            issuer=issuer,
            actor=actor,
            source="manual",
        )
        invoice = issued_result.invoice
        steps.append(_step(
            STEP_INVOICE,
            STATUS_COMPLETED,
            already_completed=not issued_result.created,
        ))
    except Exception as exc:
        return _failed_result(
            order_id,
            invoice,
            steps,
            STEP_INVOICE,
            "No se ha podido emitir la factura.",
            exc,
        )

    invoice = _refresh_invoice(db_session, invoice)
    pdf_step = _run_pdf_step(invoice, invoice_output_dir, db_session)
    steps.append(pdf_step)
    if pdf_step.status == STATUS_FAILED:
        return _workflow_result(order_id, invoice, steps, completed=False, failed_step=STEP_PDF)

    invoice = _refresh_invoice(db_session, invoice)
    accounting_step = _run_accounting_step(invoice, db_session)
    steps.append(accounting_step)
    if accounting_step.status == STATUS_FAILED:
        return _workflow_result(order_id, invoice, steps, completed=False, failed_step=STEP_ACCOUNTING)

    invoice = _refresh_invoice(db_session, invoice)
    verifactu_step = _run_verifactu_step(invoice, db_session)
    steps.append(verifactu_step)
    if verifactu_step.status == STATUS_FAILED:
        return _workflow_result(order_id, invoice, steps, completed=False, failed_step=STEP_VERIFACTU)

    invoice = _refresh_invoice(db_session, invoice)
    email_step = _run_email_step(invoice, mailer, db_session)
    steps.append(email_step)
    if email_step.status == STATUS_FAILED:
        return _workflow_result(order_id, invoice, steps, completed=False, failed_step=STEP_EMAIL)

    return _workflow_result(order_id, invoice, steps, completed=True, failed_step=None)


def _validate_workflow_configuration(
    *,
    order_id,
    issuer,
    checkout_session,
    invoice_output_dir,
    mailer,
    db_session,
):
    if not order_id:
        raise InvoiceWorkflowConfigurationError("El pedido es obligatorio.")
    if not issuer:
        raise InvoiceWorkflowConfigurationError("La configuracion del emisor es obligatoria.")
    if checkout_session is None:
        raise InvoiceWorkflowConfigurationError("La sesion de checkout es obligatoria.")
    if not invoice_output_dir:
        raise InvoiceWorkflowConfigurationError("La carpeta de facturas es obligatoria.")
    if mailer is None:
        raise InvoiceWorkflowConfigurationError("El adaptador de email es obligatorio.")
    if db_session is None:
        raise InvoiceWorkflowConfigurationError("La sesion de base de datos es obligatoria.")


def _run_pdf_step(invoice, invoice_output_dir, db_session):
    try:
        if _invoice_pdf_file_exists(invoice_output_dir, getattr(invoice, "pdf_path", None)):
            db_session.commit()
            return _step(STEP_PDF, STATUS_SKIPPED, already_completed=True)

        generate_invoice_pdf(invoice, output_dir=invoice_output_dir, regenerate=False)
        db_session.commit()
        return _step(STEP_PDF, STATUS_COMPLETED)
    except Exception:
        db_session.rollback()
        return _step(STEP_PDF, STATUS_FAILED, detail="No se ha podido generar el PDF.")


def _run_accounting_step(invoice, db_session):
    try:
        existing_entry = (
            db_session.query(AccountingEntry)
            .filter_by(invoice_id=invoice.id, entry_type=AccountingEntry.ENTRY_TYPE_SALE)
            .one_or_none()
        )
        create_accounting_entry(invoice, db_session=db_session)
        db_session.commit()
        return _step(
            STEP_ACCOUNTING,
            STATUS_SKIPPED if existing_entry is not None else STATUS_COMPLETED,
            already_completed=existing_entry is not None,
        )
    except Exception:
        db_session.rollback()
        return _step(STEP_ACCOUNTING, STATUS_FAILED, detail="No se ha podido registrar la contabilidad.")


def _run_verifactu_step(invoice, db_session):
    try:
        existing_submission = _find_usable_fiscal_submission(db_session, invoice.id)
        if existing_submission is not None:
            db_session.commit()
            return _step(STEP_VERIFACTU, STATUS_SKIPPED, already_completed=True)

        create_pending_submission(invoice, db_session=db_session)
        db_session.commit()
        return _step(STEP_VERIFACTU, STATUS_COMPLETED)
    except Exception:
        db_session.rollback()
        return _step(STEP_VERIFACTU, STATUS_FAILED, detail="No se ha podido crear el envio fiscal pendiente.")


def _run_email_step(invoice, mailer, db_session):
    attempts_before = int(getattr(invoice, "email_attempts", None) or 0)
    already_sent_before = getattr(invoice, "email_status", None) == EMAIL_STATUS_SENT

    try:
        send_invoice_email(invoice, mailer=mailer)
        db_session.commit()
        return _step(
            STEP_EMAIL,
            STATUS_SKIPPED if already_sent_before else STATUS_COMPLETED,
            already_completed=already_sent_before,
        )
    except Exception:
        invoice_id = getattr(invoice, "id", None)
        db_session.rollback()
        _persist_email_failure(db_session, invoice_id, attempts_before)
        return _step(STEP_EMAIL, STATUS_FAILED, detail="No se ha podido enviar el email de factura.")


def _find_usable_fiscal_submission(db_session, invoice_id):
    return (
        db_session.query(InvoiceFiscalSubmission)
        .filter(
            InvoiceFiscalSubmission.invoice_id == invoice_id,
            InvoiceFiscalSubmission.provider == PROVIDER_VERIFACTU,
            InvoiceFiscalSubmission.status.in_(USABLE_FISCAL_SUBMISSION_STATUSES),
        )
        .order_by(InvoiceFiscalSubmission.attempt_number.asc())
        .first()
    )


def _persist_email_failure(db_session, invoice_id, attempts_before):
    if not invoice_id:
        return

    failed_invoice = db_session.query(Invoices).get(invoice_id)
    if not failed_invoice:
        return

    failed_invoice.email_status = EMAIL_STATUS_FAILED
    failed_invoice.email_attempts = int(attempts_before or 0) + 1
    failed_invoice.email_last_error = "No se pudo enviar el email de factura."
    db_session.commit()


def _refresh_invoice(db_session, invoice):
    invoice_id = getattr(invoice, "id", None)
    if not invoice_id:
        return invoice
    return db_session.query(Invoices).get(invoice_id) or invoice


def _invoice_pdf_file_exists(output_dir, pdf_path):
    filename = os.path.basename(pdf_path or "")
    if not filename:
        return False
    return os.path.isfile(os.path.join(output_dir, filename))


def _step(name, status, *, already_completed=False, detail=None):
    return InvoiceWorkflowStepResult(
        name=name,
        status=status,
        already_completed=already_completed,
        detail=detail,
    )


def _failed_result(order_id, invoice, steps, failed_step, detail, exc):
    del exc
    steps = [*steps, _step(failed_step, STATUS_FAILED, detail=detail)]
    return _workflow_result(order_id, invoice, steps, completed=False, failed_step=failed_step)


def _workflow_result(order_id, invoice, steps, *, completed, failed_step):
    return InvoiceWorkflowResult(
        order_id=order_id,
        invoice_id=getattr(invoice, "id", None),
        invoice_number=getattr(invoice, "invoice_number", None),
        completed=completed,
        failed_step=failed_step,
        steps=tuple(steps),
    )

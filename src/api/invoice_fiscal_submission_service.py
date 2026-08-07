from datetime import datetime, timezone

from api.models import InvoiceFiscalSubmission, db


PROVIDER_VERIFACTU = InvoiceFiscalSubmission.PROVIDER_VERIFACTU

STATUS_PENDING = InvoiceFiscalSubmission.STATUS_PENDING
STATUS_SENT = InvoiceFiscalSubmission.STATUS_SENT
STATUS_ACCEPTED = InvoiceFiscalSubmission.STATUS_ACCEPTED
STATUS_REJECTED = InvoiceFiscalSubmission.STATUS_REJECTED
STATUS_FAILED = InvoiceFiscalSubmission.STATUS_FAILED


class InvoiceFiscalSubmissionError(Exception):
    """Base error for fiscal submission persistence."""


class InvoiceFiscalSubmissionValidationError(InvoiceFiscalSubmissionError):
    """Raised when a fiscal submission cannot be created or transitioned."""


def create_pending_submission(invoice, *, db_session=None, request_payload=None):
    """Create a new pending VeriFactu submission attempt for an issued invoice.

    The service deliberately does not commit. It also never mutates fiscal
    invoice data such as number, snapshot, hash, or issued_at.
    """
    session = db_session or db.session
    invoice_id = _require_invoice_id(invoice)
    attempt_number = _next_attempt_number(session, invoice_id, PROVIDER_VERIFACTU)

    submission = InvoiceFiscalSubmission(
        invoice_id=invoice_id,
        provider=PROVIDER_VERIFACTU,
        status=STATUS_PENDING,
        attempt_number=attempt_number,
        request_payload=request_payload,
    )
    session.add(submission)
    return submission


def mark_sent(submission, *, request_payload=None, external_reference=None, submitted_at=None):
    _require_submission(submission)
    submission.status = STATUS_SENT
    submission.submitted_at = submitted_at or _utcnow()
    if request_payload is not None:
        submission.request_payload = request_payload
    if external_reference is not None:
        submission.external_reference = external_reference
    return submission


def mark_accepted(
    submission,
    *,
    response_payload=None,
    response_code=None,
    response_message=None,
    verification_csv=None,
    verification_url=None,
    external_reference=None,
    response_at=None,
):
    _require_submission(submission)
    submission.status = STATUS_ACCEPTED
    submission.response_at = response_at or _utcnow()
    _apply_response_fields(
        submission,
        response_payload=response_payload,
        response_code=response_code,
        response_message=response_message,
        verification_csv=verification_csv,
        verification_url=verification_url,
        external_reference=external_reference,
    )
    submission.error_type = None
    submission.error_detail = None
    return submission


def mark_rejected(
    submission,
    *,
    response_payload=None,
    response_code=None,
    response_message=None,
    error_type=None,
    error_detail=None,
    verification_csv=None,
    verification_url=None,
    external_reference=None,
    response_at=None,
):
    _require_submission(submission)
    submission.status = STATUS_REJECTED
    submission.response_at = response_at or _utcnow()
    _apply_response_fields(
        submission,
        response_payload=response_payload,
        response_code=response_code,
        response_message=response_message,
        verification_csv=verification_csv,
        verification_url=verification_url,
        external_reference=external_reference,
    )
    submission.error_type = error_type
    submission.error_detail = error_detail
    return submission


def mark_failed(
    submission,
    *,
    error_type=None,
    error_detail=None,
    response_payload=None,
    response_code=None,
    response_message=None,
    response_at=None,
):
    _require_submission(submission)
    submission.status = STATUS_FAILED
    submission.response_at = response_at or _utcnow()
    submission.error_type = error_type
    submission.error_detail = error_detail
    if response_payload is not None:
        submission.response_payload = response_payload
    if response_code is not None:
        submission.response_code = response_code
    if response_message is not None:
        submission.response_message = response_message
    return submission


def _next_attempt_number(session, invoice_id, provider):
    last_attempt = (
        session.query(InvoiceFiscalSubmission.attempt_number)
        .filter_by(invoice_id=invoice_id, provider=provider)
        .order_by(InvoiceFiscalSubmission.attempt_number.desc())
        .first()
    )
    if not last_attempt:
        return 1
    return int(last_attempt[0] or 0) + 1


def _apply_response_fields(
    submission,
    *,
    response_payload=None,
    response_code=None,
    response_message=None,
    verification_csv=None,
    verification_url=None,
    external_reference=None,
):
    if response_payload is not None:
        submission.response_payload = response_payload
    if response_code is not None:
        submission.response_code = response_code
    if response_message is not None:
        submission.response_message = response_message
    if verification_csv is not None:
        submission.verification_csv = verification_csv
    if verification_url is not None:
        submission.verification_url = verification_url
    if external_reference is not None:
        submission.external_reference = external_reference


def _require_invoice_id(invoice):
    invoice_id = getattr(invoice, "id", None)
    if not invoice_id:
        raise InvoiceFiscalSubmissionValidationError("Issued invoice id is required.")
    return invoice_id


def _require_submission(submission):
    if submission is None:
        raise InvoiceFiscalSubmissionValidationError("Fiscal submission is required.")


def _utcnow():
    return datetime.now(timezone.utc)

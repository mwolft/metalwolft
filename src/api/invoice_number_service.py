import re
from dataclasses import dataclass


MIN_FISCAL_YEAR = 2000
MAX_FISCAL_YEAR = 2199
MAX_SEQUENCE_NUMBER = 999999
SERIES_PATTERN = re.compile(r"^[A-Z]{1,10}$")


class InvoiceNumberError(Exception):
    """Base error for fiscal invoice number allocation."""


class InvoiceNumberValidationError(InvoiceNumberError):
    """Raised when invoice number inputs are invalid."""


class InvoiceSequenceExhausted(InvoiceNumberError):
    """Raised when a fiscal sequence has reached its annual limit."""


class InvoiceSequenceConcurrencyError(InvoiceNumberError):
    """Raised when the sequence row cannot be safely allocated."""


@dataclass(frozen=True)
class InvoiceNumberAllocation:
    series: str
    fiscal_year: int
    sequence_number: int
    invoice_number: str


def format_invoice_number(series, fiscal_year, sequence_number):
    """Format a confirmed fiscal sequence number.

    Planned v1 series are `F` for ordinary invoices and `R` for future
    corrective invoices, but the validator deliberately allows other
    uppercase series so the domain can grow without schema changes.
    """
    normalized_series = normalize_invoice_series(series)
    normalized_year = validate_fiscal_year(fiscal_year)
    normalized_sequence = validate_sequence_number(sequence_number)
    return f"{normalized_series}{normalized_year:04d}{normalized_sequence:06d}"


def acquire_next_invoice_number(session, *, series, fiscal_year):
    """Allocate the next fiscal number inside the caller transaction.

    This helper does not create sessions, commit, rollback, or open an
    independent transaction. If the caller rolls back after this function
    returns, the `last_number` increment rolls back with the rest of the work.
    """
    normalized_series = normalize_invoice_series(series)
    normalized_year = validate_fiscal_year(fiscal_year)

    try:
        _ensure_invoice_sequence_row(session, normalized_series, normalized_year)
        sequence = _lock_invoice_sequence(session, normalized_series, normalized_year)

        if sequence is None:
            raise InvoiceSequenceConcurrencyError(
                "Could not lock invoice sequence row after creation."
            )

        current_last_number = int(sequence.last_number or 0)
        next_number = current_last_number + 1
        if next_number > MAX_SEQUENCE_NUMBER:
            raise InvoiceSequenceExhausted(
                f"Invoice sequence {normalized_series}/{normalized_year} is exhausted."
            )

        sequence.last_number = next_number
        session.flush()

    except InvoiceNumberError:
        raise
    except Exception as exc:
        raise InvoiceSequenceConcurrencyError(
            "Could not allocate the next invoice number safely."
        ) from exc

    return InvoiceNumberAllocation(
        series=normalized_series,
        fiscal_year=normalized_year,
        sequence_number=next_number,
        invoice_number=format_invoice_number(
            normalized_series,
            normalized_year,
            next_number,
        ),
    )


def normalize_invoice_series(series):
    if not isinstance(series, str):
        raise InvoiceNumberValidationError("Invoice series must be a string.")
    if series != series.strip():
        raise InvoiceNumberValidationError("Invoice series cannot contain surrounding spaces.")

    normalized = series.upper()
    if not normalized:
        raise InvoiceNumberValidationError("Invoice series is required.")
    if not SERIES_PATTERN.fullmatch(normalized):
        raise InvoiceNumberValidationError(
            "Invoice series must contain only uppercase letters A-Z and be at most 10 characters."
        )
    return normalized


def validate_fiscal_year(fiscal_year):
    normalized = _coerce_integer(fiscal_year, "Fiscal year")
    if normalized < MIN_FISCAL_YEAR or normalized > MAX_FISCAL_YEAR:
        raise InvoiceNumberValidationError(
            f"Fiscal year must be between {MIN_FISCAL_YEAR} and {MAX_FISCAL_YEAR}."
        )
    return normalized


def validate_sequence_number(sequence_number):
    normalized = _coerce_integer(sequence_number, "Sequence number")
    if normalized < 1:
        raise InvoiceNumberValidationError("Sequence number must be greater than zero.")
    if normalized > MAX_SEQUENCE_NUMBER:
        raise InvoiceSequenceExhausted("Invoice sequence number exceeds 999999.")
    return normalized


def _coerce_integer(value, label):
    if isinstance(value, bool):
        raise InvoiceNumberValidationError(f"{label} must be an integer.")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise InvoiceNumberValidationError(f"{label} must be an integer.")


def _ensure_invoice_sequence_row(session, series, fiscal_year):
    from sqlalchemy.dialects.postgresql import insert as postgresql_insert

    from api.models import InvoiceSequence

    insert_statement = (
        postgresql_insert(InvoiceSequence.__table__)
        .values(series=series, fiscal_year=fiscal_year, last_number=0)
        .on_conflict_do_nothing(
            index_elements=["series", "fiscal_year"],
        )
    )
    session.execute(insert_statement)


def _lock_invoice_sequence(session, series, fiscal_year):
    from api.models import InvoiceSequence

    return (
        session.query(InvoiceSequence)
        .filter_by(series=series, fiscal_year=fiscal_year)
        .with_for_update()
        .one_or_none()
    )

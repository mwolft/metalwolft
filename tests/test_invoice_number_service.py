import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import ANY, patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api import invoice_number_service as service  # noqa: E402
from api.invoice_number_service import (  # noqa: E402
    InvoiceNumberValidationError,
    InvoiceSequenceConcurrencyError,
    InvoiceSequenceExhausted,
    acquire_next_invoice_number,
    format_invoice_number,
)


class FakeSequence:
    def __init__(self, last_number=0):
        self.last_number = last_number


class FakeSession:
    def __init__(self, *, fail_flush=False):
        self.fail_flush = fail_flush
        self.flush_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0

    def flush(self):
        self.flush_calls += 1
        if self.fail_flush:
            raise RuntimeError("flush failed")

    def commit(self):
        self.commit_calls += 1

    def rollback(self):
        self.rollback_calls += 1


class InvoiceNumberFormatTest(unittest.TestCase):
    def test_formats_ordinary_invoice_number(self):
        self.assertEqual(format_invoice_number("F", 2026, 1), "F2026000001")

    def test_formats_future_corrective_invoice_number(self):
        self.assertEqual(format_invoice_number("R", 2026, 1), "R2026000001")

    def test_formats_sequence_with_leading_zeroes(self):
        self.assertEqual(format_invoice_number("F", 2026, 42), "F2026000042")

    def test_normalizes_series_to_uppercase(self):
        self.assertEqual(format_invoice_number("f", 2026, 1), "F2026000001")

    def test_same_input_produces_stable_format(self):
        first = format_invoice_number("F", 2026, 1)
        second = format_invoice_number("F", 2026, 1)

        self.assertEqual(first, second)

    def test_rejects_empty_series(self):
        with self.assertRaises(InvoiceNumberValidationError):
            format_invoice_number("", 2026, 1)

    def test_rejects_series_with_spaces(self):
        with self.assertRaises(InvoiceNumberValidationError):
            format_invoice_number(" F ", 2026, 1)

    def test_rejects_invalid_series_characters(self):
        for invalid in ("F-1", "F 1", "F1", "Ñ", "ABCDEFGHIJK"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(InvoiceNumberValidationError):
                    format_invoice_number(invalid, 2026, 1)

    def test_rejects_invalid_fiscal_year(self):
        for invalid in (1999, 2200, "year", True, 2026.5):
            with self.subTest(invalid=invalid):
                with self.assertRaises(InvoiceNumberValidationError):
                    format_invoice_number("F", invalid, 1)

    def test_rejects_invalid_sequence_number(self):
        for invalid in (0, -1, "sequence", True, 1.5):
            with self.subTest(invalid=invalid):
                with self.assertRaises(InvoiceNumberValidationError):
                    format_invoice_number("F", 2026, invalid)

    def test_rejects_exhausted_sequence_number(self):
        with self.assertRaises(InvoiceSequenceExhausted):
            format_invoice_number("F", 2026, 1000000)


class InvoiceNumberAllocationTest(unittest.TestCase):
    def allocate_with_sequence(self, sequence, *, session=None, series="F", fiscal_year=2026):
        session = session or FakeSession()
        with patch.object(service, "_ensure_invoice_sequence_row") as ensure_row, patch.object(
            service,
            "_lock_invoice_sequence",
            return_value=sequence,
        ) as lock_row:
            allocation = acquire_next_invoice_number(
                session,
                series=series,
                fiscal_year=fiscal_year,
            )
        return allocation, session, ensure_row, lock_row

    def test_first_assignment_creates_sequence_row_and_returns_first_number(self):
        allocation, session, ensure_row, lock_row = self.allocate_with_sequence(FakeSequence(0))

        ensure_row.assert_called_once_with(session, "F", 2026)
        lock_row.assert_called_once_with(session, "F", 2026)
        self.assertEqual(allocation.invoice_number, "F2026000001")
        self.assertEqual(allocation.sequence_number, 1)

    def test_existing_row_increments_to_second_assignment(self):
        sequence = FakeSequence(1)

        allocation, _, _, _ = self.allocate_with_sequence(sequence)

        self.assertEqual(sequence.last_number, 2)
        self.assertEqual(allocation.invoice_number, "F2026000002")

    def test_multiple_assignments_increment_same_transactional_row(self):
        sequence = FakeSequence(0)
        session = FakeSession()

        first, _, _, _ = self.allocate_with_sequence(sequence, session=session)
        second, _, _, _ = self.allocate_with_sequence(sequence, session=session)

        self.assertEqual(first.invoice_number, "F2026000001")
        self.assertEqual(second.invoice_number, "F2026000002")
        self.assertEqual(session.flush_calls, 2)

    def test_change_of_year_uses_requested_year(self):
        allocation, _, ensure_row, lock_row = self.allocate_with_sequence(
            FakeSequence(0),
            fiscal_year=2027,
        )

        ensure_row.assert_called_once_with(ANY, "F", 2027)
        lock_row.assert_called_once_with(ANY, "F", 2027)
        self.assertEqual(allocation.invoice_number, "F2027000001")

    def test_series_are_independent_inputs(self):
        ordinary, _, _, _ = self.allocate_with_sequence(FakeSequence(0), series="F")
        corrective, _, _, _ = self.allocate_with_sequence(FakeSequence(0), series="R")

        self.assertEqual(ordinary.invoice_number, "F2026000001")
        self.assertEqual(corrective.invoice_number, "R2026000001")

    def test_exhausted_sequence_raises_without_flushing(self):
        session = FakeSession()

        with patch.object(service, "_ensure_invoice_sequence_row"), patch.object(
            service,
            "_lock_invoice_sequence",
            return_value=FakeSequence(999999),
        ):
            with self.assertRaises(InvoiceSequenceExhausted):
                acquire_next_invoice_number(session, series="F", fiscal_year=2026)

        self.assertEqual(session.flush_calls, 0)

    def test_does_not_commit_or_rollback(self):
        _, session, _, _ = self.allocate_with_sequence(FakeSequence(0))

        self.assertEqual(session.commit_calls, 0)
        self.assertEqual(session.rollback_calls, 0)

    def test_flush_failure_preserves_original_cause_without_rollback(self):
        session = FakeSession(fail_flush=True)
        with patch.object(service, "_ensure_invoice_sequence_row"), patch.object(
            service,
            "_lock_invoice_sequence",
            return_value=FakeSequence(0),
        ):
            with self.assertRaises(InvoiceSequenceConcurrencyError) as error:
                acquire_next_invoice_number(session, series="F", fiscal_year=2026)

        self.assertIsInstance(error.exception.__cause__, RuntimeError)
        self.assertEqual(session.commit_calls, 0)
        self.assertEqual(session.rollback_calls, 0)

    def test_missing_locked_row_raises_concurrency_error(self):
        session = FakeSession()
        with patch.object(service, "_ensure_invoice_sequence_row"), patch.object(
            service,
            "_lock_invoice_sequence",
            return_value=None,
        ):
            with self.assertRaises(InvoiceSequenceConcurrencyError):
                acquire_next_invoice_number(session, series="F", fiscal_year=2026)


class InvoiceNumberServiceSourceTest(unittest.TestCase):
    def test_uses_postgresql_on_conflict_for_first_row(self):
        source = inspect.getsource(service._ensure_invoice_sequence_row)

        self.assertIn("postgresql_insert", source)
        self.assertIn("on_conflict_do_nothing", source)
        self.assertIn('index_elements=["series", "fiscal_year"]', source)

    def test_locks_sequence_row_for_update(self):
        source = inspect.getsource(service._lock_invoice_sequence)

        self.assertIn("with_for_update()", source)

    def test_does_not_query_invoice_maximums_or_legacy_generators(self):
        source = Path(service.__file__).read_text(encoding="utf-8")

        self.assertNotIn("MAX(", source)
        self.assertNotIn("COUNT(", source)
        self.assertNotIn("generate_next_invoice_number", source)
        self.assertNotIn("Invoices", source)
        self.assertNotIn("Orders", source)

    def test_helper_is_not_connected_to_legacy_callers_yet(self):
        for relative_path in (
            "src/api/routes.py",
            "src/api/invoice_issue_service.py",
            "src/api/admin.py",
        ):
            source = (ROOT_DIR / relative_path).read_text(encoding="utf-8")
            self.assertNotIn("invoice_number_service", source)
            self.assertNotIn("acquire_next_invoice_number", source)


if __name__ == "__main__":
    unittest.main()

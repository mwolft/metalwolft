import tempfile
import unittest
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


STEP_INVOICE = "invoice"
STEP_PDF = "pdf"
STEP_ACCOUNTING = "accounting"
STEP_VERIFACTU = "verifactu"
STEP_EMAIL = "email"
STATUS_COMPLETED = "completed"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_DB_TEST_DEPENDENCIES = all(
    has_package(package)
    for package in ("flask", "flask_sqlalchemy", "sqlalchemy", "slugify")
)

if HAS_DB_TEST_DEPENDENCIES:
    from api.invoice_workflow_service import (  # noqa: E402
        InvoiceWorkflowConfigurationError,
        run_invoice_workflow_for_order,
    )


class FakeDbSession:
    def __init__(self, invoice, *, lookup_invoice=True):
        self.invoice = invoice
        self.lookup_invoice = lookup_invoice
        self.accounting_entry = None
        self.fiscal_submission = None
        self.commit_count = 0
        self.rollback_count = 0

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def query(self, model):
        return FakeQuery(self, model)


class FakeQuery:
    def __init__(self, session, model):
        self.session = session
        self.model_name = getattr(model, "__name__", str(model))

    def get(self, item_id):
        if (
            self.model_name == "Invoices"
            and self.session.lookup_invoice
            and item_id == self.session.invoice.id
        ):
            return self.session.invoice
        return None

    def filter_by(self, **_kwargs):
        return self

    def filter(self, *_args):
        return self

    def order_by(self, *_args):
        return self

    def one_or_none(self):
        if self.model_name == "AccountingEntry":
            return self.session.accounting_entry
        return None

    def first(self):
        if self.model_name == "InvoiceFiscalSubmission":
            submission = self.session.fiscal_submission
            if submission and submission.status in ("PENDING", "SENT", "ACCEPTED"):
                return submission
        return None


def make_invoice(**overrides):
    data = {
        "id": 123,
        "invoice_number": "F2026000001",
        "pdf_path": None,
        "email_status": None,
        "email_attempts": 0,
        "email_last_error": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_checkout_session():
    return SimpleNamespace(id=99, order_id=355)


def run_workflow(invoice, *, session=None, output_dir=None, mailer=None):
    db_session = session or FakeDbSession(invoice)
    output_dir = output_dir or tempfile.mkdtemp()
    return run_invoice_workflow_for_order(
        355,
        issuer={"legal_name": "MetalWolft"},
        checkout_session=make_checkout_session(),
        actor="admin@example.com",
        invoice_output_dir=output_dir,
        mailer=mailer or SimpleNamespace(send=lambda _message: None),
        db_session=db_session,
    ), db_session


@unittest.skipUnless(HAS_DB_TEST_DEPENDENCIES, "Flask/SQLAlchemy test dependencies are not installed.")
class InvoiceWorkflowServiceTest(unittest.TestCase):
    def test_complete_workflow_runs_steps_in_order_and_commits_each_phase(self):
        invoice = make_invoice()
        calls = []

        def fake_issue(**kwargs):
            calls.append(STEP_INVOICE)
            kwargs["db_session"].commit()
            return SimpleNamespace(invoice=invoice, invoice_number=invoice.invoice_number, created=True)

        def fake_pdf(target_invoice, **_kwargs):
            calls.append(STEP_PDF)
            target_invoice.pdf_path = "/api/download-invoice/invoice_F2026000001.pdf"
            return SimpleNamespace(filename="invoice_F2026000001.pdf")

        def fake_accounting(target_invoice, **kwargs):
            calls.append(STEP_ACCOUNTING)
            kwargs["db_session"].accounting_entry = SimpleNamespace(id=44)
            return kwargs["db_session"].accounting_entry

        def fake_submission(target_invoice, **kwargs):
            calls.append(STEP_VERIFACTU)
            kwargs["db_session"].fiscal_submission = SimpleNamespace(id=55, status="PENDING")
            return kwargs["db_session"].fiscal_submission

        def fake_email(target_invoice, **_kwargs):
            calls.append(STEP_EMAIL)
            target_invoice.email_status = "sent"
            target_invoice.email_attempts = 1
            return SimpleNamespace(already_sent=False)

        with patch("api.invoice_workflow_service.issue_invoice_for_order", side_effect=fake_issue), patch(
            "api.invoice_workflow_service.generate_invoice_pdf", side_effect=fake_pdf
        ), patch("api.invoice_workflow_service.create_accounting_entry", side_effect=fake_accounting), patch(
            "api.invoice_workflow_service.create_pending_submission", side_effect=fake_submission
        ), patch("api.invoice_workflow_service.send_invoice_email", side_effect=fake_email):
            result, db_session = run_workflow(invoice)

        self.assertTrue(result.completed)
        self.assertIsNone(result.failed_step)
        self.assertEqual(calls, [STEP_INVOICE, STEP_PDF, STEP_ACCOUNTING, STEP_VERIFACTU, STEP_EMAIL])
        self.assertEqual([step.status for step in result.steps], [STATUS_COMPLETED] * 5)
        self.assertEqual(db_session.commit_count, 5)
        self.assertEqual(db_session.rollback_count, 0)

    def test_existing_invoice_does_not_consume_second_number(self):
        invoice = make_invoice()

        with patch("api.invoice_workflow_service.issue_invoice_for_order") as issue, patch(
            "api.invoice_workflow_service.generate_invoice_pdf"
        ) as pdf, patch("api.invoice_workflow_service.create_accounting_entry") as accounting, patch(
            "api.invoice_workflow_service.create_pending_submission"
        ) as submission, patch("api.invoice_workflow_service.send_invoice_email") as email:
            issue.return_value = SimpleNamespace(invoice=invoice, invoice_number=invoice.invoice_number, created=False)
            pdf.side_effect = lambda target_invoice, **_kwargs: setattr(
                target_invoice, "pdf_path", "/api/download-invoice/invoice_F2026000001.pdf"
            )
            accounting.side_effect = lambda _invoice, **kwargs: setattr(
                kwargs["db_session"], "accounting_entry", SimpleNamespace(id=1)
            )
            submission.side_effect = lambda _invoice, **kwargs: setattr(
                kwargs["db_session"], "fiscal_submission", SimpleNamespace(id=1, status="PENDING")
            )
            email.side_effect = lambda target_invoice, **_kwargs: setattr(target_invoice, "email_status", "sent")

            result, _db_session = run_workflow(invoice)

        self.assertEqual(result.steps[0].name, STEP_INVOICE)
        self.assertTrue(result.steps[0].already_completed)
        self.assertEqual(result.steps[0].status, STATUS_COMPLETED)
        issue.assert_called_once()

    def test_reuses_existing_pdf_accounting_verifactu_and_sent_email(self):
        invoice = make_invoice(
            pdf_path="/api/download-invoice/invoice_F2026000001.pdf",
            email_status="sent",
            email_attempts=1,
        )
        db_session = FakeDbSession(invoice)
        db_session.accounting_entry = SimpleNamespace(id=44)
        db_session.fiscal_submission = SimpleNamespace(id=55, status="PENDING")

        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "invoice_F2026000001.pdf").write_bytes(b"%PDF-1.4")
            with patch("api.invoice_workflow_service.issue_invoice_for_order") as issue, patch(
                "api.invoice_workflow_service.generate_invoice_pdf"
            ) as pdf, patch("api.invoice_workflow_service.create_accounting_entry") as accounting, patch(
                "api.invoice_workflow_service.create_pending_submission"
            ) as submission, patch("api.invoice_workflow_service.send_invoice_email") as email:
                issue.return_value = SimpleNamespace(invoice=invoice, invoice_number=invoice.invoice_number, created=False)
                email.return_value = SimpleNamespace(already_sent=True)

                result, _db_session = run_workflow(invoice, session=db_session, output_dir=temp_dir)

        self.assertTrue(result.completed)
        self.assertEqual(
            [(step.name, step.status, step.already_completed) for step in result.steps],
            [
                (STEP_INVOICE, STATUS_COMPLETED, True),
                (STEP_PDF, STATUS_SKIPPED, True),
                (STEP_ACCOUNTING, STATUS_SKIPPED, True),
                (STEP_VERIFACTU, STATUS_SKIPPED, True),
                (STEP_EMAIL, STATUS_SKIPPED, True),
            ],
        )
        pdf.assert_not_called()
        accounting.assert_called_once()
        submission.assert_not_called()
        email.assert_called_once()

    def test_failure_in_issue_stops_all_later_steps(self):
        invoice = make_invoice()

        with patch("api.invoice_workflow_service.issue_invoice_for_order", side_effect=RuntimeError("sql detail")), patch(
            "api.invoice_workflow_service.generate_invoice_pdf"
        ) as pdf, patch("api.invoice_workflow_service.create_accounting_entry") as accounting, patch(
            "api.invoice_workflow_service.create_pending_submission"
        ) as submission, patch("api.invoice_workflow_service.send_invoice_email") as email:
            result, _db_session = run_workflow(invoice)

        self.assertFalse(result.completed)
        self.assertEqual(result.failed_step, STEP_INVOICE)
        self.assertEqual(result.steps[-1].status, STATUS_FAILED)
        pdf.assert_not_called()
        accounting.assert_not_called()
        submission.assert_not_called()
        email.assert_not_called()

    def test_failure_in_pdf_preserves_invoice_and_stops_later_steps(self):
        invoice = make_invoice()

        with patch("api.invoice_workflow_service.issue_invoice_for_order") as issue, patch(
            "api.invoice_workflow_service.generate_invoice_pdf", side_effect=RuntimeError("disk path")
        ), patch("api.invoice_workflow_service.create_accounting_entry") as accounting, patch(
            "api.invoice_workflow_service.create_pending_submission"
        ) as submission, patch("api.invoice_workflow_service.send_invoice_email") as email:
            issue.return_value = SimpleNamespace(invoice=invoice, invoice_number=invoice.invoice_number, created=True)
            result, db_session = run_workflow(invoice)

        self.assertFalse(result.completed)
        self.assertEqual(result.invoice_id, invoice.id)
        self.assertEqual(result.failed_step, STEP_PDF)
        self.assertEqual(db_session.rollback_count, 1)
        accounting.assert_not_called()
        submission.assert_not_called()
        email.assert_not_called()

    def test_failure_in_accounting_preserves_invoice_and_pdf(self):
        invoice = make_invoice()

        with patch("api.invoice_workflow_service.issue_invoice_for_order") as issue, patch(
            "api.invoice_workflow_service.generate_invoice_pdf"
        ) as pdf, patch(
            "api.invoice_workflow_service.create_accounting_entry", side_effect=RuntimeError("accounting detail")
        ), patch("api.invoice_workflow_service.create_pending_submission") as submission, patch(
            "api.invoice_workflow_service.send_invoice_email"
        ) as email:
            issue.return_value = SimpleNamespace(invoice=invoice, invoice_number=invoice.invoice_number, created=True)
            pdf.side_effect = lambda target_invoice, **_kwargs: setattr(
                target_invoice, "pdf_path", "/api/download-invoice/invoice_F2026000001.pdf"
            )
            result, _db_session = run_workflow(invoice)

        self.assertFalse(result.completed)
        self.assertEqual(result.failed_step, STEP_ACCOUNTING)
        self.assertEqual(invoice.pdf_path, "/api/download-invoice/invoice_F2026000001.pdf")
        submission.assert_not_called()
        email.assert_not_called()

    def test_failure_in_verifactu_preserves_previous_steps_and_does_not_send_email(self):
        invoice = make_invoice()

        with patch("api.invoice_workflow_service.issue_invoice_for_order") as issue, patch(
            "api.invoice_workflow_service.generate_invoice_pdf"
        ) as pdf, patch("api.invoice_workflow_service.create_accounting_entry") as accounting, patch(
            "api.invoice_workflow_service.create_pending_submission", side_effect=RuntimeError("http must not happen")
        ), patch("api.invoice_workflow_service.send_invoice_email") as email:
            issue.return_value = SimpleNamespace(invoice=invoice, invoice_number=invoice.invoice_number, created=True)
            pdf.side_effect = lambda target_invoice, **_kwargs: setattr(
                target_invoice, "pdf_path", "/api/download-invoice/invoice_F2026000001.pdf"
            )
            accounting.side_effect = lambda _invoice, **kwargs: setattr(
                kwargs["db_session"], "accounting_entry", SimpleNamespace(id=1)
            )
            result, _db_session = run_workflow(invoice)

        self.assertFalse(result.completed)
        self.assertEqual(result.failed_step, STEP_VERIFACTU)
        email.assert_not_called()

    def test_failure_in_email_persists_failed_status_and_attempts(self):
        invoice = make_invoice(email_attempts=2)

        with patch("api.invoice_workflow_service.issue_invoice_for_order") as issue, patch(
            "api.invoice_workflow_service.generate_invoice_pdf"
        ) as pdf, patch("api.invoice_workflow_service.create_accounting_entry") as accounting, patch(
            "api.invoice_workflow_service.create_pending_submission"
        ) as submission, patch(
            "api.invoice_workflow_service.send_invoice_email", side_effect=RuntimeError("smtp detail")
        ):
            issue.return_value = SimpleNamespace(invoice=invoice, invoice_number=invoice.invoice_number, created=True)
            pdf.side_effect = lambda target_invoice, **_kwargs: setattr(
                target_invoice, "pdf_path", "/api/download-invoice/invoice_F2026000001.pdf"
            )
            accounting.side_effect = lambda _invoice, **kwargs: setattr(
                kwargs["db_session"], "accounting_entry", SimpleNamespace(id=1)
            )
            submission.side_effect = lambda _invoice, **kwargs: setattr(
                kwargs["db_session"], "fiscal_submission", SimpleNamespace(id=1, status="PENDING")
            )
            result, db_session = run_workflow(invoice)

        self.assertFalse(result.completed)
        self.assertEqual(result.failed_step, STEP_EMAIL)
        self.assertEqual(invoice.email_status, "failed")
        self.assertEqual(invoice.email_attempts, 3)
        self.assertEqual(invoice.email_last_error, "No se pudo enviar el email de factura.")
        self.assertEqual(db_session.commit_count, 5)
        self.assertEqual(db_session.rollback_count, 1)

    def test_failure_in_email_uses_invoice_fallback_and_still_commits_failure(self):
        invoice = make_invoice(email_attempts=0)
        db_session = FakeDbSession(invoice, lookup_invoice=False)

        with patch("api.invoice_workflow_service.issue_invoice_for_order") as issue, patch(
            "api.invoice_workflow_service.generate_invoice_pdf"
        ) as pdf, patch("api.invoice_workflow_service.create_accounting_entry") as accounting, patch(
            "api.invoice_workflow_service.create_pending_submission"
        ) as submission, patch(
            "api.invoice_workflow_service.send_invoice_email", side_effect=RuntimeError("smtp detail")
        ):
            issue.return_value = SimpleNamespace(invoice=invoice, invoice_number=invoice.invoice_number, created=True)
            pdf.side_effect = lambda target_invoice, **_kwargs: setattr(
                target_invoice, "pdf_path", "/api/download-invoice/invoice_F2026000001.pdf"
            )
            accounting.side_effect = lambda _invoice, **kwargs: setattr(
                kwargs["db_session"], "accounting_entry", SimpleNamespace(id=1)
            )
            submission.side_effect = lambda _invoice, **kwargs: setattr(
                kwargs["db_session"], "fiscal_submission", SimpleNamespace(id=1, status="PENDING")
            )
            result, _db_session = run_workflow(invoice, session=db_session)

        self.assertFalse(result.completed)
        self.assertEqual(result.failed_step, STEP_EMAIL)
        self.assertEqual(invoice.email_status, "failed")
        self.assertEqual(invoice.email_attempts, 1)
        self.assertEqual(invoice.email_last_error, "No se pudo enviar el email de factura.")
        self.assertEqual(db_session.commit_count, 5)
        self.assertEqual(db_session.rollback_count, 1)

    def test_configuration_is_required(self):
        with self.assertRaises(InvoiceWorkflowConfigurationError):
            run_invoice_workflow_for_order(
                355,
                issuer={"legal_name": "MetalWolft"},
                checkout_session=make_checkout_session(),
                actor="admin@example.com",
                invoice_output_dir="",
                mailer=SimpleNamespace(send=lambda _message: None),
                db_session=FakeDbSession(make_invoice()),
            )


class InvoiceWorkflowServiceSourceTest(unittest.TestCase):
    def test_service_has_no_excel_http_verifactu_transport_or_checkout_side_effects(self):
        source = (SRC_DIR / "api/invoice_workflow_service.py").read_text(encoding="utf-8")

        for forbidden in (
            "export_sales_accounting_entries",
            "requests",
            "_paypal",
            "stripe",
            "build_checkout_quote",
            "cleanup_cart_lines_from_checkout_quote",
            "mark_sent(",
            "mark_accepted(",
            "mark_rejected(",
            "mark_failed(",
        ):
            self.assertNotIn(forbidden, source)

    def test_service_declares_expected_result_contract(self):
        source = (SRC_DIR / "api/invoice_workflow_service.py").read_text(encoding="utf-8")

        for expected in (
            "class InvoiceWorkflowStepResult",
            "class InvoiceWorkflowResult",
            "completed: bool",
            "failed_step: str | None",
            "def to_dict(self)",
            "STEP_INVOICE = \"invoice\"",
            "STEP_PDF = \"pdf\"",
            "STEP_ACCOUNTING = \"accounting\"",
            "STEP_VERIFACTU = \"verifactu\"",
            "STEP_EMAIL = \"email\"",
        ):
            self.assertIn(expected, source)

    def test_email_failure_is_persisted_after_rollback_with_separate_commit(self):
        source = (SRC_DIR / "api/invoice_workflow_service.py").read_text(encoding="utf-8")
        email_step = source[source.index("def _run_email_step"):source.index("def _find_usable_fiscal_submission")]
        persist_helper = source[source.index("def _persist_email_failure"):source.index("def _refresh_invoice")]

        self.assertIn("db_session.rollback()", email_step)
        self.assertIn("_persist_email_failure(db_session, invoice, attempts_before)", email_step)
        self.assertIn('failed_invoice.email_status = EMAIL_STATUS_FAILED', persist_helper)
        self.assertIn('failed_invoice.email_attempts = int(attempts_before or 0) + 1', persist_helper)
        self.assertIn('failed_invoice.email_last_error = "No se pudo enviar el email de factura."', persist_helper)
        self.assertIn("failed_invoice = db_session.query(Invoices).get(invoice_id) or invoice", persist_helper)
        self.assertIn("db_session.commit()", persist_helper)


if __name__ == "__main__":
    unittest.main()

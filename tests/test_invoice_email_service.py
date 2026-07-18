import copy
import os
import shutil
import sys
import unittest
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
TEST_TMP_ROOT = ROOT_DIR / ".tmp-invoice-email-tests"
MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/a2b3c4d5e6f7_add_invoice_email_status_fields.py"
)

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.invoice_email_service import (  # noqa: E402
    EMAIL_STATUS_FAILED,
    EMAIL_STATUS_SENT,
    PDF_MIME_TYPE,
    InvoiceEmailIntegrityError,
    InvoiceEmailPdfMissing,
    InvoiceEmailRecipientMissing,
    InvoiceEmailSendError,
    InvoiceEmailSnapshotMissing,
    InvoiceEmailUnsupportedSchema,
    send_invoice_email,
)
from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash  # noqa: E402


def snapshot(overrides=None):
    data = {
        "schema_version": 1,
        "metadata": {
            "generator": "invoice_snapshot_builder_v1",
            "generated_at": "2026-07-15T10:00:00+00:00",
        },
        "issuer": {
            "legal_name": "MetalWolft Legal",
            "trade_name": "MetalWolft",
            "tax_id": "B00000000",
            "address": "Calle Taller 1",
            "postal_code": "13000",
            "city": "Ciudad Real",
            "country_code": "ES",
            "email": "admin@metalwolft.com",
        },
        "customer": {
            "legal_name": "Sergio Arias",
            "tax_id": "00000000T",
            "address": "Calle Factura 3",
            "postal_code": "13001",
            "city": "Ciudad Real",
            "country_code": "ES",
            "email": "cliente@example.com",
        },
        "operation": {
            "invoice_type": "ordinary",
            "issue_date": "2026-07-16",
            "operation_date": "2026-07-15",
            "currency": "EUR",
            "order_id": 123,
            "order_locator": "AB1234",
            "order_date": "2026-07-15",
        },
        "lines": [],
        "totals": {"total_amount": "121.00"},
        "payment": {"provider": "stripe", "status": "paid"},
        "references": {"checkout_session_id": 10, "order_id": 123},
    }
    data.update(overrides or {})
    return data


class SnapshotInvoice:
    def __init__(
        self,
        *,
        invoice_number="F2026000001",
        invoice_snapshot=None,
        stored_hash=None,
        pdf_path="/api/download-invoice/invoice_F2026000001.pdf",
    ):
        self.invoice_number = invoice_number
        self.invoice_snapshot = invoice_snapshot if invoice_snapshot is not None else snapshot()
        self.invoice_snapshot_hash = stored_hash or calculate_invoice_snapshot_hash(self.invoice_snapshot)
        self.invoice_snapshot_schema_version = self.invoice_snapshot.get("schema_version")
        self.pdf_path = pdf_path
        self.issued_at = datetime(2026, 7, 16, 9, 30)
        self.email_status = None
        self.email_sent_at = None
        self.email_last_error = None
        self.email_attempts = 0
        self.commit_called = False
        self.rollback_called = False

    @property
    def order(self):
        raise AssertionError("Invoice Email v2 must not read order")

    @property
    def user(self):
        raise AssertionError("Invoice Email v2 must not read user")

    @property
    def checkout_session(self):
        raise AssertionError("Invoice Email v2 must not read checkout_session")

    def commit(self):
        self.commit_called = True

    def rollback(self):
        self.rollback_called = True


class FakeMailer:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.sent = []

    def send(self, message):
        if self.fail:
            raise RuntimeError("smtp secret failure")
        self.sent.append(message)


@contextmanager
def temp_invoice_dir():
    TEST_TMP_ROOT.mkdir(exist_ok=True)
    case_dir = TEST_TMP_ROOT / f"case-{uuid.uuid4().hex}"
    case_dir.mkdir()
    try:
        yield case_dir
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def tearDownModule():
    shutil.rmtree(TEST_TMP_ROOT, ignore_errors=True)


def write_pdf(directory, filename="invoice_F2026000001.pdf"):
    pdf_path = directory / filename
    pdf_path.write_bytes(b"%PDF-1.4\n% invoice test\n%%EOF")
    return pdf_path


def attachment(message):
    return message.attachments[0]


def attachment_filename(attached):
    return attached.filename


def attachment_content_type(attached):
    return attached.content_type


class InvoiceEmailServiceTest(unittest.TestCase):
    def test_sends_invoice_email_from_snapshot_and_marks_sent(self):
        invoice = SnapshotInvoice()
        mailer = FakeMailer()

        with temp_invoice_dir() as tmpdir:
            write_pdf(tmpdir)
            result = send_invoice_email(invoice, mailer=mailer, invoice_folder=tmpdir)

        self.assertEqual(result.recipient, "cliente@example.com")
        self.assertEqual(result.invoice_number, "F2026000001")
        self.assertEqual(result.attachment_filename, "invoice_F2026000001.pdf")
        self.assertFalse(result.already_sent)
        self.assertEqual(invoice.email_status, EMAIL_STATUS_SENT)
        self.assertIsNotNone(invoice.email_sent_at)
        self.assertIsNone(invoice.email_last_error)
        self.assertEqual(invoice.email_attempts, 1)
        self.assertEqual(len(mailer.sent), 1)

    def test_subject_body_and_attachment_contract(self):
        invoice = SnapshotInvoice()
        mailer = FakeMailer()

        with temp_invoice_dir() as tmpdir:
            write_pdf(tmpdir)
            send_invoice_email(invoice, mailer=mailer, invoice_folder=tmpdir)

        message = mailer.sent[0]
        self.assertEqual(message.subject, "Factura F2026000001 - MetalWolft")
        self.assertEqual(message.recipients, ("cliente@example.com",))
        self.assertIn("Hola Sergio Arias", message.body)
        self.assertIn("Factura F2026000001", message.subject)
        self.assertIn("Adjuntamos la factura F2026000001", message.body)
        self.assertIn("Referencia del pedido: AB1234", message.body)
        self.assertIn("MetalWolft", message.body)
        self.assertNotIn("stripe", message.body.lower())
        self.assertNotIn("provider_reference", message.body)
        self.assertNotIn("invoice_snapshot", message.body)
        self.assertEqual(len(message.attachments), 1)
        self.assertEqual(attachment_filename(attachment(message)), "invoice_F2026000001.pdf")
        self.assertEqual(attachment_content_type(attachment(message)), PDF_MIME_TYPE)

    def test_snapshot_absent_or_invoice_absent_is_blocked(self):
        with self.assertRaises(InvoiceEmailSnapshotMissing):
            send_invoice_email(None, mailer=FakeMailer())

        invoice = SnapshotInvoice(invoice_snapshot=None)
        invoice.invoice_snapshot = None
        with self.assertRaises(InvoiceEmailSnapshotMissing):
            send_invoice_email(invoice, mailer=FakeMailer(), invoice_folder=TEST_TMP_ROOT)

    def test_unsupported_schema_is_blocked(self):
        invalid_snapshot = snapshot({"schema_version": 99})
        invoice = SnapshotInvoice(
            invoice_snapshot=invalid_snapshot,
            stored_hash=calculate_invoice_snapshot_hash(invalid_snapshot),
        )

        with self.assertRaises(InvoiceEmailUnsupportedSchema):
            send_invoice_email(invoice, mailer=FakeMailer(), invoice_folder=TEST_TMP_ROOT)

    def test_hash_mismatch_is_blocked(self):
        invoice = SnapshotInvoice(stored_hash="bad-hash")

        with self.assertRaises(InvoiceEmailIntegrityError):
            send_invoice_email(invoice, mailer=FakeMailer(), invoice_folder=TEST_TMP_ROOT)

    def test_customer_without_email_is_blocked(self):
        invalid_snapshot = snapshot({
            "customer": {
                "legal_name": "Sergio Arias",
                "email": "",
            },
        })
        invoice = SnapshotInvoice(
            invoice_snapshot=invalid_snapshot,
            stored_hash=calculate_invoice_snapshot_hash(invalid_snapshot),
        )

        with self.assertRaises(InvoiceEmailRecipientMissing):
            send_invoice_email(invoice, mailer=FakeMailer(), invoice_folder=TEST_TMP_ROOT)

    def test_missing_pdf_is_blocked(self):
        invoice = SnapshotInvoice(pdf_path=None)

        with self.assertRaises(InvoiceEmailPdfMissing):
            send_invoice_email(invoice, mailer=FakeMailer(), invoice_folder=TEST_TMP_ROOT)

        invoice = SnapshotInvoice()
        with temp_invoice_dir() as tmpdir:
            with self.assertRaises(InvoiceEmailPdfMissing):
                send_invoice_email(invoice, mailer=FakeMailer(), invoice_folder=tmpdir)

    def test_path_traversal_and_wrong_filename_are_blocked(self):
        for unsafe_path in (
            "/api/download-invoice/../secret.pdf",
            "invoice_OTHER.pdf",
            "invoice_F2026000001.txt",
            "..\\invoice_F2026000001.pdf",
        ):
            invoice = SnapshotInvoice(pdf_path=unsafe_path)
            with self.assertRaises(InvoiceEmailPdfMissing):
                send_invoice_email(invoice, mailer=FakeMailer(), invoice_folder=TEST_TMP_ROOT)

    def test_does_not_query_live_relations_or_modify_fiscal_data(self):
        invoice = SnapshotInvoice()
        before = {
            "invoice_number": invoice.invoice_number,
            "snapshot": copy.deepcopy(invoice.invoice_snapshot),
            "hash": invoice.invoice_snapshot_hash,
            "issued_at": invoice.issued_at,
        }

        with temp_invoice_dir() as tmpdir:
            write_pdf(tmpdir)
            send_invoice_email(invoice, mailer=FakeMailer(), invoice_folder=tmpdir)

        self.assertEqual(invoice.invoice_number, before["invoice_number"])
        self.assertEqual(invoice.invoice_snapshot, before["snapshot"])
        self.assertEqual(invoice.invoice_snapshot_hash, before["hash"])
        self.assertEqual(invoice.issued_at, before["issued_at"])

    def test_failed_send_marks_failed_and_sanitizes_error(self):
        invoice = SnapshotInvoice()

        with temp_invoice_dir() as tmpdir:
            write_pdf(tmpdir)
            with self.assertRaises(InvoiceEmailSendError):
                send_invoice_email(invoice, mailer=FakeMailer(fail=True), invoice_folder=tmpdir)

        self.assertEqual(invoice.email_status, EMAIL_STATUS_FAILED)
        self.assertEqual(invoice.email_attempts, 1)
        self.assertEqual(invoice.email_last_error, "No se pudo enviar el email de factura.")
        self.assertNotIn("smtp secret failure", invoice.email_last_error)

    def test_second_call_does_not_resend_when_already_sent(self):
        invoice = SnapshotInvoice()
        invoice.email_status = EMAIL_STATUS_SENT
        invoice.email_sent_at = datetime(2026, 7, 16, 10, 0)
        invoice.email_attempts = 1
        mailer = FakeMailer()

        with temp_invoice_dir() as tmpdir:
            write_pdf(tmpdir)
            result = send_invoice_email(invoice, mailer=mailer, invoice_folder=tmpdir)

        self.assertTrue(result.already_sent)
        self.assertEqual(result.sent_at, invoice.email_sent_at)
        self.assertEqual(mailer.sent, [])
        self.assertEqual(invoice.email_attempts, 1)

    def test_service_does_not_commit_or_rollback(self):
        invoice = SnapshotInvoice()

        with temp_invoice_dir() as tmpdir:
            write_pdf(tmpdir)
            send_invoice_email(invoice, mailer=FakeMailer(), invoice_folder=tmpdir)

        self.assertFalse(invoice.commit_called)
        self.assertFalse(invoice.rollback_called)

    def test_uses_explicit_invoice_folder_when_environment_points_elsewhere(self):
        invoice = SnapshotInvoice()
        mailer = FakeMailer()
        original_env_value = os.environ.get("INVOICE_FOLDER")

        with temp_invoice_dir() as valid_dir, temp_invoice_dir() as wrong_dir:
            write_pdf(valid_dir)
            os.environ["INVOICE_FOLDER"] = str(wrong_dir)
            try:
                result = send_invoice_email(invoice, mailer=mailer, invoice_folder=valid_dir)
            finally:
                if original_env_value is None:
                    os.environ.pop("INVOICE_FOLDER", None)
                else:
                    os.environ["INVOICE_FOLDER"] = original_env_value

        self.assertEqual(result.attachment_filename, "invoice_F2026000001.pdf")
        self.assertEqual(len(mailer.sent), 1)

    def test_missing_invoice_folder_is_blocked(self):
        invoice = SnapshotInvoice()

        with self.assertRaises(InvoiceEmailPdfMissing):
            send_invoice_email(invoice, mailer=FakeMailer(), invoice_folder=None)


class InvoiceEmailModelAndMigrationTest(unittest.TestCase):
    def test_invoice_model_has_nullable_email_status_fields_and_attempt_default(self):
        source = (SRC_DIR / "api/models.py").read_text(encoding="utf-8")
        block = source[source.index("class Invoices(db.Model):"):source.index("class InvoiceFiscalSubmission(db.Model):")]

        self.assertIn("email_status = db.Column(db.String(20), nullable=True)", block)
        self.assertIn("email_sent_at = db.Column(db.DateTime, nullable=True)", block)
        self.assertIn("email_last_error = db.Column(db.Text, nullable=True)", block)
        self.assertIn('email_attempts = db.Column(db.Integer, nullable=False, default=0, server_default="0")', block)

    def test_migration_adds_and_removes_only_email_fields(self):
        source = MIGRATION_PATH.read_text(encoding="utf-8")

        self.assertIn("revision = 'a2b3c4d5e6f7'", source)
        self.assertIn("down_revision = 'f1a2b3c4d5e6'", source)
        for expected in (
            "op.add_column('invoices', sa.Column('email_status'",
            "op.add_column('invoices', sa.Column('email_sent_at'",
            "op.add_column('invoices', sa.Column('email_last_error'",
            "op.add_column(",
            "sa.Column('email_attempts', sa.Integer(), server_default='0', nullable=False)",
            "op.drop_column('invoices', 'email_attempts')",
            "op.drop_column('invoices', 'email_last_error')",
            "op.drop_column('invoices', 'email_sent_at')",
            "op.drop_column('invoices', 'email_status')",
        ):
            self.assertIn(expected, source)

        self.assertNotIn("op.create_table", source)
        self.assertNotIn("op.execute", source)
        self.assertNotIn("bulk_insert", source)
        self.assertNotIn("invoice_snapshot", source)
        self.assertNotIn("invoice_number", source)

    def test_historical_invoices_can_keep_nullable_status(self):
        invoice = SnapshotInvoice()

        self.assertIsNone(invoice.email_status)
        self.assertIsNone(invoice.email_sent_at)
        self.assertIsNone(invoice.email_last_error)


class InvoiceEmailServiceSourceTest(unittest.TestCase):
    def test_source_uses_only_invoice_snapshot_pdf_and_email_fields(self):
        source = (SRC_DIR / "api/invoice_email_service.py").read_text(encoding="utf-8")

        for expected in (
            'getattr(invoice, "invoice_number"',
            'getattr(invoice, "issued_at"',
            'getattr(invoice, "invoice_snapshot"',
            'getattr(invoice, "invoice_snapshot_hash"',
            "resolve_invoice_pdf_download",
            "invoice.email_status",
            "invoice.email_sent_at",
            "invoice.email_last_error",
            "invoice.email_attempts",
        ):
            self.assertIn(expected, source)

        for forbidden in (
            "Orders",
            "OrderDetails",
            "Users",
            "CheckoutSessions",
            "InvoiceFiscalSubmission",
            "AccountingEntry",
            "export_sales_accounting_entries",
            "create_pending_submission",
            ".commit(",
            ".rollback(",
            "invoice.invoice_number =",
            "invoice.invoice_snapshot =",
            "invoice.invoice_snapshot_hash =",
            "invoice.issued_at =",
        ):
            self.assertNotIn(forbidden, source)

    def test_source_does_not_expose_smtp_details_or_payment_references(self):
        source = (SRC_DIR / "api/invoice_email_service.py").read_text(encoding="utf-8")

        self.assertNotIn("from flask", source)
        self.assertNotIn("flask_mail", source)
        self.assertNotIn("from flask_mail import Message", source)
        self.assertNotIn("flask_mail.Message", source)
        self.assertNotIn("os.getenv", source)
        self.assertIn("invoice_folder", source)
        self.assertIn("class InvoiceEmailMessage", source)
        self.assertNotIn("provider_reference", source)
        self.assertNotIn("stripe", source.lower())
        self.assertNotIn("paypal", source.lower())
        self.assertNotIn("error = str(", source)
        self.assertNotIn("email_last_error = str(", source)


if __name__ == "__main__":
    unittest.main()

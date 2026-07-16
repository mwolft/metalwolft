import copy
import importlib.util
import re
import sys
import unittest
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/e6f7a8b9c0d1_add_invoice_fiscal_submissions_table.py"
)


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
    from flask import Flask  # noqa: E402

    from api.invoice_fiscal_submission_service import (  # noqa: E402
        PROVIDER_VERIFACTU,
        STATUS_ACCEPTED,
        STATUS_FAILED,
        STATUS_PENDING,
        STATUS_REJECTED,
        STATUS_SENT,
        create_pending_submission,
        mark_accepted,
        mark_failed,
        mark_rejected,
        mark_sent,
    )
    from api.models import InvoiceFiscalSubmission, Invoices, db  # noqa: E402


def model_source():
    return (ROOT_DIR / "src/api/models.py").read_text(encoding="utf-8")


def service_source():
    return (ROOT_DIR / "src/api/invoice_fiscal_submission_service.py").read_text(encoding="utf-8")


def migration_source():
    return MIGRATION_PATH.read_text(encoding="utf-8")


def submission_model_block():
    source = model_source()
    return source[
        source.index("class InvoiceFiscalSubmission(db.Model):"):source.index("class InvoiceSequence(db.Model):")
    ]


class InvoiceFiscalSubmissionModelSourceTest(unittest.TestCase):
    def test_model_declares_expected_table_columns_and_statuses(self):
        source = submission_model_block()

        self.assertIn('__tablename__ = "invoice_fiscal_submissions"', source)
        self.assertIn("db.UniqueConstraint(", source)
        self.assertIn('"invoice_id"', source)
        self.assertIn('"provider"', source)
        self.assertIn('"attempt_number"', source)
        self.assertIn('name="uq_invoice_fiscal_submissions_invoice_provider_attempt"', source)
        self.assertIn('PROVIDER_VERIFACTU = "verifactu"', source)
        for status in ("PENDING", "SENT", "ACCEPTED", "REJECTED", "FAILED"):
            self.assertIn(f'STATUS_{status} = "{status}"', source)

        for column in (
            "id = db.Column(db.Integer, primary_key=True)",
            "invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)",
            "provider = db.Column(db.String(30), nullable=False, default=PROVIDER_VERIFACTU)",
            "status = db.Column(db.String(30), nullable=False, default=STATUS_PENDING)",
            "attempt_number = db.Column(db.Integer, nullable=False)",
            "submitted_at = db.Column(db.DateTime, nullable=True)",
            "response_at = db.Column(db.DateTime, nullable=True)",
            "request_payload = db.Column(db.JSON, nullable=True)",
            "response_payload = db.Column(db.JSON, nullable=True)",
            "response_code = db.Column(db.String(100), nullable=True)",
            "response_message = db.Column(db.Text, nullable=True)",
            "verification_csv = db.Column(db.String(255), nullable=True)",
            "verification_url = db.Column(db.String(500), nullable=True)",
            "external_reference = db.Column(db.String(255), nullable=True)",
            "error_type = db.Column(db.String(100), nullable=True)",
            "error_detail = db.Column(db.Text, nullable=True)",
        ):
            self.assertIn(column, source)

    def test_model_relates_many_submissions_to_one_invoice(self):
        source = submission_model_block()

        self.assertIn("invoice = db.relationship(", source)
        self.assertIn("'Invoices'", source)
        self.assertIn("backref=db.backref('fiscal_submissions', lazy=True)", source)

    def test_model_declares_invoice_id_index_matching_existing_migration(self):
        source = submission_model_block()

        self.assertIn("db.Index(", source)
        self.assertIn('"ix_invoice_fiscal_submissions_invoice_id"', source)
        self.assertIn('"invoice_id"', source)
        self.assertIn("unique=False", source)

    def test_model_index_matches_migration_name_without_new_migration(self):
        source = migration_source()

        self.assertIn("'ix_invoice_fiscal_submissions_invoice_id'", source)
        migration_files = [
            path.name
            for path in (ROOT_DIR / "src/migrations/versions").glob("*.py")
            if "invoice_fiscal_submissions_invoice_id" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            migration_files,
            ["e6f7a8b9c0d1_add_invoice_fiscal_submissions_table.py"],
        )


class InvoiceFiscalSubmissionMigrationTest(unittest.TestCase):
    def test_migration_creates_only_fiscal_submissions_table(self):
        source = migration_source()

        self.assertIn("revision = 'e6f7a8b9c0d1'", source)
        self.assertIn("down_revision = 'd9e0f1a2b3c4'", source)
        self.assertIn("op.create_table(", source)
        self.assertIn("'invoice_fiscal_submissions'", source)
        self.assertIn("sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'])", source)
        self.assertIn("sa.UniqueConstraint(", source)
        self.assertIn("name='uq_invoice_fiscal_submissions_invoice_provider_attempt'", source)
        self.assertNotIn("op.add_column('invoices'", source)
        self.assertNotIn("op.alter_column('invoices'", source)
        self.assertNotIn("op.create_table('invoices'", source)

    def test_migration_columns_index_and_downgrade(self):
        source = migration_source()

        for expected in (
            "sa.Column('provider', sa.String(length=30), nullable=False)",
            "sa.Column('status', sa.String(length=30), nullable=False)",
            "sa.Column('attempt_number', sa.Integer(), nullable=False)",
            "sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)",
            "sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)",
            "sa.Column('request_payload', sa.JSON(), nullable=True)",
            "sa.Column('response_payload', sa.JSON(), nullable=True)",
            "sa.Column('error_detail', sa.Text(), nullable=True)",
            "'ix_invoice_fiscal_submissions_invoice_id'",
            "op.drop_table('invoice_fiscal_submissions')",
        ):
            self.assertIn(expected, source)

    def test_migration_has_no_backfill_or_existing_table_updates(self):
        source = migration_source()

        self.assertNotRegex(source, re.compile(r"\b(insert|update|execute|bulk_insert)\b"))


class InvoiceFiscalSubmissionServiceSourceTest(unittest.TestCase):
    def test_service_has_no_http_signing_cron_or_external_side_effects(self):
        source = service_source()

        for forbidden in (
            "requests",
            "http",
            "certificate",
            "certificado",
            "xml",
            "cron",
            "queue",
            ".commit(",
            ".rollback(",
            "invoice.invoice_number =",
            "invoice.invoice_snapshot =",
            "invoice.invoice_snapshot_hash =",
            "invoice.issued_at =",
        ):
            self.assertNotIn(forbidden, source.lower())


@unittest.skipUnless(HAS_DB_TEST_DEPENDENCIES, "Flask/SQLAlchemy test dependencies are not installed.")
class InvoiceFiscalSubmissionServiceSQLiteTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def make_invoice(self):
        invoice = Invoices(
            invoice_number="F2026000001",
            invoice_type="ordinary",
            amount=121.00,
            client_name="Cliente Test",
            client_address="Calle Test 1",
            client_cif="00000000T",
            client_phone="600000000",
            order_details=[],
            invoice_snapshot={"schema_version": 1, "totals": {"total_amount": "121.00"}},
            invoice_snapshot_schema_version=1,
            invoice_snapshot_hash="a" * 64,
            issued_at=datetime(2026, 7, 15, 12, 0, 0),
        )
        db.session.add(invoice)
        db.session.commit()
        return invoice

    def fiscal_state(self, invoice):
        return {
            "invoice_number": invoice.invoice_number,
            "invoice_snapshot": copy.deepcopy(invoice.invoice_snapshot),
            "invoice_snapshot_hash": invoice.invoice_snapshot_hash,
            "issued_at": invoice.issued_at,
        }

    def assert_invoice_fiscal_state_unchanged(self, invoice, before):
        self.assertEqual(invoice.invoice_number, before["invoice_number"])
        self.assertEqual(invoice.invoice_snapshot, before["invoice_snapshot"])
        self.assertEqual(invoice.invoice_snapshot_hash, before["invoice_snapshot_hash"])
        self.assertEqual(invoice.issued_at, before["issued_at"])

    def test_create_pending_submission(self):
        invoice = self.make_invoice()
        before = self.fiscal_state(invoice)

        submission = create_pending_submission(
            invoice,
            db_session=db.session,
            request_payload={"dry_run": True},
        )
        db.session.commit()

        self.assertEqual(submission.invoice_id, invoice.id)
        self.assertEqual(submission.provider, PROVIDER_VERIFACTU)
        self.assertEqual(submission.status, STATUS_PENDING)
        self.assertEqual(submission.attempt_number, 1)
        self.assertEqual(submission.request_payload, {"dry_run": True})
        self.assert_invoice_fiscal_state_unchanged(invoice, before)

    def test_mark_sent(self):
        invoice = self.make_invoice()
        submission = create_pending_submission(invoice, db_session=db.session)

        mark_sent(
            submission,
            request_payload={"xml": "placeholder"},
            external_reference="vf-out-1",
        )
        db.session.commit()

        self.assertEqual(submission.status, STATUS_SENT)
        self.assertIsNotNone(submission.submitted_at)
        self.assertEqual(submission.request_payload, {"xml": "placeholder"})
        self.assertEqual(submission.external_reference, "vf-out-1")

    def test_mark_accepted(self):
        invoice = self.make_invoice()
        before = self.fiscal_state(invoice)
        submission = create_pending_submission(invoice, db_session=db.session)

        mark_accepted(
            submission,
            response_payload={"accepted": True},
            response_code="0",
            response_message="Aceptada",
            verification_csv="CSV123",
            verification_url="https://example.test/csv/CSV123",
            external_reference="vf-in-1",
        )
        db.session.commit()

        self.assertEqual(submission.status, STATUS_ACCEPTED)
        self.assertIsNotNone(submission.response_at)
        self.assertEqual(submission.response_payload, {"accepted": True})
        self.assertEqual(submission.response_code, "0")
        self.assertEqual(submission.response_message, "Aceptada")
        self.assertEqual(submission.verification_csv, "CSV123")
        self.assertEqual(submission.verification_url, "https://example.test/csv/CSV123")
        self.assertEqual(submission.external_reference, "vf-in-1")
        self.assertIsNone(submission.error_type)
        self.assertIsNone(submission.error_detail)
        self.assert_invoice_fiscal_state_unchanged(invoice, before)

    def test_mark_rejected(self):
        invoice = self.make_invoice()
        submission = create_pending_submission(invoice, db_session=db.session)

        mark_rejected(
            submission,
            response_payload={"accepted": False},
            response_code="VF001",
            response_message="Factura rechazada",
            error_type="validation",
            error_detail="NIF invalido",
        )
        db.session.commit()

        self.assertEqual(submission.status, STATUS_REJECTED)
        self.assertIsNotNone(submission.response_at)
        self.assertEqual(submission.response_code, "VF001")
        self.assertEqual(submission.response_message, "Factura rechazada")
        self.assertEqual(submission.error_type, "validation")
        self.assertEqual(submission.error_detail, "NIF invalido")

    def test_mark_failed(self):
        invoice = self.make_invoice()
        submission = create_pending_submission(invoice, db_session=db.session)

        mark_failed(
            submission,
            error_type="transport",
            error_detail="Timeout",
            response_code="TIMEOUT",
        )
        db.session.commit()

        self.assertEqual(submission.status, STATUS_FAILED)
        self.assertIsNotNone(submission.response_at)
        self.assertEqual(submission.error_type, "transport")
        self.assertEqual(submission.error_detail, "Timeout")
        self.assertEqual(submission.response_code, "TIMEOUT")

    def test_multiple_attempts_are_preserved_and_incremented(self):
        invoice = self.make_invoice()

        first = create_pending_submission(invoice, db_session=db.session)
        db.session.commit()
        second = create_pending_submission(invoice, db_session=db.session)
        db.session.commit()

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.attempt_number, 1)
        self.assertEqual(second.attempt_number, 2)
        self.assertEqual(
            db.session.query(InvoiceFiscalSubmission).filter_by(invoice_id=invoice.id).count(),
            2,
        )

    def test_invoice_relationship_exposes_all_attempts(self):
        invoice = self.make_invoice()
        create_pending_submission(invoice, db_session=db.session)
        create_pending_submission(invoice, db_session=db.session)
        db.session.commit()

        self.assertEqual(len(invoice.fiscal_submissions), 2)
        self.assertEqual(
            [submission.attempt_number for submission in invoice.fiscal_submissions],
            [1, 2],
        )

    def test_metadata_contains_non_unique_invoice_id_index_for_create_all(self):
        indexes = {
            index.name: index
            for index in InvoiceFiscalSubmission.__table__.indexes
        }
        index = indexes["ix_invoice_fiscal_submissions_invoice_id"]

        self.assertFalse(index.unique)
        self.assertEqual([column.name for column in index.columns], ["invoice_id"])


if __name__ == "__main__":
    unittest.main()

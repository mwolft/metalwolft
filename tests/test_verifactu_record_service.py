import copy
import importlib.util
import re
import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/b3c4d5e6f7a8_add_verifactu_records_table.py"
)
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))



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
    from sqlalchemy.exc import IntegrityError  # noqa: E402

    from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash  # noqa: E402
    from api.models import Invoices, VeriFactuRecord, db  # noqa: E402
    from api.verifactu_record_service import (  # noqa: E402
        FINGERPRINT_STATUS_NOT_CALCULATED,
        MODE_VERIFACTU,
        RECORD_TYPE_ALTA,
        STATUS_BUILT,
        VeriFactuRecordIntegrityError,
        VeriFactuRecordUnsupportedSchema,
        VeriFactuRecordValidationError,
        build_verifactu_registration_payload,
        calculate_verifactu_record_payload_hash,
        create_verifactu_registration_record,
    )


def model_source():
    return (ROOT_DIR / "src/api/models.py").read_text(encoding="utf-8")


def service_source():
    return (ROOT_DIR / "src/api/verifactu_record_service.py").read_text(encoding="utf-8")


def migration_source():
    return MIGRATION_PATH.read_text(encoding="utf-8")


def verifactu_model_block():
    source = model_source()
    return source[
        source.index("class VeriFactuRecord(db.Model):"):source.index("class AccountingEntry(db.Model):")
    ]


def snapshot(*, schema_version=1, customer_tax_id="00000000T", operation=None, lines=None):
    operation_data = {
        "invoice_type": "ordinary",
        "issue_date": "2026-07-19",
        "operation_date": "2026-07-18",
        "currency": "EUR",
        "order_id": 42,
        "order_locator": "MW-42",
    }
    if operation:
        operation_data.update(operation)

    return {
        "schema_version": schema_version,
        "metadata": {"generator": "invoice_snapshot_builder_v1"},
        "issuer": {
            "legal_name": "MetalWolft S.L.",
            "tax_id": "B00000000",
            "country_code": "ES",
        },
        "customer": {
            "legal_name": "Cliente VeriFactu",
            "tax_id": customer_tax_id,
            "country_code": "ES",
        },
        "operation": operation_data,
        "lines": lines if lines is not None else [
            {
                "line_number": 1,
                "description": "Reja a medida",
                "tax_rate": "21.00",
                "tax_base": "100.00",
                "tax_amount": "21.00",
                "line_total": "121.00",
            }
        ],
        "totals": {
            "tax_base": "100.00",
            "tax_amount": "21.00",
            "total_amount": "121.00",
        },
        "payment": {"provider": "stripe", "status": "paid"},
        "references": {"order_id": 42},
    }


class VeriFactuRecordModelAndMigrationTest(unittest.TestCase):
    def test_model_declares_expected_table_columns_constraints_and_indexes(self):
        source = verifactu_model_block()

        self.assertIn('__tablename__ = "verifactu_records"', source)
        self.assertIn('name="uq_verifactu_records_invoice_record_type"', source)
        self.assertIn('"ix_verifactu_records_invoice_id"', source)
        self.assertIn("unique=False", source)
        for expected in (
            "invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)",
            "record_type = db.Column(db.String(30), nullable=False)",
            "record_payload = db.Column(db.JSON, nullable=False)",
            "record_payload_hash = db.Column(db.String(64), nullable=False)",
            "fingerprint = db.Column(db.String(128), nullable=True)",
            "fingerprint_algorithm = db.Column(db.String(100), nullable=True)",
            "fingerprint_status = db.Column(db.String(30), nullable=False, default=\"NOT_CALCULATED\")",
            "system_id = db.Column(db.String(100), nullable=False)",
            "software_name = db.Column(db.String(120), nullable=False)",
            "software_version = db.Column(db.String(50), nullable=False)",
            "total_amount = db.Column(db.Numeric(12, 2), nullable=False)",
            "currency = db.Column(db.String(3), nullable=False)",
        ):
            self.assertIn(expected, source)

    def test_model_relates_many_records_to_one_invoice(self):
        source = verifactu_model_block()

        self.assertIn("invoice = db.relationship(", source)
        self.assertIn("'Invoices'", source)
        self.assertIn("backref=db.backref('verifactu_records', lazy=True)", source)

    def test_migration_creates_only_verifactu_records_table(self):
        source = migration_source()

        self.assertIn("revision = 'b3c4d5e6f7a8'", source)
        self.assertIn("down_revision = 'a2b3c4d5e6f7'", source)
        self.assertIn("op.create_table(", source)
        self.assertIn("'verifactu_records'", source)
        self.assertIn("sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'])", source)
        self.assertIn("sa.UniqueConstraint(", source)
        self.assertIn("name='uq_verifactu_records_invoice_record_type'", source)
        self.assertIn("'ix_verifactu_records_invoice_id'", source)
        self.assertIn("op.drop_table('verifactu_records')", source)
        self.assertNotIn("op.add_column('invoices'", source)
        self.assertNotIn("op.alter_column('invoices'", source)
        self.assertNotIn("op.create_table('invoices'", source)

    def test_migration_has_no_backfill_or_existing_table_updates(self):
        self.assertNotRegex(migration_source(), re.compile(r"\b(insert|update|execute|bulk_insert)\b"))


class VeriFactuRecordServiceSourceTest(unittest.TestCase):
    def test_service_has_no_transmission_signing_qr_or_official_fingerprint_claim(self):
        source = service_source().lower()

        for forbidden in (
            "requests",
            "http",
            "certificate",
            "certificado",
            "xml",
            "qr",
            "aeat",
            ".commit(",
            ".rollback(",
            "invoice.invoice_number =",
            "invoice.invoice_snapshot =",
            "invoice.invoice_snapshot_hash =",
            "invoice.issued_at =",
        ):
            self.assertNotIn(forbidden, source)

        self.assertIn("fingerprint=None", service_source())
        self.assertIn("fingerprint_algorithm=None", service_source())
        self.assertIn("FINGERPRINT_STATUS_NOT_CALCULATED", service_source())


@unittest.skipUnless(HAS_DB_TEST_DEPENDENCIES, "Flask/SQLAlchemy test dependencies are not installed.")
class VeriFactuRecordServiceSQLiteTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self._invoice_number_sequence = 1

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def make_invoice(self, *, invoice_snapshot=None, stored_hash=None):
        fiscal_snapshot = invoice_snapshot if invoice_snapshot is not None else snapshot()
        invoice_number = f"F2026{self._invoice_number_sequence:06d}"
        self._invoice_number_sequence += 1
        invoice = Invoices(
            invoice_number=invoice_number,
            invoice_type="ordinary",
            amount=121.00,
            client_name="Cliente VeriFactu",
            client_address="Calle Fiscal 1",
            client_cif="00000000T",
            client_phone="600000000",
            order_details=[],
            invoice_snapshot=fiscal_snapshot,
            invoice_snapshot_schema_version=fiscal_snapshot.get("schema_version") if isinstance(fiscal_snapshot, dict) else None,
            invoice_snapshot_hash=stored_hash or calculate_invoice_snapshot_hash(fiscal_snapshot),
            issued_at=datetime(2026, 7, 19, 10, 30, tzinfo=timezone.utc),
        )
        db.session.add(invoice)
        db.session.commit()
        return invoice

    def create_record(self, invoice):
        return create_verifactu_registration_record(
            invoice,
            db_session=db.session,
            system_id="metalwolft-dev-01",
            software_name="MetalWolft",
            software_version="2026.7",
        )

    def fiscal_state(self, invoice):
        return {
            "invoice_number": invoice.invoice_number,
            "invoice_snapshot": copy.deepcopy(invoice.invoice_snapshot),
            "invoice_snapshot_hash": invoice.invoice_snapshot_hash,
            "issued_at": invoice.issued_at,
            "amount": invoice.amount,
        }

    def assert_invoice_unchanged(self, invoice, before):
        self.assertEqual(invoice.invoice_number, before["invoice_number"])
        self.assertEqual(invoice.invoice_snapshot, before["invoice_snapshot"])
        self.assertEqual(invoice.invoice_snapshot_hash, before["invoice_snapshot_hash"])
        self.assertEqual(invoice.issued_at, before["issued_at"])
        self.assertEqual(invoice.amount, before["amount"])

    def test_create_verifactu_registration_record(self):
        invoice = self.make_invoice()
        before = self.fiscal_state(invoice)

        result = self.create_record(invoice)
        db.session.commit()
        record = result.record

        self.assertTrue(result.created)
        self.assertEqual(record.invoice_id, invoice.id)
        self.assertEqual(record.provider, "verifactu")
        self.assertEqual(record.mode, MODE_VERIFACTU)
        self.assertEqual(record.record_type, RECORD_TYPE_ALTA)
        self.assertEqual(record.status, STATUS_BUILT)
        self.assertEqual(record.schema_version, 1)
        self.assertEqual(record.invoice_number, "F2026000001")
        self.assertEqual(record.invoice_snapshot_hash, invoice.invoice_snapshot_hash)
        self.assertEqual(record.system_id, "metalwolft-dev-01")
        self.assertEqual(record.software_name, "MetalWolft")
        self.assertEqual(record.software_version, "2026.7")
        self.assertEqual(record.issuer_tax_id, "B00000000")
        self.assertEqual(record.recipient_tax_id, "00000000T")
        self.assertEqual(record.total_amount, Decimal("121.00"))
        self.assertEqual(record.currency, "EUR")
        self.assertIsNone(record.fingerprint)
        self.assertIsNone(record.fingerprint_algorithm)
        self.assertEqual(record.fingerprint_status, FINGERPRINT_STATUS_NOT_CALCULATED)
        self.assertEqual(record.record_payload["record_type"], "alta")
        self.assertEqual(record.record_payload["mode"], "VERI*FACTU")
        self.assertEqual(record.record_payload["invoice"]["invoice_number"], "F2026000001")
        self.assertEqual(record.record_payload["system"]["software_name"], "MetalWolft")
        self.assertEqual(
            record.record_payload_hash,
            calculate_verifactu_record_payload_hash(record.record_payload),
        )
        self.assert_invoice_unchanged(invoice, before)

    def test_idempotency_returns_existing_record_without_rebuilding(self):
        invoice = self.make_invoice()
        first = self.create_record(invoice)
        db.session.commit()
        payload = dict(first.record.record_payload)
        payload["manual_marker"] = "kept"
        first.record.record_payload = payload
        db.session.commit()

        second = self.create_record(invoice)

        self.assertFalse(second.created)
        self.assertEqual(first.record.id, second.record.id)
        self.assertEqual(second.record.record_payload["manual_marker"], "kept")
        self.assertEqual(db.session.query(VeriFactuRecord).count(), 1)

    def test_unique_invoice_record_type_is_enforced(self):
        invoice = self.make_invoice()
        self.create_record(invoice)
        db.session.commit()

        db.session.add(VeriFactuRecord(
            invoice_id=invoice.id,
            provider="verifactu",
            mode="VERI*FACTU",
            record_type="alta",
            status="BUILT",
            schema_version=1,
            invoice_number="F2026000001",
            invoice_issued_at=invoice.issued_at,
            invoice_snapshot_hash=invoice.invoice_snapshot_hash,
            record_payload={"duplicate": True},
            record_payload_hash="b" * 64,
            fingerprint_status=FINGERPRINT_STATUS_NOT_CALCULATED,
            system_id="other",
            software_name="MetalWolft",
            software_version="2026.7",
            issuer_tax_id="B00000000",
            recipient_tax_id="00000000T",
            total_amount=Decimal("121.00"),
            currency="EUR",
        ))
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_payload_builder_is_deterministic(self):
        invoice = self.make_invoice()
        system = {
            "system_id": "metalwolft-dev-01",
            "software_name": "MetalWolft",
            "software_version": "2026.7",
        }

        first = build_verifactu_registration_payload(invoice, snapshot=invoice.invoice_snapshot, system=system)
        second = build_verifactu_registration_payload(invoice, snapshot=invoice.invoice_snapshot, system=system)

        self.assertEqual(first, second)
        self.assertEqual(
            calculate_verifactu_record_payload_hash(first),
            calculate_verifactu_record_payload_hash(second),
        )

    def test_snapshot_absent_hash_mismatch_and_unsupported_schema_are_rejected(self):
        invoice = self.make_invoice()
        invoice.invoice_snapshot = None
        with self.assertRaises(VeriFactuRecordValidationError):
            self.create_record(invoice)

        db.session.rollback()
        bad_hash_invoice = self.make_invoice(stored_hash="bad-hash")
        with self.assertRaises(VeriFactuRecordIntegrityError):
            self.create_record(bad_hash_invoice)

        db.session.rollback()
        unsupported = snapshot(schema_version=99)
        unsupported_invoice = self.make_invoice(
            invoice_snapshot=unsupported,
            stored_hash=calculate_invoice_snapshot_hash(unsupported),
        )
        with self.assertRaises(VeriFactuRecordUnsupportedSchema):
            self.create_record(unsupported_invoice)

    def test_missing_system_identity_and_fiscal_fields_are_rejected(self):
        invoice = self.make_invoice()

        with self.assertRaises(VeriFactuRecordValidationError):
            create_verifactu_registration_record(
                invoice,
                db_session=db.session,
                system_id="",
                software_name="MetalWolft",
                software_version="2026.7",
            )

        db.session.rollback()
        missing_tax_id_snapshot = snapshot(customer_tax_id=None)
        missing_tax_id_invoice = self.make_invoice(
            invoice_snapshot=missing_tax_id_snapshot,
            stored_hash=calculate_invoice_snapshot_hash(missing_tax_id_snapshot),
        )
        with self.assertRaises(VeriFactuRecordValidationError):
            self.create_record(missing_tax_id_invoice)

    def test_currency_and_corrective_invoice_are_rejected(self):
        usd = snapshot(operation={"currency": "USD"})
        usd_invoice = self.make_invoice(invoice_snapshot=usd, stored_hash=calculate_invoice_snapshot_hash(usd))
        with self.assertRaises(VeriFactuRecordValidationError):
            self.create_record(usd_invoice)

        db.session.rollback()
        corrective = snapshot(operation={"invoice_type": "corrective"})
        corrective_invoice = self.make_invoice(
            invoice_snapshot=corrective,
            stored_hash=calculate_invoice_snapshot_hash(corrective),
        )
        with self.assertRaises(VeriFactuRecordValidationError):
            self.create_record(corrective_invoice)


if __name__ == "__main__":
    unittest.main()

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
READY_MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/c5d6e7f8a9b0_add_verifactu_ready_fields.py"
)
CHAIN_MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/d6e7f8a9b0c1_add_verifactu_chain_state.py"
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
    from api.models import Invoices, VeriFactuChainState, VeriFactuRecord, db  # noqa: E402
    from api.verifactu_record_service import (  # noqa: E402
        FINGERPRINT_STATUS_NOT_CALCULATED,
        MODE_VERIFACTU,
        RECORD_TYPE_ALTA,
        STATUS_BUILT,
        STATUS_READY,
        VeriFactuRecordConcurrencyError,
        VeriFactuRecordIntegrityError,
        VeriFactuRecordUnsupportedSchema,
        VeriFactuRecordValidationError,
        build_verifactu_chain_key,
        build_verifactu_registration_payload,
        calculate_verifactu_record_payload_hash,
        create_verifactu_registration_record,
        prepare_verifactu_record_for_submission,
        verifactu_system_identity_from_config,
    )


def model_source():
    return (ROOT_DIR / "src/api/models.py").read_text(encoding="utf-8")


def service_source():
    return (ROOT_DIR / "src/api/verifactu_record_service.py").read_text(encoding="utf-8")


def migration_source():
    return MIGRATION_PATH.read_text(encoding="utf-8")


def ready_migration_source():
    return READY_MIGRATION_PATH.read_text(encoding="utf-8")


def chain_migration_source():
    return CHAIN_MIGRATION_PATH.read_text(encoding="utf-8")


def verifactu_model_block():
    source = model_source()
    return source[
        source.index("class VeriFactuRecord(db.Model):"):source.index("class AccountingEntry(db.Model):")
    ]


def verifactu_chain_state_model_block():
    source = model_source()
    return source[
        source.index("class VeriFactuChainState(db.Model):"):source.index("class AccountingEntry(db.Model):")
    ]


def snapshot(*, schema_version=1, issuer_tax_id="B00000000", customer_tax_id="00000000T", operation=None, lines=None):
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
            "tax_id": issuer_tax_id,
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
        self.assertIn('name="uq_verifactu_records_fingerprint"', source)
        self.assertIn('name="uq_verifactu_records_chain_sequence"', source)
        self.assertIn('"ix_verifactu_records_invoice_id"', source)
        self.assertIn('"ix_verifactu_records_previous_record_id"', source)
        self.assertIn('"ix_verifactu_records_chain_key_sequence"', source)
        self.assertIn("unique=False", source)
        self.assertIn("unique=True", source)
        self.assertIn("ck_verifactu_records_previous_not_self", source)
        self.assertIn("ck_verifactu_records_chain_sequence_positive", source)
        self.assertIn("ck_verifactu_records_ready_chain_complete", source)
        self.assertIn("ck_verifactu_records_first_previous_coherent", source)
        for expected in (
            "invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)",
            "record_type = db.Column(db.String(30), nullable=False)",
            "record_payload = db.Column(db.JSON, nullable=False)",
            "record_payload_hash = db.Column(db.String(64), nullable=False)",
            "official_payload = db.Column(db.JSON, nullable=True)",
            "official_payload_schema_version = db.Column(db.Integer, nullable=True)",
            "chain_key = db.Column(db.String(300), nullable=True)",
            "chain_sequence = db.Column(db.Integer, nullable=True)",
            "fingerprint = db.Column(db.String(128), nullable=True)",
            "fingerprint_algorithm = db.Column(db.String(100), nullable=True)",
            "fingerprint_status = db.Column(db.String(30), nullable=False, default=\"NOT_CALCULATED\")",
            "fingerprint_input = db.Column(db.Text, nullable=True)",
            "fingerprint_calculated_at = db.Column(db.DateTime, nullable=True)",
            "previous_record_id = db.Column(db.Integer, db.ForeignKey('verifactu_records.id'), nullable=True)",
            "previous_fingerprint = db.Column(db.String(128), nullable=True)",
            "is_first_record = db.Column(db.Boolean, nullable=True)",
            "system_id = db.Column(db.String(100), nullable=False)",
            "software_name = db.Column(db.String(120), nullable=False)",
            "software_version = db.Column(db.String(50), nullable=False)",
            "installation_id = db.Column(db.String(100), nullable=True)",
            "producer_name = db.Column(db.String(120), nullable=True)",
            "producer_tax_id = db.Column(db.String(50), nullable=True)",
            "generation_timestamp = db.Column(db.DateTime, nullable=True)",
            "generation_timezone = db.Column(db.String(50), nullable=True)",
            "ready_at = db.Column(db.DateTime, nullable=True)",
            "total_amount = db.Column(db.Numeric(12, 2), nullable=False)",
            "currency = db.Column(db.String(3), nullable=False)",
        ):
            self.assertIn(expected, source)

    def test_model_relates_many_records_to_one_invoice(self):
        source = verifactu_model_block()

        self.assertIn("invoice = db.relationship(", source)
        self.assertIn("'Invoices'", source)
        self.assertIn("backref=db.backref('verifactu_records', lazy=True)", source)
        self.assertIn("previous_record = db.relationship(", source)
        self.assertIn("remote_side=[id]", source)

    def test_chain_state_model_declares_persisted_head_and_indexes(self):
        source = verifactu_chain_state_model_block()

        self.assertIn('__tablename__ = "verifactu_chain_states"', source)
        self.assertIn('name="uq_verifactu_chain_states_chain_key"', source)
        self.assertIn('"ix_verifactu_chain_states_chain_key"', source)
        for expected in (
            "chain_key = db.Column(db.String(300), nullable=False)",
            "issuer_tax_id = db.Column(db.String(50), nullable=False)",
            "mode = db.Column(db.String(30), nullable=False, default=VeriFactuRecord.MODE_VERIFACTU)",
            "system_id = db.Column(db.String(100), nullable=False)",
            "installation_id = db.Column(db.String(100), nullable=False)",
            "producer_tax_id = db.Column(db.String(50), nullable=False)",
            "last_record_id = db.Column(db.Integer, db.ForeignKey('verifactu_records.id'), nullable=True)",
            "last_fingerprint = db.Column(db.String(128), nullable=True)",
            "next_sequence = db.Column(db.Integer, nullable=False, default=1, server_default=\"1\")",
        ):
            self.assertIn(expected, source)

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

    def test_ready_migration_adds_only_verifactu_ready_fields(self):
        source = ready_migration_source()

        self.assertIn("revision = 'c5d6e7f8a9b0'", source)
        self.assertIn("down_revision = 'b3c4d5e6f7a8'", source)
        self.assertIn("op.add_column('verifactu_records'", source)
        self.assertIn("official_payload", source)
        self.assertIn("fingerprint_input", source)
        self.assertIn("previous_record_id", source)
        self.assertIn("ready_at", source)
        self.assertIn("uq_verifactu_records_fingerprint", source)
        self.assertIn("fk_verifactu_records_previous_record_id", source)
        self.assertIn("ck_verifactu_records_previous_not_self", source)
        self.assertIn("ix_verifactu_records_previous_record_id", source)
        self.assertNotIn("op.add_column('invoices'", source)
        self.assertNotIn("op.create_table(", source)
        self.assertNotRegex(source, re.compile(r"\b(insert|update|execute|bulk_insert)\b"))

    def test_ready_migration_downgrade_removes_only_added_fields(self):
        source = ready_migration_source()

        self.assertIn("op.drop_index('ix_verifactu_records_previous_record_id'", source)
        self.assertIn("op.drop_constraint('ck_verifactu_records_previous_not_self'", source)
        self.assertIn("op.drop_constraint('fk_verifactu_records_previous_record_id'", source)
        self.assertIn("op.drop_constraint('uq_verifactu_records_fingerprint'", source)
        self.assertIn("op.drop_column('verifactu_records', 'official_payload')", source)
        self.assertNotIn("op.drop_table", source)

    def test_chain_migration_adds_chain_state_without_backfill(self):
        source = chain_migration_source()

        self.assertIn("revision = 'd6e7f8a9b0c1'", source)
        self.assertIn("down_revision = 'c5d6e7f8a9b0'", source)
        self.assertIn("op.add_column('verifactu_records'", source)
        self.assertIn("chain_key", source)
        self.assertIn("chain_sequence", source)
        self.assertIn("op.create_table(", source)
        self.assertIn("'verifactu_chain_states'", source)
        self.assertIn("uq_verifactu_chain_states_chain_key", source)
        self.assertIn("uq_verifactu_records_chain_sequence", source)
        self.assertIn("ck_verifactu_records_ready_chain_complete", source)
        self.assertIn("ck_verifactu_records_first_previous_coherent", source)
        self.assertIn("ix_verifactu_records_chain_key_sequence", source)
        self.assertNotIn("op.add_column('invoices'", source)
        self.assertNotRegex(source, re.compile(r"\b(insert|update|execute|bulk_insert)\b"))

    def test_chain_migration_downgrade_removes_chain_state_only(self):
        source = chain_migration_source()

        self.assertIn("op.drop_table('verifactu_chain_states')", source)
        self.assertIn("op.drop_column('verifactu_records', 'chain_sequence')", source)
        self.assertIn("op.drop_column('verifactu_records', 'chain_key')", source)
        self.assertNotIn("op.drop_table('verifactu_records')", source)


class VeriFactuRecordServiceSourceTest(unittest.TestCase):
    def test_service_has_no_transmission_signing_qr_or_transport_claim(self):
        source = service_source().lower()

        for forbidden in (
            "requests",
            "http",
            "certificate",
            "certificado",
            "xml",
            "qr",
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
        self.assertIn("prepare_verifactu_record_for_submission", service_source())
        self.assertIn("build_registration_fingerprint_input", service_source())
        self.assertIn("calculate_verifactu_fingerprint", service_source())

    def test_service_uses_chain_state_lock_and_not_last_ready_scan(self):
        source = service_source()
        lower_source = source.lower()

        self.assertIn("VeriFactuChainState", source)
        self.assertIn(".with_for_update()", source)
        self.assertIn("chain_state.next_sequence", source)
        self.assertIn("chain_state.last_record_id", source)
        self.assertIn("build_verifactu_chain_key", source)
        self.assertNotIn(".order_by(\n            VeriFactuRecord.ready_at.desc()", source)
        self.assertNotIn("max(", lower_source)


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

    def create_record(self, invoice, *, system_id="metalwolft-dev-01", software_name="MetalWolft", software_version="2026.7"):
        return create_verifactu_registration_record(
            invoice,
            db_session=db.session,
            system_id=system_id,
            software_name=software_name,
            software_version=software_version,
        )

    def system_identity(
        self,
        *,
        system_id="metalwolft-dev-01",
        system_name="MetalWolft",
        system_version="2026.7",
        installation_id="DEV-001",
        producer_name="MetalWolft S.L.",
        producer_tax_id="B00000000",
    ):
        return verifactu_system_identity_from_config({
            "VERIFACTU_SYSTEM_ID": system_id,
            "VERIFACTU_SYSTEM_NAME": system_name,
            "VERIFACTU_SYSTEM_VERSION": system_version,
            "VERIFACTU_INSTALLATION_ID": installation_id,
            "VERIFACTU_PRODUCER_NAME": producer_name,
            "VERIFACTU_PRODUCER_TAX_ID": producer_tax_id,
        })

    def prepare_record(self, record, *, generation_timestamp=None, system_identity=None):
        return prepare_verifactu_record_for_submission(
            record,
            db_session=db.session,
            system_identity=system_identity or self.system_identity(),
            generation_timestamp=generation_timestamp or datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc),
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

    def test_create_verifactu_registration_record_from_v2_snapshot(self):
        invoice = self.make_invoice(invoice_snapshot=snapshot(schema_version=2))

        result = self.create_record(invoice)

        self.assertTrue(result.created)
        self.assertEqual(result.record.total_amount, Decimal("121.00"))

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

    def test_prepare_record_calculates_fingerprint_and_marks_ready(self):
        invoice = self.make_invoice()
        result = self.create_record(invoice)
        before = self.fiscal_state(invoice)

        ready = self.prepare_record(result.record)
        db.session.commit()
        record = ready.record

        self.assertTrue(ready.prepared)
        self.assertEqual(record.status, STATUS_READY)
        self.assertEqual(record.fingerprint_status, "CALCULATED")
        self.assertEqual(record.fingerprint_algorithm, "SHA-256")
        self.assertEqual(len(record.fingerprint), 64)
        self.assertEqual(record.fingerprint, record.fingerprint.upper())
        self.assertIn("IDEmisorFactura=B00000000", record.fingerprint_input)
        self.assertIn("TipoFactura=F1", record.fingerprint_input)
        self.assertIn("&Huella=&", record.fingerprint_input)
        self.assertEqual(record.official_payload_schema_version, 1)
        self.assertEqual(record.official_payload["RegistroAlta"]["TipoFactura"], "F1")
        self.assertEqual(record.official_payload["RegistroAlta"]["Huella"], record.fingerprint)
        self.assertEqual(ready.chain_sequence, 1)
        self.assertEqual(record.chain_sequence, 1)
        self.assertEqual(record.chain_key, "B00000000|VERI*FACTU|B00000000|metalwolft-dev-01|DEV-001")
        self.assertIsNone(record.previous_record_id)
        self.assertIsNone(record.previous_fingerprint)
        self.assertTrue(record.is_first_record)
        self.assertEqual(record.installation_id, "DEV-001")
        self.assertEqual(record.producer_tax_id, "B00000000")
        self.assertEqual(record.generation_timezone, "+00:00")
        chain_state = db.session.query(VeriFactuChainState).filter_by(chain_key=record.chain_key).one()
        self.assertEqual(chain_state.last_record_id, record.id)
        self.assertEqual(chain_state.last_fingerprint, record.fingerprint)
        self.assertEqual(chain_state.next_sequence, 2)
        self.assert_invoice_unchanged(invoice, before)

    def test_prepare_record_is_idempotent_and_does_not_recalculate_ready_record(self):
        invoice = self.make_invoice()
        first = self.create_record(invoice)
        ready = self.prepare_record(
            first.record,
            generation_timestamp=datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc),
        )
        db.session.commit()
        first_fingerprint = ready.record.fingerprint
        first_input = ready.record.fingerprint_input
        chain_state_before = db.session.query(VeriFactuChainState).filter_by(chain_key=ready.record.chain_key).one()
        next_sequence_before = chain_state_before.next_sequence
        head_before = chain_state_before.last_record_id

        second = self.prepare_record(
            ready.record,
            generation_timestamp=datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc),
        )

        self.assertFalse(second.prepared)
        self.assertEqual(second.record.fingerprint, first_fingerprint)
        self.assertEqual(second.record.fingerprint_input, first_input)
        chain_state_after = db.session.query(VeriFactuChainState).filter_by(chain_key=ready.record.chain_key).one()
        self.assertEqual(chain_state_after.next_sequence, next_sequence_before)
        self.assertEqual(chain_state_after.last_record_id, head_before)

    def test_prepare_record_links_to_previous_ready_record_for_same_system(self):
        first_invoice = self.make_invoice()
        first_record = self.create_record(first_invoice).record
        self.prepare_record(
            first_record,
            generation_timestamp=datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc),
        )
        db.session.commit()

        second_invoice = self.make_invoice()
        second_record = self.create_record(second_invoice).record
        ready = self.prepare_record(
            second_record,
            generation_timestamp=datetime(2026, 7, 19, 12, 5, tzinfo=timezone.utc),
        )

        self.assertTrue(ready.prepared)
        self.assertEqual(second_record.chain_sequence, 2)
        self.assertEqual(ready.previous_record_id, first_record.id)
        self.assertFalse(ready.is_first_record)
        self.assertEqual(second_record.previous_fingerprint, first_record.fingerprint)
        self.assertIn(f"&Huella={first_record.fingerprint}&", second_record.fingerprint_input)

    def test_third_record_links_to_second_as_immediate_previous(self):
        first = self.create_record(self.make_invoice()).record
        self.prepare_record(first, generation_timestamp=datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc))
        db.session.commit()

        second = self.create_record(self.make_invoice()).record
        self.prepare_record(second, generation_timestamp=datetime(2026, 7, 19, 12, 5, tzinfo=timezone.utc))
        db.session.commit()

        third = self.create_record(self.make_invoice()).record
        self.prepare_record(third, generation_timestamp=datetime(2026, 7, 19, 12, 10, tzinfo=timezone.utc))

        self.assertEqual(third.chain_sequence, 3)
        self.assertEqual(third.previous_record_id, second.id)
        self.assertEqual(third.previous_fingerprint, second.fingerprint)

    def test_distinct_system_installation_and_issuer_do_not_share_chain(self):
        default_record = self.create_record(self.make_invoice()).record
        self.prepare_record(default_record)
        db.session.commit()

        other_system_identity = self.system_identity(system_id="metalwolft-dev-02", installation_id="DEV-001")
        other_system_record = self.create_record(
            self.make_invoice(),
            system_id="metalwolft-dev-02",
        ).record
        self.prepare_record(other_system_record, system_identity=other_system_identity)

        other_installation_identity = self.system_identity(installation_id="DEV-002")
        other_installation_record = self.create_record(self.make_invoice()).record
        self.prepare_record(other_installation_record, system_identity=other_installation_identity)

        other_issuer_snapshot = snapshot(issuer_tax_id="B11111111")
        other_issuer_record = self.create_record(
            self.make_invoice(
                invoice_snapshot=other_issuer_snapshot,
                stored_hash=calculate_invoice_snapshot_hash(other_issuer_snapshot),
            )
        ).record
        self.prepare_record(other_issuer_record)

        self.assertEqual(other_system_record.chain_sequence, 1)
        self.assertEqual(other_installation_record.chain_sequence, 1)
        self.assertEqual(other_issuer_record.chain_sequence, 1)
        self.assertEqual(db.session.query(VeriFactuChainState).count(), 4)
        self.assertEqual(len({
            default_record.chain_key,
            other_system_record.chain_key,
            other_installation_record.chain_key,
            other_issuer_record.chain_key,
        }), 4)

    def test_chain_key_is_built_from_issuer_mode_producer_system_and_installation(self):
        chain_key = build_verifactu_chain_key(
            issuer_tax_id="B00000000",
            mode="VERI*FACTU",
            system_identity=self.system_identity(),
        )

        self.assertEqual(chain_key, "B00000000|VERI*FACTU|B00000000|metalwolft-dev-01|DEV-001")

    def test_duplicate_chain_position_and_duplicate_child_are_rejected_by_db(self):
        first = self.create_record(self.make_invoice()).record
        self.prepare_record(first)
        db.session.commit()

        duplicate_position = VeriFactuRecord(
            invoice_id=first.invoice_id,
            provider="verifactu",
            mode="VERI*FACTU",
            record_type="anulacion",
            status=STATUS_READY,
            schema_version=1,
            invoice_number="F2026999999",
            invoice_issued_at=first.invoice_issued_at,
            invoice_snapshot_hash=first.invoice_snapshot_hash,
            record_payload={"duplicate": True},
            record_payload_hash="c" * 64,
            official_payload={"duplicate": True},
            official_payload_schema_version=1,
            chain_key=first.chain_key,
            chain_sequence=first.chain_sequence,
            fingerprint="D" * 64,
            fingerprint_algorithm="SHA-256",
            fingerprint_status="CALCULATED",
            fingerprint_input="duplicate",
            fingerprint_calculated_at=first.fingerprint_calculated_at,
            is_first_record=True,
            system_id=first.system_id,
            software_name=first.software_name,
            software_version=first.software_version,
            installation_id=first.installation_id,
            producer_name=first.producer_name,
            producer_tax_id=first.producer_tax_id,
            generation_timestamp=first.generation_timestamp,
            generation_timezone=first.generation_timezone,
            ready_at=first.ready_at,
            issuer_tax_id=first.issuer_tax_id,
            recipient_tax_id=first.recipient_tax_id,
            total_amount=first.total_amount,
            currency=first.currency,
        )
        db.session.add(duplicate_position)
        with self.assertRaises(IntegrityError):
            db.session.commit()

        db.session.rollback()
        second = self.create_record(self.make_invoice()).record
        self.prepare_record(second)
        db.session.commit()

        duplicate_child = VeriFactuRecord(
            invoice_id=second.invoice_id,
            provider="verifactu",
            mode="VERI*FACTU",
            record_type="anulacion",
            status=STATUS_READY,
            schema_version=1,
            invoice_number="F2026999998",
            invoice_issued_at=second.invoice_issued_at,
            invoice_snapshot_hash=second.invoice_snapshot_hash,
            record_payload={"duplicate": True},
            record_payload_hash="e" * 64,
            official_payload={"duplicate": True},
            official_payload_schema_version=1,
            chain_key=second.chain_key,
            chain_sequence=3,
            fingerprint="E" * 64,
            fingerprint_algorithm="SHA-256",
            fingerprint_status="CALCULATED",
            fingerprint_input="duplicate-child",
            fingerprint_calculated_at=second.fingerprint_calculated_at,
            previous_record_id=second.previous_record_id,
            previous_fingerprint=second.previous_fingerprint,
            is_first_record=False,
            system_id=second.system_id,
            software_name=second.software_name,
            software_version=second.software_version,
            installation_id=second.installation_id,
            producer_name=second.producer_name,
            producer_tax_id=second.producer_tax_id,
            generation_timestamp=second.generation_timestamp,
            generation_timezone=second.generation_timezone,
            ready_at=second.ready_at,
            issuer_tax_id=second.issuer_tax_id,
            recipient_tax_id=second.recipient_tax_id,
            total_amount=second.total_amount,
            currency=second.currency,
        )
        db.session.add(duplicate_child)
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_first_and_following_record_constraints_reject_incoherent_references(self):
        first = self.create_record(self.make_invoice()).record
        self.prepare_record(first)
        db.session.commit()

        first.previous_record_id = first.id
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_altered_chain_head_is_rejected(self):
        first = self.create_record(self.make_invoice()).record
        self.prepare_record(first)
        db.session.commit()
        chain_state = db.session.query(VeriFactuChainState).filter_by(chain_key=first.chain_key).one()
        chain_state.last_fingerprint = "bad"
        db.session.commit()

        second = self.create_record(self.make_invoice()).record
        with self.assertRaises(VeriFactuRecordIntegrityError):
            self.prepare_record(second)

    def test_error_during_fingerprint_calculation_does_not_consume_sequence_after_rollback(self):
        invoice = self.make_invoice()
        invoice.invoice_number = "F2026=bad"
        db.session.commit()
        record = self.create_record(invoice).record

        with self.assertRaises(VeriFactuRecordValidationError):
            self.prepare_record(record)
        db.session.rollback()

        self.assertEqual(db.session.query(VeriFactuChainState).count(), 0)

    def test_prepare_record_rejects_missing_system_identity_and_payload_hash_mismatch(self):
        invoice = self.make_invoice()
        record = self.create_record(invoice).record

        with self.assertRaises(VeriFactuRecordValidationError):
            prepare_verifactu_record_for_submission(
                record,
                db_session=db.session,
                system_identity=verifactu_system_identity_from_config({
                    "VERIFACTU_SYSTEM_ID": "",
                    "VERIFACTU_SYSTEM_NAME": "MetalWolft",
                    "VERIFACTU_SYSTEM_VERSION": "2026.7",
                    "VERIFACTU_INSTALLATION_ID": "DEV-001",
                    "VERIFACTU_PRODUCER_NAME": "MetalWolft S.L.",
                    "VERIFACTU_PRODUCER_TAX_ID": "B00000000",
                }),
                generation_timestamp=datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc),
            )

        db.session.rollback()
        record.record_payload_hash = "bad"
        with self.assertRaises(VeriFactuRecordIntegrityError):
            self.prepare_record(record)

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

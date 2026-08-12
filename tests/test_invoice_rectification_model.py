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
    / "src/migrations/versions/b2c3d4e5f6a7_add_invoice_rectification_fields.py"
)
AEAT_TYPE_MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/c1d2e3f4a5b6_add_invoice_rectification_aeat_type.py"
)
LEGACY_AEAT_AUDIT_MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/d7e8f9a0b1c2_add_invoice_legacy_rectification_aeat_audit.py"
)


def read(path):
    return (ROOT_DIR / path).read_text(encoding="utf-8")


def models_source():
    return read("src/api/models.py")


def invoices_block():
    source = models_source()
    return source[
        source.index("class Invoices(db.Model):"):source.index("class InvoiceFiscalSubmission(db.Model):")
    ]


def migration_source():
    return MIGRATION_PATH.read_text(encoding="utf-8")


def aeat_type_migration_source():
    return AEAT_TYPE_MIGRATION_PATH.read_text(encoding="utf-8")


def legacy_aeat_audit_migration_source():
    return LEGACY_AEAT_AUDIT_MIGRATION_PATH.read_text(encoding="utf-8")


class InvoiceRectificationModelSourceTest(unittest.TestCase):
    def test_new_rectification_fields_and_relationship_are_declared(self):
        source = invoices_block()

        self.assertIn("original_invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)", source)
        self.assertIn('db.Index(', source)
        self.assertIn('"ix_invoices_original_invoice_id"', source)
        self.assertIn("rectification_type = db.Column(db.String(30), nullable=True)", source)
        self.assertIn("rectification_reason = db.Column(db.String(50), nullable=True)", source)
        self.assertIn("rectification_aeat_type = db.Column(db.String(2), nullable=True)", source)
        self.assertIn("rectification_aeat_classified_at = db.Column(db.DateTime, nullable=True)", source)
        self.assertIn("rectification_aeat_classified_by = db.Column(db.String(255), nullable=True)", source)
        self.assertIn("original_invoice = db.relationship(", source)
        self.assertIn("backref=db.backref('corrective_invoices', lazy=True)", source)
        self.assertIn("remote_side=[id]", source)
        self.assertIn("foreign_keys=[original_invoice_id]", source)

    def test_rectification_constraints_are_declared(self):
        source = invoices_block()

        self.assertIn("ck_invoices_rectification_consistency", source)
        self.assertIn("ck_invoices_invoice_type_valid", source)
        self.assertIn("ck_invoices_rectification_type_valid", source)
        self.assertIn("ck_invoices_rectification_reason_valid", source)
        self.assertIn("ck_invoices_rectification_aeat_type_valid", source)
        self.assertIn("ck_invoices_rectification_aeat_type_corrective_only", source)
        self.assertIn("ck_invoices_rectification_aeat_classified_at_corrective_only", source)
        self.assertIn("ck_invoices_rectification_aeat_classified_by_corrective_only", source)
        self.assertIn("ck_invoices_rectification_aeat_classification_audit_complete", source)
        self.assertIn("ck_invoices_original_invoice_not_self", source)
        self.assertIn("invoice_type = 'corrective'", source)
        self.assertIn("invoice_type = 'ordinary'", source)
        self.assertIn("rectification_type IN ('differences', 'substitution')", source)
        self.assertIn("rectification_reason IS NULL OR rectification_reason IN (", source)
        self.assertIn("'invoice_error'", source)
        self.assertIn("'shipping_error'", source)
        self.assertIn("'R1', 'R2', 'R3', 'R4', 'R5'", source)
        self.assertNotIn("ondelete='CASCADE'", source)
        self.assertNotIn("cascade='delete'", source)
        self.assertNotIn("cascade='delete-orphan'", source)


class InvoiceRectificationMigrationTest(unittest.TestCase):
    def test_migration_is_chained_from_current_invoice_head(self):
        source = migration_source()

        self.assertIn("revision = 'b2c3d4e5f6a7'", source)
        self.assertIn("down_revision = 'a2b3c4d5e6f7'", source)

    def test_migration_adds_new_columns_and_constraints(self):
        source = migration_source()

        self.assertIn("op.add_column('invoices', sa.Column('original_invoice_id', sa.Integer(), nullable=True))", source)
        self.assertIn("op.add_column('invoices', sa.Column('rectification_type', sa.String(length=30), nullable=True))", source)
        self.assertIn("op.add_column('invoices', sa.Column('rectification_reason', sa.String(length=50), nullable=True))", source)
        self.assertIn("'ix_invoices_original_invoice_id'", source)
        self.assertIn("op.create_foreign_key(", source)
        self.assertIn("'fk_invoices_original_invoice_id'", source)
        self.assertIn("'ck_invoices_rectification_consistency'", source)
        self.assertIn("'ck_invoices_invoice_type_valid'", source)
        self.assertIn("'ck_invoices_rectification_type_valid'", source)
        self.assertIn("'ck_invoices_rectification_reason_valid'", source)
        self.assertIn("'ck_invoices_original_invoice_not_self'", source)

    def test_downgrade_drops_constraints_before_columns(self):
        source = migration_source()

        self.assertLess(
            source.index("op.drop_constraint('fk_invoices_original_invoice_id'"),
            source.index("op.drop_column('invoices', 'original_invoice_id')"),
        )

    def test_migration_index_is_non_unique(self):
        source = migration_source()

        self.assertIn("op.create_index(", source)
        self.assertIn("'ix_invoices_original_invoice_id'", source)
        self.assertIn("unique=False", source)
        self.assertIn("op.drop_index('ix_invoices_original_invoice_id'", source)

    def test_aeat_type_migration_is_additive_and_merges_current_heads(self):
        source = aeat_type_migration_source()

        self.assertIn('revision = "c1d2e3f4a5b6"', source)
        self.assertIn('down_revision = ("e5f6a7b8c9d0", "f1a2b3c4d5e6")', source)
        self.assertIn('sa.Column("rectification_aeat_type", sa.String(length=2), nullable=True)', source)
        self.assertIn("ck_invoices_rectification_aeat_type_valid", source)
        self.assertIn("ck_invoices_rectification_aeat_type_corrective_only", source)
        self.assertNotIn("UPDATE invoices", source)

    def test_legacy_aeat_audit_migration_is_additive_and_chained_from_current_head(self):
        source = legacy_aeat_audit_migration_source()

        self.assertIn('revision = "d7e8f9a0b1c2"', source)
        self.assertIn('down_revision = "c6d7e8f9a0b1"', source)
        self.assertIn('"rectification_aeat_classified_at"', source)
        self.assertIn('"rectification_aeat_classified_by"', source)
        self.assertNotIn("UPDATE invoices", source)

try:
    from flask import Flask  # noqa: E402
    from sqlalchemy.exc import IntegrityError  # noqa: E402

    from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash  # noqa: E402
    from api.models import Invoices, db  # noqa: E402

    HAS_DB_TEST_DEPENDENCIES = True
except Exception:  # pragma: no cover - import guard for stripped test envs
    HAS_DB_TEST_DEPENDENCIES = False


@unittest.skipUnless(HAS_DB_TEST_DEPENDENCIES, "Flask/SQLAlchemy test dependencies are not installed.")
class InvoiceRectificationSQLiteTest(unittest.TestCase):
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

    def make_invoice(self, **overrides):
        base_snapshot = {
            "schema_version": 2,
            "metadata": {"generator": "test"},
            "issuer": {
                "legal_name": "MetalWolft",
                "tax_id": "B12345678",
                "address": "Calle Metal 1",
                "postal_code": "13005",
                "city": "Ciudad Real",
                "country_code": "ES",
            },
            "customer": {
                "legal_name": "Cliente",
                "tax_id": "00000000T",
                "address": "Calle Cliente 1",
                "postal_code": "13005",
                "city": "Ciudad Real",
                "country_code": "ES",
            },
            "operation": {
                "invoice_type": "ordinary",
                "issue_date": "2026-08-07",
                "operation_date": "2026-08-07",
                "currency": "EUR",
                "order_id": 1,
            },
            "lines": [],
            "totals": {
                "tax_base": "1.39",
                "tax_amount": "0.30",
                "total_amount": "1.69",
            },
            "payment": {"provider": "stripe"},
            "references": {"checkout_session_id": 1, "order_id": 1, "source": "manual"},
        }
        snapshot = overrides.pop("invoice_snapshot", base_snapshot)
        invoice = Invoices(
            invoice_number=overrides.pop("invoice_number", "F2026000001"),
            invoice_type=overrides.pop("invoice_type", "ordinary"),
            amount=overrides.pop("amount", 1.69),
            client_name=overrides.pop("client_name", "Cliente"),
            client_address=overrides.pop("client_address", "Calle Cliente 1"),
            client_cif=overrides.pop("client_cif", "00000000T"),
            client_phone=overrides.pop("client_phone", "600000000"),
            order_details=overrides.pop("order_details", []),
            invoice_snapshot=snapshot,
            invoice_snapshot_schema_version=snapshot.get("schema_version"),
            invoice_snapshot_hash=overrides.pop(
                "invoice_snapshot_hash",
                calculate_invoice_snapshot_hash(snapshot),
            ),
            issued_at=overrides.pop("issued_at", None),
            **overrides,
        )
        db.session.add(invoice)
        return invoice

    def assert_integrity_error(self):
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_ordinary_invoice_can_be_stored_without_rectification_reference(self):
        self.make_invoice()

        db.session.commit()

        saved = db.session.query(Invoices).one()
        self.assertEqual(saved.invoice_type, "ordinary")
        self.assertIsNone(saved.original_invoice_id)
        self.assertIsNone(saved.rectification_type)
        self.assertIsNone(saved.rectification_reason)
        self.assertIsNone(saved.rectification_aeat_type)
        self.assertIsNone(saved.rectification_aeat_classified_at)
        self.assertIsNone(saved.rectification_aeat_classified_by)
        self.assertEqual(len(saved.corrective_invoices), 0)

    def test_corrective_invoice_can_reference_original_invoice(self):
        original = self.make_invoice(invoice_number="F2026000001")
        db.session.commit()

        corrective_snapshot = {
            **original.invoice_snapshot,
            "operation": {
                **original.invoice_snapshot["operation"],
                "invoice_type": "corrective",
            },
        }
        corrective = self.make_invoice(
            invoice_number="R2026000001",
            invoice_type="corrective",
            amount=-1.69,
            invoice_snapshot=corrective_snapshot,
            client_cif=None,
            client_phone="600000000",
            original_invoice_id=original.id,
            rectification_type="differences",
            rectification_reason="invoice_error",
            rectification_aeat_type="R4",
        )

        db.session.commit()

        self.assertEqual(corrective.original_invoice_id, original.id)
        self.assertIs(corrective.original_invoice, original)
        self.assertEqual(len(original.corrective_invoices), 1)
        self.assertEqual(original.corrective_invoices[0].invoice_number, "R2026000001")

    def test_legacy_invoices_and_rectifications_can_keep_a_null_aeat_type(self):
        original = self.make_invoice(invoice_number="F2026000001")
        db.session.commit()

        self.make_invoice(
            invoice_number="R2026000001",
            invoice_type="corrective",
            amount=-1.69,
            original_invoice_id=original.id,
            rectification_type="differences",
            rectification_reason="invoice_error",
        )

        db.session.commit()

    def test_invalid_or_non_corrective_aeat_type_is_rejected(self):
        original = self.make_invoice(invoice_number="F2026000001")
        db.session.commit()

        self.make_invoice(
            invoice_number="R2026000001",
            invoice_type="corrective",
            amount=-1.69,
            original_invoice_id=original.id,
            rectification_type="differences",
            rectification_reason="invoice_error",
            rectification_aeat_type="R9",
        )
        self.assert_integrity_error()

    def test_legacy_aeat_audit_fields_must_be_complete_and_corrective_only(self):
        original = self.make_invoice(invoice_number="F2026000001")
        db.session.commit()

        self.make_invoice(
            invoice_number="R2026000001",
            invoice_type="corrective",
            amount=-1.69,
            original_invoice_id=original.id,
            rectification_type="differences",
            rectification_reason="invoice_error",
            rectification_aeat_type="R1",
            rectification_aeat_classified_at=datetime(2026, 8, 12, 10, 0, 0),
        )
        self.assert_integrity_error()

        self.make_invoice(
            invoice_number="F2026000002",
            invoice_type="ordinary",
            rectification_aeat_classified_at=datetime(2026, 8, 12, 10, 0, 0),
            rectification_aeat_classified_by="flask_admin:admin",
        )
        self.assert_integrity_error()

        self.make_invoice(
            invoice_number="F2026000002",
            invoice_type="ordinary",
            rectification_aeat_type="R4",
        )
        self.assert_integrity_error()

    def test_corrective_without_original_is_rejected(self):
        self.make_invoice(
            invoice_number="R2026000001",
            invoice_type="corrective",
            amount=-1.69,
            client_cif=None,
            rectification_type="differences",
            rectification_reason="invoice_error",
        )

        self.assert_integrity_error()

    def test_ordinary_with_original_is_rejected(self):
        original = self.make_invoice(invoice_number="F2026000001")
        db.session.commit()

        self.make_invoice(
            invoice_number="F2026000002",
            invoice_type="ordinary",
            original_invoice_id=original.id,
        )

        self.assert_integrity_error()

    def test_corrective_without_rectification_type_or_reason_is_rejected(self):
        original = self.make_invoice(invoice_number="F2026000001")
        db.session.commit()

        self.make_invoice(
            invoice_number="R2026000001",
            invoice_type="corrective",
            amount=-1.69,
            original_invoice_id=original.id,
            rectification_reason="invoice_error",
        )

        self.assert_integrity_error()

    def test_self_reference_is_rejected(self):
        invoice = self.make_invoice(invoice_number="R2026000001", invoice_type="ordinary")
        db.session.flush()
        invoice.invoice_type = "corrective"
        invoice.original_invoice_id = invoice.id
        invoice.rectification_type = "differences"
        invoice.rectification_reason = "invoice_error"

        self.assert_integrity_error()

    def test_disallowed_values_are_rejected(self):
        original = self.make_invoice(invoice_number="F2026000001")
        db.session.commit()

        invalid_invoice = self.make_invoice(
            invoice_number="R2026000001",
            invoice_type="corrective",
            amount=-1.69,
            client_cif=None,
            original_invoice_id=original.id,
            rectification_type="invalid",
            rectification_reason="invoice_error",
        )

        with self.subTest("rectification_type"):
            self.assert_integrity_error()

        db.session.add(invalid_invoice)
        invalid_invoice.rectification_type = "differences"
        invalid_invoice.rectification_reason = "invalid"

        with self.subTest("rectification_reason"):
            self.assert_integrity_error()

        db.session.add(
            Invoices(
                invoice_number="R2026000002",
                invoice_type="transfer",
                amount=-1.69,
                client_name="Cliente",
                client_address="Calle Cliente 1",
                client_cif=None,
                client_phone="600000000",
                order_details=[],
                invoice_snapshot=original.invoice_snapshot,
                invoice_snapshot_schema_version=original.invoice_snapshot_schema_version,
                invoice_snapshot_hash=original.invoice_snapshot_hash,
                issued_at=None,
            )
        )

        with self.subTest("invoice_type"):
            self.assert_integrity_error()


if __name__ == "__main__":
    unittest.main()

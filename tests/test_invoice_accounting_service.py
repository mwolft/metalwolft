import copy
import importlib.util
import re
import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/f1a2b3c4d5e6_add_accounting_entries_table.py"
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
    from sqlalchemy.exc import IntegrityError  # noqa: E402

    from api.invoice_accounting_service import (  # noqa: E402
        ENTRY_TYPE_SALE,
        STATUS_PENDING,
        AccountingEntryIntegrityError,
        AccountingEntryUnsupportedSchema,
        AccountingEntryValidationError,
        create_accounting_entry,
    )
    from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash  # noqa: E402
    from api.models import AccountingEntry, Invoices, db  # noqa: E402


def model_source():
    return (ROOT_DIR / "src/api/models.py").read_text(encoding="utf-8")


def service_source():
    return (ROOT_DIR / "src/api/invoice_accounting_service.py").read_text(encoding="utf-8")


def migration_source():
    return MIGRATION_PATH.read_text(encoding="utf-8")


def accounting_entry_block():
    source = model_source()
    return source[
        source.index("class AccountingEntry(db.Model):"):source.index("class InvoiceSequence(db.Model):")
    ]


class AccountingEntryModelSourceTest(unittest.TestCase):
    def test_model_declares_expected_table_columns_and_statuses(self):
        source = accounting_entry_block()

        self.assertIn('__tablename__ = "accounting_entries"', source)
        self.assertIn('ENTRY_TYPE_SALE = "sale"', source)
        self.assertIn('STATUS_PENDING = "pending"', source)
        self.assertIn('STATUS_RECORDED = "recorded"', source)
        self.assertIn('STATUS_FAILED = "failed"', source)

        for expected in (
            "invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)",
            "entry_type = db.Column(db.String(30), nullable=False, default=ENTRY_TYPE_SALE)",
            "status = db.Column(db.String(30), nullable=False, default=STATUS_PENDING)",
            "invoice_number = db.Column(db.String(50), nullable=False)",
            "invoice_date = db.Column(db.Date, nullable=False)",
            "customer_name = db.Column(db.String(255), nullable=False)",
            "customer_tax_id = db.Column(db.String(50), nullable=True)",
            "taxable_base = db.Column(db.Numeric(12, 2), nullable=False)",
            "vat_amount = db.Column(db.Numeric(12, 2), nullable=False)",
            "total_amount = db.Column(db.Numeric(12, 2), nullable=False)",
            "currency = db.Column(db.String(3), nullable=False)",
            "payment_provider = db.Column(db.String(30), nullable=True)",
            "order_id = db.Column(db.Integer, nullable=True)",
            "recorded_at = db.Column(db.DateTime, nullable=True)",
            "error_message = db.Column(db.Text, nullable=True)",
        ):
            self.assertIn(expected, source)

    def test_model_declares_unique_invoice_and_type_constraint(self):
        source = accounting_entry_block()

        self.assertIn("db.UniqueConstraint(", source)
        self.assertIn('"invoice_id"', source)
        self.assertIn('"entry_type"', source)
        self.assertIn('name="uq_accounting_entries_invoice_entry_type"', source)

    def test_model_declares_invoice_id_index_matching_existing_migration(self):
        source = accounting_entry_block()

        self.assertIn("db.Index(", source)
        self.assertIn('"ix_accounting_entries_invoice_id"', source)
        self.assertIn('"invoice_id"', source)
        self.assertIn("unique=False", source)

    def test_model_index_matches_migration_name_without_new_migration(self):
        source = migration_source()

        self.assertIn("'ix_accounting_entries_invoice_id'", source)
        migration_files = [
            path.name
            for path in (ROOT_DIR / "src/migrations/versions").glob("*.py")
            if "ix_accounting_entries_invoice_id" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            migration_files,
            ["f1a2b3c4d5e6_add_accounting_entries_table.py"],
        )

    def test_model_relates_many_entries_to_one_invoice(self):
        source = accounting_entry_block()

        self.assertIn("invoice = db.relationship(", source)
        self.assertIn("'Invoices'", source)
        self.assertIn("backref=db.backref('accounting_entries', lazy=True)", source)


class AccountingEntryMigrationTest(unittest.TestCase):
    def test_migration_creates_only_accounting_entries_table(self):
        source = migration_source()

        self.assertIn("revision = 'f1a2b3c4d5e6'", source)
        self.assertIn("down_revision = 'e6f7a8b9c0d1'", source)
        self.assertIn("op.create_table(", source)
        self.assertIn("'accounting_entries'", source)
        self.assertIn("sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'])", source)
        self.assertNotIn("op.add_column('invoices'", source)
        self.assertNotIn("op.alter_column('invoices'", source)
        self.assertNotIn("op.add_column('orders'", source)

    def test_migration_columns_constraint_index_and_downgrade(self):
        source = migration_source()

        for expected in (
            "sa.Column('taxable_base', sa.Numeric(12, 2), nullable=False)",
            "sa.Column('vat_amount', sa.Numeric(12, 2), nullable=False)",
            "sa.Column('total_amount', sa.Numeric(12, 2), nullable=False)",
            "sa.UniqueConstraint(",
            "name='uq_accounting_entries_invoice_entry_type'",
            "'ix_accounting_entries_invoice_id'",
            "op.drop_table('accounting_entries')",
        ):
            self.assertIn(expected, source)

    def test_migration_has_no_backfill_or_existing_table_updates(self):
        source = migration_source()

        self.assertNotRegex(source, re.compile(r"\b(insert|update|execute|bulk_insert)\b"))


class AccountingEntryServiceSourceTest(unittest.TestCase):
    def test_service_uses_snapshot_hash_and_decimal_money(self):
        source = service_source()

        self.assertIn("calculate_invoice_snapshot_hash", source)
        self.assertIn("Decimal", source)
        self.assertIn("ROUND_HALF_UP", source)
        self.assertIn("db.Numeric", accounting_entry_block())

    def test_service_is_idempotent_and_does_not_commit_or_rollback(self):
        source = service_source()

        self.assertIn(".filter_by(invoice_id=invoice_id, entry_type=ENTRY_TYPE_SALE)", source)
        self.assertIn(".one_or_none()", source)
        self.assertIn("if existing_entry:", source)
        self.assertIn("session.flush()", source)
        self.assertNotIn(".commit(", source)
        self.assertNotIn(".rollback(", source)

    def test_service_does_not_use_live_order_customer_or_checkout_data(self):
        source = service_source()

        for forbidden in (
            "OrderDetails",
            "Orders",
            "Users",
            "CheckoutSessions",
            "invoice.order",
            "invoice.user",
            "invoice.checkout_session",
            "joinedload",
            "send_email",
        ):
            self.assertNotIn(forbidden, source)

    def test_service_has_no_excel_csv_or_external_side_effects(self):
        source = service_source().lower()

        for forbidden in (
            "excel",
            "openpyxl",
            ".xlsx",
            "csv",
            "requests",
            "http",
            "verifactu",
            "cron",
            "queue",
        ):
            self.assertNotIn(forbidden, source)

    def test_service_does_not_modify_invoice_fiscal_fields(self):
        source = service_source()

        for forbidden in (
            "invoice.invoice_number =",
            "invoice.invoice_snapshot =",
            "invoice.invoice_snapshot_hash =",
            "invoice.issued_at =",
        ):
            self.assertNotIn(forbidden, source)


@unittest.skipUnless(HAS_DB_TEST_DEPENDENCIES, "Flask/SQLAlchemy test dependencies are not installed.")
class AccountingEntryServiceSQLiteTest(unittest.TestCase):
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

    def snapshot(self, *, provider="stripe", tax_id="00000000T", schema_version=1):
        return {
            "schema_version": schema_version,
            "metadata": {"generator": "invoice_snapshot_builder_v1"},
            "customer": {
                "legal_name": "Cliente Contable",
                "tax_id": tax_id,
            },
            "operation": {
                "issue_date": "2026-07-15",
                "currency": "EUR",
                "order_id": 321,
            },
            "payment": {
                "provider": provider,
            },
            "totals": {
                "tax_base": "100.00",
                "tax_amount": "21.00",
                "total_amount": "121.00",
            },
        }

    def make_invoice(self, *, snapshot=None, stored_hash=None):
        invoice_snapshot = snapshot if snapshot is not None else self.snapshot()
        invoice = Invoices(
            invoice_number="F2026000001",
            invoice_type="ordinary",
            amount=121.00,
            client_name="Legacy Name",
            client_address="Legacy Address",
            client_cif="LEGACY-CIF",
            client_phone="600000000",
            order_details=[],
            invoice_snapshot=invoice_snapshot,
            invoice_snapshot_schema_version=invoice_snapshot.get("schema_version"),
            invoice_snapshot_hash=stored_hash or calculate_invoice_snapshot_hash(invoice_snapshot),
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

    def test_create_accounting_entry_from_snapshot(self):
        invoice = self.make_invoice()
        before = self.fiscal_state(invoice)

        entry = create_accounting_entry(invoice, db_session=db.session)
        db.session.commit()

        self.assertEqual(entry.invoice_id, invoice.id)
        self.assertEqual(entry.entry_type, ENTRY_TYPE_SALE)
        self.assertEqual(entry.status, STATUS_PENDING)
        self.assertEqual(entry.invoice_number, "F2026000001")
        self.assertEqual(entry.invoice_date, date(2026, 7, 15))
        self.assertEqual(entry.customer_name, "Cliente Contable")
        self.assertEqual(entry.customer_tax_id, "00000000T")
        self.assertEqual(entry.taxable_base, Decimal("100.00"))
        self.assertEqual(entry.vat_amount, Decimal("21.00"))
        self.assertEqual(entry.total_amount, Decimal("121.00"))
        self.assertEqual(entry.currency, "EUR")
        self.assertEqual(entry.payment_provider, "stripe")
        self.assertEqual(entry.order_id, 321)
        self.assert_invoice_fiscal_state_unchanged(invoice, before)

    def test_idempotency_returns_existing_entry(self):
        invoice = self.make_invoice()

        first = create_accounting_entry(invoice, db_session=db.session)
        db.session.commit()
        second = create_accounting_entry(invoice, db_session=db.session)

        self.assertEqual(first.id, second.id)
        self.assertEqual(db.session.query(AccountingEntry).count(), 1)

    def test_snapshot_absent_is_rejected(self):
        invoice = self.make_invoice()
        invoice.invoice_snapshot = None

        with self.assertRaises(AccountingEntryValidationError):
            create_accounting_entry(invoice, db_session=db.session)

    def test_hash_invalid_is_rejected(self):
        invoice = self.make_invoice(stored_hash="bad-hash")

        with self.assertRaises(AccountingEntryIntegrityError):
            create_accounting_entry(invoice, db_session=db.session)

    def test_schema_unsupported_is_rejected(self):
        invalid_snapshot = self.snapshot(schema_version=999)
        invoice = self.make_invoice(
            snapshot=invalid_snapshot,
            stored_hash=calculate_invoice_snapshot_hash(invalid_snapshot),
        )

        with self.assertRaises(AccountingEntryUnsupportedSchema):
            create_accounting_entry(invoice, db_session=db.session)

    def test_unique_invoice_and_entry_type_is_enforced(self):
        invoice = self.make_invoice()
        create_accounting_entry(invoice, db_session=db.session)
        db.session.commit()

        db.session.add(AccountingEntry(
            invoice_id=invoice.id,
            entry_type=ENTRY_TYPE_SALE,
            status=STATUS_PENDING,
            invoice_number="F2026000001",
            invoice_date=date(2026, 7, 15),
            customer_name="Duplicado",
            taxable_base=Decimal("1.00"),
            vat_amount=Decimal("0.21"),
            total_amount=Decimal("1.21"),
            currency="EUR",
        ))
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_customer_tax_id_can_be_missing(self):
        invoice = self.make_invoice(snapshot=self.snapshot(tax_id=None))

        entry = create_accounting_entry(invoice, db_session=db.session)

        self.assertIsNone(entry.customer_tax_id)

    def test_paypal_invoice_is_copied(self):
        invoice = self.make_invoice(snapshot=self.snapshot(provider="paypal"))

        entry = create_accounting_entry(invoice, db_session=db.session)

        self.assertEqual(entry.payment_provider, "paypal")

    def test_invoice_relationship_exposes_entries(self):
        invoice = self.make_invoice()
        create_accounting_entry(invoice, db_session=db.session)
        db.session.commit()

        self.assertEqual(len(invoice.accounting_entries), 1)

    def test_metadata_contains_non_unique_invoice_id_index_for_create_all(self):
        indexes = {
            index.name: index
            for index in AccountingEntry.__table__.indexes
        }
        index = indexes["ix_accounting_entries_invoice_id"]

        self.assertFalse(index.unique)
        self.assertEqual([column.name for column in index.columns], ["invoice_id"])


if __name__ == "__main__":
    unittest.main()

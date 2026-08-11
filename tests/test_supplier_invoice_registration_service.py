import copy
import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from flask import Flask  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402

from api.models import (  # noqa: E402
    AccountingEntry,
    Invoices,
    SupplierInvoice,
    SupplierInvoiceReceptionSequence,
    SupplierInvoiceTaxBreakdown,
    db,
)
from api.supplier_invoice_registration_service import (  # noqa: E402
    SupplierInvoiceDuplicateError,
    SupplierInvoiceRegistrationValidationError,
    build_supplier_invoice_snapshot,
    register_supplier_invoice,
)
from api.supplier_invoice_snapshot_integrity import (  # noqa: E402
    calculate_supplier_invoice_snapshot_hash,
)


MIGRATION_PATH = ROOT_DIR / "src/migrations/versions/d2e3f4a5b6c7_add_supplier_invoices.py"


class SupplierInvoiceRegistrationServiceTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        db.session.add(SupplierInvoiceReceptionSequence(id=1, last_number=0))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def make_draft(self, *, total_amount="121.00", breakdowns=None, **overrides):
        invoice = SupplierInvoice(
            supplier_legal_name=overrides.pop("supplier_legal_name", "Acero Proveedor SL"),
            supplier_tax_id=overrides.pop("supplier_tax_id", "B12345678"),
            supplier_invoice_number=overrides.pop("supplier_invoice_number", "P-2026-001"),
            issue_date=overrides.pop("issue_date", date(2026, 8, 11)),
            operation_date=overrides.pop("operation_date", None),
            concept=overrides.pop("concept", "Material de taller"),
            total_amount=Decimal(total_amount),
            **overrides,
        )
        db.session.add(invoice)
        db.session.flush()
        for position, values in enumerate(
            breakdowns or [("100.00", "21.00", "21.00", "21.00")],
            start=1,
        ):
            db.session.add(
                SupplierInvoiceTaxBreakdown(
                    supplier_invoice_id=invoice.id,
                    position=position,
                    tax_base=Decimal(values[0]),
                    tax_rate=Decimal(values[1]),
                    tax_amount=Decimal(values[2]),
                    deductible_tax_amount=Decimal(values[3]),
                )
            )
        db.session.flush()
        return invoice

    def test_draft_can_have_multiple_tax_breakdowns(self):
        invoice = self.make_draft(
            total_amount="133.10",
            breakdowns=[
                ("100.00", "21.00", "21.00", "21.00"),
                ("11.00", "10.00", "1.10", "1.10"),
            ],
        )
        db.session.commit()

        self.assertEqual(invoice.status, SupplierInvoice.STATUS_DRAFT)
        self.assertIsNone(invoice.reception_number)
        self.assertEqual(len(invoice.tax_breakdowns), 2)

    def test_valid_registration_assigns_reception_and_freezes_snapshot(self):
        invoice = self.make_draft()
        result = register_supplier_invoice(
            invoice,
            db_session=db.session,
            actor="admin",
            registered_at=datetime(2026, 8, 11, 10, 30, 0),
        )
        db.session.commit()

        self.assertTrue(result.registered)
        self.assertEqual(invoice.status, SupplierInvoice.STATUS_REGISTERED)
        self.assertEqual(invoice.reception_number, 1)
        self.assertEqual(invoice.snapshot_schema_version, 1)
        self.assertEqual(invoice.fiscal_snapshot["supplier"]["tax_id"], "B12345678")
        self.assertEqual(invoice.fiscal_snapshot["tax_breakdowns"][0]["tax_base"], "100.00")
        self.assertEqual(invoice.fiscal_snapshot["totals"]["tax_amount"], "21.00")
        self.assertEqual(
            invoice.snapshot_hash,
            calculate_supplier_invoice_snapshot_hash(invoice.fiscal_snapshot),
        )

    def test_registration_is_idempotent_and_does_not_consume_another_number(self):
        invoice = self.make_draft()
        register_supplier_invoice(invoice, db_session=db.session, registered_at=datetime(2026, 8, 11, 10, 30, 0))
        db.session.commit()
        original_snapshot = copy.deepcopy(invoice.fiscal_snapshot)

        result = register_supplier_invoice(invoice, db_session=db.session)
        db.session.commit()

        sequence = db.session.get(SupplierInvoiceReceptionSequence, 1)
        self.assertFalse(result.registered)
        self.assertEqual(invoice.reception_number, 1)
        self.assertEqual(sequence.last_number, 1)
        self.assertEqual(invoice.fiscal_snapshot, original_snapshot)

    def test_invalid_registration_does_not_consume_a_reception_number(self):
        invoice = self.make_draft(total_amount="120.00")

        with self.assertRaises(SupplierInvoiceRegistrationValidationError):
            register_supplier_invoice(invoice, db_session=db.session)

        self.assertIsNone(invoice.reception_number)
        self.assertEqual(db.session.get(SupplierInvoiceReceptionSequence, 1).last_number, 0)

    def test_snapshot_and_hash_are_deterministic_for_same_validated_input(self):
        first = self.make_draft()
        second = self.make_draft(supplier_invoice_number="P-2026-002")
        registered_at = datetime(2026, 8, 11, 10, 30, 0)
        for invoice in (first, second):
            invoice.reception_number = 7
            invoice.registered_by = "admin"

        first_snapshot = build_supplier_invoice_snapshot(
            first,
            breakdowns=[{
                "position": 1,
                "tax_base": Decimal("100.00"),
                "tax_rate": Decimal("21.00"),
                "tax_amount": Decimal("21.00"),
                "deductible_tax_amount": Decimal("21.00"),
            }],
            total_amount=Decimal("121.00"),
            registered_at=registered_at,
        )
        second.supplier_invoice_number = first.supplier_invoice_number
        second_snapshot = build_supplier_invoice_snapshot(
            second,
            breakdowns=[{
                "position": 1,
                "tax_base": Decimal("100.00"),
                "tax_rate": Decimal("21.00"),
                "tax_amount": Decimal("21.00"),
                "deductible_tax_amount": Decimal("21.00"),
            }],
            total_amount=Decimal("121.00"),
            registered_at=registered_at,
        )

        self.assertEqual(first_snapshot, second_snapshot)
        self.assertEqual(
            calculate_supplier_invoice_snapshot_hash(first_snapshot),
            calculate_supplier_invoice_snapshot_hash(second_snapshot),
        )

    def test_scope_and_supplier_validation_reject_unsupported_or_missing_values(self):
        service_cases = [
            ("missing-tax-id", {"supplier_tax_id": None}),
        ]
        for label, overrides in service_cases:
            with self.subTest(label=label):
                invoice = self.make_draft(**overrides)
                with self.assertRaises(SupplierInvoiceRegistrationValidationError):
                    register_supplier_invoice(invoice, db_session=db.session)
                db.session.rollback()

        database_cases = [
            ("usd", {"currency": "USD"}),
            ("foreign", {"supplier_country_code": "FR"}),
            ("aib", {"tax_treatment": "intra_community"}),
            ("isp", {"tax_treatment": "reverse_charge"}),
        ]
        for label, overrides in database_cases:
            with self.subTest(label=label):
                with self.assertRaises(IntegrityError):
                    self.make_draft(**overrides)
                db.session.rollback()

    def test_deductible_tax_cannot_exceed_supported_tax(self):
        with self.assertRaises(IntegrityError):
            self.make_draft(breakdowns=[("100.00", "21.00", "21.00", "21.01")])
            db.session.commit()
        db.session.rollback()

    def test_duplicate_requires_explicit_override_and_records_it_in_snapshot(self):
        first = self.make_draft()
        register_supplier_invoice(first, db_session=db.session, registered_at=datetime(2026, 8, 11, 10, 0, 0))
        db.session.commit()
        second = self.make_draft()

        with self.assertRaises(SupplierInvoiceDuplicateError):
            register_supplier_invoice(second, db_session=db.session)

        result = register_supplier_invoice(
            second,
            db_session=db.session,
            allow_duplicate=True,
            registered_at=datetime(2026, 8, 11, 11, 0, 0),
        )
        db.session.commit()

        self.assertTrue(result.duplicate_override_used)
        self.assertEqual(second.reception_number, 2)
        self.assertTrue(second.fiscal_snapshot["registration"]["duplicate_override_used"])

    def test_registered_constraint_requires_complete_snapshot(self):
        invoice = self.make_draft()
        invoice.status = SupplierInvoice.STATUS_REGISTERED
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_sales_models_are_not_part_of_the_supplier_registration_service(self):
        source = (SRC_DIR / "api/supplier_invoice_registration_service.py").read_text(encoding="utf-8")
        self.assertNotIn("Invoices", source)
        self.assertNotIn("AccountingEntry", source)


class SupplierInvoiceMigrationSourceTest(unittest.TestCase):
    def test_migration_creates_only_supplier_invoice_tables_and_sequence(self):
        source = MIGRATION_PATH.read_text(encoding="utf-8")
        self.assertIn('revision = "d2e3f4a5b6c7"', source)
        self.assertIn('down_revision = "c1d2e3f4a5b6"', source)
        self.assertIn('"supplier_invoices"', source)
        self.assertIn('"supplier_invoice_tax_breakdowns"', source)
        self.assertIn('"supplier_invoice_reception_sequences"', source)
        self.assertNotIn('"invoices",', source)
        self.assertNotIn('"accounting_entries"', source)


if __name__ == "__main__":
    unittest.main()

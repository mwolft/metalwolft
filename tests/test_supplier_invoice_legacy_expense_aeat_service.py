import copy
import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from api.supplier_invoice_legacy_expense_aeat_service import (  # noqa: E402
    LegacySupplierInvoiceExpenseAeatError,
    classify_legacy_supplier_invoice_expense_aeat,
    is_legacy_supplier_invoice_eligible_for_manual_classification,
    legacy_supplier_invoice_expense_data_for_export,
    legacy_supplier_invoice_expense_details,
)
from api.supplier_invoice_snapshot_integrity import calculate_supplier_invoice_snapshot_hash  # noqa: E402


class SupplierInvoiceLegacyExpenseAeatServiceTest(unittest.TestCase):
    def make_invoice(self, *, supplier_tax_id="B13019559", operation_date="2026-06-12", **overrides):
        snapshot = {
            "schema_version": 1,
            "supplier": {
                "legal_name": "Hierros y Aceros Ciudad Real, S.L.",
                "tax_id": supplier_tax_id,
                "country_code": "ES",
                "tax_id_type": "NIF",
            },
            "document": {
                "supplier_invoice_number": "HYA-2026-001",
                "reception_number": 1,
                "issue_date": "2026-06-12",
                "operation_date": operation_date,
                "concept": "Material",
                "currency": "EUR",
                "fiscal_invoice_type": "F1",
                "tax_treatment": "domestic_standard",
                "special_regime_key": None,
            },
            "tax_breakdowns": [{
                "position": 1,
                "tax_base": "35.76",
                "tax_rate": "21.00",
                "tax_amount": "7.51",
                "deductible_tax_amount": "7.51",
            }],
            "totals": {
                "tax_base": "35.76",
                "tax_amount": "7.51",
                "deductible_tax_amount": "7.51",
                "total_amount": "43.27",
            },
            "registration": {
                "registered_at": "2026-06-12T00:00:00",
                "registered_by": "admin",
                "source": "manual",
                "duplicate_override_used": False,
            },
        }
        invoice = SimpleNamespace(
            status="registered",
            snapshot_schema_version=1,
            fiscal_snapshot=snapshot,
            snapshot_hash=calculate_supplier_invoice_snapshot_hash(snapshot),
            reception_number=1,
            aeat_expense_concept_code=None,
            expense_deductible_amount=None,
            legacy_expense_received_at=None,
            legacy_expense_classified_at=None,
            legacy_expense_classified_by=None,
            received_at=datetime(2020, 1, 1),
        )
        for key, value in overrides.items():
            setattr(invoice, key, value)
        return invoice

    def test_details_propose_g01_deductible_base_and_issue_date(self):
        details = legacy_supplier_invoice_expense_details(self.make_invoice())
        self.assertEqual(details["proposed_expense_code"], "G01")
        self.assertEqual(details["proposed_expense_deductible_amount"], Decimal("35.76"))
        self.assertEqual(details["proposed_received_at"], date(2026, 6, 12))

    def test_details_propose_g03_for_other_national_supplier(self):
        details = legacy_supplier_invoice_expense_details(
            self.make_invoice(supplier_tax_id="B99999999")
        )
        self.assertEqual(details["proposed_expense_code"], "G03")

    def test_classification_persists_audit_without_mutating_snapshot_or_hash(self):
        invoice = self.make_invoice()
        original_snapshot = copy.deepcopy(invoice.fiscal_snapshot)
        original_hash = invoice.snapshot_hash

        classify_legacy_supplier_invoice_expense_aeat(
            invoice,
            aeat_expense_concept_code="G01",
            expense_deductible_amount="35.76",
            legacy_expense_received_at="2026-06-12",
            actor="flask_admin:admin",
            classified_at=datetime(2026, 8, 12, 10, 0, 0),
        )

        self.assertEqual(invoice.aeat_expense_concept_code, "G01")
        self.assertEqual(invoice.expense_deductible_amount, Decimal("35.76"))
        self.assertEqual(invoice.legacy_expense_received_at, date(2026, 6, 12))
        self.assertEqual(invoice.legacy_expense_classified_by, "flask_admin:admin")
        self.assertEqual(invoice.legacy_expense_classified_at, datetime(2026, 8, 12, 10, 0, 0))
        self.assertEqual(invoice.fiscal_snapshot, original_snapshot)
        self.assertEqual(invoice.snapshot_hash, original_hash)

    def test_existing_untraced_values_are_only_proposals(self):
        invoice = self.make_invoice(
            aeat_expense_concept_code="G01",
            expense_deductible_amount=Decimal("35.76"),
        )
        self.assertTrue(is_legacy_supplier_invoice_eligible_for_manual_classification(invoice))
        with self.assertRaisesRegex(LegacySupplierInvoiceExpenseAeatError, "requiere clasificaci"):
            legacy_supplier_invoice_expense_data_for_export(invoice, invoice.fiscal_snapshot)

    def test_invalid_hash_or_out_of_scope_v1_is_not_eligible(self):
        invalid_hash = self.make_invoice(snapshot_hash="0" * 64)
        self.assertFalse(is_legacy_supplier_invoice_eligible_for_manual_classification(invalid_hash))
        out_of_scope = self.make_invoice()
        out_of_scope.fiscal_snapshot["supplier"]["country_code"] = "FR"
        out_of_scope.snapshot_hash = calculate_supplier_invoice_snapshot_hash(out_of_scope.fiscal_snapshot)
        self.assertFalse(is_legacy_supplier_invoice_eligible_for_manual_classification(out_of_scope))

    def test_partial_audit_is_rejected(self):
        invoice = self.make_invoice(legacy_expense_classified_at=datetime(2026, 8, 12))
        self.assertFalse(is_legacy_supplier_invoice_eligible_for_manual_classification(invoice))
        with self.assertRaises(LegacySupplierInvoiceExpenseAeatError):
            legacy_supplier_invoice_expense_data_for_export(invoice, invoice.fiscal_snapshot)


if __name__ == "__main__":
    unittest.main()

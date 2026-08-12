import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from api.aeat_received_expense_ledger_service import (  # noqa: E402
    AEAT_RECEIVED_EXPENSE_LEDGER_COLUMN_KEYS,
    AeatReceivedExpenseLedgerValidationError,
    prepare_aeat_received_expense_ledger_rows,
)
from api.supplier_invoice_snapshot_integrity import (  # noqa: E402
    calculate_supplier_invoice_snapshot_hash,
)


class AeatReceivedExpenseLedgerServiceTest(unittest.TestCase):
    def make_invoice(self, **overrides):
        snapshot = {
            "schema_version": 2,
            "supplier": {
                "legal_name": "Hierros y Aceros Ciudad Real, S.L.",
                "tax_id": "B13019559",
                "country_code": "ES",
                "tax_id_type": "NIF",
            },
            "document": {
                "supplier_invoice_number": "HYACR-2026-001",
                "reception_number": 7,
                "issue_date": "2026-06-12",
                "operation_date": "2026-06-12",
                "received_at": "2026-06-12T00:00:00",
                "concept": None,
                "currency": "EUR",
                "fiscal_invoice_type": "F1",
                "tax_treatment": "domestic_standard",
                "special_regime_key": None,
            },
            "tax_breakdowns": [
                {
                    "position": 1,
                    "tax_base": "35.76",
                    "tax_rate": "21.00",
                    "tax_amount": "7.51",
                    "deductible_tax_amount": "7.51",
                }
            ],
            "totals": {
                "tax_base": "35.76",
                "tax_amount": "7.51",
                "deductible_tax_amount": "7.51",
                "total_amount": "43.27",
            },
            "expense_classification": {
                "aeat_expense_concept_code": "G01",
                "expense_deductible_amount": "35.76",
            },
            "registration": {
                "registered_at": "2026-06-12T00:00:00",
                "registered_by": "admin",
                "source": "manual",
                "duplicate_override_used": False,
            },
        }
        snapshot = overrides.pop("snapshot", snapshot)
        invoice = SimpleNamespace(
            status=overrides.pop("status", "registered"),
            snapshot_schema_version=overrides.pop("snapshot_schema_version", 2),
            fiscal_snapshot=snapshot,
            snapshot_hash=overrides.pop(
                "snapshot_hash", calculate_supplier_invoice_snapshot_hash(snapshot)
            ),
            reception_number=overrides.pop("reception_number", 7),
        )
        for key, value in overrides.items():
            setattr(invoice, key, value)
        return invoice

    def prepared_rows(self, **overrides):
        return prepare_aeat_received_expense_ledger_rows([self.make_invoice(**overrides)])

    def test_normal_national_invoice_builds_a_complete_internal_row(self):
        row = self.prepared_rows()[0]

        self.assertEqual(row["exercise"], 2026)
        self.assertEqual(row["period"], "2T")
        self.assertEqual(row["activity_code"], "A")
        self.assertEqual(row["activity_type"], "3")
        self.assertEqual(row["iae_code"], "3141")
        self.assertEqual(row["invoice_type"], "F1")
        self.assertEqual(row["expense_concept_code"], "G01")
        self.assertEqual(row["deductible_expense_amount"], Decimal("35.76"))
        self.assertEqual(row["issue_date"], date(2026, 6, 12))
        self.assertEqual(row["operation_date"], date(2026, 6, 12))
        self.assertEqual(row["received_date"], date(2026, 6, 12))
        self.assertEqual(row["supplier_tax_id"], "B13019559")
        self.assertEqual(row["supplier_legal_name"], "Hierros y Aceros Ciudad Real, S.L.")
        self.assertEqual(row["operation_key"], "01")
        self.assertEqual(row["total_amount"], Decimal("43.27"))
        self.assertEqual(row["tax_base"], Decimal("35.76"))
        self.assertEqual(row["tax_rate"], Decimal("21.00"))
        self.assertEqual(row["tax_amount"], Decimal("7.51"))
        self.assertEqual(row["deductible_tax_amount"], Decimal("7.51"))
        self.assertEqual(len(row), 42)
        self.assertEqual(tuple(row), AEAT_RECEIVED_EXPENSE_LEDGER_COLUMN_KEYS)
        for field in (
            "tax_id_type", "country_code", "investment_good", "reverse_charge",
            "deductible_later", "deduction_exercise", "deduction_period",
            "equivalence_surcharge_rate", "equivalence_surcharge_amount",
            "payment_date", "payment_amount", "payment_method", "payment_method_id",
            "withholding_type", "withholding_amount", "billing_agreement",
            "property_situation", "cadastral_reference", "external_reference",
        ):
            self.assertIsNone(row[field])

    def test_g03_is_preserved_from_the_snapshot(self):
        invoice = self.make_invoice()
        invoice.fiscal_snapshot["expense_classification"]["aeat_expense_concept_code"] = "G03"
        invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(invoice.fiscal_snapshot)

        self.assertEqual(
            prepare_aeat_received_expense_ledger_rows([invoice])[0]["expense_concept_code"],
            "G03",
        )

    def test_missing_operation_date_uses_the_frozen_issue_date(self):
        invoice = self.make_invoice()
        invoice.fiscal_snapshot["document"]["operation_date"] = None
        invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(invoice.fiscal_snapshot)

        row = prepare_aeat_received_expense_ledger_rows([invoice])[0]

        self.assertEqual(row["issue_date"], date(2026, 6, 12))
        self.assertEqual(row["operation_date"], date(2026, 6, 12))
        self.assertIsNone(invoice.fiscal_snapshot["document"]["operation_date"])

    def test_multiple_breakdowns_use_each_base_when_expense_equals_total_base(self):
        invoice = self.make_invoice()
        snapshot = invoice.fiscal_snapshot
        snapshot["tax_breakdowns"] = [
            {"position": 2, "tax_base": "20.00", "tax_rate": "21.00", "tax_amount": "4.20", "deductible_tax_amount": "4.20"},
            {"position": 1, "tax_base": "10.00", "tax_rate": "10.00", "tax_amount": "1.00", "deductible_tax_amount": "1.00"},
        ]
        snapshot["totals"] = {
            "tax_base": "30.00", "tax_amount": "5.20", "deductible_tax_amount": "5.20", "total_amount": "35.20"
        }
        snapshot["expense_classification"]["expense_deductible_amount"] = "30.00"
        invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(snapshot)

        rows = prepare_aeat_received_expense_ledger_rows([invoice])

        self.assertEqual(
            [row["deductible_expense_amount"] for row in rows],
            [Decimal("10.00"), Decimal("20.00")],
        )

    def test_multiple_breakdowns_with_adjusted_expense_are_rejected_without_proration(self):
        invoice = self.make_invoice()
        snapshot = invoice.fiscal_snapshot
        snapshot["tax_breakdowns"] = [
            {"position": 1, "tax_base": "20.00", "tax_rate": "21.00", "tax_amount": "4.20", "deductible_tax_amount": "4.20"},
            {"position": 2, "tax_base": "10.00", "tax_rate": "10.00", "tax_amount": "1.00", "deductible_tax_amount": "1.00"},
        ]
        snapshot["totals"] = {
            "tax_base": "30.00", "tax_amount": "5.20", "deductible_tax_amount": "5.20", "total_amount": "35.20"
        }
        snapshot["expense_classification"]["expense_deductible_amount"] = "29.00"
        invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(snapshot)

        with self.assertRaisesRegex(AeatReceivedExpenseLedgerValidationError, "No se puede repartir"):
            prepare_aeat_received_expense_ledger_rows([invoice])

    def test_v1_snapshot_is_rejected_with_reception_context(self):
        invoice = self.make_invoice(snapshot={"schema_version": 1}, snapshot_schema_version=1, reception_number=4)
        invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(invoice.fiscal_snapshot)

        with self.assertRaisesRegex(AeatReceivedExpenseLedgerValidationError, "numero de recepcion 4.*v1"):
            prepare_aeat_received_expense_ledger_rows([invoice])

    def test_altered_snapshot_hash_is_rejected(self):
        with self.assertRaisesRegex(AeatReceivedExpenseLedgerValidationError, "integridad"):
            self.prepared_rows(snapshot_hash="0" * 64)

    def test_out_of_scope_currency_and_tax_treatment_are_rejected(self):
        for field, value in (("currency", "USD"), ("tax_treatment", "intra_community")):
            with self.subTest(field=field):
                invoice = self.make_invoice()
                invoice.fiscal_snapshot["document"][field] = value
                invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(invoice.fiscal_snapshot)
                with self.assertRaises(AeatReceivedExpenseLedgerValidationError):
                    prepare_aeat_received_expense_ledger_rows([invoice])

    def test_unreconciled_snapshot_is_rejected(self):
        invoice = self.make_invoice()
        invoice.fiscal_snapshot["totals"]["tax_amount"] = "7.50"
        invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(invoice.fiscal_snapshot)

        with self.assertRaisesRegex(AeatReceivedExpenseLedgerValidationError, "no reconcilian"):
            prepare_aeat_received_expense_ledger_rows([invoice])

    def test_invalid_aeat_lengths_are_rejected_without_truncation(self):
        invoice = self.make_invoice()
        invoice.fiscal_snapshot["supplier"]["legal_name"] = "X" * 121
        invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(invoice.fiscal_snapshot)

        with self.assertRaisesRegex(AeatReceivedExpenseLedgerValidationError, "longitud maxima"):
            prepare_aeat_received_expense_ledger_rows([invoice])

    def test_period_is_derived_from_frozen_received_at(self):
        invoice = self.make_invoice()
        invoice.fiscal_snapshot["document"]["received_at"] = "2026-11-30T12:00:00"
        invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(invoice.fiscal_snapshot)

        row = prepare_aeat_received_expense_ledger_rows([invoice])[0]
        self.assertEqual(row["exercise"], 2026)
        self.assertEqual(row["period"], "4T")


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from api.aeat_received_expense_ledger_service import (  # noqa: E402
    AeatReceivedExpenseLedgerValidationError,
)
from api.aeat_received_expense_ledger_xlsx_service import (  # noqa: E402
    AEAT_RECEIVED_EXPENSE_LEDGER_SHEET_NAME,
    export_aeat_received_expense_ledger,
    generate_aeat_received_expense_ledger_workbook,
)
from api.supplier_invoice_snapshot_integrity import (  # noqa: E402
    calculate_supplier_invoice_snapshot_hash,
)


class AeatReceivedExpenseLedgerXlsxServiceTest(unittest.TestCase):
    def make_invoice(self, *, received_at="2026-06-12T00:00:00", reception_number=7, **overrides):
        snapshot = {
            "schema_version": 2,
            "supplier": {
                "legal_name": "Hierros y Aceros Ciudad Real, S.L.",
                "tax_id": "B13019559",
                "country_code": "ES",
                "tax_id_type": "NIF",
            },
            "document": {
                "supplier_invoice_number": f"HYA-{reception_number}",
                "reception_number": reception_number,
                "issue_date": received_at[:10],
                "operation_date": received_at[:10],
                "received_at": received_at,
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
                "registered_at": received_at,
                "registered_by": "admin",
                "source": "manual",
                "duplicate_override_used": False,
            },
        }
        snapshot = overrides.pop("snapshot", snapshot)
        return SimpleNamespace(
            status=overrides.pop("status", "registered"),
            snapshot_schema_version=overrides.pop("snapshot_schema_version", 2),
            fiscal_snapshot=snapshot,
            snapshot_hash=overrides.pop(
                "snapshot_hash", calculate_supplier_invoice_snapshot_hash(snapshot)
            ),
            reception_number=reception_number,
        )

    def test_workbook_uses_exact_sheet_headers_types_and_empty_cells(self):
        workbook, rows = generate_aeat_received_expense_ledger_workbook(
            [self.make_invoice()], year=2026, period="2T"
        )
        worksheet = workbook[AEAT_RECEIVED_EXPENSE_LEDGER_SHEET_NAME]

        self.assertEqual(workbook.sheetnames, ["RECIBIDAS_GASTOS"])
        self.assertEqual(worksheet.max_column, 42)
        self.assertEqual(worksheet.max_row, 3)
        self.assertEqual(worksheet.freeze_panes, "A3")
        self.assertEqual(worksheet["A2"].value, "Ejercicio")
        self.assertEqual(worksheet["A3"].value, 2026)
        self.assertEqual(worksheet["I3"].value.isoformat(), "2026-06-12")
        self.assertEqual(worksheet["I3"].number_format, "dd/mm/yyyy")
        self.assertEqual(worksheet["Z3"].value, Decimal("43.27"))
        self.assertEqual(worksheet["Z3"].number_format, "#,##0.00")
        self.assertEqual(worksheet["AB3"].value, 21)
        self.assertEqual(worksheet["AB3"].number_format, "0.00")
        self.assertIsNone(worksheet["P3"].value)
        self.assertIsNone(worksheet["Q3"].value)
        self.assertEqual(len(rows), 1)

        output = BytesIO()
        workbook.save(output)
        self.assertGreater(len(output.getvalue()), 0)

    def test_period_selection_is_cumulative_and_excludes_other_years(self):
        invoices = [
            self.make_invoice(received_at="2026-02-01T00:00:00", reception_number=1),
            self.make_invoice(received_at="2026-05-01T00:00:00", reception_number=2),
            self.make_invoice(received_at="2026-08-01T00:00:00", reception_number=3),
            self.make_invoice(received_at="2026-11-01T00:00:00", reception_number=4),
            self.make_invoice(received_at="2025-11-01T00:00:00", reception_number=5),
        ]

        expected = {
            "1T": [1],
            "2T": [1, 2],
            "3T": [1, 2, 3],
            "4T": [1, 2, 3, 4],
        }
        for period, receptions in expected.items():
            with self.subTest(period=period):
                _, rows = generate_aeat_received_expense_ledger_workbook(
                    invoices, year=2026, period=period
                )
                self.assertEqual([row["reception_number"] for row in rows], receptions)

    def test_multiple_vat_breakdowns_write_multiple_rows(self):
        invoice = self.make_invoice()
        snapshot = invoice.fiscal_snapshot
        snapshot["tax_breakdowns"] = [
            {"position": 1, "tax_base": "10.00", "tax_rate": "10.00", "tax_amount": "1.00", "deductible_tax_amount": "1.00"},
            {"position": 2, "tax_base": "20.00", "tax_rate": "21.00", "tax_amount": "4.20", "deductible_tax_amount": "4.20"},
        ]
        snapshot["totals"] = {
            "tax_base": "30.00", "tax_amount": "5.20", "deductible_tax_amount": "5.20", "total_amount": "35.20"
        }
        snapshot["expense_classification"]["expense_deductible_amount"] = "30.00"
        invoice.snapshot_hash = calculate_supplier_invoice_snapshot_hash(snapshot)

        workbook, rows = generate_aeat_received_expense_ledger_workbook(
            [invoice], year=2026, period="2T"
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(workbook.active.max_row, 4)
        self.assertEqual(
            [row["total_amount"] for row in rows],
            [Decimal("11.00"), Decimal("24.20")],
        )

    def test_preparation_error_prevents_writing_a_workbook(self):
        invoice = self.make_invoice(snapshot_hash="0" * 64)
        output_path = ROOT_DIR / f"recibidas-invalid-{uuid4()}.xlsx"
        with self.assertRaises(AeatReceivedExpenseLedgerValidationError):
            export_aeat_received_expense_ledger(
                [invoice],
                year=2026,
                period="2T",
                output_path=output_path,
            )
        self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()

import copy
import shutil
import sys
import unittest
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from api.aeat_sales_ledger_service import (  # noqa: E402
    AEAT_HEADER_ROW_1,
    AEAT_HEADER_ROW_2,
    AEAT_SALES_LEDGER_SHEET_NAME,
    DATE_FORMAT,
    MONEY_FORMAT,
    AeatSalesLedgerValidationError,
    AeatSalesLedgerWriteError,
    export_aeat_sales_ledger,
    generate_aeat_sales_ledger_workbook,
)
from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash  # noqa: E402


TEST_TMP_ROOT = ROOT_DIR / "tmp-aeat-sales-ledger-tests"


@dataclass
class InvoiceDouble:
    id: int
    invoice_number: str
    invoice_snapshot: dict | None
    invoice_snapshot_hash: str | None
    issued_at: datetime | None = datetime(2026, 7, 18, 10, 0, 0)
    invoice_type: str | None = "ordinary"

    @property
    def order(self):
        raise AssertionError("AEAT ledger must not read live order data")

    @property
    def user(self):
        raise AssertionError("AEAT ledger must not read live user data")

    @property
    def checkout_session(self):
        raise AssertionError("AEAT ledger must not read live checkout data")


@dataclass
class AccountingEntryDouble:
    id: int
    invoice_date: date
    invoice_number: str
    invoice: InvoiceDouble
    entry_type: str = "sale"
    currency: str = "EUR"
    customer_name: str = "Projection Customer"
    customer_tax_id: str | None = "PROJECTION-TAX"
    taxable_base: Decimal = Decimal("100.00")
    vat_amount: Decimal = Decimal("21.00")
    total_amount: Decimal = Decimal("121.00")
    payment_provider: str | None = "stripe"
    order_id: int | None = 123
    status: str = "pending"

    @property
    def order(self):
        raise AssertionError("AEAT ledger must not read live order relationship")

    @property
    def user(self):
        raise AssertionError("AEAT ledger must not read live user relationship")

    @property
    def checkout_session(self):
        raise AssertionError("AEAT ledger must not read live checkout relationship")


@contextmanager
def temp_export_dir():
    TEST_TMP_ROOT.mkdir(exist_ok=True)
    case_dir = TEST_TMP_ROOT / f"case-{uuid.uuid4().hex}"
    case_dir.mkdir()
    try:
        yield case_dir
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def tearDownModule():
    shutil.rmtree(TEST_TMP_ROOT, ignore_errors=True)


def snapshot(**overrides):
    data = {
        "schema_version": 1,
        "metadata": {"generator": "invoice_snapshot_builder_v1"},
        "issuer": {
            "legal_name": "MetalWolft",
            "tax_id": "B00000000",
            "country_code": "ES",
        },
        "customer": {
            "legal_name": "Cliente Fiscal",
            "tax_id": "00000000T",
            "country_code": "ES",
        },
        "operation": {
            "invoice_type": "ordinary",
            "issue_date": "2026-07-18",
            "operation_date": "2026-07-17",
            "currency": "EUR",
            "order_id": 42,
        },
        "lines": [
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
        "payment": {"provider": "stripe"},
        "references": {"order_id": 42},
    }
    data.update(overrides)
    return data


def invoice(*, invoice_number="F2026000001", invoice_snapshot=None, stored_hash=None):
    fiscal_snapshot = snapshot() if invoice_snapshot is None else invoice_snapshot
    return InvoiceDouble(
        id=1,
        invoice_number=invoice_number,
        invoice_snapshot=fiscal_snapshot,
        invoice_snapshot_hash=stored_hash or (
            calculate_invoice_snapshot_hash(fiscal_snapshot)
            if isinstance(fiscal_snapshot, dict)
            else None
        ),
    )


def entry(**overrides):
    data = {
        "id": 1,
        "invoice_date": date(2026, 7, 18),
        "invoice_number": "F2026000001",
        "invoice": invoice(),
    }
    data.update(overrides)
    return AccountingEntryDouble(**data)


def export_and_open(entries, path):
    result = export_aeat_sales_ledger(entries, output_path=path)
    workbook = load_workbook(path, data_only=True)
    return result, workbook


def normalized_header(header):
    return [value or None for value in header]


class AeatSalesLedgerServiceTest(unittest.TestCase):
    def test_valid_export_creates_sheet_headers_and_single_row(self):
        with temp_export_dir() as tmpdir:
            result, workbook = export_and_open([entry()], tmpdir / "aeat.xlsx")
            sheet = workbook[AEAT_SALES_LEDGER_SHEET_NAME]

            self.assertEqual(result.filename, "aeat.xlsx")
            self.assertEqual(result.row_count, 1)
            self.assertGreater(result.file_size, 0)
            self.assertEqual(sheet.max_column, 36)
            self.assertEqual([cell.value for cell in sheet[1]], normalized_header(AEAT_HEADER_ROW_1))
            self.assertEqual([cell.value for cell in sheet[2]], normalized_header(AEAT_HEADER_ROW_2))

    def test_row_mapping_matches_aeat_sales_ledger_v1(self):
        with temp_export_dir() as tmpdir:
            _, workbook = export_and_open([entry()], tmpdir / "aeat.xlsx")
            sheet = workbook[AEAT_SALES_LEDGER_SHEET_NAME]

            self.assertEqual(sheet["A3"].value, 2026)
            self.assertEqual(sheet["B3"].value, "3T")
            self.assertEqual(sheet["C3"].value, "A")
            self.assertEqual(sheet["D3"].value, "3")
            self.assertEqual(sheet["E3"].value, "3141")
            self.assertEqual(sheet["F3"].value, "F1")
            self.assertEqual(sheet["G3"].value, "I01")
            self.assertEqual(sheet["H3"].value, Decimal("100.00"))
            self.assertEqual(sheet["I3"].value.date(), date(2026, 7, 18))
            self.assertEqual(sheet["J3"].value.date(), date(2026, 7, 17))
            self.assertIsNone(sheet["K3"].value)
            self.assertEqual(sheet["L3"].value, "F2026000001")
            self.assertIsNone(sheet["M3"].value)
            self.assertEqual(sheet["N3"].value, "4")
            self.assertEqual(sheet["O3"].value, "ES")
            self.assertEqual(sheet["P3"].value, "00000000T")
            self.assertEqual(sheet["Q3"].value, "Cliente Fiscal")
            self.assertEqual(sheet["R3"].value, "1")
            self.assertEqual(sheet["S3"].value, "S1")
            self.assertIsNone(sheet["T3"].value)
            self.assertEqual(sheet["U3"].value, Decimal("121.00"))
            self.assertEqual(sheet["V3"].value, Decimal("100.00"))
            self.assertEqual(sheet["W3"].value, Decimal("21.00"))
            self.assertEqual(sheet["X3"].value, Decimal("21.00"))
            self.assertEqual(sheet["AJ3"].value, "order:42")

    def test_dates_amounts_formats_filter_and_freeze_panes_are_configured(self):
        with temp_export_dir() as tmpdir:
            _, workbook = export_and_open([entry()], tmpdir / "aeat.xlsx")
            sheet = workbook[AEAT_SALES_LEDGER_SHEET_NAME]

            self.assertEqual(sheet["I3"].number_format, DATE_FORMAT)
            self.assertEqual(sheet["J3"].number_format, DATE_FORMAT)
            self.assertEqual(sheet["H3"].number_format, MONEY_FORMAT)
            self.assertEqual(sheet["U3"].number_format, MONEY_FORMAT)
            self.assertEqual(sheet["V3"].number_format, MONEY_FORMAT)
            self.assertEqual(sheet["X3"].number_format, MONEY_FORMAT)
            self.assertEqual(sheet.freeze_panes, "A3")
            self.assertEqual(sheet.auto_filter.ref, "A2:AJ3")
            self.assertTrue(all(cell.font.bold for cell in sheet[1]))
            self.assertTrue(all(cell.font.bold for cell in sheet[2]))

    def test_rows_are_sorted_deterministically(self):
        entries = [
            entry(
                id=3,
                invoice_number="F2026000003",
                invoice=invoice(invoice_number="F2026000003"),
            ),
            entry(
                id=2,
                invoice_number="F2026000002",
                invoice=invoice(
                    invoice_number="F2026000002",
                    invoice_snapshot=snapshot(operation={**snapshot()["operation"], "issue_date": "2026-07-17"}),
                ),
            ),
            entry(id=1),
        ]

        with temp_export_dir() as tmpdir:
            _, workbook = export_and_open(entries, tmpdir / "aeat.xlsx")
            sheet = workbook[AEAT_SALES_LEDGER_SHEET_NAME]

            self.assertEqual(
                [sheet.cell(row=row, column=12).value for row in range(3, 6)],
                ["F2026000002", "F2026000001", "F2026000003"],
            )

    def test_generate_workbook_public_helper_does_not_write_file(self):
        workbook = generate_aeat_sales_ledger_workbook([entry()])

        self.assertEqual(workbook.sheetnames, [AEAT_SALES_LEDGER_SHEET_NAME])

    def test_existing_file_without_overwrite_is_rejected(self):
        with temp_export_dir() as tmpdir:
            output_path = tmpdir / "aeat.xlsx"
            output_path.write_bytes(b"existing")

            with self.assertRaises(AeatSalesLedgerWriteError):
                export_aeat_sales_ledger([entry()], output_path=output_path)

            self.assertEqual(output_path.read_bytes(), b"existing")

    def test_overwrite_is_allowed_explicitly(self):
        with temp_export_dir() as tmpdir:
            output_path = tmpdir / "aeat.xlsx"
            output_path.write_bytes(b"existing")

            result = export_aeat_sales_ledger(
                [entry()],
                output_path=output_path,
                overwrite=True,
            )

            self.assertGreater(result.file_size, len(b"existing"))
            self.assertEqual(load_workbook(output_path).sheetnames, [AEAT_SALES_LEDGER_SHEET_NAME])

    def test_invalid_output_path_and_empty_entries_are_rejected(self):
        with temp_export_dir() as tmpdir:
            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger([entry()], output_path=tmpdir / "aeat.xls")
            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger([entry()], output_path="../aeat.xlsx")
            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger([], output_path=tmpdir / "aeat.xlsx")

    def test_legacy_invoice_without_snapshot_is_rejected(self):
        with temp_export_dir() as tmpdir:
            legacy_invoice = InvoiceDouble(
                id=1,
                invoice_number="F2026000001",
                invoice_snapshot=None,
                invoice_snapshot_hash=None,
            )
            legacy_entry = entry(invoice=legacy_invoice)

            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger([legacy_entry], output_path=tmpdir / "aeat.xlsx")

    def test_hash_mismatch_is_rejected(self):
        with temp_export_dir() as tmpdir:
            bad_entry = entry(invoice=invoice(stored_hash="bad-hash"))

            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger([bad_entry], output_path=tmpdir / "aeat.xlsx")

    def test_unsupported_schema_and_corrective_invoice_are_rejected(self):
        with temp_export_dir() as tmpdir:
            unsupported = snapshot(schema_version=999)
            unsupported_entry = entry(invoice=invoice(invoice_snapshot=unsupported))
            corrective_snapshot = snapshot(
                operation={**snapshot()["operation"], "invoice_type": "corrective"}
            )
            corrective_entry = entry(invoice=invoice(invoice_snapshot=corrective_snapshot))

            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger([unsupported_entry], output_path=tmpdir / "unsupported.xlsx")
            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger([corrective_entry], output_path=tmpdir / "corrective.xlsx")

    def test_non_sale_non_eur_and_missing_tax_id_are_rejected(self):
        with temp_export_dir() as tmpdir:
            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger([entry(entry_type="purchase")], output_path=tmpdir / "type.xlsx")
            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger([entry(currency="USD")], output_path=tmpdir / "currency.xlsx")
            without_tax_id = snapshot(customer={**snapshot()["customer"], "tax_id": None})
            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger(
                    [entry(invoice=invoice(invoice_snapshot=without_tax_id))],
                    output_path=tmpdir / "tax-id.xlsx",
                )

    def test_projection_mismatch_is_rejected(self):
        with temp_export_dir() as tmpdir:
            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger(
                    [entry(total_amount=Decimal("120.99"))],
                    output_path=tmpdir / "amount.xlsx",
                )
            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger(
                    [entry(invoice_number="F2026000099")],
                    output_path=tmpdir / "number.xlsx",
                )

    def test_multiple_vat_rates_are_rejected(self):
        with temp_export_dir() as tmpdir:
            multi_rate = snapshot(
                lines=[
                    {**snapshot()["lines"][0], "tax_rate": "21.00"},
                    {**snapshot()["lines"][0], "line_number": 2, "tax_rate": "10.00"},
                ]
            )

            with self.assertRaises(AeatSalesLedgerValidationError):
                export_aeat_sales_ledger(
                    [entry(invoice=invoice(invoice_snapshot=multi_rate))],
                    output_path=tmpdir / "aeat.xlsx",
                )

    def test_operation_date_falls_back_to_snapshot_issue_date(self):
        operation = copy.deepcopy(snapshot()["operation"])
        operation.pop("operation_date")
        fallback_snapshot = snapshot(operation=operation)

        with temp_export_dir() as tmpdir:
            _, workbook = export_and_open(
                [entry(invoice=invoice(invoice_snapshot=fallback_snapshot))],
                tmpdir / "aeat.xlsx",
            )
            sheet = workbook[AEAT_SALES_LEDGER_SHEET_NAME]

            self.assertEqual(sheet["J3"].value.date(), date(2026, 7, 18))

    def test_export_does_not_mutate_entries_or_invoice_snapshot(self):
        invoice_double = invoice()
        before_snapshot = copy.deepcopy(invoice_double.invoice_snapshot)
        accounting_entry = entry(invoice=invoice_double)

        with temp_export_dir() as tmpdir:
            export_aeat_sales_ledger([accounting_entry], output_path=tmpdir / "aeat.xlsx")

        self.assertEqual(invoice_double.invoice_snapshot, before_snapshot)
        self.assertEqual(accounting_entry.status, "pending")


if __name__ == "__main__":
    unittest.main()

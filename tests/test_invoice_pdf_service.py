import copy
import re
import shutil
import sys
import unittest
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
TEST_TMP_ROOT = ROOT_DIR / ".tmp-invoice-pdf-tests"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.invoice_pdf_service import (  # noqa: E402
    InvoicePdfIntegrityError,
    InvoicePdfSnapshotMissing,
    InvoicePdfUnsupportedSchema,
    InvoicePdfWriteError,
    generate_invoice_pdf,
)
from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash  # noqa: E402


def snapshot(overrides=None):
    data = {
        "schema_version": 1,
        "metadata": {
            "generator": "invoice_snapshot_builder_v1",
            "generated_at": "2026-07-15T10:00:00+00:00",
        },
        "issuer": {
            "legal_name": "MetalWolft Legal",
            "trade_name": "MetalWolft",
            "tax_id": "B00000000",
            "address": "Calle Taller 1",
            "postal_code": "13000",
            "city": "Ciudad Real",
            "province": "Ciudad Real",
            "country_code": "ES",
            "email": "admin@metalwolft.com",
            "phone": "600111222",
        },
        "customer": {
            "legal_name": "Sergio Arias",
            "tax_id": "00000000T",
            "address": "Calle Factura 3",
            "postal_code": "13001",
            "city": "Ciudad Real",
            "province": "Ciudad Real",
            "country_code": "ES",
            "email": "cliente@example.com",
            "phone": "600000000",
        },
        "operation": {
            "invoice_type": "ordinary",
            "issue_date": "2026-07-16",
            "operation_date": "2026-07-15",
            "currency": "EUR",
            "order_id": 123,
            "order_locator": "AB1234",
            "order_date": "2026-07-15",
            "discount_code": "REJAS10",
        },
        "lines": [
            {
                "line_number": 1,
                "line_type": "product",
                "product_id": 7,
                "model": "Reja fija Pittsburgh",
                "description": "Reja fija Pittsburgh",
                "quantity": "1",
                "unit_amount_before_discount": "95.00",
                "line_amount_before_discount": "95.00",
                "discount_amount": "9.50",
                "line_total": "85.50",
                "tax_rate": "21.00",
                "tax_base": "70.66",
                "tax_amount": "14.84",
                "configuration": {
                    "height_cm": "30",
                    "width_cm": "30",
                    "anchoring": "Sin obra: con agujeros interiores",
                    "color": "satinado_blanco",
                },
            },
            {
                "line_number": 2,
                "line_type": "shipping",
                "product_id": None,
                "model": None,
                "description": "Gastos de envío",
                "quantity": "1",
                "unit_amount_before_discount": "21.00",
                "line_amount_before_discount": "21.00",
                "discount_amount": "2.10",
                "line_total": "18.90",
                "tax_rate": "21.00",
                "tax_base": "15.62",
                "tax_amount": "3.28",
                "configuration": None,
            },
        ],
        "totals": {
            "products_amount_before_discount": "95.00",
            "shipping_amount_before_discount": "21.00",
            "total_amount_before_discount": "116.00",
            "discount_amount": "11.60",
            "total_amount": "104.40",
            "tax_base": "86.28",
            "tax_amount": "18.12",
            "rounding_adjustment": "0.00",
        },
        "payment": {
            "provider": "stripe",
            "provider_reference": "pi_secret_full_reference_123",
            "status": "paid",
            "paid_at": None,
        },
        "references": {
            "checkout_session_id": 10,
            "order_id": 123,
            "source": "manual",
            "actor": {"email": "admin@example.com"},
        },
    }
    data.update(overrides or {})
    return data


class SnapshotOnlyInvoice:
    def __init__(self, invoice_number="F2026000001", invoice_snapshot=None, stored_hash=None):
        self.invoice_number = invoice_number
        self.issued_at = datetime(2026, 7, 16, 9, 30)
        self.invoice_snapshot = invoice_snapshot if invoice_snapshot is not None else snapshot()
        self.invoice_snapshot_hash = stored_hash or calculate_invoice_snapshot_hash(self.invoice_snapshot)
        self.pdf_path = None
        self.commit_called = False

    @property
    def order(self):
        raise AssertionError("Renderer v2 must not read order")

    @property
    def order_details(self):
        raise AssertionError("Renderer v2 must not read order_details")

    @property
    def product(self):
        raise AssertionError("Renderer v2 must not read product")

    @property
    def checkout_session(self):
        raise AssertionError("Renderer v2 must not read checkout_session")

    def commit(self):
        self.commit_called = True


def pdf_text(path):
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def normalized_pdf_text(path):
    return re.sub(r"\s+", " ", pdf_text(path))


@contextmanager
def temp_invoice_dir():
    TEST_TMP_ROOT.mkdir(exist_ok=True)
    case_dir = TEST_TMP_ROOT / f"case-{uuid.uuid4().hex}"
    case_dir.mkdir()
    try:
        yield str(case_dir)
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def tearDownModule():
    shutil.rmtree(TEST_TMP_ROOT, ignore_errors=True)


class InvoicePdfServiceTest(unittest.TestCase):
    def test_generates_valid_pdf_from_snapshot_and_updates_pdf_path(self):
        invoice = SnapshotOnlyInvoice()

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            output_path = Path(tmpdir) / result.filename

            self.assertTrue(output_path.exists())
            self.assertGreater(result.file_size, 1000)
            self.assertEqual(result.filename, "invoice_F2026000001.pdf")
            self.assertEqual(result.pdf_path, "/api/download-invoice/invoice_F2026000001.pdf")
            self.assertEqual(invoice.pdf_path, result.pdf_path)
            self.assertTrue(output_path.read_bytes().startswith(b"%PDF"))

    def test_pdf_text_includes_invoice_number_issuer_customer_lines_shipping_discount_and_totals(self):
        invoice = SnapshotOnlyInvoice()

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            text = normalized_pdf_text(Path(tmpdir) / result.filename)

        for expected in (
            "MetalWolft",
            "F2026000001",
            "MetalWolft Legal",
            "B00000000",
            "Sergio Arias",
            "00000000T",
            "AB1234",
            "Reja fija Pittsburgh",
            "Sin obra: con agujeros interiores",
            "satinado blanco",
            "Gastos de",
            "Descuento",
            "Base imponible",
            "IVA 21",
            "104.40 EUR",
            "EUR",
        ):
            self.assertIn(expected, text)

    def test_pdf_does_not_include_full_payment_reference(self):
        invoice = SnapshotOnlyInvoice()

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            text = pdf_text(Path(tmpdir) / result.filename)

        self.assertNotIn("pi_secret_full_reference_123", text)
        self.assertNotIn("stripe", text.lower())

    def test_does_not_query_live_relations(self):
        invoice = SnapshotOnlyInvoice()

        with temp_invoice_dir() as tmpdir:
            generate_invoice_pdf(invoice, output_dir=tmpdir)

    def test_historical_snapshot_with_null_tax_id_remains_readable(self):
        historical_snapshot = snapshot()
        historical_snapshot["customer"] = {
            **historical_snapshot["customer"],
            "tax_id": None,
        }
        invoice = SnapshotOnlyInvoice(
            invoice_snapshot=historical_snapshot,
            stored_hash=calculate_invoice_snapshot_hash(historical_snapshot),
        )

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            text = normalized_pdf_text(Path(tmpdir) / result.filename)

        self.assertIn("Sergio Arias", text)

    def test_missing_invoice_or_snapshot_fails(self):
        with temp_invoice_dir() as tmpdir:
            with self.assertRaises(InvoicePdfSnapshotMissing):
                generate_invoice_pdf(None, output_dir=tmpdir)

            invoice = SnapshotOnlyInvoice(invoice_snapshot=None)
            invoice.invoice_snapshot = None
            with self.assertRaises(InvoicePdfSnapshotMissing):
                generate_invoice_pdf(invoice, output_dir=tmpdir)

    def test_hash_mismatch_fails_without_generating_pdf(self):
        invoice = SnapshotOnlyInvoice(stored_hash="bad-hash")

        with temp_invoice_dir() as tmpdir:
            with self.assertRaises(InvoicePdfIntegrityError):
                generate_invoice_pdf(invoice, output_dir=tmpdir)
            self.assertEqual(list(Path(tmpdir).iterdir()), [])

    def test_unsupported_schema_fails(self):
        invalid_snapshot = snapshot({"schema_version": 999})
        invoice = SnapshotOnlyInvoice(
            invoice_snapshot=invalid_snapshot,
            stored_hash=calculate_invoice_snapshot_hash(invalid_snapshot),
        )

        with temp_invoice_dir() as tmpdir:
            with self.assertRaises(InvoicePdfUnsupportedSchema):
                generate_invoice_pdf(invoice, output_dir=tmpdir)

    def test_filename_is_sanitized_and_path_traversal_is_impossible(self):
        invoice = SnapshotOnlyInvoice(invoice_number="../F2026/000001")

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)

            self.assertEqual(result.filename, "invoice_F2026_000001.pdf")
            self.assertEqual(Path(tmpdir, result.filename).parent.resolve(), Path(tmpdir).resolve())
            self.assertTrue(Path(tmpdir, result.filename).exists())

    def test_service_does_not_commit_or_change_fiscal_data(self):
        invoice = SnapshotOnlyInvoice()
        original_snapshot = copy.deepcopy(invoice.invoice_snapshot)
        original_hash = invoice.invoice_snapshot_hash
        original_number = invoice.invoice_number

        with temp_invoice_dir() as tmpdir:
            generate_invoice_pdf(invoice, output_dir=tmpdir)

        self.assertEqual(invoice.invoice_snapshot, original_snapshot)
        self.assertEqual(invoice.invoice_snapshot_hash, original_hash)
        self.assertEqual(invoice.invoice_number, original_number)
        self.assertFalse(invoice.commit_called)

    def test_second_run_returns_existing_file_without_rewriting(self):
        invoice = SnapshotOnlyInvoice()

        with temp_invoice_dir() as tmpdir:
            first = generate_invoice_pdf(invoice, output_dir=tmpdir)
            output_path = Path(tmpdir) / first.filename
            first_mtime = output_path.stat().st_mtime_ns
            second = generate_invoice_pdf(invoice, output_dir=tmpdir)

            self.assertEqual(first.filename, second.filename)
            self.assertEqual(first.pdf_path, second.pdf_path)
            self.assertEqual(first.file_size, second.file_size)
            self.assertEqual(output_path.stat().st_mtime_ns, first_mtime)

    def test_existing_unreferenced_file_is_not_overwritten(self):
        invoice = SnapshotOnlyInvoice()

        with temp_invoice_dir() as tmpdir:
            existing_path = Path(tmpdir) / "invoice_F2026000001.pdf"
            existing_path.write_bytes(b"existing")

            with self.assertRaises(InvoicePdfWriteError):
                generate_invoice_pdf(invoice, output_dir=tmpdir)
            self.assertEqual(existing_path.read_bytes(), b"existing")

    def test_regenerate_explicitly_overwrites_existing_referenced_file(self):
        invoice = SnapshotOnlyInvoice()

        with temp_invoice_dir() as tmpdir:
            first = generate_invoice_pdf(invoice, output_dir=tmpdir)
            output_path = Path(tmpdir) / first.filename
            output_path.write_bytes(b"stale")
            result = generate_invoice_pdf(invoice, output_dir=tmpdir, regenerate=True)

            self.assertGreater(result.file_size, len(b"stale"))
            self.assertTrue(output_path.read_bytes().startswith(b"%PDF"))

    def test_write_error_is_sanitized(self):
        invoice = SnapshotOnlyInvoice()

        with temp_invoice_dir() as tmpdir:
            file_as_output_dir = Path(tmpdir) / "not-a-directory"
            file_as_output_dir.write_text("x", encoding="utf-8")

            with self.assertRaisesRegex(InvoicePdfWriteError, "No se pudo escribir"):
                generate_invoice_pdf(invoice, output_dir=file_as_output_dir)

    def test_source_stays_snapshot_only_and_avoids_side_effects(self):
        source = (SRC_DIR / "api/invoice_pdf_service.py").read_text(encoding="utf-8")

        for forbidden in (
            "Orders",
            "OrderDetails",
            "Products",
            "CheckoutSessions",
            "invoice.order",
            "invoice.order_details",
            "invoice.product",
            "invoice.checkout_session",
            "query",
            "db.session",
            ".commit(",
            "send_email",
            "render_original_order_invoice_pdf",
            "VeriFactu",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

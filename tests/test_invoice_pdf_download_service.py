from types import SimpleNamespace
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.invoice_pdf_download_service import (  # noqa: E402
    InvoicePdfDownloadFileMissing,
    InvoicePdfDownloadInvalidPath,
    InvoicePdfDownloadUnavailable,
    resolve_invoice_pdf_download,
)


class InvoicePdfDownloadServiceTest(unittest.TestCase):
    def test_resolves_existing_internal_url_inside_allowed_directory(self):
        invoice = SimpleNamespace(
            invoice_number="F-2026/000001",
            pdf_path="/api/download-invoice/invoice_F2026000001.pdf",
        )

        with patch("api.invoice_pdf_download_service.os.path.isfile", return_value=True):
            result = resolve_invoice_pdf_download(invoice, "C:/metalwolft/invoices")

        self.assertEqual(result.filename, "invoice_F2026000001.pdf")
        self.assertEqual(result.download_name, "factura_F-2026_000001.pdf")
        self.assertNotIn("/api/download-invoice", result.file_path)

    def test_accepts_safe_simple_filename_with_spaces_unicode_and_uppercase_extension(self):
        invoice = SimpleNamespace(
            invoice_number="Factura Nº 1",
            pdf_path="Factura Cliente Álvarez.PDF",
        )

        with patch("api.invoice_pdf_download_service.os.path.isfile", return_value=True):
            result = resolve_invoice_pdf_download(invoice, "/var/app/invoices")

        self.assertEqual(result.filename, "Factura Cliente Álvarez.PDF")
        self.assertEqual(result.download_name, "factura_Factura_N_1.pdf")

    def test_rejects_missing_pdf_reference(self):
        invoice = SimpleNamespace(invoice_number="F2026000001", pdf_path=None)

        with self.assertRaises(InvoicePdfDownloadUnavailable):
            resolve_invoice_pdf_download(invoice, "invoices")

    def test_rejects_missing_invoice_folder(self):
        invoice = SimpleNamespace(
            invoice_number="F2026000001",
            pdf_path="/api/download-invoice/invoice.pdf",
        )

        with self.assertRaises(InvoicePdfDownloadInvalidPath):
            resolve_invoice_pdf_download(invoice, "")

    def test_rejects_invalid_or_external_paths(self):
        unsafe_paths = (
            "../archivo.pdf",
            "..\\archivo.pdf",
            "/tmp/archivo.pdf",
            "C:\\facturas\\archivo.pdf",
            "https://example.com/archivo.pdf",
            "/api/download-invoice/../archivo.pdf",
            "/api/download-invoice/..\\archivo.pdf",
            "/api/download-invoice/archivo",
            "/api/download-invoice/archivo.txt",
            "/api/download-invoice/archivo.pdf?download=1",
            "/api/download-invoice/archivo.pdf#fragment",
        )

        for unsafe_path in unsafe_paths:
            with self.subTest(unsafe_path=unsafe_path):
                invoice = SimpleNamespace(invoice_number="F2026000001", pdf_path=unsafe_path)
                with self.assertRaises(InvoicePdfDownloadInvalidPath):
                    resolve_invoice_pdf_download(invoice, "invoices")

    def test_rejects_missing_physical_file_without_regenerating(self):
        invoice = SimpleNamespace(
            invoice_number="F2026000001",
            pdf_path="/api/download-invoice/missing.pdf",
        )

        with patch("api.invoice_pdf_download_service.os.path.isfile", return_value=False):
            with self.assertRaises(InvoicePdfDownloadFileMissing):
                resolve_invoice_pdf_download(invoice, "C:/metalwolft/invoices")

    def test_download_name_falls_back_to_original_filename_when_invoice_number_is_empty(self):
        invoice = SimpleNamespace(
            invoice_number=" /\\ ",
            pdf_path="/api/download-invoice/invoice_F2026000001.pdf",
        )

        with patch("api.invoice_pdf_download_service.os.path.isfile", return_value=True):
            result = resolve_invoice_pdf_download(invoice, "C:/metalwolft/invoices")

        self.assertEqual(result.download_name, "invoice_F2026000001.pdf")

    def test_rejects_commonpath_value_errors_as_invalid_paths(self):
        invoice = SimpleNamespace(
            invoice_number="F2026000001",
            pdf_path="/api/download-invoice/invoice_F2026000001.pdf",
        )

        with (
            patch("api.invoice_pdf_download_service.os.path.isfile", return_value=True),
            patch(
                "api.invoice_pdf_download_service.os.path.commonpath",
                side_effect=ValueError("different drives"),
            ),
        ):
            with self.assertRaises(InvoicePdfDownloadInvalidPath):
                resolve_invoice_pdf_download(invoice, "C:/metalwolft/invoices")


if __name__ == "__main__":
    unittest.main()

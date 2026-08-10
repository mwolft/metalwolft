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
    _line_description,
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
                    "screw_option": "long_150",
                    "screw_length_mm": 150,
                    "screw_supplement": "8.95",
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


def snapshot_v2(overrides=None):
    data = snapshot()
    data["schema_version"] = 2
    data["metadata"]["generator"] = "invoice_snapshot_builder_v2"
    data["lines"][0].update(
        {
            "unit_price_net": "78.512397",
            "line_tax_base_before_discount": "78.51",
            "discount_tax_base": "7.85",
        }
    )
    data["lines"][1].update(
        {
            "unit_price_net": "17.355372",
            "line_tax_base_before_discount": "17.36",
            "discount_tax_base": "1.74",
        }
    )
    data.update(overrides or {})
    return data


def rectification_snapshot_v3(overrides=None):
    data = copy.deepcopy(snapshot_v2())
    data["schema_version"] = 3
    data["metadata"]["generator"] = "invoice_snapshot_builder_v3"
    data["operation"]["invoice_type"] = "corrective"
    data["operation"]["rectification"] = {
        "rectification_type": "differences",
        "rectification_scope": "total",
        "rectification_reason": "invoice_error",
        "original_invoice_id": 789,
        "original_invoice_number": "F2026000001",
        "original_invoice_issued_at": "2026-07-16T09:30:00",
    }
    for line in data["lines"]:
        for field in (
            "unit_price_net",
            "unit_amount_before_discount",
            "line_amount_before_discount",
            "discount_amount",
            "line_tax_base_before_discount",
            "discount_tax_base",
            "line_total",
            "tax_base",
            "tax_amount",
        ):
            line[field] = f"-{line[field]}" if line[field] != "0.00" else "0.00"
    for field in (
        "products_amount_before_discount",
        "shipping_amount_before_discount",
        "total_amount_before_discount",
        "discount_amount",
        "total_amount",
        "tax_base",
        "tax_amount",
    ):
        data["totals"][field] = f"-{data['totals'][field]}" if data["totals"][field] != "0.00" else "0.00"
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


def pdf_metadata(path):
    return PdfReader(str(path)).metadata


def pdf_page_count(path):
    return len(PdfReader(str(path)).pages)


def first_page_contains_image(path):
    page = PdfReader(str(path)).pages[0]
    resources = page.get("/Resources")
    if not resources:
        return False
    resources = resources.get_object()
    xobjects = resources.get("/XObject")
    if not xobjects:
        return False
    return any(
        image.get_object().get("/Subtype") == "/Image"
        for image in xobjects.get_object().values()
    )


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
    def test_line_description_includes_synthetic_enamel_for_satin_and_forge(self):
        for color, expected in (
            ("satinado_blanco", "Blanco liso · Esmalte sintético"),
            ("forja_gris", "Gris acero forja · Esmalte sintético"),
        ):
            with self.subTest(color=color):
                description = _line_description(
                    {
                        "description": "Reja fija Albany",
                        "configuration": {
                            "height_cm": "100",
                            "width_cm": "100",
                            "anchoring": "Sin obra: con agujeros interiores",
                            "color": color,
                            "screw_option": "long_150",
                            "screw_length_mm": 150,
                            "screw_supplement": "8.95",
                        },
                    }
                )

                self.assertIn(expected, description)
                self.assertIn("Tornillos 150 mm", description)

    def test_claws_line_omits_screws(self):
        description = _line_description(
            {
                "description": "Reja fija Albany",
                "configuration": {
                    "height_cm": "100",
                    "width_cm": "100",
                    "anchoring": "Con obra: con garras metálicas",
                    "color": "forja_negro",
                    "screw_option": "not_applicable",
                    "screw_length_mm": None,
                    "screw_supplement": "0.00",
                },
            }
        )

        self.assertIn("Garras metálicas", description)
        self.assertIn("Negro forja · Esmalte sintético", description)
        self.assertNotIn("Tornillos", description)

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
            "30 × 30 cm",
            "Agujeros interiores",
            "Blanco liso",
            "Esmalte sintético",
            "Tornillos 150 mm",
            "Gastos de",
            "Descuento",
            "Base imponible",
            "IVA 21",
            "104,40 €",
            "EUR",
        ):
            self.assertIn(expected, text)

    def test_pdf_v2_shows_frozen_net_unit_price_and_net_discount(self):
        invoice = SnapshotOnlyInvoice(invoice_snapshot=snapshot_v2())

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            text = normalized_pdf_text(Path(tmpdir) / result.filename)

        self.assertIn("Precio unitario sin IVA", text)
        self.assertIn("Descuento s/base", text)
        self.assertIn("78,512397 €", text)
        self.assertIn("-7,85 €", text)
        self.assertNotIn("Importe original", text)

    def test_pdf_v3_rectification_uses_the_v2_fiscal_line_presentation(self):
        fiscal_snapshot = rectification_snapshot_v3()
        original_snapshot = copy.deepcopy(fiscal_snapshot)

        invoice = SnapshotOnlyInvoice(invoice_number="R2026000001", invoice_snapshot=fiscal_snapshot)
        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            text = normalized_pdf_text(Path(tmpdir) / result.filename)

        self.assertIn("Factura rectificativa", text)
        self.assertIn("R2026000001", text)
        self.assertIn("RECTIFICA LA FACTURA", text)
        self.assertIn("F2026000001", text)
        self.assertIn("-78,512397 €", text)
        self.assertIn("-85,50 €", text)
        self.assertIn("Precio unitario sin IVA", text)
        self.assertIn("Descuento s/base", text)
        self.assertEqual(fiscal_snapshot, original_snapshot)

    def test_pdf_v3_rejects_a_rectification_without_original_reference(self):
        fiscal_snapshot = rectification_snapshot_v3()
        del fiscal_snapshot["operation"]["rectification"]["original_invoice_number"]
        invoice = SnapshotOnlyInvoice(invoice_number="R2026000001", invoice_snapshot=fiscal_snapshot)

        with temp_invoice_dir() as tmpdir:
            with self.assertRaisesRegex(InvoicePdfSnapshotMissing, "original_invoice_number"):
                generate_invoice_pdf(invoice, output_dir=tmpdir)

    def test_pdf_v1_remains_renderable_without_v2_line_fields(self):
        invoice = SnapshotOnlyInvoice(invoice_snapshot=snapshot())

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            text = normalized_pdf_text(Path(tmpdir) / result.filename)

        self.assertIn("Importe original", text)
        self.assertNotIn("Precio unitario sin IVA", text)

    def test_pdf_uses_brand_asset_and_current_document_color(self):
        invoice = SnapshotOnlyInvoice()

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            output_path = Path(tmpdir) / result.filename

            self.assertTrue(first_page_contains_image(output_path))
            self.assertIn("METALWOLFT", normalized_pdf_text(output_path))

        source = (SRC_DIR / "api/invoice_pdf_service.py").read_text(encoding="utf-8")
        self.assertIn('BRAND_RED = "#cf1c35"', source)

    def test_pdf_hides_internal_hash_and_customer_contact_but_keeps_integrity_validation(self):
        invoice = SnapshotOnlyInvoice()
        original_hash = invoice.invoice_snapshot_hash

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            output_path = Path(tmpdir) / result.filename
            text = normalized_pdf_text(output_path)
            metadata = pdf_metadata(output_path)

        self.assertNotIn("Integridad fiscal", text)
        self.assertNotIn(original_hash, text)
        self.assertNotIn(original_hash, str(metadata))
        self.assertNotIn("cliente@example.com", text)
        self.assertNotIn("600000000", text)
        self.assertNotIn("600111222", text)
        self.assertIn("admin@metalwolft.com", text)
        self.assertEqual(invoice.invoice_snapshot_hash, original_hash)

    def test_pdf_shows_operation_date_only_when_it_differs_from_issue_date(self):
        invoice = SnapshotOnlyInvoice()

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            text = normalized_pdf_text(Path(tmpdir) / result.filename)

        self.assertIn("FECHA DE EXPEDICIÓN 16/07/2026", text)
        self.assertIn("FECHA DE OPERACIÓN 15/07/2026", text)

        same_date_snapshot = snapshot()
        same_date_snapshot["operation"] = {
            **same_date_snapshot["operation"],
            "operation_date": "2026-07-16",
        }
        same_date_invoice = SnapshotOnlyInvoice(
            invoice_snapshot=same_date_snapshot,
            stored_hash=calculate_invoice_snapshot_hash(same_date_snapshot),
        )
        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(same_date_invoice, output_dir=tmpdir)
            text = normalized_pdf_text(Path(tmpdir) / result.filename)

        self.assertNotIn("FECHA DE OPERACIÓN", text)

    def test_company_and_individual_legal_names_are_rendered_from_snapshot(self):
        company_snapshot = snapshot()
        company_snapshot["customer"] = {
            **company_snapshot["customer"],
            "legal_name": "CONSTRUCCIONES EJEMPLO SL",
            "tax_id": "B12345678",
        }
        company_invoice = SnapshotOnlyInvoice(
            invoice_snapshot=company_snapshot,
            stored_hash=calculate_invoice_snapshot_hash(company_snapshot),
        )

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(company_invoice, output_dir=tmpdir)
            company_text = normalized_pdf_text(Path(tmpdir) / result.filename)

        self.assertIn("CONSTRUCCIONES EJEMPLO SL", company_text)
        self.assertIn("B12345678", company_text)

        individual_invoice = SnapshotOnlyInvoice()
        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(individual_invoice, output_dir=tmpdir)
            individual_text = normalized_pdf_text(Path(tmpdir) / result.filename)

        self.assertIn("Sergio Arias", individual_text)
        self.assertIn("00000000T", individual_text)

    def test_multiple_long_lines_paginate_and_repeat_the_table_header(self):
        multipage_snapshot = snapshot()
        source_line = multipage_snapshot["lines"][0]
        multipage_snapshot["lines"] = []
        for index in range(1, 46):
            line = copy.deepcopy(source_line)
            line["line_number"] = index
            line["description"] = (
                f"Reja a medida de prueba {index} con una descripción suficientemente larga "
                "para comprobar el ajuste de texto dentro de la columna MARKER"
            )
            multipage_snapshot["lines"].append(line)
        invoice = SnapshotOnlyInvoice(
            invoice_snapshot=multipage_snapshot,
            stored_hash=calculate_invoice_snapshot_hash(multipage_snapshot),
        )

        with temp_invoice_dir() as tmpdir:
            result = generate_invoice_pdf(invoice, output_dir=tmpdir)
            output_path = Path(tmpdir) / result.filename
            text = normalized_pdf_text(output_path)
            page_count = pdf_page_count(output_path)

        self.assertGreater(page_count, 1)
        self.assertGreaterEqual(text.count("Producto / configuración"), 2)
        self.assertIn("Reja a medida de prueba 45", text)
        self.assertIn("MARKER", text)
        self.assertIn("104,40 €", text)

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

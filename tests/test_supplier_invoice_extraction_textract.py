import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from api.supplier_invoice_extraction_provider import SupplierInvoiceExtractionProviderError  # noqa: E402
from api.supplier_invoice_extraction_textract import (  # noqa: E402
    TEXTRACT_MAX_SYNC_BYTES,
    TextractSupplierInvoiceExtractionProvider,
    TextractSupplierInvoiceExtractionSettings,
    build_textract_supplier_invoice_extraction_payload,
)


def summary_field(field_type, value, *, label="", page=1, confidence=98, vendor=False, currency="EUR"):
    field = {
        "Type": {"Text": field_type},
        "ValueDetection": {"Text": value, "Confidence": confidence},
        "PageNumber": page,
        "Currency": {"Code": currency, "Confidence": confidence},
    }
    if label:
        field["LabelDetection"] = {"Text": label}
    if vendor:
        field["GroupProperties"] = [{"Types": ["VENDOR"]}]
    return field


def textract_response(*, fields=None):
    return {"ExpenseDocuments": [{"ExpenseIndex": 1, "SummaryFields": fields or [
        summary_field("VENDOR_NAME", "SEUR GEOPOST SLU", vendor=True),
        summary_field("VENDOR_ADDRESS", "Calle Ejemplo 1\nNIF B82516600", vendor=True),
        summary_field("INVOICE_RECEIPT_ID", "SEUR-2026-001"),
        summary_field("INVOICE_RECEIPT_DATE", "25-07-2026"),
        summary_field("TOTAL", "536,93 €", label="Total factura"),
        summary_field("SUBTOTAL", "443,74 €", label="Base imponible"),
        summary_field("TAX", "93,19 €", label="IVA 21,00%"),
    ]}]}


def textract_client_error(error_class, code):
    try:
        error = error_class({"Error": {"Code": code}}, "AnalyzeExpense")
    except TypeError:  # Lightweight fallback classes used when boto3 is not installed in a test venv.
        error = error_class()
    if not hasattr(error, "response"):
        error.response = {"Error": {"Code": code}}
    return error


def textract_timeout_error(error_class):
    try:
        return error_class(endpoint_url="https://textract.eu-south-2.amazonaws.com")
    except TypeError:
        return error_class()


class TextractSupplierInvoiceExtractionProviderTest(unittest.TestCase):
    def _provider(self, response=None):
        client = Mock()
        client.analyze_expense.return_value = response or textract_response()
        settings = TextractSupplierInvoiceExtractionSettings(
            region="eu-south-2", access_key_id="test", secret_access_key="test"
        )
        return TextractSupplierInvoiceExtractionProvider(settings, client=client), client

    def test_maps_vendor_invoice_date_total_currency_and_verified_vat(self):
        provider, client = self._provider()
        payload = provider.extract(b"image", "image/png")

        self.assertEqual(payload["fields"]["supplier_legal_name"]["value"], "SEUR GEOPOST SLU")
        self.assertEqual(payload["fields"]["supplier_tax_id"]["value"], "B82516600")
        self.assertEqual(payload["fields"]["supplier_invoice_number"]["value"], "SEUR-2026-001")
        self.assertEqual(payload["fields"]["issue_date"]["value"], "2026-07-25")
        self.assertEqual(payload["fields"]["total_amount"]["value"], "536.93")
        self.assertEqual(payload["fields"]["currency"]["value"], "EUR")
        self.assertEqual(payload["tax_breakdowns"], [{
            "tax_base": "443.74", "tax_rate": "21.00", "tax_amount": "93.19",
            "deductible_tax_amount": None, "confidence": 0.98, "source": {"page": 1},
        }])
        self.assertIsNone(payload["fields"]["fiscal_invoice_type"]["value"])
        self.assertIsNone(payload["fields"]["tax_treatment"]["value"])
        client.analyze_expense.assert_called_once_with(Document={"Bytes": b"image"})

    def test_receiver_tax_id_is_never_used_as_supplier_tax_id(self):
        fields = textract_response()["ExpenseDocuments"][0]["SummaryFields"]
        fields[1] = summary_field("VENDOR_ADDRESS", "Calle Ejemplo 1", vendor=True)
        fields.append(summary_field("OTHER", "05703874N", label="DNI/CIF"))
        payload = build_textract_supplier_invoice_extraction_payload(textract_response(fields=fields))
        self.assertIsNone(payload["fields"]["supplier_tax_id"]["value"])

    def test_multiple_subtotals_are_not_used_without_tax_and_total_coherence(self):
        fields = textract_response()["ExpenseDocuments"][0]["SummaryFields"]
        fields[5] = summary_field("SUBTOTAL", "441,99 €", label="Subtotal")
        fields.insert(6, summary_field("SUBTOTAL", "1,75 €", label="Subtotal"))
        payload = build_textract_supplier_invoice_extraction_payload(textract_response(fields=fields))
        self.assertEqual(payload["tax_breakdowns"], [])
        self.assertIn("No se ha podido identificar una base imponible de IVA de forma inequívoca.", payload["warnings"])

    def test_multiple_totals_keep_the_best_explicit_candidate_with_a_warning(self):
        fields = textract_response()["ExpenseDocuments"][0]["SummaryFields"]
        fields.append(summary_field("TOTAL", "1,75 €", label="Subtotal final", confidence=99))
        payload = build_textract_supplier_invoice_extraction_payload(textract_response(fields=fields))
        self.assertEqual(payload["fields"]["total_amount"]["value"], "536.93")
        self.assertIn("Se han detectado varios totales; revisa el importe propuesto.", payload["warnings"])

    def test_ambiguous_date_without_spanish_context_is_not_normalized(self):
        fields = textract_response()["ExpenseDocuments"][0]["SummaryFields"]
        fields[0] = summary_field("VENDOR_NAME", "Proveedor", vendor=False)
        fields[1] = summary_field("VENDOR_ADDRESS", "Calle Ejemplo 1", vendor=False)
        fields[3] = summary_field("INVOICE_RECEIPT_DATE", "05/06/2026")
        payload = build_textract_supplier_invoice_extraction_payload(textract_response(fields=fields))
        self.assertIsNone(payload["fields"]["issue_date"]["value"])
        self.assertIn("La fecha detectada es ambigua y requiere revisión manual.", payload["warnings"])

    def test_real_spanish_invoice_patterns_are_normalized_without_using_receiver_tax_id(self):
        fields = [
            {
                "Type": {"Text": "NAME"},
                "ValueDetection": {"Text": "HIERROS ACERGOM, S.L.L.", "Confidence": 99.698},
                "PageNumber": 1,
                "GroupProperties": [{"Types": ["VENDOR"]}],
            },
            {
                "Type": {"Text": "VENDOR_NAME"},
                "ValueDetection": {"Text": "HIERROS ACERGOM, S.L.L.", "Confidence": 99.698},
                "PageNumber": 1,
            },
            {
                "Type": {"Text": "INVOICE_RECEIPT_ID"},
                "LabelDetection": {"Text": "Código"},
                "ValueDetection": {"Text": "43002146", "Confidence": 99.0},
                "PageNumber": 1,
            },
            {
                "Type": {"Text": "INVOICE_RECEIPT_ID"},
                "LabelDetection": {"Text": "Factura"},
                "ValueDetection": {"Text": "076088", "Confidence": 98.682},
                "PageNumber": 1,
            },
            {
                "Type": {"Text": "INVOICE_RECEIPT_DATE"},
                "LabelDetection": {"Text": "Fecha"},
                "ValueDetection": {"Text": "12/06/2026", "Confidence": 75.324},
                "PageNumber": 1,
            },
            {
                "Type": {"Text": "SUBTOTAL"},
                "LabelDetection": {"Text": "B. Imponible"},
                "ValueDetection": {"Text": "319,24", "Confidence": 90.277},
                "PageNumber": 1,
            },
            {
                "Type": {"Text": "TAX"},
                "LabelDetection": {"Text": "Importe IVA %"},
                "ValueDetection": {"Text": "67,04", "Confidence": 96.250},
                "PageNumber": 1,
            },
            {
                "Type": {"Text": "OTHER"},
                "LabelDetection": {"Text": "% IVA"},
                "ValueDetection": {"Text": "21,00", "Confidence": 99.848},
                "PageNumber": 1,
            },
            {
                "Type": {"Text": "TOTAL"},
                "LabelDetection": {"Text": "TOTAL"},
                "ValueDetection": {"Text": "386,28", "Confidence": 98.485},
                "PageNumber": 1,
            },
            {
                "Type": {"Text": "OTHER"},
                "LabelDetection": {"Text": "CIF:"},
                "ValueDetection": {"Text": "B13559141", "Confidence": 99.920},
                "PageNumber": 1,
            },
            {
                "Type": {"Text": "OTHER"},
                "LabelDetection": {"Text": "DNI/CIF"},
                "ValueDetection": {"Text": "05703874N", "Confidence": 99.615},
                "PageNumber": 1,
            },
        ]
        payload = build_textract_supplier_invoice_extraction_payload(textract_response(fields=fields))

        self.assertEqual(payload["fields"]["supplier_legal_name"]["value"], "HIERROS ACERGOM, S.L.L.")
        self.assertEqual(payload["fields"]["supplier_tax_id"]["value"], "B13559141")
        self.assertEqual(payload["fields"]["supplier_invoice_number"]["value"], "076088")
        self.assertEqual(payload["fields"]["issue_date"]["value"], "2026-06-12")
        self.assertEqual(payload["fields"]["total_amount"]["value"], "386.28")
        self.assertEqual(payload["tax_breakdowns"], [{
            "tax_base": "319.24", "tax_rate": "21.00", "tax_amount": "67.04",
            "deductible_tax_amount": None, "confidence": 0.90277, "source": {"page": 1},
        }])

    def test_tax_breakdown_is_not_inferred_when_the_real_style_does_not_reconcile(self):
        fields = [
            summary_field("SUBTOTAL", "319,24", label="B. Imponible"),
            summary_field("TAX", "67,03", label="Importe IVA %"),
            summary_field("OTHER", "21,00", label="% IVA"),
            summary_field("TOTAL", "386,28", label="TOTAL"),
        ]
        payload = build_textract_supplier_invoice_extraction_payload(textract_response(fields=fields))
        self.assertEqual(payload["tax_breakdowns"], [])
        self.assertIn("No se ha podido identificar una base imponible de IVA de forma inequívoca.", payload["warnings"])

    def test_multiple_tax_rates_are_kept_separate_when_each_breakdown_reconciles(self):
        fields = textract_response()["ExpenseDocuments"][0]["SummaryFields"][:5]
        fields[4] = summary_field("TOTAL", "126,00 €", label="Total factura")
        fields.extend([
            summary_field("SUBTOTAL", "100,00 €", label="Base imponible 21%"),
            summary_field("TAX", "21,00 €", label="IVA 21%"),
            summary_field("SUBTOTAL", "5,00 €", label="Base imponible 0%"),
            summary_field("TAX", "0,00 €", label="IVA 0%"),
        ])
        payload = build_textract_supplier_invoice_extraction_payload(textract_response(fields=fields))
        self.assertEqual(len(payload["tax_breakdowns"]), 2)
        self.assertEqual(payload["tax_breakdowns"][1]["tax_rate"], "0.00")

    def test_provider_rejects_oversized_and_unsupported_documents_without_calling_aws(self):
        provider, client = self._provider()
        with self.assertRaisesRegex(SupplierInvoiceExtractionProviderError, "límite") as too_large:
            provider.extract(b"x" * (TEXTRACT_MAX_SYNC_BYTES + 1), "image/png")
        self.assertEqual(too_large.exception.code, "document_too_large")
        with self.assertRaisesRegex(SupplierInvoiceExtractionProviderError, "formato") as unsupported:
            provider.extract(b"image", "image/tiff")
        self.assertEqual(unsupported.exception.code, "unsupported_document")
        client.analyze_expense.assert_not_called()

    def test_timeout_and_access_denied_are_exposed_as_safe_domain_errors(self):
        provider, client = self._provider()
        from api.supplier_invoice_extraction_textract import ClientError, ReadTimeoutError

        client.analyze_expense.side_effect = textract_timeout_error(ReadTimeoutError)
        with self.assertRaises(SupplierInvoiceExtractionProviderError) as timeout:
            provider.extract(b"image", "image/png")
        self.assertEqual(timeout.exception.code, "provider_timeout")

        client.analyze_expense.side_effect = textract_client_error(ClientError, "AccessDeniedException")
        with self.assertRaises(SupplierInvoiceExtractionProviderError) as access_denied:
            provider.extract(b"image", "image/png")
        self.assertEqual(access_denied.exception.code, "access_denied")

        client.analyze_expense.side_effect = textract_client_error(ClientError, "ThrottlingException")
        with self.assertRaises(SupplierInvoiceExtractionProviderError) as throttling:
            provider.extract(b"image", "image/png")
        self.assertEqual(throttling.exception.code, "throttled")

    def test_provider_rejects_multi_page_pdf_before_calling_aws(self):
        from pypdf import PdfWriter

        buffer = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.add_blank_page(width=100, height=100)
        writer.write(buffer)
        provider, client = self._provider()

        with self.assertRaises(SupplierInvoiceExtractionProviderError) as unsupported:
            provider.extract(buffer.getvalue(), "application/pdf")

        self.assertEqual(unsupported.exception.code, "unsupported_document")
        client.analyze_expense.assert_not_called()


if __name__ == "__main__":
    unittest.main()

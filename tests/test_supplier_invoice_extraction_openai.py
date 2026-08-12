import base64
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from api.supplier_invoice_extraction_openai import (  # noqa: E402
    OpenAISupplierInvoiceExtractionProvider,
    OpenAISupplierInvoiceExtractionSettings,
    build_openai_supplier_invoice_extraction_payload,
)
from api.supplier_invoice_extraction_provider import SupplierInvoiceExtractionProviderError  # noqa: E402


def proposal(**overrides):
    value = {
        "supplier_legal_name": "HIERROS ACERGOM, S.L.L.",
        "supplier_tax_id": "b13559141",
        "supplier_invoice_number": "076088",
        "issue_date": "2026-06-12",
        "operation_date": None,
        "concept": "Material de acero",
        "currency": "eur",
        "total_amount": "386.28",
        "tax_breakdowns": [{"tax_base": "319.24", "tax_rate": "21.00", "tax_amount": "67.04"}],
    }
    value.update(overrides)
    return value


class OpenAISupplierInvoiceExtractionProviderTest(unittest.TestCase):
    def _provider(self, output=None):
        client = Mock()
        client.responses.create.return_value = SimpleNamespace(
            output_text=json.dumps(output or proposal()),
            usage=SimpleNamespace(input_tokens=120, output_tokens=80, total_tokens=200),
        )
        settings = OpenAISupplierInvoiceExtractionSettings(api_key="test", model="gpt-4.1-mini", timeout_seconds=45)
        return OpenAISupplierInvoiceExtractionProvider(settings, client=client), client

    def test_pdf_uses_one_private_structured_responses_call_and_returns_canonical_payload(self):
        provider, client = self._provider()

        payload = provider.extract(b"private-pdf", "application/pdf")

        self.assertEqual(payload["fields"]["supplier_tax_id"]["value"], "B13559141")
        self.assertEqual(payload["fields"]["currency"]["value"], "EUR")
        self.assertIsNone(payload["fields"]["fiscal_invoice_type"]["value"])
        self.assertIsNone(payload["fields"]["tax_treatment"]["value"])
        self.assertEqual(payload["tax_breakdowns"][0]["deductible_tax_amount"], None)
        self.assertEqual(payload["warnings"], [
            "El tipo fiscal requiere revisión manual.",
            "El tratamiento fiscal requiere revisión manual.",
        ])
        request = client.responses.create.call_args.kwargs
        self.assertFalse(request["store"])
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        self.assertTrue(request["text"]["format"]["strict"])
        file_input = request["input"][0]["content"][0]
        self.assertEqual(file_input["type"], "input_file")
        self.assertEqual(file_input["file_data"], "data:application/pdf;base64," + base64.b64encode(b"private-pdf").decode())
        self.assertEqual(provider.last_usage, {"input_tokens": 120, "output_tokens": 80, "total_tokens": 200})

    def test_images_use_private_data_urls_without_public_uploads(self):
        provider, client = self._provider()

        provider.extract(b"private-image", "image/png")

        image_input = client.responses.create.call_args.kwargs["input"][0]["content"][0]
        self.assertEqual(image_input["type"], "input_image")
        self.assertEqual(image_input["image_url"], "data:image/png;base64," + base64.b64encode(b"private-image").decode())

    def test_invalid_or_unreconciled_breakdown_is_not_silently_accepted(self):
        payload = build_openai_supplier_invoice_extraction_payload(
            proposal(tax_breakdowns=[{"tax_base": "319.24", "tax_rate": "21.00", "tax_amount": "67.03"}])
        )

        self.assertEqual(payload["tax_breakdowns"], [])
        self.assertIn("El desglose de IVA propuesto no coincide con el total de la factura.", payload["warnings"])

    def test_rejects_unsupported_document_and_invalid_response(self):
        provider, client = self._provider(output={"not": "the schema"})
        with self.assertRaises(SupplierInvoiceExtractionProviderError) as unsupported:
            provider.extract(b"image", "image/tiff")
        self.assertEqual(unsupported.exception.code, "unsupported_document")
        client.responses.create.assert_not_called()

        with self.assertRaises(SupplierInvoiceExtractionProviderError) as invalid:
            provider.extract(b"image", "image/png")
        self.assertEqual(invalid.exception.code, "invalid_response")


if __name__ == "__main__":
    unittest.main()

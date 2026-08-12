import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from flask import Flask


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from api.models import (  # noqa: E402
    SupplierInvoice,
    SupplierInvoiceDocument,
    SupplierInvoiceExtraction,
    db,
)
from api.supplier_invoice_extraction_provider import (  # noqa: E402
    FakeSupplierInvoiceExtractionProvider,
)
from api.supplier_invoice_extraction_service import (  # noqa: E402
    SupplierInvoiceExtractionApplyError,
    SupplierInvoiceExtractionEligibilityError,
    SupplierInvoiceExtractionPayloadError,
    apply_supplier_invoice_extraction,
    calculate_supplier_invoice_extraction_payload_hash,
    normalize_supplier_invoice_extraction_payload,
    run_supplier_invoice_extraction,
)


def extraction_payload(*, total="121.00", tax_amount="21.00", warnings=None):
    def field(value, confidence=0.98):
        return {"value": value, "confidence": confidence, "source": {"page": 1}}

    return {
        "schema_version": 1,
        "fields": {
            "supplier_legal_name": field("Acero Proveedor SL"),
            "supplier_tax_id": field("b12345678"),
            "supplier_invoice_number": field("P-2026-001"),
            "issue_date": field("2026-08-11"),
            "operation_date": field(None, None),
            "concept": field("Material de taller"),
            "currency": field("EUR"),
            "total_amount": field(total),
            "fiscal_invoice_type": field("F1"),
            "tax_treatment": field("domestic_standard"),
        },
        "tax_breakdowns": [
            {
                "tax_base": "100.00",
                "tax_rate": "21.00",
                "tax_amount": tax_amount,
                "deductible_tax_amount": None,
                "confidence": 0.98,
                "source": {"page": 1},
            }
        ],
        "warnings": warnings or [],
    }


class SupplierInvoiceExtractionServiceTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SQLALCHEMY_DATABASE_URI="sqlite://",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SECRET_KEY="supplier-extraction-tests",
        )
        db.init_app(self.app)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.invoice = SupplierInvoice(status=SupplierInvoice.STATUS_DRAFT)
        db.session.add(self.invoice)
        db.session.flush()
        self.document = SupplierInvoiceDocument(
            supplier_invoice=self.invoice,
            storage_provider="r2",
            storage_key="supplier-invoices/2026/08/test.pdf",
            original_filename="test.pdf",
            mime_type="application/pdf",
            file_size=4,
            sha256="a" * 64,
        )
        db.session.add(self.document)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _storage(self):
        storage = Mock()
        storage.get_document.return_value = b"test"
        return storage

    def _extract(self, payload=None):
        return run_supplier_invoice_extraction(
            self.document,
            provider=FakeSupplierInvoiceExtractionProvider(payload=payload or extraction_payload()),
            db_session=db.session,
            storage=self._storage(),
        )

    def test_valid_payload_is_normalized_hashed_and_keeps_invoice_unchanged(self):
        result = self._extract()
        db.session.commit()

        self.assertTrue(result.succeeded)
        self.assertEqual(result.extraction.status, SupplierInvoiceExtraction.STATUS_EXTRACTED)
        self.assertEqual(result.extraction.extraction_payload["fields"]["supplier_tax_id"]["value"], "B12345678")
        self.assertIsNone(result.extraction.extraction_payload["tax_breakdowns"][0]["deductible_tax_amount"])
        self.assertEqual(
            result.extraction.payload_hash,
            calculate_supplier_invoice_extraction_payload_hash(
                normalize_supplier_invoice_extraction_payload(result.extraction.extraction_payload)
            ),
        )
        self.assertEqual(self.invoice.status, SupplierInvoice.STATUS_DRAFT)
        self.assertIsNone(self.invoice.reception_number)
        self.assertIsNone(self.invoice.fiscal_snapshot)

    def test_each_execution_creates_a_new_attempt_without_overwriting_history(self):
        first = self._extract().extraction
        second = self._extract().extraction
        db.session.commit()

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(len(self.document.extractions), 2)
        self.assertEqual(first.status, SupplierInvoiceExtraction.STATUS_EXTRACTED)
        self.assertEqual(second.status, SupplierInvoiceExtraction.STATUS_EXTRACTED)

    def test_provider_failure_is_persisted_as_failed_attempt(self):
        result = run_supplier_invoice_extraction(
            self.document,
            provider=FakeSupplierInvoiceExtractionProvider(error="provider unavailable"),
            db_session=db.session,
            storage=self._storage(),
        )
        db.session.commit()

        self.assertFalse(result.succeeded)
        self.assertEqual(result.extraction.status, SupplierInvoiceExtraction.STATUS_FAILED)
        self.assertEqual(result.extraction.error_code, "provider_error")
        self.assertEqual(self.document.processing_status, SupplierInvoiceDocument.STATUS_FAILED)

    def test_provider_failure_keeps_a_safe_specific_error_code(self):
        result = run_supplier_invoice_extraction(
            self.document,
            provider=FakeSupplierInvoiceExtractionProvider(
                error="access denied", error_code="access_denied"
            ),
            db_session=db.session,
            storage=self._storage(),
        )
        self.assertFalse(result.succeeded)
        self.assertEqual(result.extraction.error_code, "access_denied")

    def test_float_money_is_rejected_and_tax_mismatch_becomes_a_warning(self):
        invalid = extraction_payload()
        invalid["fields"]["total_amount"]["value"] = 121.0
        with self.assertRaises(SupplierInvoiceExtractionPayloadError):
            normalize_supplier_invoice_extraction_payload(invalid)

        warning_payload = normalize_supplier_invoice_extraction_payload(
            extraction_payload(total="119.00", tax_amount="20.00")
        )
        self.assertIn(
            "El total extraído no coincide con la suma de las bases y cuotas de IVA.",
            warning_payload["warnings"],
        )
        self.assertIn(
            "Una cuota de IVA extraída no coincide con su base y tipo.",
            warning_payload["warnings"],
        )

    def test_multiple_vat_breakdowns_are_preserved_and_duplicate_signals_are_warnings(self):
        payload = extraction_payload(total="126.00")
        payload["tax_breakdowns"] = [
            {
                "tax_base": "100.00",
                "tax_rate": "21.00",
                "tax_amount": "21.00",
                "deductible_tax_amount": None,
                "confidence": 0.98,
                "source": {"page": 1},
            },
            {
                "tax_base": "5.00",
                "tax_rate": "0.00",
                "tax_amount": "0.00",
                "deductible_tax_amount": None,
                "confidence": 0.91,
                "source": {"page": 1},
            },
        ]
        existing = SupplierInvoice(
            supplier_legal_name="Coincidencia SL",
            supplier_tax_id="B12345678",
            supplier_invoice_number="P-2026-001",
            issue_date=date(2026, 8, 11),
            total_amount=Decimal("126.00"),
        )
        duplicate_document = SupplierInvoiceDocument(
            storage_provider="r2",
            storage_key="supplier-invoices/2026/08/duplicate.pdf",
            original_filename="duplicate.pdf",
            mime_type="application/pdf",
            file_size=4,
            sha256="a" * 64,
        )
        db.session.add_all([existing, duplicate_document])
        db.session.commit()

        result = self._extract(payload)
        self.assertEqual(len(result.extraction.extraction_payload["tax_breakdowns"]), 2)
        self.assertIn("Existe otro documento recibido con el mismo hash.", result.extraction.extraction_payload["warnings"])
        self.assertIn(
            "Existe una factura recibida con el mismo proveedor y número.",
            result.extraction.extraction_payload["warnings"],
        )
        self.assertIn(
            "Existe una factura recibida con la misma fecha e importe total.",
            result.extraction.extraction_payload["warnings"],
        )

    def test_apply_to_draft_requires_explicit_breakdown_confirmation_and_human_deduction(self):
        extraction = self._extract().extraction
        with self.assertRaises(SupplierInvoiceExtractionApplyError):
            apply_supplier_invoice_extraction(extraction, self.invoice, db_session=db.session)

        apply_supplier_invoice_extraction(
            extraction,
            self.invoice,
            replace_tax_breakdowns=True,
            deductible_tax_amounts=["0.00"],
            db_session=db.session,
        )
        db.session.commit()

        self.assertEqual(extraction.status, SupplierInvoiceExtraction.STATUS_APPLIED)
        self.assertEqual(self.document.processing_status, SupplierInvoiceDocument.STATUS_APPLIED)
        self.assertEqual(self.invoice.status, SupplierInvoice.STATUS_NEEDS_REVIEW)
        self.assertEqual(self.invoice.supplier_legal_name, "Acero Proveedor SL")
        self.assertEqual(self.invoice.total_amount, Decimal("121.00"))
        self.assertEqual(len(self.invoice.tax_breakdowns), 1)
        self.assertEqual(self.invoice.tax_breakdowns[0].deductible_tax_amount, Decimal("0.00"))
        self.assertEqual(self.invoice.aeat_expense_concept_code, "G03")
        self.assertEqual(self.invoice.expense_deductible_amount, Decimal("100.00"))
        self.assertIsNone(self.invoice.reception_number)
        self.assertIsNone(self.invoice.fiscal_snapshot)

    def test_apply_preserves_manual_expense_classification_decisions(self):
        self.invoice.aeat_expense_concept_code = "G01"
        self.invoice.expense_deductible_amount = Decimal("55.00")
        extraction = self._extract().extraction

        apply_supplier_invoice_extraction(
            extraction,
            self.invoice,
            replace_tax_breakdowns=True,
            deductible_tax_amounts=["21.00"],
            db_session=db.session,
        )

        self.assertEqual(self.invoice.aeat_expense_concept_code, "G01")
        self.assertEqual(self.invoice.expense_deductible_amount, Decimal("55.00"))

    def test_manual_data_requires_explicit_replacement_and_registered_is_rejected(self):
        self.invoice.supplier_legal_name = "Dato manual SL"
        extraction = self._extract().extraction
        with self.assertRaises(SupplierInvoiceExtractionApplyError):
            apply_supplier_invoice_extraction(extraction, self.invoice, db_session=db.session)

        self.invoice.status = SupplierInvoice.STATUS_REGISTERED
        with self.assertRaises(SupplierInvoiceExtractionApplyError):
            apply_supplier_invoice_extraction(
                extraction,
                self.invoice,
                replace_existing_fields=True,
                replace_tax_breakdowns=True,
                deductible_tax_amounts=["0.00"],
                db_session=db.session,
            )
        with self.assertRaises(SupplierInvoiceExtractionEligibilityError):
            self._extract()


class SupplierInvoiceExtractionMigrationSourceTest(unittest.TestCase):
    def test_migration_is_additive_and_preserves_document_restriction(self):
        source = (
            ROOT_DIR
            / "src/migrations/versions/a4b5c6d7e8f9_add_supplier_invoice_extractions.py"
        ).read_text(encoding="utf-8")
        self.assertIn('down_revision = "f3a4b5c6d7e8"', source)
        self.assertIn("supplier_invoice_extractions", source)
        self.assertIn("ondelete=\"RESTRICT\"", source)
        self.assertIn("'needs_review'", source)


if __name__ == "__main__":
    unittest.main()

import hashlib
import importlib.util
import sys
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_DOCUMENT_DEPS = all(
    has_package(package)
    for package in ("flask", "flask_sqlalchemy", "sqlalchemy", "PIL", "pypdf", "werkzeug")
)

if HAS_DOCUMENT_DEPS:
    from flask import Flask
    from pypdf import PdfWriter
    from werkzeug.datastructures import FileStorage

    from api.models import (
        SupplierInvoice,
        SupplierInvoiceDocument,
        SupplierInvoiceExtraction,
        SupplierInvoiceTaxBreakdown,
        db,
    )
    from api.supplier_invoice_document_service import (
        SupplierInvoiceDocumentDeletionBlockedError,
        SupplierInvoiceDocumentDeletionStorageError,
        SupplierInvoiceDocumentImmutabilityError,
        SupplierInvoiceDocumentPersistenceError,
        SupplierInvoiceDocumentValidationError,
        can_delete_supplier_invoice_document,
        delete_supplier_invoice_document,
        upload_supplier_invoice_document,
        validate_supplier_invoice_document_upload,
    )
    from api.supplier_invoice_document_storage import (
        R2SupplierInvoiceDocumentStorage,
        SupplierInvoiceDocumentStorageOperationError,
        SupplierInvoiceDocumentStorageSettings,
    )


@unittest.skipUnless(HAS_DOCUMENT_DEPS, "Supplier document dependencies are not installed.")
class SupplierInvoiceDocumentServiceTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            self.invoice = self._make_invoice()
            db.session.commit()
            self.invoice_id = self.invoice.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _make_invoice(self, *, registered=False):
        invoice = SupplierInvoice(
            supplier_legal_name="Acero Proveedor SL",
            supplier_tax_id="B12345678",
            supplier_invoice_number="P-2026-001",
            issue_date=date(2026, 8, 11),
            concept="Material de taller",
            total_amount=Decimal("121.00"),
        )
        db.session.add(invoice)
        db.session.flush()
        db.session.add(
            SupplierInvoiceTaxBreakdown(
                supplier_invoice_id=invoice.id,
                position=1,
                tax_base=Decimal("100.00"),
                tax_rate=Decimal("21.00"),
                tax_amount=Decimal("21.00"),
                deductible_tax_amount=Decimal("21.00"),
            )
        )
        if registered:
            invoice.status = SupplierInvoice.STATUS_REGISTERED
            invoice.reception_number = 1
            invoice.registered_at = date(2026, 8, 11)
            invoice.fiscal_snapshot = {"schema_version": 1}
            invoice.snapshot_schema_version = 1
            invoice.snapshot_hash = "a" * 64
        return invoice

    def _valid_pdf_content(self):
        output = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(output)
        return output.getvalue()

    def _file(self, content, filename, mimetype):
        return FileStorage(stream=BytesIO(content), filename=filename, content_type=mimetype)

    def test_valid_pdf_upload_persists_private_metadata_and_sha256(self):
        storage = Mock()
        content = self._valid_pdf_content()
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            result = upload_supplier_invoice_document(
                self._file(content, "factura proveedor.pdf", "application/pdf"),
                supplier_invoice=invoice,
                actor="admin",
                db_session=db.session,
                storage=storage,
            )
            db.session.commit()

            document = db.session.get(SupplierInvoiceDocument, result.document.id)
            self.assertEqual(document.supplier_invoice_id, invoice.id)
            self.assertEqual(document.mime_type, "application/pdf")
            self.assertEqual(document.file_size, len(content))
            self.assertEqual(document.sha256, hashlib.sha256(content).hexdigest())
            self.assertEqual(document.processing_status, SupplierInvoiceDocument.STATUS_UPLOADED)
            self.assertNotIn("proveedor", document.storage_key.lower())
            self.assertNotIn("B12345678", document.storage_key)
            self.assertRegex(document.storage_key, r"^supplier-invoices/\d{4}/\d{2}/[0-9a-f]{32}\.pdf$")
            storage.put_document.assert_called_once()
            self.assertEqual(result.duplicate_count, 0)

    def test_valid_jpeg_and_png_are_accepted(self):
        from PIL import Image

        for image_format, extension, mime_type in (
            ("JPEG", "jpg", "image/jpeg"),
            ("PNG", "png", "image/png"),
        ):
            with self.subTest(image_format=image_format):
                image_data = BytesIO()
                Image.new("RGB", (2, 2), "white").save(image_data, format=image_format)
                validated = validate_supplier_invoice_document_upload(
                    self._file(image_data.getvalue(), f"factura.{extension}", mime_type)
                )
                self.assertEqual(validated.mime_type, mime_type)

    def test_pdf_only_restriction_reuses_the_standard_document_validation(self):
        from PIL import Image

        image_data = BytesIO()
        Image.new("RGB", (2, 2), "white").save(image_data, format="PNG")
        with self.assertRaisesRegex(SupplierInvoiceDocumentValidationError, "Solo se admiten archivos PDF"):
            validate_supplier_invoice_document_upload(
                self._file(image_data.getvalue(), "factura.png", "image/png"),
                allowed_mime_types={"application/pdf"},
            )

        validated = validate_supplier_invoice_document_upload(
            self._file(self._valid_pdf_content(), "factura.pdf", "application/pdf"),
            allowed_mime_types={"application/pdf"},
        )
        self.assertEqual(validated.mime_type, "application/pdf")

    def test_invalid_content_and_mismatched_mime_are_rejected(self):
        with self.assertRaises(SupplierInvoiceDocumentValidationError):
            validate_supplier_invoice_document_upload(
                self._file(b"not a pdf", "factura.pdf", "application/pdf")
            )
        with self.assertRaises(SupplierInvoiceDocumentValidationError):
            validate_supplier_invoice_document_upload(
                self._file(self._valid_pdf_content(), "factura.pdf", "image/png")
            )

    def test_oversized_file_is_rejected_before_storage(self):
        oversized = b"x" * ((15 * 1024 * 1024) + 1)
        with self.assertRaises(SupplierInvoiceDocumentValidationError):
            validate_supplier_invoice_document_upload(
                self._file(oversized, "factura.pdf", "application/pdf")
            )

    def test_duplicate_hash_is_a_warning_not_a_blocker(self):
        storage = Mock()
        content = self._valid_pdf_content()
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            first = upload_supplier_invoice_document(
                self._file(content, "one.pdf", "application/pdf"),
                supplier_invoice=invoice,
                db_session=db.session,
                storage=storage,
            )
            db.session.commit()
            second = upload_supplier_invoice_document(
                self._file(content, "two.pdf", "application/pdf"),
                supplier_invoice=invoice,
                db_session=db.session,
                storage=storage,
            )
            self.assertEqual(first.duplicate_count, 0)
            self.assertEqual(second.duplicate_count, 1)

    def test_registered_supplier_invoice_rejects_new_documents(self):
        storage = Mock()
        with self.app.app_context():
            invoice = self._make_invoice(registered=True)
            db.session.add(invoice)
            db.session.commit()
            with self.assertRaises(SupplierInvoiceDocumentImmutabilityError):
                upload_supplier_invoice_document(
                    self._file(self._valid_pdf_content(), "factura.pdf", "application/pdf"),
                    supplier_invoice=invoice,
                    db_session=db.session,
                    storage=storage,
                )
            storage.put_document.assert_not_called()

    def test_storage_failure_leaves_no_document_metadata(self):
        storage = Mock()
        storage.put_document.side_effect = SupplierInvoiceDocumentStorageOperationError("R2 unavailable")
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            with self.assertRaises(SupplierInvoiceDocumentStorageOperationError):
                upload_supplier_invoice_document(
                    self._file(self._valid_pdf_content(), "factura.pdf", "application/pdf"),
                    supplier_invoice=invoice,
                    db_session=db.session,
                    storage=storage,
                )
            self.assertEqual(db.session.query(SupplierInvoiceDocument).count(), 0)

    def test_metadata_failure_compensates_the_uploaded_object(self):
        class FailingSession:
            def query(self, *_args):
                return self

            def filter(self, *_args):
                return self

            def count(self):
                return 0

            def add(self, _document):
                pass

            def flush(self):
                raise RuntimeError("database unavailable")

        storage = Mock()
        with self.app.app_context():
            with self.assertRaises(SupplierInvoiceDocumentPersistenceError):
                upload_supplier_invoice_document(
                    self._file(self._valid_pdf_content(), "factura.pdf", "application/pdf"),
                    db_session=FailingSession(),
                    storage=storage,
                )
        storage.put_document.assert_called_once()
        storage.delete_document.assert_called_once()

    def test_r2_adapter_uses_the_private_s3_client(self):
        client = Mock()
        settings = SupplierInvoiceDocumentStorageSettings(
            provider="r2",
            bucket_name="bucket",
            endpoint_url="https://example.r2.cloudflarestorage.com",
            access_key_id="key",
            secret_access_key="secret",
        )
        adapter = R2SupplierInvoiceDocumentStorage(settings, client=client)

        adapter.put_document(storage_key="supplier-invoices/2026/08/test.pdf", content=b"pdf", mime_type="application/pdf")
        client.put_object.assert_called_once_with(
            Bucket="bucket",
            Key="supplier-invoices/2026/08/test.pdf",
            Body=b"pdf",
            ContentType="application/pdf",
        )

    def test_delete_document_removes_each_permitted_extraction_state(self):
        storage = Mock()
        permitted_statuses = (
            SupplierInvoiceExtraction.STATUS_FAILED,
            SupplierInvoiceExtraction.STATUS_EXTRACTED,
            SupplierInvoiceExtraction.STATUS_NEEDS_REVIEW,
        )
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            for index, status in enumerate(permitted_statuses, start=1):
                document = SupplierInvoiceDocument(
                    supplier_invoice=invoice,
                    storage_provider="r2",
                    storage_key=f"supplier-invoices/2026/08/delete-{index}.pdf",
                    original_filename=f"delete-{index}.pdf",
                    mime_type="application/pdf",
                    file_size=4,
                    sha256=(str(index) * 64),
                    processing_status=status,
                )
                db.session.add(document)
                db.session.flush()
                extraction = SupplierInvoiceExtraction(
                    supplier_invoice_document=document,
                    provider="fake",
                    extractor_version="fake-v1",
                    status=status,
                    payload_schema_version=1,
                    extraction_payload={"schema_version": 1},
                    payload_hash="a" * 64,
                    completed_at=datetime.now(timezone.utc),
                )
                db.session.add(extraction)
                db.session.commit()

                self.assertTrue(can_delete_supplier_invoice_document(document))
                delete_supplier_invoice_document(document, db_session=db.session, storage=storage)
                self.assertIsNone(db.session.get(SupplierInvoiceDocument, document.id))
                self.assertIsNone(db.session.get(SupplierInvoiceExtraction, extraction.id))

        self.assertEqual(storage.delete_document.call_count, len(permitted_statuses))

    def test_delete_document_blocks_noneditable_invoices_and_extractions(self):
        storage = Mock()
        blocked_statuses = (
            SupplierInvoiceExtraction.STATUS_EXTRACTING,
            SupplierInvoiceExtraction.STATUS_APPLIED,
        )
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            for index, status in enumerate(blocked_statuses, start=1):
                document = SupplierInvoiceDocument(
                    supplier_invoice=invoice,
                    storage_provider="r2",
                    storage_key=f"supplier-invoices/2026/08/blocked-{index}.pdf",
                    original_filename="blocked.pdf",
                    mime_type="application/pdf",
                    file_size=4,
                    sha256=(str(index) * 64),
                    processing_status=status,
                )
                db.session.add(document)
                db.session.flush()
                db.session.add(
                    SupplierInvoiceExtraction(
                        supplier_invoice_document=document,
                        provider="fake",
                        extractor_version="fake-v1",
                        status=status,
                        payload_schema_version=1,
                        extraction_payload={"schema_version": 1} if status == "applied" else None,
                        payload_hash="b" * 64 if status == "applied" else None,
                        completed_at=datetime.now(timezone.utc) if status == "applied" else None,
                    )
                )
                db.session.commit()
                self.assertFalse(can_delete_supplier_invoice_document(document))
                with self.assertRaises(SupplierInvoiceDocumentDeletionBlockedError):
                    delete_supplier_invoice_document(document, db_session=db.session, storage=storage)

            invoice.status = SupplierInvoice.STATUS_CANCELLED
            db.session.commit()
            standalone = SupplierInvoiceDocument(
                supplier_invoice=invoice,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/cancelled.pdf",
                original_filename="cancelled.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="c" * 64,
            )
            db.session.add(standalone)
            db.session.commit()
            self.assertFalse(can_delete_supplier_invoice_document(standalone))

            registered = self._make_invoice(registered=True)
            db.session.add(registered)
            db.session.flush()
            registered_document = SupplierInvoiceDocument(
                supplier_invoice=registered,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/registered.pdf",
                original_filename="registered.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="g" * 64,
            )
            db.session.add(registered_document)
            db.session.commit()
            self.assertFalse(can_delete_supplier_invoice_document(registered_document))

        storage.delete_document.assert_not_called()

    def test_delete_document_storage_failure_is_marked_and_can_be_retried(self):
        storage = Mock()
        storage.delete_document.side_effect = [
            SupplierInvoiceDocumentStorageOperationError("R2 unavailable"),
            None,
        ]
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            document = SupplierInvoiceDocument(
                supplier_invoice=invoice,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/retry.pdf",
                original_filename="retry.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="d" * 64,
            )
            db.session.add(document)
            db.session.commit()
            document_id = document.id

            with self.assertRaises(SupplierInvoiceDocumentDeletionStorageError):
                delete_supplier_invoice_document(document, db_session=db.session, storage=storage)
            failed = db.session.get(SupplierInvoiceDocument, document_id)
            self.assertEqual(failed.processing_status, SupplierInvoiceDocument.STATUS_DELETE_FAILED)
            self.assertTrue(can_delete_supplier_invoice_document(failed))

            delete_supplier_invoice_document(failed, db_session=db.session, storage=storage)
            self.assertIsNone(db.session.get(SupplierInvoiceDocument, document_id))

    def test_delete_document_keeps_other_documents_and_extractions(self):
        storage = Mock()
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            first = SupplierInvoiceDocument(
                supplier_invoice=invoice,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/remove.pdf",
                original_filename="remove.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="e" * 64,
            )
            second = SupplierInvoiceDocument(
                supplier_invoice=invoice,
                storage_provider="r2",
                storage_key="supplier-invoices/2026/08/keep.pdf",
                original_filename="keep.pdf",
                mime_type="application/pdf",
                file_size=4,
                sha256="f" * 64,
            )
            db.session.add_all((first, second))
            db.session.flush()
            second_extraction = SupplierInvoiceExtraction(
                supplier_invoice_document=second,
                provider="fake",
                extractor_version="fake-v1",
                status=SupplierInvoiceExtraction.STATUS_FAILED,
                payload_schema_version=1,
                completed_at=datetime.now(timezone.utc),
            )
            db.session.add(second_extraction)
            db.session.commit()
            first_id, second_id, extraction_id = first.id, second.id, second_extraction.id

            delete_supplier_invoice_document(first, db_session=db.session, storage=storage)
            self.assertIsNone(db.session.get(SupplierInvoiceDocument, first_id))
            self.assertIsNotNone(db.session.get(SupplierInvoiceDocument, second_id))
            self.assertIsNotNone(db.session.get(SupplierInvoiceExtraction, extraction_id))

    def test_document_relationship_is_many_to_one_without_delete_cascade(self):
        relationship = SupplierInvoice.documents.property
        extraction_relationship = SupplierInvoiceDocument.extractions.property
        foreign_key = next(iter(SupplierInvoiceDocument.__table__.foreign_keys))

        self.assertNotIn("delete", relationship.cascade)
        self.assertNotIn("delete-orphan", relationship.cascade)
        self.assertNotIn("delete", extraction_relationship.cascade)
        self.assertNotIn("delete-orphan", extraction_relationship.cascade)
        self.assertEqual(foreign_key.ondelete, "RESTRICT")


if __name__ == "__main__":
    unittest.main()

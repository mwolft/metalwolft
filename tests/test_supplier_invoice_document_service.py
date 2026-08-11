import hashlib
import importlib.util
import sys
import unittest
from datetime import date
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
        SupplierInvoiceTaxBreakdown,
        db,
    )
    from api.supplier_invoice_document_service import (
        SupplierInvoiceDocumentImmutabilityError,
        SupplierInvoiceDocumentPersistenceError,
        SupplierInvoiceDocumentValidationError,
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

    def test_document_relationship_is_many_to_one_without_delete_cascade(self):
        relationship = SupplierInvoice.documents.property
        foreign_key = next(iter(SupplierInvoiceDocument.__table__.foreign_keys))

        self.assertNotIn("delete", relationship.cascade)
        self.assertNotIn("delete-orphan", relationship.cascade)
        self.assertEqual(foreign_key.ondelete, "RESTRICT")


if __name__ == "__main__":
    unittest.main()

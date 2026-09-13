import sys
import unittest
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from PIL import Image
from pypdf import PdfWriter
from werkzeug.datastructures import FileStorage


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.design_result_service import (  # noqa: E402
    DesignResultPersistenceError,
    DesignResultStateError,
    DesignResultValidationError,
    is_design_result_available,
    result_metadata_state,
    upload_design_result,
)
from api.models import (  # noqa: E402
    Categories,
    DesignRequest,
    DesignRequestItem,
    OrderDetails,
    Orders,
    Products,
    Users,
    db,
)
from api.private_object_storage import PrivateObjectStorageOperationError  # noqa: E402


class _PrivateStorage:
    def __init__(self, *, fail_put=False):
        self.fail_put = fail_put
        self.puts = []
        self.deleted = []

    def put_object(self, *, storage_key, content, mime_type):
        if self.fail_put:
            raise PrivateObjectStorageOperationError("R2 unavailable")
        self.puts.append((storage_key, content, mime_type))

    def delete_object(self, *, storage_key):
        self.deleted.append(storage_key)


class DesignResultServiceTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            DESIGN_RESULT_MAX_BYTES=15 * 1024 * 1024,
        )
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            category = Categories(
                nombre="Rejas",
                descripcion="Categoría de pruebas",
                slug="rejas-design-result-test",
            )
            db.session.add(category)
            db.session.flush()
            self.product = Products(
                slug="reja-design-result-test",
                nombre="Reja de prueba",
                descripcion="Producto de pruebas",
                precio=100,
                categoria_id=category.id,
            )
            self.user = Users(
                email="cliente-design@example.test",
                password="not-a-real-password",
                firstname="Cliente",
                lastname="Diseño",
            )
            db.session.add_all((self.product, self.user))
            db.session.commit()
            self.product_id = self.product.id
            self.user_id = self.user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_in_progress_request(self, suffix):
        product = db.session.get(Products, self.product_id)
        order = Orders(
            user_id=self.user_id,
            locator=f"DR{suffix:04d}",
            total_amount=24.95,
            order_status="pendiente",
        )
        db.session.add(order)
        db.session.flush()
        detail = OrderDetails(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            line_type="design_service",
            alto=120,
            ancho=200,
            screw_option="not_applicable",
            screw_supplement=0,
            precio_total=24.95,
            shipping_cost=0,
        )
        design_request = DesignRequest(
            reference=f"DP-RESULT-{suffix}",
            creation_key=f"design-result-{suffix}",
            user_id=self.user_id,
            order_id=order.id,
            subtotal_gross=24.95,
            price_gross=24.95,
            discount_amount=0,
            currency="EUR",
            lead_time_hours=24,
            status=DesignRequest.STATUS_IN_PROGRESS,
        )
        db.session.add_all((detail, design_request))
        db.session.flush()
        db.session.add(
            DesignRequestItem(
                design_request_id=design_request.id,
                product_id=product.id,
                product_name=product.nombre,
                width_cm=200,
                height_cm=120,
                order_detail_id=detail.id,
            )
        )
        db.session.commit()
        return design_request.id

    @staticmethod
    def _pdf_bytes():
        output = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(output)
        return output.getvalue()

    @staticmethod
    def _image_bytes(image_format):
        output = BytesIO()
        Image.new("RGB", (8, 8), color="white").save(output, format=image_format)
        return output.getvalue()

    @staticmethod
    def _upload(content, filename, mime_type):
        return FileStorage(
            stream=BytesIO(content),
            filename=filename,
            content_type=mime_type,
        )

    def test_uploads_pdf_png_and_jpeg_then_closes_delivery(self):
        cases = (
            ("resultado.pdf", "application/pdf", self._pdf_bytes()),
            ("resultado.png", "image/png", self._image_bytes("PNG")),
            ("resultado.jpg", "image/jpeg", self._image_bytes("JPEG")),
        )
        with self.app.app_context():
            for index, (filename, mime_type, content) in enumerate(cases, start=1):
                request_id = self._create_in_progress_request(index)
                storage = _PrivateStorage()
                result = upload_design_result(
                    design_request_id=request_id,
                    file_storage=self._upload(content, filename, mime_type),
                    db_session=db.session,
                    storage=storage,
                    now=datetime(2026, 9, 12, tzinfo=timezone.utc),
                )
                db.session.commit()

                design_request = db.session.get(DesignRequest, request_id)
                self.assertEqual(design_request.status, DesignRequest.STATUS_DELIVERED)
                self.assertEqual(design_request.result_filename, filename)
                self.assertEqual(design_request.result_mime, mime_type)
                self.assertEqual(design_request.result_size, len(content))
                self.assertEqual(len(design_request.result_sha256), 64)
                self.assertTrue(design_request.result_storage_key.startswith("design-results/2026/09/"))
                self.assertTrue(is_design_result_available(design_request))
                self.assertEqual(result_metadata_state(design_request), "complete")
                self.assertEqual(len(storage.puts), 1)
                self.assertEqual(storage.puts[0][2], mime_type)
                self.assertEqual(result.storage_key, design_request.result_storage_key)

    def test_rejects_invalid_extension_mime_content_and_size_without_mutating_request(self):
        cases = (
            ("resultado.txt", "text/plain", b"not allowed"),
            ("resultado.pdf", "image/png", self._pdf_bytes()),
            ("resultado.png", "image/png", b"not an image"),
            ("resultado.pdf", "application/pdf", b"x" * ((15 * 1024 * 1024) + 1)),
        )
        with self.app.app_context():
            for index, (filename, mime_type, content) in enumerate(cases, start=10):
                request_id = self._create_in_progress_request(index)
                storage = _PrivateStorage()
                with self.assertRaises(DesignResultValidationError):
                    upload_design_result(
                        design_request_id=request_id,
                        file_storage=self._upload(content, filename, mime_type),
                        db_session=db.session,
                        storage=storage,
                    )
                design_request = db.session.get(DesignRequest, request_id)
                self.assertEqual(design_request.status, DesignRequest.STATUS_IN_PROGRESS)
                self.assertEqual(result_metadata_state(design_request), "empty")
                self.assertEqual(storage.puts, [])

    def test_blocks_pending_delivered_and_partial_requests_without_new_upload(self):
        with self.app.app_context():
            pending_id = self._create_in_progress_request(20)
            pending_request = db.session.get(DesignRequest, pending_id)
            pending_request.status = DesignRequest.STATUS_PENDING
            db.session.commit()

            delivered_id = self._create_in_progress_request(21)
            delivered_request = db.session.get(DesignRequest, delivered_id)
            delivered_request.status = DesignRequest.STATUS_DELIVERED
            delivered_request.result_storage_key = "design-results/existing.pdf"
            db.session.commit()

            partial_id = self._create_in_progress_request(22)
            partial_request = db.session.get(DesignRequest, partial_id)
            partial_request.result_filename = "partial.pdf"
            db.session.commit()

            for request_id in (pending_id, delivered_id, partial_id):
                storage = _PrivateStorage()
                with self.assertRaises(DesignResultStateError):
                    upload_design_result(
                        design_request_id=request_id,
                        file_storage=self._upload(
                            self._pdf_bytes(), "resultado.pdf", "application/pdf"
                        ),
                        db_session=db.session,
                        storage=storage,
                    )
                self.assertEqual(storage.puts, [])

    def test_storage_failure_and_metadata_flush_failure_do_not_leave_a_delivered_request(self):
        with self.app.app_context():
            storage_failure_id = self._create_in_progress_request(30)
            failing_storage = _PrivateStorage(fail_put=True)
            with self.assertRaises(PrivateObjectStorageOperationError):
                upload_design_result(
                    design_request_id=storage_failure_id,
                    file_storage=self._upload(
                        self._pdf_bytes(), "resultado.pdf", "application/pdf"
                    ),
                    db_session=db.session,
                    storage=failing_storage,
                )
            self.assertEqual(
                db.session.get(DesignRequest, storage_failure_id).status,
                DesignRequest.STATUS_IN_PROGRESS,
            )

            flush_failure_id = self._create_in_progress_request(31)
            storage = _PrivateStorage()
            with patch.object(db.session, "flush", side_effect=RuntimeError("database write failed")):
                with self.assertRaises(DesignResultPersistenceError):
                    upload_design_result(
                        design_request_id=flush_failure_id,
                        file_storage=self._upload(
                            self._pdf_bytes(), "resultado.pdf", "application/pdf"
                        ),
                        db_session=db.session,
                        storage=storage,
                    )
            self.assertEqual(len(storage.puts), 1)
            self.assertEqual(storage.deleted, [storage.puts[0][0]])
            db.session.rollback()

    def test_second_upload_after_commit_is_rejected_without_a_second_object(self):
        with self.app.app_context():
            request_id = self._create_in_progress_request(40)
            storage = _PrivateStorage()
            upload_design_result(
                design_request_id=request_id,
                file_storage=self._upload(self._pdf_bytes(), "resultado.pdf", "application/pdf"),
                db_session=db.session,
                storage=storage,
            )
            db.session.commit()

            with self.assertRaises(DesignResultStateError):
                upload_design_result(
                    design_request_id=request_id,
                    file_storage=self._upload(self._pdf_bytes(), "otro.pdf", "application/pdf"),
                    db_session=db.session,
                    storage=storage,
                )
            self.assertEqual(len(storage.puts), 1)


if __name__ == "__main__":
    unittest.main()

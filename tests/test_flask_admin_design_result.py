import base64
import json
import re
import struct
import sys
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from flask import Flask
from flask_admin import Admin
from pypdf import PdfWriter
from PIL import Image
from sqlalchemy.orm import configure_mappers
from werkzeug.datastructures import FileStorage


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import api.admin as admin_module  # noqa: E402
from api.models import (  # noqa: E402
    Categories,
    DesignRequest,
    DesignRequestItem,
    DesignDeliverable,
    OrderDetails,
    Orders,
    Products,
    Users,
    db,
)
from api.design_delivery_service import validate_glb, DesignDeliveryError  # noqa: E402
from api.private_object_storage import PrivateObjectStorageOperationError  # noqa: E402


class _Storage:
    def __init__(self):
        self.puts = []
        self.deleted = []
        self.objects = {}

    def put_object(self, *, storage_key, content, mime_type):
        self.puts.append((storage_key, content, mime_type))
        self.objects[storage_key] = content

    def delete_object(self, *, storage_key):
        self.deleted.append(storage_key)
        self.objects.pop(storage_key, None)

    def get_object(self, *, storage_key):
        return self.objects[storage_key]


class FlaskAdminDesignResultTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"
        configure_mappers()
        self.app = Flask(__name__, template_folder=str(SRC_DIR / "templates"))
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            FRONTEND_URL="https://www.metalwolft.com",
            MAIL_USERNAME="admin@example.test",
        )
        db.init_app(self.app)
        self.admin = Admin(self.app, url="/admin")
        self.view = admin_module.DesignRequestAdminView(
            DesignRequest,
            db.session,
            name="Solicitudes",
        )
        self.admin.add_view(self.view)
        with self.app.app_context():
            db.create_all()
            self.request_id = self._create_design_request()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_design_request(self):
        category = Categories(
            nombre="Rejas",
            descripcion="Categoría de pruebas",
            slug="rejas-admin-design-result",
        )
        user = Users(
            email="admin-design-result@example.test",
            password="not-a-real-password",
            firstname="Ana",
            lastname="Cliente",
        )
        db.session.add_all((category, user))
        db.session.flush()
        product = Products(
            slug="reja-admin-design-result",
            nombre="Reja Maryland",
            descripcion="Producto de pruebas",
            precio=100,
            categoria_id=category.id,
        )
        db.session.add(product)
        db.session.flush()
        order = Orders(user_id=user.id, locator="DRADMIN1", total_amount=24.95)
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
            reference="DP-ADMIN-1",
            creation_key="admin-design-result-1",
            user_id=user.id,
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
    def _csrf_and_submission(html):
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', html)
        submission = re.search(r'name="submission_token" value="([^"]+)"', html)
        if not csrf or not submission:
            raise AssertionError("The secure upload form did not include both tokens.")
        return csrf.group(1), submission.group(1)

    def _auth_header(self):
        token = base64.b64encode(b"admin:secret").decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _upload_url(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".upload_result"):
                return rule.rule.replace("<int:design_request_id>", str(self.request_id))
        raise AssertionError("The design result upload route was not registered.")

    def _v2_url(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".manage_deliverables"):
                return rule.rule.replace("<int:design_request_id>", str(self.request_id))
        raise AssertionError("The design deliverables route was not registered.")

    def _v2_form(self):
        response = self.client.get(self._v2_url(), headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        return self._csrf_and_submission(response.data.decode("utf-8"))

    @staticmethod
    def _glb_bytes(external=False):
        scene = {"asset": {"version": "2.0"}, "scenes": [{}]}
        if external:
            scene["buffers"] = [{"uri": "https://example.test/model.bin"}]
        payload = json.dumps(scene).encode("utf-8")
        payload += b" " * (-len(payload) % 4)
        return struct.pack("<4sII", b"glTF", 2, 20 + len(payload)) + struct.pack("<II", len(payload), 0x4E4F534A) + payload

    @staticmethod
    def _png_bytes():
        output = BytesIO()
        Image.new("RGB", (2, 2), "white").save(output, format="PNG")
        return output.getvalue()

    def test_v2_glb_rejects_external_dependencies(self):
        with self.assertRaisesRegex(DesignDeliveryError, "recursos externos"):
            validate_glb(FileStorage(stream=BytesIO(self._glb_bytes(True)), filename="private.glb"))
        with self.assertRaises(DesignDeliveryError):
            validate_glb(FileStorage(stream=BytesIO(b"not a glb"), filename="invalid.glb"))
        self.assertEqual(validate_glb(FileStorage(stream=BytesIO(self._glb_bytes()), filename="private.glb")), self._glb_bytes())

    def test_v2_admin_requires_authentication(self):
        self.assertEqual(self.client.get(self._v2_url()).status_code, 401)

    def test_v2_admin_delivers_multiple_files_once_and_updates(self):
        with self.app.app_context():
            request_model = db.session.get(DesignRequest, self.request_id)
            second = DesignRequestItem(
                design_request_id=request_model.id, product_id=request_model.items[0].product_id,
                product_name="Reja Maryland", width_cm=180, height_cm=100,
            )
            db.session.add(second)
            db.session.commit()
            first_id, second_id = [item.id for item in request_model.items]
        csrf, submission = self._v2_form()
        storage = _Storage()
        send_email = Mock(return_value=True)
        with (
            patch("api.admin.get_private_object_storage", return_value=storage),
            patch("api.admin.send_design_result_ready_email", send_email),
        ):
            response = self.client.post(
                self._v2_url(),
                data={
                    "csrf_token": csrf, "submission_token": submission,
                    "customer_message": "Diseños preparados", "notify": "yes",
                    f"glb_{first_id}": (BytesIO(self._glb_bytes()), "modelo.glb", "model/gltf-binary"),
                    f"images_{first_id}": [
                        (BytesIO(self._png_bytes()), "vista.png", "image/png"),
                        (BytesIO(self._png_bytes()), "detalle.png", "image/png"),
                    ],
                    f"pdfs_{second_id}": [
                        (BytesIO(self._pdf_bytes()), "plano.pdf", "application/pdf"),
                        (BytesIO(self._pdf_bytes()), "instrucciones.pdf", "application/pdf"),
                    ],
                },
                headers=self._auth_header(), follow_redirects=False,
            )
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            self.assertNotIn("error", [category for category, _message in session.get("_flashes", [])], session.get("_flashes"))
        send_email.assert_called_once()
        with self.app.app_context():
            request_model = db.session.get(DesignRequest, self.request_id)
            self.assertEqual(request_model.status, DesignRequest.STATUS_DELIVERED)
            self.assertEqual(request_model.customer_message, "Diseños preparados")
            self.assertEqual(len([file for item in request_model.items for file in item.deliverables if file.active]), 5)
            old_glb = next(file for file in request_model.items[0].deliverables if file.kind == "glb")
            old_glb_id = old_glb.id
        csrf, submission = self._v2_form()
        with (
            patch("api.admin.get_private_object_storage", return_value=storage),
            patch("api.admin.send_design_result_ready_email", send_email),
        ):
            response = self.client.post(
                self._v2_url(),
                data={
                    "csrf_token": csrf, "submission_token": submission,
                    "customer_message": "Diseños preparados", "retire_ids": str(old_glb_id),
                    f"glb_{first_id}": (BytesIO(self._glb_bytes()), "modelo-v2.glb", "model/gltf-binary"),
                },
                headers=self._auth_header(), follow_redirects=False,
            )
        self.assertEqual(response.status_code, 302)
        send_email.assert_called_once()
        with self.app.app_context():
            self.assertFalse(db.session.get(DesignDeliverable, old_glb_id).active)
            self.assertEqual(len([file for file in db.session.get(DesignRequestItem, first_id).deliverables if file.kind == "glb" and file.active]), 1)
        self.assertEqual(len(storage.puts), 6)

    def test_v2_rejects_incomplete_delivery_without_changing_status(self):
        csrf, submission = self._v2_form()
        storage = _Storage()
        with patch("api.admin.get_private_object_storage", return_value=storage):
            response = self.client.post(
                self._v2_url(),
                data={"csrf_token": csrf, "submission_token": submission, "customer_message": "Listo"},
                headers=self._auth_header(),
            )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            request_model = db.session.get(DesignRequest, self.request_id)
            self.assertEqual(request_model.status, DesignRequest.STATUS_IN_PROGRESS)
            self.assertIsNone(request_model.customer_message)

    def test_v2_email_failure_does_not_lose_delivery(self):
        with self.app.app_context():
            item_id = db.session.get(DesignRequest, self.request_id).items[0].id
        csrf, submission = self._v2_form()
        storage = _Storage()
        with (
            patch("api.admin.get_private_object_storage", return_value=storage),
            patch("api.admin.send_design_result_ready_email", return_value=False) as send_email,
        ):
            response = self.client.post(
                self._v2_url(),
                data={
                    "csrf_token": csrf, "submission_token": submission,
                    "customer_message": "Listo", "notify": "yes",
                    f"pdfs_{item_id}": (BytesIO(self._pdf_bytes()), "plano.pdf", "application/pdf"),
                },
                headers=self._auth_header(),
            )
        self.assertEqual(response.status_code, 302)
        send_email.assert_called_once()
        with self.client.session_transaction() as session:
            self.assertIn("warning", [category for category, _ in session.get("_flashes", [])])
        with self.app.app_context():
            self.assertEqual(db.session.get(DesignRequest, self.request_id).status, DesignRequest.STATUS_DELIVERED)

    def test_v2_storage_failure_compensates_and_rolls_back(self):
        class FailingStorage(_Storage):
            def put_object(self, *, storage_key, content, mime_type):
                if self.puts:
                    raise PrivateObjectStorageOperationError("synthetic failure")
                super().put_object(storage_key=storage_key, content=content, mime_type=mime_type)

        with self.app.app_context():
            item_id = db.session.get(DesignRequest, self.request_id).items[0].id
        csrf, submission = self._v2_form()
        storage = FailingStorage()
        with patch("api.admin.get_private_object_storage", return_value=storage):
            response = self.client.post(
                self._v2_url(),
                data={
                    "csrf_token": csrf, "submission_token": submission,
                    f"images_{item_id}": [
                        (BytesIO(self._png_bytes()), "uno.png", "image/png"),
                        (BytesIO(self._png_bytes()), "dos.png", "image/png"),
                    ],
                },
                headers=self._auth_header(),
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(storage.deleted), 2)
        self.assertFalse(storage.objects)
        with self.app.app_context():
            self.assertEqual(db.session.get(DesignRequest, self.request_id).status, DesignRequest.STATUS_IN_PROGRESS)
            self.assertEqual(db.session.query(DesignDeliverable).count(), 0)

    def test_v2_cannot_retire_last_file_of_delivered_design(self):
        with self.app.app_context():
            request_model = db.session.get(DesignRequest, self.request_id)
            request_model.status = DesignRequest.STATUS_DELIVERED
            file = DesignDeliverable(
                design_request_item_id=request_model.items[0].id,
                kind="pdf", storage_key="design-results/test-last.pdf",
                filename="last.pdf", mime_type="application/pdf", size_bytes=8,
                sha256="a" * 64,
            )
            db.session.add(file)
            db.session.commit()
            file_id = file.id
        csrf, submission = self._v2_form()
        with patch("api.admin.get_private_object_storage", return_value=_Storage()):
            response = self.client.post(
                self._v2_url(),
                data={"csrf_token": csrf, "submission_token": submission, "retire_ids": str(file_id)},
                headers=self._auth_header(),
            )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertTrue(db.session.get(DesignDeliverable, file_id).active)
            self.assertEqual(db.session.get(DesignRequest, self.request_id).status, DesignRequest.STATUS_DELIVERED)

    def _edit_status(self, initial_status, submitted_status):
        with self.app.app_context():
            design_request = db.session.get(DesignRequest, self.request_id)
            design_request.status = initial_status
            db.session.commit()
        with self.app.test_request_context():
            edit_url = self.view.get_url(f"{self.view.endpoint}.edit_view", id=self.request_id)
        response = self.client.post(
            edit_url,
            data={"status": submitted_status},
            headers=self._auth_header(),
            follow_redirects=True,
        )
        with self.app.app_context():
            db.session.expire_all()
            persisted_status = db.session.get(DesignRequest, self.request_id).status
        return response, persisted_status

    def test_admin_edit_starts_pending_request(self):
        response, status = self._edit_status(DesignRequest.STATUS_PENDING, DesignRequest.STATUS_IN_PROGRESS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(status, DesignRequest.STATUS_IN_PROGRESS)
        self.assertNotIn(b"Failed to update record", response.data)

    def test_admin_edit_rejects_unpaid_request_without_persisting(self):
        response, status = self._edit_status(DesignRequest.STATUS_PENDING_PAYMENT, DesignRequest.STATUS_IN_PROGRESS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(status, DesignRequest.STATUS_PENDING_PAYMENT)
        self.assertIn(b"Failed to update record", response.data)

    def test_admin_edit_allows_unchanged_status(self):
        response, status = self._edit_status(DesignRequest.STATUS_PENDING, DesignRequest.STATUS_PENDING)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(status, DesignRequest.STATUS_PENDING)
        self.assertNotIn(b"Failed to update record", response.data)

    def test_admin_edit_cannot_deliver_without_upload(self):
        response, status = self._edit_status(DesignRequest.STATUS_IN_PROGRESS, DesignRequest.STATUS_DELIVERED)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(status, DesignRequest.STATUS_IN_PROGRESS)
        self.assertIn(b"SUBIR RESULTADO", response.data)

    def _upload_form(self):
        response = self.client.get(self._upload_url(), headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn("SUBIR Y ENTREGAR", response.get_data(as_text=True))
        return self._csrf_and_submission(response.get_data(as_text=True))

    def test_upload_commits_delivery_then_sends_one_email_and_rejects_replay(self):
        csrf_token, submission_token = self._upload_form()
        storage = _Storage()
        send_email = Mock(return_value=True)
        data = {
            "csrf_token": csrf_token,
            "submission_token": submission_token,
            "result": (BytesIO(self._pdf_bytes()), "resultado.pdf", "application/pdf"),
        }

        with (
            patch("api.design_result_service.get_private_object_storage", return_value=storage),
            patch("api.admin.send_design_result_ready_email", send_email),
        ):
            response = self.client.post(
                self._upload_url(),
                data=data,
                headers=self._auth_header(),
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            design_request = db.session.get(DesignRequest, self.request_id)
            self.assertEqual(design_request.status, DesignRequest.STATUS_DELIVERED)
            self.assertTrue(design_request.result_storage_key)
        self.assertEqual(len(storage.puts), 1)
        send_email.assert_called_once()

        replay = self.client.post(
            self._upload_url(),
            data={
                "csrf_token": csrf_token,
                "submission_token": submission_token,
                "result": (BytesIO(self._pdf_bytes()), "otro.pdf", "application/pdf"),
            },
            headers=self._auth_header(),
            follow_redirects=False,
        )
        self.assertEqual(replay.status_code, 302)
        self.assertEqual(len(storage.puts), 1)
        send_email.assert_called_once()

    def test_invalid_csrf_does_not_upload_or_send(self):
        storage = _Storage()
        send_email = Mock(return_value=True)
        with (
            patch("api.design_result_service.get_private_object_storage", return_value=storage),
            patch("api.admin.send_design_result_ready_email", send_email),
        ):
            response = self.client.post(
                self._upload_url(),
                data={
                    "csrf_token": "invalid",
                    "submission_token": "invalid",
                    "result": (BytesIO(self._pdf_bytes()), "resultado.pdf", "application/pdf"),
                },
                headers=self._auth_header(),
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(storage.puts, [])
        send_email.assert_not_called()

    def test_crud_cannot_mark_a_request_delivered_without_uploading_a_result(self):
        with self.app.app_context():
            design_request = db.session.get(DesignRequest, self.request_id)
            form = SimpleNamespace(
                status=SimpleNamespace(data=DesignRequest.STATUS_DELIVERED)
            )
            with self.assertRaisesRegex(ValueError, "SUBIR RESULTADO"):
                self.view.on_model_change(form, design_request, False)

    def test_email_failure_after_commit_does_not_revert_the_delivered_result(self):
        csrf_token, submission_token = self._upload_form()
        storage = _Storage()
        send_email = Mock(return_value=False)
        with (
            patch("api.design_result_service.get_private_object_storage", return_value=storage),
            patch("api.admin.send_design_result_ready_email", send_email),
        ):
            response = self.client.post(
                self._upload_url(),
                data={
                    "csrf_token": csrf_token,
                    "submission_token": submission_token,
                    "result": (BytesIO(self._pdf_bytes()), "resultado.pdf", "application/pdf"),
                },
                headers=self._auth_header(),
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 302)
        send_email.assert_called_once()
        self.assertEqual(storage.deleted, [])
        with self.app.app_context():
            design_request = db.session.get(DesignRequest, self.request_id)
            self.assertEqual(design_request.status, DesignRequest.STATUS_DELIVERED)
            self.assertTrue(design_request.result_storage_key)

    def test_commit_failure_compensates_private_object_and_never_sends_email(self):
        csrf_token, submission_token = self._upload_form()
        storage = _Storage()
        send_email = Mock(return_value=True)
        with (
            patch("api.design_result_service.get_private_object_storage", return_value=storage),
            patch("api.admin.send_design_result_ready_email", send_email),
            patch.object(self.view.session, "commit", side_effect=RuntimeError("db unavailable")),
        ):
            response = self.client.post(
                self._upload_url(),
                data={
                    "csrf_token": csrf_token,
                    "submission_token": submission_token,
                    "result": (BytesIO(self._pdf_bytes()), "resultado.pdf", "application/pdf"),
                },
                headers=self._auth_header(),
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(storage.puts), 1)
        self.assertEqual(storage.deleted, [storage.puts[0][0]])
        send_email.assert_not_called()
        with self.app.app_context():
            design_request = db.session.get(DesignRequest, self.request_id)
            self.assertEqual(design_request.status, DesignRequest.STATUS_IN_PROGRESS)
            self.assertIsNone(design_request.result_storage_key)


if __name__ == "__main__":
    unittest.main()

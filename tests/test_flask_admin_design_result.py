import base64
import re
import sys
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from flask import Flask
from flask_admin import Admin
from pypdf import PdfWriter
from sqlalchemy.orm import configure_mappers


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import api.admin as admin_module  # noqa: E402
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


class _Storage:
    def __init__(self):
        self.puts = []
        self.deleted = []

    def put_object(self, *, storage_key, content, mime_type):
        self.puts.append((storage_key, content, mime_type))

    def delete_object(self, *, storage_key):
        self.deleted.append(storage_key)


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

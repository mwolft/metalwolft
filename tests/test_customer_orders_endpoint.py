import importlib.util
import os
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.customer_order_serializers import (  # noqa: E402
    public_order_status,
    serialize_customer_order_detail,
    serialize_customer_order_summary,
)


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ENDPOINT_DEPS = all(
    has_package(package)
    for package in ("flask", "flask_jwt_extended", "flask_sqlalchemy", "sqlalchemy")
)

if HAS_ENDPOINT_DEPS:
    from flask import Flask  # noqa: E402
    from flask_jwt_extended import JWTManager, create_access_token  # noqa: E402

    from api.models import Categories, Invoices, OrderDetails, Orders, Products, Users, db  # noqa: E402
    from api.routes import api  # noqa: E402


class CustomerOrderSerializerTest(unittest.TestCase):
    def test_public_status_mapping_uses_safe_fallback(self):
        self.assertEqual(
            public_order_status("fabricacion"),
            {"code": "fabricacion", "label": "En fabricación"},
        )
        self.assertEqual(
            public_order_status("estado_historico"),
            {"code": "revision", "label": "En revisión"},
        )
        self.assertEqual(
            public_order_status(None),
            {"code": "revision", "label": "En revisión"},
        )

    def test_customer_order_summary_uses_stable_public_fields(self):
        class Order:
            id = 123
            locator = "UW0586"
            order_date = datetime(2026, 7, 20, 8, 30, 0)
            total_amount = 245.9
            order_status = "pendiente"
            estimated_delivery_at = date(2026, 8, 14)

        self.assertEqual(
            serialize_customer_order_summary(Order()),
            {
                "id": 123,
                "reference": "UW0586",
                "created_at": "2026-07-20T08:30:00",
                "total": "245.90",
                "currency": "EUR",
                "status": {"code": "pendiente", "label": "Pendiente"},
                "estimated_delivery_at": "2026-08-14",
            },
        )

    def test_customer_order_detail_uses_public_fields_and_lines(self):
        class Product:
            nombre = "Reja Essex"

        class Detail:
            id = 7
            product = Product()
            quantity = 2
            alto = 120.5
            ancho = 80.0
            color = "satinado_blanco"
            anclaje = "Sin obra: con pletinas"
            firstname = "Ana"
            lastname = "Cliente"
            shipping_address = "Calle de entrega 12"
            shipping_postal_code = "28013"
            shipping_city = "Madrid"

        class Order:
            id = 123
            locator = "UW0586"
            order_date = datetime(2026, 7, 20, 8, 30, 0)
            total_amount = 245.9
            order_status = "fabricacion"
            estimated_delivery_at = None
            order_details = [Detail()]

        self.assertEqual(
            serialize_customer_order_detail(Order()),
            {
                "id": 123,
                "reference": "UW0586",
                "created_at": "2026-07-20T08:30:00",
                "total": "245.90",
                "currency": "EUR",
                "status": {"code": "fabricacion", "label": "En fabricación"},
                "estimated_delivery_at": None,
                "shipping_address": {
                    "recipient": "Ana Cliente",
                    "address": "Calle de entrega 12",
                    "postal_code": "28013",
                    "city": "Madrid",
                },
                "lines": [
                    {
                        "id": 7,
                        "product_name": "Reja Essex",
                        "quantity": 2,
                        "configuration": {
                            "alto": "120.5",
                            "ancho": "80",
                            "color": "satinado_blanco",
                            "anclaje": "Sin obra: con pletinas",
                            "screw_option": "standard",
                            "screw_length_mm": 70,
                            "screw_supplement": "0.00",
                        },
                    }
                ],
                "invoice": {
                    "available": False,
                    "number": None,
                    "issued_at": None,
                },
            },
        )


@unittest.skipUnless(HAS_ENDPOINT_DEPS, "Flask/JWT/SQLAlchemy test dependencies are not installed.")
class CustomerOrdersEndpointTest(unittest.TestCase):
    def setUp(self):
        self.invoice_dir = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            INVOICE_FOLDER=self.invoice_dir.name,
        )
        JWTManager(self.app)
        db.init_app(self.app)
        self.app.register_blueprint(api, url_prefix="/api")

        with self.app.app_context():
            db.create_all()
            self.user_a = self._create_user("cliente-a@example.test")
            self.user_b = self._create_user("cliente-b@example.test")
            self.admin = self._create_user("admin@example.test", is_admin=True)
            self.empty_user = self._create_user("sin-pedidos@example.test")
            self.category = self._create_category()
            self.product = self._create_product(self.category)

            self.user_a_old_order = self._create_order(
                self.user_a,
                locator="AA0001",
                total_amount=245.9,
                order_status="fabricacion",
                order_date=datetime(2026, 7, 19, 8, 30, 0),
            )
            self.user_a_old_order.estimated_delivery_at = date(2026, 8, 14)
            self._create_order_detail(
                self.user_a_old_order,
                product=self.product,
                quantity=2,
                alto=120.5,
                ancho=80.0,
                color="satinado_blanco",
                anclaje="Sin obra: con pletinas",
                firstname="Ana",
                lastname="Cliente",
                shipping_city="Madrid",
            )
            self.user_a_new_order = self._create_order(
                self.user_a,
                locator="AA0002",
                total_amount=95,
                order_status="estado_historico",
                order_date=datetime(2026, 7, 20, 8, 30, 0),
            )
            self._create_order_detail(
                self.user_a_new_order,
                product=self.product,
                quantity=1,
                alto=30.0,
                ancho=30.0,
                color="satinado_negro",
                anclaje="Sin obra: con agujeros interiores",
                firstname="Ana",
                lastname="Cliente",
                shipping_city="Madrid",
            )
            self.user_b_order = self._create_order(
                self.user_b,
                locator="BB0001",
                total_amount=999.99,
                order_status="entregado",
                order_date=datetime(2026, 7, 21, 8, 30, 0),
            )
            self.user_b_order.estimated_delivery_at = date(2030, 1, 2)
            self._create_order_detail(
                self.user_b_order,
                product=self.product,
                quantity=1,
                alto=200.0,
                ancho=100.0,
                color="forja_negro",
                anclaje="Sin obra: con pletinas",
                firstname="Bea",
                lastname="Cliente",
                shipping_city="Valencia",
            )
            self.admin_order = self._create_order(
                self.admin,
                locator="AD0001",
                total_amount=10,
                order_status="pendiente",
                order_date=datetime(2026, 7, 22, 8, 30, 0),
            )
            self._create_order_detail(
                self.admin_order,
                product=self.product,
                quantity=1,
                alto=None,
                ancho=None,
                color=None,
                anclaje=None,
                firstname="Admin",
                lastname="User",
                shipping_city="Sevilla",
            )
            db.session.commit()
            self.user_a_old_order_id = self.user_a_old_order.id
            self.user_a_new_order_id = self.user_a_new_order.id
            self.user_b_order_id = self.user_b_order.id

            self.user_a_token = self._token_for(self.user_a)
            self.user_b_token = self._token_for(self.user_b)
            self.empty_user_token = self._token_for(self.empty_user)
            self.admin_token = self._token_for(self.admin)
            self.missing_user_token = create_access_token(
                identity="999999",
                additional_claims={"email": "missing@example.test", "is_admin": False},
            )

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.invoice_dir.cleanup()

    def _create_user(self, email, *, is_admin=False):
        user = Users(
            email=email,
            password="not-a-real-password",
            firstname="Cliente",
            lastname="Test",
            is_admin=is_admin,
        )
        db.session.add(user)
        db.session.flush()
        return user

    def _create_order(self, user, *, locator, total_amount, order_status, order_date):
        order = Orders(
            user_id=user.id,
            locator=locator,
            total_amount=total_amount,
            order_status=order_status,
            order_date=order_date,
        )
        db.session.add(order)
        db.session.flush()
        return order

    def _create_category(self):
        category = Categories(
            nombre="Rejas",
            descripcion="Categoria de pruebas",
            slug="rejas-test",
        )
        db.session.add(category)
        db.session.flush()
        return category

    def _create_product(self, category):
        product = Products(
            slug="reja-essex-test",
            nombre="Reja Essex",
            descripcion="Producto de pruebas",
            precio=100.0,
            categoria_id=category.id,
        )
        db.session.add(product)
        db.session.flush()
        return product

    def _create_order_detail(
        self,
        order,
        *,
        product,
        quantity,
        alto,
        ancho,
        color,
        anclaje,
        firstname,
        lastname,
        shipping_city,
    ):
        detail = OrderDetails(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            alto=alto,
            ancho=ancho,
            color=color,
            anclaje=anclaje,
            precio_total=95.0,
            firstname=firstname,
            lastname=lastname,
            shipping_city=shipping_city,
            shipping_postal_code="28001",
            shipping_address="Calle privada 1",
            billing_address="Calle fiscal 1",
            billing_city="Madrid",
            billing_postal_code="28002",
            CIF="00000000T",
        )
        db.session.add(detail)
        return detail

    def _create_invoice(
        self,
        order,
        *,
        invoice_number="F2026000001",
        pdf_path="/api/download-invoice/invoice_F2026000001.pdf",
        issued_at=datetime(2026, 7, 20, 8, 30, 0),
        invoice_type="ordinary",
    ):
        invoice = Invoices(
            invoice_number=invoice_number,
            order_id=order.id,
            invoice_type=invoice_type,
            pdf_path=pdf_path,
            amount=order.total_amount,
            client_name="Cliente Test",
            client_address="Calle fiscal privada",
            client_cif="00000000T",
            order_details=[],
            issued_at=issued_at,
        )
        db.session.add(invoice)
        db.session.flush()
        return invoice

    def _write_invoice_pdf(self, filename="invoice_F2026000001.pdf", content=b"%PDF-1.4 test"):
        path = os.path.join(self.invoice_dir.name, filename)
        with open(path, "wb") as file:
            file.write(content)
        return path

    def _token_for(self, user):
        return create_access_token(
            identity=str(user.id),
            additional_claims={"email": user.email, "is_admin": bool(user.is_admin)},
        )

    def _auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_requires_jwt(self):
        response = self.client.get("/api/customer/orders")

        self.assertEqual(response.status_code, 401)

    def test_detail_requires_jwt(self):
        response = self.client.get(f"/api/customer/orders/{self.user_a_old_order_id}")

        self.assertEqual(response.status_code, 401)

    def test_invalid_jwt_is_rejected(self):
        response = self.client.get(
            "/api/customer/orders",
            headers={"Authorization": "Bearer invalid-token"},
        )

        self.assertIn(response.status_code, (401, 422))

    def test_missing_user_from_valid_token_is_rejected(self):
        response = self.client.get(
            "/api/customer/orders",
            headers=self._auth(self.missing_user_token),
        )

        self.assertEqual(response.status_code, 401)

    def test_detail_missing_user_from_valid_token_is_rejected(self):
        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}",
            headers=self._auth(self.missing_user_token),
        )

        self.assertEqual(response.status_code, 401)

    def test_user_only_receives_own_orders_and_query_user_id_is_ignored(self):
        response = self.client.get(
            f"/api/customer/orders?user_id={self.user_b.id}",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        references = [order["reference"] for order in payload["orders"]]

        self.assertEqual(references, ["AA0002", "AA0001"])
        self.assertNotIn("BB0001", references)

    def test_user_without_orders_receives_empty_list(self):
        response = self.client.get(
            "/api/customer/orders",
            headers=self._auth(self.empty_user_token),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"orders": []})

    def test_response_contains_only_public_order_card_fields(self):
        response = self.client.get(
            "/api/customer/orders",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        order = response.get_json()["orders"][0]

        self.assertEqual(
            set(order.keys()),
            {
                "id",
                "reference",
                "created_at",
                "total",
                "currency",
                "status",
                "estimated_delivery_at",
            },
        )
        self.assertEqual(set(order["status"].keys()), {"code", "label"})

        response_text = response.get_data(as_text=True)
        for forbidden in (
            "user_id",
            "email",
            "shipping_address",
            "billing_address",
            "CIF",
            "order_details",
            "payment_intent",
            "provider_order_id",
            "checkout_session",
            "invoice_number",
            "pdf_path",
            "invoice_snapshot",
            "invoice_snapshot_hash",
            "verifactu",
            "accounting",
        ):
            self.assertNotIn(forbidden, response_text)

    def test_known_and_unknown_statuses_are_mapped_by_backend(self):
        response = self.client.get(
            "/api/customer/orders",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        orders = response.get_json()["orders"]

        self.assertEqual(
            orders[1]["status"],
            {"code": "fabricacion", "label": "En fabricación"},
        )
        self.assertEqual(
            orders[0]["status"],
            {"code": "revision", "label": "En revisión"},
        )
        self.assertEqual(
            public_order_status(None),
            {"code": "revision", "label": "En revisión"},
        )

    def test_amounts_dates_and_ordering_are_stable(self):
        response = self.client.get(
            "/api/customer/orders",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        orders = response.get_json()["orders"]

        self.assertEqual([order["reference"] for order in orders], ["AA0002", "AA0001"])
        self.assertEqual(orders[0]["created_at"], "2026-07-20T08:30:00")
        self.assertEqual(orders[0]["total"], "95.00")
        self.assertEqual(orders[0]["currency"], "EUR")
        self.assertIsNone(orders[0]["estimated_delivery_at"])
        self.assertEqual(orders[1]["total"], "245.90")
        self.assertEqual(orders[1]["estimated_delivery_at"], "2026-08-14")
        self.assertNotIn("2030-01-02", response.get_data(as_text=True))

    def test_admin_uses_customer_view_and_only_receives_own_orders(self):
        response = self.client.get(
            "/api/customer/orders",
            headers=self._auth(self.admin_token),
        )

        self.assertEqual(response.status_code, 200)
        references = [order["reference"] for order in response.get_json()["orders"]]

        self.assertEqual(references, ["AD0001"])
        self.assertNotIn("AA0001", references)
        self.assertNotIn("BB0001", references)

    def test_detail_returns_own_order(self):
        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["order"]["reference"], "AA0001")
        self.assertEqual(payload["order"]["status"], {"code": "fabricacion", "label": "En fabricación"})
        self.assertEqual(payload["order"]["estimated_delivery_at"], "2026-08-14")

    def test_detail_foreign_order_returns_404(self):
        response = self.client.get(
            f"/api/customer/orders/{self.user_b_order_id}",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"message": "Order not found"})

    def test_detail_missing_order_returns_404(self):
        response = self.client.get(
            "/api/customer/orders/999999",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"message": "Order not found"})

    def test_detail_contains_only_public_fields(self):
        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        order = response.get_json()["order"]

        self.assertEqual(
            set(order.keys()),
            {
                "id",
                "reference",
                "created_at",
                "total",
                "currency",
                "status",
                "estimated_delivery_at",
                "shipping_address",
                "lines",
                "invoice",
            },
        )
        self.assertEqual(
            set(order["shipping_address"].keys()),
            {"recipient", "address", "postal_code", "city"},
        )
        self.assertEqual(
            set(order["lines"][0].keys()),
            {"id", "product_name", "quantity", "configuration"},
        )
        self.assertEqual(
            set(order["lines"][0]["configuration"].keys()),
            {
                "alto",
                "ancho",
                "color",
                "anclaje",
                "screw_option",
                "screw_length_mm",
                "screw_supplement",
            },
        )
        self.assertEqual(
            set(order["invoice"].keys()),
            {"available", "number", "issued_at"},
        )

    def test_detail_lines_and_shipping_address_are_serialized(self):
        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        order = response.get_json()["order"]

        self.assertEqual(
            order["shipping_address"],
            {
                "recipient": "Ana Cliente",
                "address": "Calle privada 1",
                "postal_code": "28001",
                "city": "Madrid",
            },
        )
        self.assertEqual(
            order["lines"],
            [
                {
                    "id": order["lines"][0]["id"],
                    "product_name": "Reja Essex",
                    "quantity": 2,
                    "configuration": {
                        "alto": "120.5",
                        "ancho": "80",
                        "color": "satinado_blanco",
                        "anclaje": "Sin obra: con pletinas",
                        "screw_option": "standard",
                        "screw_length_mm": 70,
                        "screw_supplement": "0.00",
                    },
                }
            ],
        )

    def test_detail_does_not_expose_sensitive_fields(self):
        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        response_text = response.get_data(as_text=True)

        for forbidden in (
            "user_id",
            "email",
            "phone",
            "telefono",
            "billing_postal_code",
            "billing_address",
            "CIF",
            "NIF",
            "payment_intent",
            "provider_order_id",
            "checkout_session",
            "invoice_number",
            "pdf_path",
            "invoice_snapshot",
            "hash",
            "verifactu",
            "accounting",
            "estimated_delivery_note",
        ):
            self.assertNotIn(forbidden, response_text)

    def test_detail_invoice_is_unavailable_without_invoice(self):
        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["order"]["invoice"],
            {"available": False, "number": None, "issued_at": None},
        )

    def test_detail_invoice_is_available_only_with_resolvable_pdf(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.user_a_old_order_id)
            self._write_invoice_pdf("invoice_F2026000001.pdf")
            self._create_invoice(order)
            db.session.commit()

        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["order"]["invoice"],
            {
                "available": True,
                "number": "F2026000001",
                "issued_at": "2026-07-20T08:30:00",
            },
        )

    def test_detail_invoice_without_pdf_is_not_available(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.user_a_old_order_id)
            self._create_invoice(order, pdf_path=None)
            db.session.commit()

        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["order"]["invoice"],
            {"available": False, "number": None, "issued_at": None},
        )

    def test_detail_invoice_does_not_expose_pdf_or_internal_invoice_data(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.user_a_old_order_id)
            self._write_invoice_pdf("invoice_F2026000001.pdf")
            invoice = self._create_invoice(order)
            invoice.invoice_snapshot = {"sensitive": "snapshot"}
            invoice.invoice_snapshot_hash = "internal-hash"
            db.session.commit()

        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        response_text = response.get_data(as_text=True)
        self.assertIn('"invoice"', response_text)
        self.assertNotIn("pdf_path", response_text)
        self.assertNotIn("invoice_snapshot", response_text)
        self.assertNotIn("internal-hash", response_text)
        self.assertNotIn("sensitive", response_text)

    def test_download_invoice_requires_jwt(self):
        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}/invoice",
        )

        self.assertEqual(response.status_code, 401)

    def test_download_invoice_missing_user_from_valid_token_is_rejected(self):
        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}/invoice",
            headers=self._auth(self.missing_user_token),
        )

        self.assertEqual(response.status_code, 401)

    def test_download_invoice_for_own_order_returns_pdf_attachment(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.user_a_old_order_id)
            self._write_invoice_pdf("invoice_F2026000001.pdf", b"%PDF-1.4 customer")
            self._create_invoice(order)
            db.session.commit()

        with (
            patch("api.routes.generate_invoice_pdf") as generate_invoice_pdf,
            patch("api.routes.render_original_order_invoice_pdf") as legacy_renderer,
            patch("api.routes.db.session.commit") as commit,
        ):
            response = self.client.get(
                f"/api/customer/orders/{self.user_a_old_order_id}/invoice",
                headers=self._auth(self.user_a_token),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("attachment", response.headers.get("Content-Disposition", ""))
        self.assertIn("factura_F2026000001.pdf", response.headers.get("Content-Disposition", ""))
        self.assertEqual(response.data, b"%PDF-1.4 customer")
        generate_invoice_pdf.assert_not_called()
        legacy_renderer.assert_not_called()
        commit.assert_not_called()

    def test_download_invoice_foreign_order_returns_404(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.user_b_order_id)
            self._write_invoice_pdf("invoice_F2026000001.pdf")
            self._create_invoice(order)
            db.session.commit()

        response = self.client.get(
            f"/api/customer/orders/{self.user_b_order_id}/invoice",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"message": "Invoice not found"})

    def test_download_invoice_missing_order_returns_404(self):
        response = self.client.get(
            "/api/customer/orders/999999/invoice",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"message": "Invoice not found"})

    def test_download_invoice_without_invoice_returns_404(self):
        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}/invoice",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"message": "Invoice not found"})

    def test_download_invoice_without_pdf_returns_404(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.user_a_old_order_id)
            self._create_invoice(order, pdf_path=None)
            db.session.commit()

        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}/invoice",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"message": "Invoice not found"})

    def test_download_invoice_missing_physical_file_returns_404(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.user_a_old_order_id)
            self._create_invoice(order)
            db.session.commit()

        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}/invoice",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"message": "Invoice not found"})

    def test_download_invoice_unsafe_pdf_path_returns_404(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.user_a_old_order_id)
            self._create_invoice(order, pdf_path="../secret.pdf")
            db.session.commit()

        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}/invoice",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"message": "Invoice not found"})

    def test_download_invoice_ignores_client_selected_file_parameters(self):
        with self.app.app_context():
            own_order = db.session.get(Orders, self.user_a_old_order_id)
            foreign_order = db.session.get(Orders, self.user_b_order_id)
            self._write_invoice_pdf("invoice_F2026000001.pdf", b"%PDF-own")
            self._write_invoice_pdf("invoice_F2026000002.pdf", b"%PDF-foreign")
            self._create_invoice(own_order)
            self._create_invoice(
                foreign_order,
                invoice_number="F2026000002",
                pdf_path="/api/download-invoice/invoice_F2026000002.pdf",
            )
            db.session.commit()

        response = self.client.get(
            (
                f"/api/customer/orders/{self.user_a_old_order_id}/invoice"
                "?filename=invoice_F2026000002.pdf&invoice_id=999&user_id=999"
            ),
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"%PDF-own")

    def test_download_invoice_does_not_modify_invoice(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.user_a_old_order_id)
            self._write_invoice_pdf("invoice_F2026000001.pdf")
            invoice = self._create_invoice(order)
            db.session.commit()
            before = {
                "invoice_number": invoice.invoice_number,
                "pdf_path": invoice.pdf_path,
                "issued_at": invoice.issued_at,
                "amount": invoice.amount,
            }
            invoice_id = invoice.id

        response = self.client.get(
            f"/api/customer/orders/{self.user_a_old_order_id}/invoice",
            headers=self._auth(self.user_a_token),
        )

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            invoice = db.session.get(Invoices, invoice_id)
            self.assertEqual(invoice.invoice_number, before["invoice_number"])
            self.assertEqual(invoice.pdf_path, before["pdf_path"])
            self.assertEqual(invoice.issued_at, before["issued_at"])
            self.assertEqual(invoice.amount, before["amount"])


if __name__ == "__main__":
    unittest.main()

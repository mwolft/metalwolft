import importlib.util
import sys
import unittest
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.customer_order_serializers import public_order_status, serialize_customer_order_summary  # noqa: E402


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

    from api.models import Orders, Users, db  # noqa: E402
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

        self.assertEqual(
            serialize_customer_order_summary(Order()),
            {
                "id": 123,
                "reference": "UW0586",
                "created_at": "2026-07-20T08:30:00",
                "total": "245.90",
                "currency": "EUR",
                "status": {"code": "pendiente", "label": "Pendiente"},
            },
        )


@unittest.skipUnless(HAS_ENDPOINT_DEPS, "Flask/JWT/SQLAlchemy test dependencies are not installed.")
class CustomerOrdersEndpointTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
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

            self._create_order(
                self.user_a,
                locator="AA0001",
                total_amount=245.9,
                order_status="fabricacion",
                order_date=datetime(2026, 7, 19, 8, 30, 0),
            )
            self._create_order(
                self.user_a,
                locator="AA0002",
                total_amount=95,
                order_status="estado_historico",
                order_date=datetime(2026, 7, 20, 8, 30, 0),
            )
            self._create_order(
                self.user_b,
                locator="BB0001",
                total_amount=999.99,
                order_status="entregado",
                order_date=datetime(2026, 7, 21, 8, 30, 0),
            )
            self._create_order(
                self.admin,
                locator="AD0001",
                total_amount=10,
                order_status="pendiente",
                order_date=datetime(2026, 7, 22, 8, 30, 0),
            )
            db.session.commit()

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
        return order

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
            {"id", "reference", "created_at", "total", "currency", "status"},
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
        self.assertEqual(orders[1]["total"], "245.90")

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


if __name__ == "__main__":
    unittest.main()

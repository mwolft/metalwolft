import importlib.util
import sys
import unittest
from decimal import Decimal
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_DEPS = all(has_package(package) for package in ("flask", "flask_jwt_extended", "flask_sqlalchemy", "sqlalchemy", "slugify"))


if HAS_DEPS:
    from flask import Flask
    from flask_jwt_extended import JWTManager, create_access_token

    from api.models import Categories, CheckoutSessions, DesignRequest, DesignServiceConfig, OrderDetails, Orders, Products, Users, db
    from api.routes import _finalize_order_from_checkout_quote, api
    from api.design_service import create_design_request


def _fake_stripe_module():
    module = ModuleType("stripe")

    class StripeError(Exception):
        pass

    class PaymentIntent:
        @staticmethod
        def create(**kwargs):
            return {
                "id": "pi_design_1",
                "client_secret": "pi_design_1_secret",
                "status": "requires_confirmation",
                **kwargs,
            }

        @staticmethod
        def modify(intent_id, **kwargs):
            return {
                "id": intent_id,
                "client_secret": f"{intent_id}_secret",
                "status": "requires_confirmation",
                **kwargs,
            }

    module.PaymentIntent = PaymentIntent
    module.error = SimpleNamespace(StripeError=StripeError)
    return module


@unittest.skipUnless(HAS_DEPS, "Flask/JWT/SQLAlchemy test dependencies are not installed.")
class DesignPaymentEndpointTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="design-payment-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            MAIL_USERNAME="no-reply@example.test",
        )
        JWTManager(self.app)
        db.init_app(self.app)
        self.app.register_blueprint(api, url_prefix="/api")
        with self.app.app_context():
            db.create_all()
            category = Categories(nombre="Diseño", descripcion="Tests", slug="diseno")
            db.session.add(category)
            db.session.flush()
            product = Products(nombre="Maryland", descripcion="Modelo", precio=100, categoria_id=category.id, slug="maryland")
            user = Users(email="owner@example.test", password="x")
            outsider = Users(email="outsider@example.test", password="x")
            db.session.add_all([product, user, outsider, DesignServiceConfig(
                id=1, is_active=True, base_price_gross=Decimal("24.95"), currency="EUR", lead_time_hours=24
            )])
            db.session.commit()
            self.user_id = user.id
            self.outsider_id = outsider.id
            self.product_id = product.id
            self.request = create_design_request(
                db_session=db.session,
                user_id=user.id,
                items=[{"product_id": product.id, "width_cm": 200, "height_cm": 120}],
                creation_key="design-request-create",
            ).design_request
            db.session.commit()
            self.request_id = self.request.id
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def headers(self, user_id):
        with self.app.app_context():
            token = create_access_token(identity=str(user_id), additional_claims={"email": "owner@example.test", "is_admin": False})
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def customer_data():
        return {
            "firstname": "Ana", "lastname": "Cliente", "email": "owner@example.test", "phone": "600000000",
            "legal_name": "Ana Cliente", "tax_id": "00000000T", "billing_address": "Calle Fiscal 1",
            "billing_postal_code": "13001", "billing_city": "Ciudad Real",
        }

    def test_stripe_payment_uses_frozen_design_quote_and_reuses_one_session(self):
        payload = {"payment_method_id": "pm_test", "idempotency_key": "pay-design-1", "customer_data": self.customer_data()}
        with patch.dict(sys.modules, {"stripe": _fake_stripe_module()}):
            first = self.client.post(f"/api/design-requests/{self.request_id}/stripe/payment-intent", json=payload, headers=self.headers(self.user_id))
            second = self.client.post(f"/api/design-requests/{self.request_id}/stripe/payment-intent", json=payload, headers=self.headers(self.user_id))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.get_json()["amount_used_cents"], 2495)
        with self.app.app_context():
            self.assertEqual(CheckoutSessions.query.filter_by(design_request_id=self.request_id).count(), 1)
            self.assertEqual(db.session.get(DesignRequest, self.request_id).status, "pending_payment")
            session = CheckoutSessions.query.filter_by(design_request_id=self.request_id).one()
            self.assertEqual(session.shipping_cost, 0.0)
            self.assertNotIn("shipping_address", session.customer_snapshot)

    def test_payment_rejects_another_users_design_request(self):
        with patch.dict(sys.modules, {"stripe": _fake_stripe_module()}):
            response = self.client.post(
                f"/api/design-requests/{self.request_id}/stripe/payment-intent",
                json={"payment_method_id": "pm_test", "idempotency_key": "pay-design-2", "customer_data": self.customer_data()},
                headers=self.headers(self.outsider_id),
            )
        self.assertEqual(response.status_code, 400)
        with self.app.app_context():
            self.assertEqual(CheckoutSessions.query.count(), 0)

    def test_paypal_order_uses_the_same_frozen_design_session(self):
        with patch("api.routes._paypal_request", return_value={"id": "pp_design_1", "status": "CREATED", "links": []}):
            response = self.client.post(
                f"/api/design-requests/{self.request_id}/paypal/create-order",
                json={"idempotency_key": "paypal-design-1", "customer_data": self.customer_data()},
                headers=self.headers(self.user_id),
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["provider_order_id"], "pp_design_1")
        with self.app.app_context():
            checkout_session = CheckoutSessions.query.filter_by(design_request_id=self.request_id).one()
            self.assertEqual(checkout_session.payment_provider, "paypal")
            self.assertEqual(checkout_session.shipping_cost, 0.0)

    def test_second_provider_cannot_open_a_parallel_payment_session(self):
        with patch.dict(sys.modules, {"stripe": _fake_stripe_module()}):
            stripe_response = self.client.post(
                f"/api/design-requests/{self.request_id}/stripe/payment-intent",
                json={"payment_method_id": "pm_test", "idempotency_key": "stripe-one", "customer_data": self.customer_data()},
                headers=self.headers(self.user_id),
            )
        self.assertEqual(stripe_response.status_code, 200)
        paypal_response = self.client.post(
            f"/api/design-requests/{self.request_id}/paypal/create-order",
            json={"idempotency_key": "paypal-second", "customer_data": self.customer_data()},
            headers=self.headers(self.user_id),
        )
        self.assertEqual(paypal_response.status_code, 400)
        with self.app.app_context():
            self.assertEqual(CheckoutSessions.query.filter_by(design_request_id=self.request_id).count(), 1)

    def test_confirmation_is_private_and_uses_design_request_not_query_totals(self):
        response = self.client.get(
            f"/api/design-requests/{self.request_id}/confirmation",
            headers=self.headers(self.user_id),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["reference"], self.request.reference)
        self.assertEqual(payload["total_amount"], "24.95")
        self.assertEqual(payload["order"], None)
        outsider = self.client.get(
            f"/api/design-requests/{self.request_id}/confirmation",
            headers=self.headers(self.outsider_id),
        )
        self.assertEqual(outsider.status_code, 404)

    def test_common_finalizer_creates_one_digital_order_and_marks_request_paid(self):
        payload = {"payment_method_id": "pm_test", "idempotency_key": "pay-design-finalize", "customer_data": self.customer_data()}
        with patch.dict(sys.modules, {"stripe": _fake_stripe_module()}):
            response = self.client.post(
                f"/api/design-requests/{self.request_id}/stripe/payment-intent",
                json=payload,
                headers=self.headers(self.user_id),
            )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context(), patch("api.routes.send_order_confirmation_email"):
            checkout_session = CheckoutSessions.query.filter_by(design_request_id=self.request_id).one()
            checkout_session.status = "paid"
            order, created = _finalize_order_from_checkout_quote(
                user=db.session.get(Users, self.user_id),
                checkout_quote=checkout_session.quote_snapshot,
                customer_snapshot=checkout_session.customer_snapshot,
                checkout_session=checkout_session,
            )
            self.assertTrue(created)
            self.assertEqual(order.shipping_cost, 0.0)
            self.assertEqual(Orders.query.count(), 1)
            details = OrderDetails.query.filter_by(order_id=order.id).all()
            self.assertEqual(len(details), 1)
            self.assertEqual(details[0].line_type, "design_service")
            self.assertIsNone(details[0].shipping_address)
            self.assertEqual(db.session.get(DesignRequest, self.request_id).status, "pending")
            retried_order, retried_created = _finalize_order_from_checkout_quote(
                user=db.session.get(Users, self.user_id),
                checkout_quote=checkout_session.quote_snapshot,
                customer_snapshot=checkout_session.customer_snapshot,
                checkout_session=checkout_session,
            )
            self.assertFalse(retried_created)
            self.assertEqual(retried_order.id, order.id)


if __name__ == "__main__":
    unittest.main()

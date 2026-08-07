import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ENDPOINT_DEPS = all(
    has_package(package)
    for package in (
        "flask",
        "flask_jwt_extended",
        "flask_sqlalchemy",
        "sqlalchemy",
    )
)


if HAS_ENDPOINT_DEPS:
    from flask import Flask

    from api.product_lifecycle import ProductNotAvailableForSaleError
    from api import routes


def checkout_quote():
    return {
        "lines": [
            {
                "product_id": 1,
                "quantity": 1,
                "alto": 30,
                "ancho": 30,
                "anclaje": "Sin obra: con agujeros interiores",
                "color": "satinado_blanco",
                "unit_price": 100.0,
                "line_total": 100.0,
            }
        ],
        "subtotal": 100.0,
        "shipping_cost": 21.0,
        "discount_code": None,
        "discount_percent": 0.0,
        "discount_amount": 0.0,
        "total_amount": 121.0,
    }


def customer_data(**overrides):
    values = {
        "firstname": "Sergio",
        "lastname": "Arias",
        "email": "cliente@example.com",
        "phone": "600000000",
        "legal_name": "Sergio Arias",
        "billing_address": "Calle Factura 3",
        "billing_postal_code": "13001",
        "billing_city": "Ciudad Real",
        "shipping_address": "",
        "shipping_postal_code": "",
        "shipping_city": "",
        "tax_id": "00000000T",
    }
    values.update(overrides)
    return values


def customer_payload(**overrides):
    return {"customer_data": customer_data(**overrides)}


def checkout_session(**overrides):
    values = {
        "id": 10,
        "status": "pending_payment",
        "payment_provider": "paypal",
        "payment_intent_id": None,
        "provider_order_id": None,
        "provider_capture_id": None,
        "provider_status": None,
        "public_checkout_token": "checkout-token",
        "quote_snapshot": checkout_quote(),
        "total_amount": 121.0,
        "order_id": None,
        "customer_snapshot": {},
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@unittest.skipUnless(
    HAS_ENDPOINT_DEPS,
    "Flask/JWT/SQLAlchemy test dependencies are not installed.",
)
class PaymentProductLifecycleEndpointTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.current_user = {"user_id": 7, "email": "buyer@example.test"}
        self.db_session = MagicMock()
        self.fake_db = SimpleNamespace(session=self.db_session)

    def call_endpoint(self, endpoint, payload):
        with self.app.test_request_context(json=payload):
            with patch.object(routes, "get_jwt_identity", return_value=self.current_user):
                return endpoint.__wrapped__()

    def assert_rejected_before_stripe(self, quote_error):
        payment_intent = SimpleNamespace(
            create=MagicMock(),
            modify=MagicMock(),
        )
        stripe_module = SimpleNamespace(PaymentIntent=payment_intent, api_key=None)

        with patch.dict(sys.modules, {"stripe": stripe_module}):
            with patch.object(routes, "db", self.fake_db):
                with patch.object(
                    routes,
                    "_build_checkout_quote_from_request",
                    side_effect=quote_error,
                ):
                    response, status = self.call_endpoint(
                        routes.create_payment_intent,
                        {
                            "payment_method_id": "pm_test",
                            **customer_payload(),
                        },
                    )

        self.assertEqual(status, 400)
        self.assertIn("error", response.get_json())
        payment_intent.create.assert_not_called()
        payment_intent.modify.assert_not_called()

    def assert_rejected_before_paypal(self, quote_error):
        provider_request = MagicMock()

        with patch.object(routes, "db", self.fake_db):
            with patch.object(
                routes,
                "_build_checkout_quote_from_request",
                side_effect=quote_error,
            ):
                with patch.object(routes, "_paypal_request", provider_request):
                    response, status = self.call_endpoint(
                        routes.create_paypal_order,
                        customer_payload(),
                    )

        self.assertEqual(status, 400)
        self.assertIn("error", response.get_json())
        provider_request.assert_not_called()

    def test_available_product_allows_stripe_payment_intent_creation(self):
        intent = {
            "id": "pi_test",
            "client_secret": "pi_test_secret",
            "status": "requires_confirmation",
        }
        payment_intent = SimpleNamespace(
            create=MagicMock(return_value=intent),
            modify=MagicMock(),
        )
        stripe_module = SimpleNamespace(PaymentIntent=payment_intent, api_key=None)
        session = checkout_session(
            payment_provider="stripe",
            payment_intent_id="pi_test",
        )
        upsert_checkout_session = MagicMock(return_value=session)
        payload = {
            "payment_method_id": "pm_test",
            "email": "legacy-stripe@example.com",
            **customer_payload(email="", tax_id="  b12345678  "),
        }

        with patch.dict(sys.modules, {"stripe": stripe_module}):
            with patch.object(routes, "db", self.fake_db):
                with patch.object(
                    routes,
                    "_build_checkout_quote_from_request",
                    return_value=checkout_quote(),
                ):
                    with patch.object(
                        routes,
                        "_upsert_checkout_session",
                        upsert_checkout_session,
                    ):
                        response, status = self.call_endpoint(
                            routes.create_payment_intent,
                            payload,
                        )

        self.assertEqual(status, 200)
        self.assertEqual(response.get_json()["amount_used_cents"], 12100)
        self.assertEqual(
            upsert_checkout_session.call_args.kwargs["customer_snapshot"]["email"],
            "legacy-stripe@example.com",
        )
        self.assertEqual(
            upsert_checkout_session.call_args.kwargs["customer_snapshot"]["tax_id"],
            "B12345678",
        )
        self.assertEqual(
            payment_intent.create.call_args.kwargs["receipt_email"],
            "legacy-stripe@example.com",
        )
        payment_intent.create.assert_called_once()
        payment_intent.modify.assert_not_called()

    def test_unavailable_product_prevents_stripe_provider_call(self):
        self.assert_rejected_before_stripe(
            ProductNotAvailableForSaleError(
                "Este producto ya no esta disponible para la venta."
            )
        )

    def test_missing_product_prevents_stripe_provider_call(self):
        self.assert_rejected_before_stripe(
            ValueError("Producto con ID 999 no encontrado")
        )

    def test_available_product_allows_paypal_order_creation(self):
        session = checkout_session()
        upsert_checkout_session = MagicMock(return_value=session)
        provider_request = MagicMock(
            return_value={"id": "PAYPAL-ORDER", "status": "CREATED", "links": []}
        )

        with patch.object(routes, "db", self.fake_db):
            with patch.object(
                routes,
                "_build_checkout_quote_from_request",
                return_value=checkout_quote(),
            ):
                with patch.object(
                    routes,
                    "_upsert_paypal_checkout_session",
                    upsert_checkout_session,
                ):
                    with patch.object(routes, "_paypal_request", provider_request):
                        response, status = self.call_endpoint(
                            routes.create_paypal_order,
                            customer_payload(email="", tax_id="  x1234567l  "),
                        )

        self.assertEqual(status, 200)
        self.assertEqual(response.get_json()["provider_order_id"], "PAYPAL-ORDER")
        self.assertEqual(
            upsert_checkout_session.call_args.kwargs["customer_snapshot"]["email"],
            "buyer@example.test",
        )
        self.assertEqual(
            upsert_checkout_session.call_args.kwargs["customer_snapshot"]["tax_id"],
            "X1234567L",
        )
        provider_request.assert_called_once()

    def test_unavailable_product_prevents_paypal_provider_call(self):
        self.assert_rejected_before_paypal(
            ProductNotAvailableForSaleError(
                "Este producto ya no esta disponible para la venta."
            )
        )

    def test_missing_product_prevents_paypal_provider_call(self):
        self.assert_rejected_before_paypal(
            ValueError("Producto con ID 999 no encontrado")
        )

    def test_paypal_existing_order_is_reused_without_new_provider_call(self):
        existing = checkout_session(
            provider_order_id="PAYPAL-EXISTING",
            provider_status="CREATED",
        )
        provider_request = MagicMock()
        quote_builder = MagicMock()

        with patch.object(routes, "db", self.fake_db):
            with patch.object(
                routes,
                "_get_checkout_session_by_public_token",
                return_value=existing,
            ):
                with patch.object(
                    routes,
                    "_build_checkout_quote_from_request",
                    quote_builder,
                ):
                    with patch.object(routes, "_paypal_request", provider_request):
                        response, status = self.call_endpoint(
                            routes.create_paypal_order,
                            {
                                "checkout_token": "checkout-token",
                                **customer_payload(),
                            },
                        )

        self.assertEqual(status, 200)
        self.assertEqual(response.get_json()["provider_order_id"], "PAYPAL-EXISTING")
        self.assertEqual(response.get_json()["created_via"], "existing_checkout_session")
        quote_builder.assert_not_called()
        provider_request.assert_not_called()

    def test_invalid_customer_snapshot_is_rejected_before_stripe_provider_call(self):
        payment_intent = SimpleNamespace(create=MagicMock(), modify=MagicMock())
        stripe_module = SimpleNamespace(PaymentIntent=payment_intent, api_key=None)

        with patch.dict(sys.modules, {"stripe": stripe_module}):
            with patch.object(routes, "db", self.fake_db):
                with patch.object(
                    routes,
                    "_build_checkout_quote_from_request",
                    return_value=checkout_quote(),
                ):
                    response, status = self.call_endpoint(
                        routes.create_payment_intent,
                        {
                            "payment_method_id": "pm_test",
                            **customer_payload(phone=["600000000"]),
                        },
                    )

        self.assertEqual(status, 400)
        self.assertEqual(response.get_json()["code"], "INVALID_CUSTOMER_DATA")
        self.assertEqual(response.get_json()["field"], "phone")
        payment_intent.create.assert_not_called()
        payment_intent.modify.assert_not_called()

    def test_missing_tax_id_is_rejected_before_stripe_provider_call(self):
        payment_intent = SimpleNamespace(create=MagicMock(), modify=MagicMock())
        stripe_module = SimpleNamespace(PaymentIntent=payment_intent, api_key=None)

        with patch.dict(sys.modules, {"stripe": stripe_module}):
            with patch.object(routes, "db", self.fake_db):
                with patch.object(
                    routes,
                    "_build_checkout_quote_from_request",
                    return_value=checkout_quote(),
                ):
                    response, status = self.call_endpoint(
                        routes.create_payment_intent,
                        {
                            "payment_method_id": "pm_test",
                            **customer_payload(tax_id=""),
                        },
                    )

        self.assertEqual(status, 400)
        self.assertEqual(response.get_json()["code"], "INVALID_CUSTOMER_DATA")
        self.assertEqual(response.get_json()["field"], "tax_id")
        payment_intent.create.assert_not_called()
        payment_intent.modify.assert_not_called()

    def test_missing_legal_name_is_rejected_before_stripe_provider_call(self):
        payment_intent = SimpleNamespace(create=MagicMock(), modify=MagicMock())
        stripe_module = SimpleNamespace(PaymentIntent=payment_intent, api_key=None)

        with patch.dict(sys.modules, {"stripe": stripe_module}):
            with patch.object(routes, "db", self.fake_db):
                with patch.object(
                    routes,
                    "_build_checkout_quote_from_request",
                    return_value=checkout_quote(),
                ):
                    response, status = self.call_endpoint(
                        routes.create_payment_intent,
                        {
                            "payment_method_id": "pm_test",
                            **customer_payload(legal_name=""),
                        },
                    )

        self.assertEqual(status, 400)
        self.assertEqual(response.get_json()["code"], "INVALID_CUSTOMER_DATA")
        self.assertEqual(response.get_json()["field"], "legal_name")
        payment_intent.create.assert_not_called()
        payment_intent.modify.assert_not_called()

    def test_missing_tax_id_is_rejected_before_paypal_provider_call(self):
        provider_request = MagicMock()

        with patch.object(routes, "db", self.fake_db):
            with patch.object(routes, "_paypal_request", provider_request):
                response, status = self.call_endpoint(
                    routes.create_paypal_order,
                    customer_payload(tax_id=""),
                )

        self.assertEqual(status, 400)
        self.assertEqual(response.get_json()["code"], "INVALID_CUSTOMER_DATA")
        self.assertEqual(response.get_json()["field"], "tax_id")
        provider_request.assert_not_called()

    def test_missing_legal_name_is_rejected_before_paypal_provider_call(self):
        provider_request = MagicMock()

        with patch.object(routes, "db", self.fake_db):
            with patch.object(routes, "_paypal_request", provider_request):
                response, status = self.call_endpoint(
                    routes.create_paypal_order,
                    customer_payload(legal_name=""),
                )

        self.assertEqual(status, 400)
        self.assertEqual(response.get_json()["code"], "INVALID_CUSTOMER_DATA")
        self.assertEqual(response.get_json()["field"], "legal_name")
        provider_request.assert_not_called()

    def test_paypal_can_complete_customer_snapshot_before_order_exists(self):
        existing_snapshot = routes._extract_customer_snapshot(
            customer_payload(),
            require_checkout_fields=True,
        )
        captured = checkout_session(
            provider_order_id="PAYPAL-ORDER",
            provider_capture_id="PAYPAL-CAPTURE",
            provider_status="COMPLETED",
            status="paid",
            customer_snapshot=existing_snapshot,
        )

        with patch.object(routes, "db", self.fake_db):
            with patch.object(
                routes,
                "_get_checkout_session_by_public_token",
                return_value=captured,
            ):
                response, status = self.call_endpoint(
                    routes.capture_paypal_order,
                    {
                        "checkout_token": "checkout-token",
                        "customer_data": {"phone": "611111111"},
                    },
                )

        self.assertEqual(status, 200)
        self.assertEqual(captured.customer_snapshot["phone"], "611111111")
        self.assertEqual(captured.customer_snapshot["email"], "cliente@example.com")
        self.assertEqual(response.get_json()["provider_capture_id"], "PAYPAL-CAPTURE")

    def test_paypal_finalized_order_cannot_mutate_customer_snapshot(self):
        original_snapshot = routes._extract_customer_snapshot(
            customer_payload(),
            require_checkout_fields=True,
        )
        finalized = checkout_session(
            provider_order_id="PAYPAL-ORDER",
            provider_capture_id="PAYPAL-CAPTURE",
            provider_status="COMPLETED",
            status="order_created",
            order_id=321,
            customer_snapshot=dict(original_snapshot),
        )
        provider_request = MagicMock()

        with patch.object(routes, "db", self.fake_db):
            with patch.object(
                routes,
                "_get_checkout_session_by_public_token",
                return_value=finalized,
            ):
                with patch.object(routes, "_paypal_request", provider_request):
                    response, status = self.call_endpoint(
                        routes.capture_paypal_order,
                        {
                            "checkout_token": "checkout-token",
                            "customer_data": {
                                "phone": ["invalid-type"],
                                "legal_name": "ALTERED COMPANY SL",
                            },
                        },
                    )

        self.assertEqual(status, 200)
        self.assertEqual(finalized.customer_snapshot, original_snapshot)
        self.assertEqual(response.get_json()["message"], "Checkout session already finalized.")
        provider_request.assert_not_called()

    def test_confirmed_paypal_capture_is_not_revalidated_against_live_products(self):
        captured = checkout_session(
            provider_order_id="PAYPAL-ORDER",
            provider_capture_id="PAYPAL-CAPTURE",
            provider_status="COMPLETED",
            status="paid",
        )
        quote_builder = MagicMock(
            side_effect=AssertionError("confirmed capture must use its stored session")
        )
        provider_request = MagicMock()

        with patch.object(routes, "db", self.fake_db):
            with patch.object(
                routes,
                "_get_checkout_session_by_public_token",
                return_value=captured,
            ):
                with patch.object(
                    routes,
                    "_build_checkout_quote_from_request",
                    quote_builder,
                ):
                    with patch.object(routes, "_paypal_request", provider_request):
                        response, status = self.call_endpoint(
                            routes.capture_paypal_order,
                            {"checkout_token": "checkout-token"},
                        )

        self.assertEqual(status, 200)
        self.assertEqual(response.get_json()["provider_capture_id"], "PAYPAL-CAPTURE")
        quote_builder.assert_not_called()
        provider_request.assert_not_called()


class ConfirmedPaymentSnapshotRegressionTest(unittest.TestCase):
    def test_order_finalizer_does_not_revalidate_live_product_availability(self):
        source = (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")
        start = source.index("def _finalize_order_from_checkout_quote")
        end = source.index("@api.route('/delivery-estimate'", start)
        finalizer = source[start:end]

        self.assertIn("_build_order_details_from_checkout_quote(checkout_quote)", finalizer)
        self.assertNotIn("ensure_product_available_for_sale", finalizer)
        self.assertNotIn("build_checkout_quote", finalizer)

    def test_legacy_checkout_exposes_legal_name_in_form_and_payload(self):
        source = (ROOT_DIR / "src/front/js/component/CheckoutForm.jsx").read_text(encoding="utf-8")

        self.assertIn('"legal_name"', source)
        self.assertIn('Nombre fiscal / Razón social', source)
        self.assertIn('name="legal_name"', source)
        self.assertIn('value={formData.legal_name}', source)
        self.assertIn('customer_data: formData', source)
        self.assertIn('customerData={formData}', source)
        self.assertIn('buildLegalName(', source)
        self.assertIn('hasUserEditedLegalNameRef', source)


if __name__ == "__main__":
    unittest.main()

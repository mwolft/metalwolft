import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.payment_amounts import PaymentAmountValidationError, validate_payment_amount


class PaymentAmountValidationTest(unittest.TestCase):
    def assert_rejected(self, provider, total_amount, currency="eur"):
        with self.assertRaises(PaymentAmountValidationError):
            validate_payment_amount(provider, total_amount, currency=currency)

    def test_stripe_eur_rejects_zero(self):
        self.assert_rejected("stripe", 0)

    def test_stripe_eur_rejects_one_cent(self):
        self.assert_rejected("stripe", "0.01")

    def test_stripe_eur_rejects_below_minimum(self):
        self.assert_rejected("stripe", Decimal("0.49"))

    def test_stripe_eur_accepts_minimum(self):
        self.assertEqual(validate_payment_amount("stripe", "0.50"), Decimal("0.50"))

    def test_stripe_eur_accepts_above_minimum(self):
        self.assertEqual(validate_payment_amount("stripe", "1.25"), Decimal("1.25"))

    def test_paypal_eur_rejects_zero(self):
        self.assert_rejected("paypal", 0)

    def test_paypal_eur_accepts_one_cent(self):
        self.assertEqual(validate_payment_amount("paypal", "0.01"), Decimal("0.01"))

    def test_paypal_eur_accepts_above_minimum(self):
        self.assertEqual(validate_payment_amount("paypal", 2), Decimal("2"))

    def test_negative_total_is_rejected(self):
        self.assert_rejected("stripe", "-1")

    def test_unknown_currency_is_rejected(self):
        self.assert_rejected("stripe", "1", currency="usd")

    def test_unknown_provider_is_rejected(self):
        self.assert_rejected("redsys", "1")

    def test_convertible_decimal_value_is_accepted(self):
        self.assertEqual(validate_payment_amount("paypal", 1), Decimal("1"))

    def test_invalid_amount_is_rejected(self):
        self.assert_rejected("stripe", "not-a-number")

    def test_non_finite_amount_is_rejected(self):
        self.assert_rejected("stripe", "NaN")


class PaymentAmountRoutesRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")

    def test_stripe_validates_amount_before_cents_or_provider_calls(self):
        start = self.source.index("def create_payment_intent")
        end = self.source.index("@api.route('/paypal/create-order'")
        source = self.source[start:end]

        validation_index = source.index('validate_payment_amount("stripe"')
        cents_index = source.index('amount = int(round(checkout_quote["total_amount"] * 100))')
        modify_index = source.index("stripe.PaymentIntent.modify(")
        create_index = source.index("stripe.PaymentIntent.create(")

        self.assertLess(validation_index, cents_index)
        self.assertLess(validation_index, modify_index)
        self.assertLess(validation_index, create_index)
        self.assertIn("PAYMENT_AMOUNT_NOT_SUPPORTED", source)
        self.assertIn("return jsonify(PAYMENT_AMOUNT_NOT_SUPPORTED_RESPONSE), 400", source)

    def test_paypal_validates_amount_before_session_or_provider_request(self):
        start = self.source.index("def create_paypal_order")
        end = self.source.index("@api.route('/paypal/capture-order'")
        source = self.source[start:end]

        validation_index = source.index('validate_payment_amount("paypal"')
        upsert_index = source.index("_upsert_paypal_checkout_session(")
        request_index = source.index("_paypal_request(")

        self.assertLess(validation_index, upsert_index)
        self.assertLess(validation_index, request_index)
        self.assertIn("PAYMENT_AMOUNT_NOT_SUPPORTED", source)
        self.assertIn("return jsonify(PAYMENT_AMOUNT_NOT_SUPPORTED_RESPONSE), 400", source)

    def test_paypal_runtime_error_is_sanitized(self):
        start = self.source.index("def create_paypal_order")
        end = self.source.index("@api.route('/paypal/capture-order'")
        source = self.source[start:end]

        runtime_error_block = source[source.index("except RuntimeError as e:"):]
        self.assertIn("logger.exception", runtime_error_block)
        self.assertIn("PAYPAL_ORDER_CREATION_FAILED", runtime_error_block)
        self.assertIn("No se ha podido iniciar el pago con PayPal.", runtime_error_block)
        self.assertNotIn('return jsonify({"error": str(e)}), 502', runtime_error_block)


if __name__ == "__main__":
    unittest.main()

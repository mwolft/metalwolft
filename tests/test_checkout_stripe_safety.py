import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.checkout_cart_cleanup import cleanup_cart_lines_from_checkout_quote
from api.checkout_payment_security import is_modifiable_stripe_checkout_session


DEFAULT_LINE = {
    "product_id": 1,
    "quantity": 1,
    "alto": 30,
    "ancho": 30,
    "anclaje": "Sin obra: con agujeros interiores",
    "color": "satinado_blanco",
    "screw_option": "standard",
}


class FakeQuery:
    def __init__(self, items):
        self.items = items

    def filter_by(self, **filters):
        return FakeFilteredQuery([
            item for item in self.items
            if all(getattr(item, key) == value for key, value in filters.items())
        ])


class FakeFilteredQuery:
    def __init__(self, items):
        self.items = items

    def all(self):
        return list(self.items)


class FakeSession:
    def __init__(self, items):
        self.items = items
        self.deleted = []

    def delete(self, item):
        self.deleted.append(item)
        self.items.remove(item)


def cart_item(**overrides):
    values = {
        "id": 1,
        "usuario_id": 10,
        "producto_id": 1,
        "alto": 30.0,
        "ancho": 30.0,
        "anclaje": "Sin obra: con agujeros interiores",
        "color": "satinado_blanco",
        "screw_option": "standard",
        "quantity": 1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def quote_with_lines(*lines):
    return {"lines": list(lines)}


class CheckoutCartCleanupTest(unittest.TestCase):
    def cleanup(self, items, *lines):
        session = FakeSession(items)
        cart_model = SimpleNamespace(query=FakeQuery(items))
        cleanup_cart_lines_from_checkout_quote(
            db_session=session,
            cart_model=cart_model,
            user_id=10,
            checkout_quote=quote_with_lines(*lines),
        )
        return session

    def test_order_created_removes_exact_matching_cart_line(self):
        items = [cart_item(quantity=1)]

        session = self.cleanup(items, DEFAULT_LINE)

        self.assertEqual(items, [])
        self.assertEqual(len(session.deleted), 1)

    def test_order_created_subtracts_quantity_when_cart_has_more_units(self):
        items = [cart_item(quantity=3)]

        session = self.cleanup(items, DEFAULT_LINE)

        self.assertEqual(items[0].quantity, 2)
        self.assertEqual(session.deleted, [])

    def test_later_added_line_is_preserved(self):
        later_line = cart_item(id=2, producto_id=2, quantity=1)
        items = [cart_item(quantity=1), later_line]

        self.cleanup(items, DEFAULT_LINE)

        self.assertEqual(items, [later_line])

    def test_different_measurements_of_same_product_are_preserved(self):
        different_measurement = cart_item(id=2, alto=31.0, ancho=30.0, quantity=1)
        items = [cart_item(quantity=1), different_measurement]

        self.cleanup(items, DEFAULT_LINE)

        self.assertEqual(items, [different_measurement])

    def test_different_configuration_of_same_product_is_preserved(self):
        different_color = cart_item(id=2, color="forja_negro", quantity=1)
        items = [cart_item(quantity=1), different_color]

        self.cleanup(items, DEFAULT_LINE)

        self.assertEqual(items, [different_color])

    def test_different_anchor_of_same_product_is_preserved(self):
        different_anchor = cart_item(id=2, anclaje="Sin obra: con pletinas", quantity=1)
        items = [cart_item(quantity=1), different_anchor]

        self.cleanup(items, DEFAULT_LINE)

        self.assertEqual(items, [different_anchor])

    def test_different_screw_option_of_same_product_is_preserved(self):
        long_screws = cart_item(id=2, screw_option="long_150", quantity=1)
        items = [cart_item(quantity=1), long_screws]

        self.cleanup(items, DEFAULT_LINE)

        self.assertEqual(items, [long_screws])

    def test_duplicate_matching_lines_are_consumed_once_when_total_covers_purchase(self):
        items = [cart_item(id=1, quantity=1), cart_item(id=2, quantity=1)]
        purchased_two = {**DEFAULT_LINE, "quantity": 2}

        session = self.cleanup(items, purchased_two)

        self.assertEqual(items, [])
        self.assertEqual(len(session.deleted), 2)

    def test_duplicate_matching_lines_are_preserved_when_total_is_lower_than_purchase(self):
        first = cart_item(id=1, quantity=1)
        second = cart_item(id=2, quantity=1)
        items = [first, second]
        purchased_three = {**DEFAULT_LINE, "quantity": 3}

        session = self.cleanup(items, purchased_three)

        self.assertEqual(items, [first, second])
        self.assertEqual(session.deleted, [])

    def test_repeated_cleanup_after_line_is_removed_does_not_fail(self):
        items = [cart_item(quantity=1)]

        self.cleanup(items, DEFAULT_LINE)
        second_session = self.cleanup(items, DEFAULT_LINE)

        self.assertEqual(items, [])
        self.assertEqual(second_session.deleted, [])

    def test_reduced_line_is_preserved(self):
        items = [cart_item(quantity=1)]
        purchased_two = {**DEFAULT_LINE, "quantity": 2}

        session = self.cleanup(items, purchased_two)

        self.assertEqual(items[0].quantity, 1)
        self.assertEqual(session.deleted, [])


class CheckoutPaymentIntentSecurityTest(unittest.TestCase):
    def test_foreign_or_missing_payment_intent_is_not_modifiable(self):
        self.assertFalse(is_modifiable_stripe_checkout_session(None, "pi_foreign"))

    def test_valid_own_payment_intent_can_be_reused(self):
        checkout_session = SimpleNamespace(
            payment_provider="stripe",
            payment_intent_id="pi_own",
            order_id=None,
            status="pending_payment",
        )

        self.assertTrue(is_modifiable_stripe_checkout_session(checkout_session, "pi_own"))

    def test_finalized_payment_intent_is_not_modifiable(self):
        checkout_session = SimpleNamespace(
            payment_provider="stripe",
            payment_intent_id="pi_paid",
            order_id=123,
            status="order_created",
        )

        self.assertFalse(is_modifiable_stripe_checkout_session(checkout_session, "pi_paid"))

    def test_final_provider_status_without_order_is_not_modifiable(self):
        checkout_session = SimpleNamespace(
            payment_provider="stripe",
            payment_intent_id="pi_succeeded",
            order_id=None,
            status="succeeded",
        )

        self.assertFalse(is_modifiable_stripe_checkout_session(checkout_session, "pi_succeeded"))


class CheckoutSourceRegressionTest(unittest.TestCase):
    def test_processing_path_does_not_clear_cart_from_legacy_checkout(self):
        source = (ROOT_DIR / "src/front/js/component/CheckoutForm.jsx").read_text(encoding="utf-8")
        start = source.index("const handleOrderCompletion")
        end = source.index("const handlePayPalCheckoutContext")
        handle_order_completion = source[start:end]

        self.assertNotIn("actions.clearCart", handle_order_completion)
        self.assertIn("attemptOrderFallback: false", source)

    def test_create_payment_intent_unexpected_error_is_sanitized(self):
        source = (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")
        start = source.index("def create_payment_intent")
        end = source.index("@api.route('/paypal/create-order'")
        create_payment_intent_source = source[start:end]

        self.assertIn("No hemos podido preparar el pago", create_payment_intent_source)
        self.assertIn("logger.exception", create_payment_intent_source)


if __name__ == "__main__":
    unittest.main()

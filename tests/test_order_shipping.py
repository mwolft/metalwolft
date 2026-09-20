import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.order_shipping import (  # noqa: E402
    shipping_address_from_order,
    shipping_address_from_customer_snapshot,
    shipping_address_from_order_details,
    shipping_address_lines,
)


class OrderShippingAddressTest(unittest.TestCase):
    def test_checkout_snapshot_keeps_different_shipping_with_optional_fields(self):
        address = shipping_address_from_customer_snapshot(
            {
                "firstname": "Ana",
                "lastname": "Cliente",
                "billing_address": "Calle Fiscal 1",
                "billing_postal_code": "13001",
                "billing_city": "Ciudad Real",
                "shipping_address": "Calle Entrega 12",
                "shipping_postal_code": "28013",
                "shipping_city": "Madrid",
                "shipping_province": "Madrid",
                "shipping_country_code": "ES",
            }
        )

        self.assertFalse(address.same_as_billing)
        self.assertEqual(
            shipping_address_lines(address),
            ("Ana Cliente", "Calle Entrega 12", "28013 Madrid", "Madrid", "ES"),
        )

    def test_checkout_snapshot_marks_shipping_equal_to_billing(self):
        address = shipping_address_from_customer_snapshot(
            {
                "firstname": "Ana",
                "lastname": "Cliente",
                "billing_address": "Calle Mayor 1",
                "billing_postal_code": "13001",
                "billing_city": "Ciudad Real",
            }
        )

        self.assertTrue(address.same_as_billing)
        self.assertEqual(address.address, "Calle Mayor 1")

    def test_historical_order_details_remain_usable_without_checkout_session(self):
        detail = SimpleNamespace(
            firstname="Ana",
            lastname="Cliente",
            shipping_address="Calle Entrega 12",
            shipping_postal_code="28013",
            shipping_city="Madrid",
            billing_address=None,
            billing_postal_code=None,
            billing_city=None,
        )

        address = shipping_address_from_order_details([detail])

        self.assertEqual(
            shipping_address_lines(address),
            ("Ana Cliente", "Calle Entrega 12", "28013 Madrid"),
        )
        self.assertIsNone(address.province)
        self.assertIsNone(address.country_code)

    def test_order_prefers_operational_details_over_confirmation_and_checkout_snapshots(self):
        detail = SimpleNamespace(
            firstname="Ana",
            lastname="Cliente",
            shipping_address="Calle Operativa 1",
            shipping_postal_code="13001",
            shipping_city="Ciudad Real",
            billing_address=None,
            billing_postal_code=None,
            billing_city=None,
        )
        order = SimpleNamespace(
            order_details=[detail],
            confirmed_order_context=SimpleNamespace(
                customer_snapshot={
                    "shipping_address": "Calle Contexto 2",
                    "shipping_postal_code": "28013",
                    "shipping_city": "Madrid",
                }
            ),
            checkout_session=SimpleNamespace(
                customer_snapshot={
                    "shipping_address": "Calle Checkout 3",
                    "shipping_postal_code": "41001",
                    "shipping_city": "Sevilla",
                }
            ),
        )

        address = shipping_address_from_order(order)

        self.assertEqual(address.address, "Calle Operativa 1")
        self.assertEqual(address.city, "Ciudad Real")

    def test_order_uses_confirmation_snapshot_when_operational_details_are_empty(self):
        detail = SimpleNamespace(
            firstname=None,
            lastname=None,
            shipping_address=None,
            shipping_postal_code=None,
            shipping_city=None,
            billing_address=None,
            billing_postal_code=None,
            billing_city=None,
        )
        order = SimpleNamespace(
            order_details=[detail],
            confirmed_order_context=SimpleNamespace(
                customer_snapshot={
                    "firstname": "Ana",
                    "lastname": "Cliente",
                    "shipping_address": "Calle Contexto 2",
                    "shipping_postal_code": "28013",
                    "shipping_city": "Madrid",
                }
            ),
            checkout_session=SimpleNamespace(
                customer_snapshot={
                    "shipping_address": "Calle Checkout 3",
                    "shipping_postal_code": "41001",
                    "shipping_city": "Sevilla",
                }
            ),
        )

        address = shipping_address_from_order(order)

        self.assertEqual(address.address, "Calle Contexto 2")
        self.assertEqual(address.city, "Madrid")

    def test_order_uses_checkout_snapshot_when_confirmation_snapshot_is_empty(self):
        detail = SimpleNamespace(
            firstname=None,
            lastname=None,
            shipping_address=None,
            shipping_postal_code=None,
            shipping_city=None,
            billing_address=None,
            billing_postal_code=None,
            billing_city=None,
        )
        order = SimpleNamespace(
            order_details=[detail],
            confirmed_order_context=SimpleNamespace(customer_snapshot={}),
            checkout_session=SimpleNamespace(
                customer_snapshot={
                    "firstname": "Ana",
                    "lastname": "Cliente",
                    "shipping_address": "Calle Checkout 3",
                    "shipping_postal_code": "41001",
                    "shipping_city": "Sevilla",
                }
            ),
        )

        address = shipping_address_from_order(order)

        self.assertEqual(address.address, "Calle Checkout 3")
        self.assertEqual(address.city, "Sevilla")

    def test_order_without_any_address_remains_empty(self):
        order = SimpleNamespace(
            order_details=[],
            confirmed_order_context=SimpleNamespace(customer_snapshot={}),
            checkout_session=SimpleNamespace(customer_snapshot={}),
        )

        address = shipping_address_from_order(order)

        self.assertFalse(address.is_available)
        self.assertEqual(shipping_address_lines(address), ())


if __name__ == "__main__":
    unittest.main()

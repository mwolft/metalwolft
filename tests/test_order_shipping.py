import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.order_shipping import (  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()

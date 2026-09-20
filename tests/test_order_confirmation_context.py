import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from api.order_confirmation_context import get_order_customer_snapshot  # noqa: E402


class OrderConfirmationCustomerSnapshotTest(unittest.TestCase):
    def test_prefers_a_complete_confirmed_customer_snapshot(self):
        order = SimpleNamespace(
            confirmed_order_context=SimpleNamespace(
                customer_snapshot={
                    "email": "confirmed@example.test",
                    "phone": "600000001",
                }
            ),
            checkout_session=SimpleNamespace(
                customer_snapshot={
                    "email": "checkout@example.test",
                    "phone": "600000002",
                }
            ),
        )

        snapshot = get_order_customer_snapshot(order)

        self.assertEqual(snapshot["email"], "confirmed@example.test")
        self.assertEqual(snapshot["phone"], "600000001")

    def test_falls_back_per_missing_field_without_discarding_confirmed_values(self):
        order = SimpleNamespace(
            confirmed_order_context=SimpleNamespace(
                customer_snapshot={"email": "confirmed@example.test"}
            ),
            checkout_session=SimpleNamespace(
                customer_snapshot={
                    "email": "checkout@example.test",
                    "phone": "600000002",
                }
            ),
        )

        snapshot = get_order_customer_snapshot(order)

        self.assertEqual(snapshot["email"], "confirmed@example.test")
        self.assertEqual(snapshot["phone"], "600000002")

    def test_empty_confirmed_snapshot_falls_back_to_historical_checkout(self):
        order = SimpleNamespace(
            confirmed_order_context=SimpleNamespace(customer_snapshot={}),
            checkout_session=SimpleNamespace(
                customer_snapshot={
                    "email": "checkout@example.test",
                    "phone": "600000003",
                }
            ),
        )

        snapshot = get_order_customer_snapshot(order)

        self.assertEqual(snapshot["email"], "checkout@example.test")
        self.assertEqual(snapshot["phone"], "600000003")


if __name__ == "__main__":
    unittest.main()

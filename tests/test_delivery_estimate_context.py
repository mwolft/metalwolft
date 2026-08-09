import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.delivery_estimate_service import (  # noqa: E402
    OPENING_TYPE_FIXED,
    OPENING_TYPE_HINGED,
    build_delivery_estimate,
    calculate_delivery_adjustment_days,
)


class DeliveryEstimateContextTest(unittest.TestCase):
    config = SimpleNamespace(delivery_days=15, range_days=7, is_active=True)
    today = date(2026, 8, 9)

    def cart_line(self, quantity, opening_type=OPENING_TYPE_FIXED):
        return SimpleNamespace(
            quantity=quantity,
            product=SimpleNamespace(opening_type=opening_type),
        )

    def test_quantity_adjustments_apply_only_once(self):
        cases = (
            (1, 0),
            (3, 0),
            (4, 2),
            (5, 2),
            (6, 5),
        )

        for quantity, expected_adjustment in cases:
            with self.subTest(quantity=quantity):
                self.assertEqual(
                    calculate_delivery_adjustment_days([self.cart_line(quantity)]),
                    expected_adjustment,
                )

    def test_hinged_and_quantity_adjustments_accumulate(self):
        self.assertEqual(
            calculate_delivery_adjustment_days([
                self.cart_line(1, OPENING_TYPE_HINGED),
            ]),
            3,
        )
        self.assertEqual(
            calculate_delivery_adjustment_days([
                self.cart_line(3),
                self.cart_line(1, OPENING_TYPE_HINGED),
            ]),
            5,
        )
        self.assertEqual(
            calculate_delivery_adjustment_days([
                self.cart_line(5),
                self.cart_line(1, OPENING_TYPE_HINGED),
            ]),
            8,
        )

    def test_legacy_availability_flag_does_not_classify_the_cart_line(self):
        fixed_product_available_as_hinged = SimpleNamespace(
            opening_type=OPENING_TYPE_FIXED,
            has_abatible=True,
        )
        cart_line = SimpleNamespace(quantity=1, product=fixed_product_available_as_hinged)

        self.assertEqual(calculate_delivery_adjustment_days([cart_line]), 0)

    def test_contextual_range_moves_both_dates_by_the_same_amount(self):
        global_estimate = build_delivery_estimate(self.config, today=self.today)
        contextual_estimate = build_delivery_estimate(
            self.config,
            cart_items=[
                self.cart_line(5),
                self.cart_line(1, OPENING_TYPE_HINGED),
            ],
            today=self.today,
        )

        self.assertEqual(global_estimate["start_date"], "2026-08-24")
        self.assertEqual(global_estimate["end_date"], "2026-08-31")
        self.assertEqual(contextual_estimate["start_date"], "2026-09-01")
        self.assertEqual(contextual_estimate["end_date"], "2026-09-08")


if __name__ == "__main__":
    unittest.main()

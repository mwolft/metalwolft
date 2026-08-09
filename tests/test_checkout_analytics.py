import unittest
from types import SimpleNamespace

from api.checkout_analytics import (
    CheckoutAnalyticsSnapshotError,
    build_confirmed_purchase_payload,
)


def checkout_session(provider):
    return SimpleNamespace(
        payment_provider=provider,
        quote_snapshot={
            "lines": [
                {
                    "product_id": 42,
                    "product_name": "Reja fija Albany",
                    "unit_price": 139.0,
                    "quantity": 2,
                }
            ],
            "shipping_cost": 15.0,
            "discount_code": "REJAS10",
            "total_amount": 265.2,
        },
    )


class CheckoutAnalyticsPayloadTest(unittest.TestCase):
    def test_stripe_and_paypal_use_the_same_frozen_purchase_contract(self):
        order = SimpleNamespace(id=91, locator="QE2885")

        stripe_payload = build_confirmed_purchase_payload(
            order=order,
            checkout_session=checkout_session("stripe"),
        )
        paypal_payload = build_confirmed_purchase_payload(
            order=order,
            checkout_session=checkout_session("paypal"),
        )

        self.assertEqual(stripe_payload, paypal_payload)
        self.assertEqual(
            stripe_payload,
            {
                "transaction_id": "QE2885",
                "value": 265.2,
                "currency": "EUR",
                "shipping": 15.0,
                "coupon": "REJAS10",
                "items": [
                    {
                        "item_id": 42,
                        "item_name": "Reja fija Albany",
                        "price": 139.0,
                        "quantity": 2,
                    }
                ],
            },
        )

    def test_missing_frozen_lines_are_rejected(self):
        with self.assertRaises(CheckoutAnalyticsSnapshotError):
            build_confirmed_purchase_payload(
                order=SimpleNamespace(id=91, locator="QE2885"),
                checkout_session=SimpleNamespace(quote_snapshot={}),
            )


if __name__ == "__main__":
    unittest.main()

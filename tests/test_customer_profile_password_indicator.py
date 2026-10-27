from types import SimpleNamespace
import unittest

from api.customer_profile import serialize_customer_profile


class CustomerProfilePasswordIndicatorTest(unittest.TestCase):
    def test_password_indicator_does_not_expose_hash(self):
        fields = dict(
            id=1, email="test@example.invalid", firstname=None, lastname=None,
            phone=None, shipping_address=None, shipping_city=None,
            shipping_postal_code=None, billing_address=None, billing_city=None,
            billing_postal_code=None, CIF=None,
        )
        local = serialize_customer_profile(SimpleNamespace(**fields, password="bcrypt-hash"))
        google = serialize_customer_profile(SimpleNamespace(**fields, password=None))
        self.assertIs(local["has_password"], True)
        self.assertIs(google["has_password"], False)
        self.assertNotIn("password", local)

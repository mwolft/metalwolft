import importlib.util
import sys
import unittest
import ast
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ADMIN_PATH = SRC_DIR / "api" / "admin.py"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ROUTE_DEPS = all(
    has_package(package)
    for package in ("flask", "flask_jwt_extended", "flask_sqlalchemy", "sqlalchemy")
)


if HAS_ROUTE_DEPS:
    from api import routes
    from api.models import Orders


def user_with_phone(phone):
    return SimpleNamespace(
        firstname=None,
        lastname=None,
        phone=phone,
        shipping_address=None,
        shipping_city=None,
        shipping_postal_code=None,
        billing_address=None,
        billing_city=None,
        billing_postal_code=None,
        CIF=None,
    )


class CustomerPhoneAdminContractTest(unittest.TestCase):
    def test_users_admin_lists_phone_with_a_readable_label(self):
        tree = ast.parse(ADMIN_PATH.read_text(encoding="utf-8"))
        users_view = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "UsersAdminView"
        )
        assignments = {
            target.id: statement.value
            for statement in users_view.body
            if isinstance(statement, ast.Assign)
            for target in statement.targets
            if isinstance(target, ast.Name)
        }

        self.assertIn("phone", ast.literal_eval(assignments["column_list"]))
        labels = ast.literal_eval(assignments["column_labels"])
        self.assertEqual(labels["phone"], "Teléfono")

    def test_public_customer_order_contract_does_not_add_phone(self):
        source = (SRC_DIR / "api" / "customer_order_serializers.py").read_text(encoding="utf-8")

        self.assertNotIn('"phone"', source)


@unittest.skipUnless(HAS_ROUTE_DEPS, "Flask/SQLAlchemy test dependencies are not installed.")
class CustomerPhonePropagationTest(unittest.TestCase):
    def test_checkout_phone_fills_an_empty_user_profile_phone(self):
        user = user_with_phone(None)

        updated = routes._sync_user_from_customer_context(user, {"phone": "600 123 123"})

        self.assertTrue(updated)
        self.assertEqual(user.phone, "600 123 123")

    def test_checkout_phone_never_overwrites_an_existing_user_profile_phone(self):
        user = user_with_phone("611 111 111")

        updated = routes._sync_user_from_customer_context(user, {"phone": "600 123 123"})

        self.assertFalse(updated)
        self.assertEqual(user.phone, "611 111 111")

    def test_legacy_context_without_phone_keeps_profile_unchanged(self):
        user = user_with_phone(None)

        updated = routes._sync_user_from_customer_context(user, {})

        self.assertFalse(updated)
        self.assertIsNone(user.phone)

    def test_order_phone_uses_only_the_checkout_snapshot(self):
        order = SimpleNamespace(
            checkout_session=SimpleNamespace(customer_snapshot={"phone": "600 123 123"}),
            user=SimpleNamespace(phone="611 111 111"),
        )

        self.assertEqual(Orders.customer_phone_snapshot.fget(order), "600 123 123")

    def test_order_without_snapshot_never_falls_back_to_live_user_phone(self):
        order = SimpleNamespace(
            checkout_session=None,
            user=SimpleNamespace(phone="611 111 111"),
        )

        self.assertIsNone(Orders.customer_phone_snapshot.fget(order))


if __name__ == "__main__":
    unittest.main()

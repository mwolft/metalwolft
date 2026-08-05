import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.customer_profile import (  # noqa: E402
    normalize_customer_profile_update,
    serialize_customer_profile,
)
from api.customer_snapshot import CustomerSnapshotValidationError  # noqa: E402


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ENDPOINT_DEPS = all(
    has_package(package)
    for package in ("flask", "flask_jwt_extended", "flask_sqlalchemy", "sqlalchemy")
)

if HAS_ENDPOINT_DEPS:
    from flask import Flask  # noqa: E402
    from flask_jwt_extended import JWTManager, create_access_token  # noqa: E402

    from api.models import Users, db  # noqa: E402
    from api.routes import api  # noqa: E402


class CustomerProfileContractTest(unittest.TestCase):
    def test_normalization_reuses_customer_snapshot_limits(self):
        normalized = normalize_customer_profile_update(
            {
                "firstname": "  Ana  ",
                "phone": "  600 123 123  ",
                "CIF": " b12345678 ",
            }
        )

        self.assertEqual(normalized["firstname"], "Ana")
        self.assertEqual(normalized["phone"], "600 123 123")
        self.assertEqual(normalized["CIF"], "B12345678")

    def test_invalid_phone_type_is_rejected_without_echoing_value(self):
        with self.assertRaises(CustomerSnapshotValidationError) as context:
            normalize_customer_profile_update({"phone": ["private-value"]})

        self.assertEqual(context.exception.field, "phone")
        self.assertNotIn("private-value", str(context.exception))

    def test_empty_phone_is_normalized_to_none(self):
        self.assertIsNone(normalize_customer_profile_update({"phone": "   "})["phone"])

    def test_profile_serializer_includes_nullable_phone(self):
        profile = serialize_customer_profile(
            SimpleNamespace(
                id=1,
                email="profile@example.test",
                firstname="Cliente",
                lastname="Historico",
                phone=None,
                shipping_address=None,
                shipping_city=None,
                shipping_postal_code=None,
                billing_address=None,
                billing_city=None,
                billing_postal_code=None,
                CIF=None,
            )
        )

        self.assertIn("phone", profile)
        self.assertIsNone(profile["phone"])


@unittest.skipUnless(
    HAS_ENDPOINT_DEPS,
    "Flask/JWT/SQLAlchemy test dependencies are not installed.",
)
class CustomerProfileEndpointTest(unittest.TestCase):
    def setUp(self):
        self.invoice_dir = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            INVOICE_FOLDER=self.invoice_dir.name,
        )
        JWTManager(self.app)
        db.init_app(self.app)
        self.app.register_blueprint(api, url_prefix="/api")

        with self.app.app_context():
            self.user = Users(
                email="profile@example.test",
                password="not-a-real-password",
                firstname="Cliente",
                lastname="Historico",
                phone=None,
                billing_address="Calle Fiscal 1",
                billing_city="Ciudad Real",
                billing_postal_code="13001",
                shipping_address="Calle Entrega 2",
                shipping_city="Toledo",
                shipping_postal_code="45001",
                CIF="12345678Z",
                is_active=True,
                is_admin=False,
            )
            self.other_user = Users(
                email="other@example.test",
                password="not-a-real-password",
                firstname="Otro",
                lastname="Cliente",
                phone="611111111",
                is_active=True,
                is_admin=False,
            )
            db.session.add_all([self.user, self.other_user])
            db.session.commit()
            self.user_id = self.user.id
            self.other_user_id = self.other_user.id
            self.token = self._token_for(self.user)

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.invoice_dir.cleanup()

    def _token_for(self, user):
        return create_access_token(
            identity=str(user.id),
            additional_claims={"email": user.email, "is_admin": bool(user.is_admin)},
        )

    def _auth(self):
        return {"Authorization": f"Bearer {self.token}"}

    def test_historical_user_with_null_phone_is_returned(self):
        response = self.client.get("/api/me", headers=self._auth())

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json()["phone"])

    def test_profile_saves_and_normalizes_phone_and_names(self):
        response = self.client.patch(
            "/api/me",
            headers=self._auth(),
            json={
                "firstname": "  Ana María  ",
                "lastname": "  García López  ",
                "phone": "  600 123 123  ",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["firstname"], "Ana María")
        self.assertEqual(payload["lastname"], "García López")
        self.assertEqual(payload["phone"], "600 123 123")

        with self.app.app_context():
            user = db.session.get(Users, self.user_id)
            self.assertEqual(user.phone, "600 123 123")

    def test_invalid_phone_returns_controlled_400(self):
        response = self.client.patch(
            "/api/me",
            headers=self._auth(),
            json={"phone": ["600000000"]},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["field"], "phone")
        self.assertNotIn("600000000", response.get_data(as_text=True))

    def test_overlong_phone_returns_controlled_400(self):
        response = self.client.patch(
            "/api/me",
            headers=self._auth(),
            json={"phone": "1" * 51},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["field"], "phone")

    def test_partial_update_preserves_omitted_fields_and_email(self):
        response = self.client.patch(
            "/api/me",
            headers=self._auth(),
            json={"phone": "600000001", "email": "changed@example.test"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["email"], "profile@example.test")
        self.assertEqual(payload["billing_address"], "Calle Fiscal 1")
        self.assertEqual(payload["shipping_address"], "Calle Entrega 2")

    def test_empty_phone_can_clear_nullable_profile_field(self):
        with self.app.app_context():
            user = db.session.get(Users, self.user_id)
            user.phone = "600000002"
            db.session.commit()

        response = self.client.patch(
            "/api/me",
            headers=self._auth(),
            json={"phone": "   "},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json()["phone"])

    def test_profile_endpoint_cannot_target_another_user(self):
        response = self.client.patch(
            "/api/me",
            headers=self._auth(),
            json={"id": self.other_user_id, "firstname": "Actualizado"},
        )

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            current_user = db.session.get(Users, self.user_id)
            other_user = db.session.get(Users, self.other_user_id)
            self.assertEqual(current_user.firstname, "Actualizado")
            self.assertEqual(other_user.firstname, "Otro")

        forbidden = self.client.put(
            f"/api/users/{self.other_user_id}",
            headers=self._auth(),
            json={"firstname": "No permitido"},
        )
        self.assertEqual(forbidden.status_code, 403)

    def test_legacy_cif_update_remains_compatible(self):
        response = self.client.put(
            "/api/me",
            headers=self._auth(),
            json={"CIF": "  b12345678  "},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["CIF"], "B12345678")


if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from api.models import db, Users, ExternalIdentity, Orders
from api.routes import api
from api.google_identity import GoogleIdentityError, verify_google_identity
from api.password_recovery_endpoints import auth_bp


class GoogleCustomerAuthTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="test-only-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        JWTManager(self.app)
        db.init_app(self.app)
        self.app.register_blueprint(api, url_prefix="/api")
        self.app.register_blueprint(auth_bp, url_prefix="/api/auth")
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()
        self.verifier = patch("api.routes.verify_google_identity")
        self.verify = self.verifier.start()
        self.verify.return_value = {"sub": "google-sub-1", "email": "new@example.test"}

    def tearDown(self):
        self.verifier.stop()
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_new_google_customer_reuses_local_session_and_checkout_identity(self):
        response = self.client.post("/api/auth/google", json={"credential": "mock"})
        self.assertEqual(response.status_code, 200)
        user_id = response.json["results"]["id"]
        token = response.json["access_token"]
        with self.app.app_context():
            user = db.session.get(Users, user_id)
            self.assertIsNone(user.password)
            self.assertFalse(user.is_admin)
            self.assertEqual(ExternalIdentity.query.filter_by(user_id=user_id).one().provider_subject, "google-sub-1")
        self.assertEqual(self.client.post("/api/login", json={"email": "new@example.test", "password": "wrong"}).status_code, 401)
        orders = self.client.get("/api/customer/orders", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(orders.status_code, 200)
        self.assertEqual(orders.json["orders"], [])
        checkout = self.client.post(
            "/api/checkout/quote", json={}, headers={"Authorization": f"Bearer {token}"}
        )
        self.assertIn(checkout.status_code, (200, 400))

    def test_repeat_login_preserves_user_and_orders(self):
        first = self.client.post("/api/auth/google", json={"credential": "mock"})
        user_id = first.json["results"]["id"]
        with self.app.app_context():
            db.session.add(Orders(user_id=user_id, total_amount=100, locator="TEST0001"))
            db.session.commit()
        again = self.client.post("/api/auth/google", json={"credential": "mock"})
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json["results"]["id"], user_id)
        with self.app.app_context():
            self.assertEqual(Orders.query.filter_by(user_id=user_id).count(), 1)

    def test_existing_email_is_not_auto_linked(self):
        with self.app.app_context():
            db.session.add(Users(email="NEW@example.test", password="existing-hash", is_admin=False))
            db.session.commit()
        response = self.client.post("/api/auth/google", json={"credential": "mock"})
        self.assertEqual(response.status_code, 409)
        self.assertIn("Accede con tu contraseña", response.json["message"])
        with self.app.app_context():
            self.assertEqual(Users.query.count(), 1)
            self.assertEqual(ExternalIdentity.query.count(), 0)

    def test_authenticated_link_keeps_original_user_and_password(self):
        import bcrypt
        password = bcrypt.hashpw(b"existing-password", bcrypt.gensalt()).decode()
        with self.app.app_context():
            user = Users(email="new@example.test", password=password, is_admin=False)
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        login = self.client.post("/api/login", json={"email": "new@example.test", "password": "existing-password"})
        self.assertEqual(login.status_code, 200)
        link = self.client.post(
            "/api/auth/google/link", json={"credential": "mock", "password": "existing-password"},
            headers={"Authorization": f"Bearer {login.json['access_token']}"},
        )
        self.assertEqual(link.status_code, 200)
        google_login = self.client.post("/api/auth/google", json={"credential": "mock"})
        self.assertEqual(google_login.json["results"]["id"], user_id)
        self.assertEqual(self.client.post("/api/login", json={"email": "new@example.test", "password": "existing-password"}).status_code, 200)

    def test_link_cannot_take_identity_from_another_user(self):
        first = self.client.post("/api/auth/google", json={"credential": "mock"})
        self.verify.return_value = {"sub": "another-google", "email": "other@example.test"}
        second = self.client.post("/api/auth/google", json={"credential": "mock"})
        self.verify.return_value = {"sub": "google-sub-1", "email": "new@example.test"}
        with self.app.app_context():
            other = db.session.get(Users, second.json["results"]["id"])
            import bcrypt
            other.password = bcrypt.hashpw(b"other-password", bcrypt.gensalt()).decode()
            db.session.commit()
        response = self.client.post(
            "/api/auth/google/link", json={"credential": "mock", "password": "other-password"},
            headers={"Authorization": f"Bearer {second.json['access_token']}"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertNotEqual(first.json["results"]["id"], second.json["results"]["id"])

    def test_link_requires_current_password_and_session(self):
        import bcrypt
        password = bcrypt.hashpw(b"current-password", bcrypt.gensalt()).decode()
        with self.app.app_context():
            db.session.add(Users(email="new@example.test", password=password, is_admin=False))
            db.session.commit()
        login = self.client.post("/api/login", json={"email": "new@example.test", "password": "current-password"})
        self.assertEqual(self.client.post("/api/auth/google/link", json={"credential": "mock"}).status_code, 401)
        wrong = self.client.post(
            "/api/auth/google/link", json={"credential": "mock", "password": "wrong"},
            headers={"Authorization": f"Bearer {login.json['access_token']}"},
        )
        self.assertEqual(wrong.status_code, 403)
        with self.app.app_context():
            self.assertEqual(ExternalIdentity.query.count(), 0)

    def test_inactive_linked_account_cannot_access_with_google(self):
        first = self.client.post("/api/auth/google", json={"credential": "mock"})
        with self.app.app_context():
            user = db.session.get(Users, first.json["results"]["id"])
            user.is_active = False
            db.session.commit()
        self.assertEqual(self.client.post("/api/auth/google", json={"credential": "mock"}).status_code, 403)

    def test_invalid_google_token_is_rejected(self):
        self.verify.side_effect = GoogleIdentityError("Credencial de Google inválida.")
        self.assertEqual(self.client.post("/api/auth/google", json={"credential": "bad"}).status_code, 401)
        self.assertEqual(self.client.post("/api/auth/google", json=[]).status_code, 400)

    def test_verification_failure_keeps_browser_message_generic(self):
        self.verify.side_effect = GoogleIdentityError("No se pudo verificar la identidad de Google.")
        response = self.client.post("/api/auth/google", json={"credential": "sensitive-credential"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "No se pudo verificar la identidad de Google."})
        self.assertNotIn("sensitive-credential", response.get_data(as_text=True))

    def test_password_reset_requires_reset_purpose_and_supports_google_only_user(self):
        self.client.post("/api/auth/google", json={"credential": "mock"})
        with self.app.app_context():
            wrong_token = create_access_token(identity="new@example.test")
            reset_token = create_access_token(
                identity="new@example.test", additional_claims={"purpose": "password_reset"}
            )
        wrong = self.client.post("/api/auth/reset-password", json={"token": wrong_token, "password": "new-password"})
        self.assertEqual(wrong.status_code, 400)
        reset = self.client.post("/api/auth/reset-password", json={"token": reset_token, "password": "new-password"})
        self.assertEqual(reset.status_code, 200)
        self.assertEqual(self.client.post("/api/login", json={"email": "new@example.test", "password": "new-password"}).status_code, 200)


class GoogleTokenValidationTest(unittest.TestCase):
    @patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-client-id"})
    def test_development_diagnostics_do_not_expose_credentials_or_exception_details(self):
        import jwt

        app = Flask(__name__)
        app.config["APP_ENV"] = "development"
        with app.app_context(), patch.object(app.logger, "warning") as warning:
            with patch(
                "api.google_identity._jwks.get_signing_key_from_jwt",
                side_effect=jwt.PyJWKClientConnectionError("sensitive-token-and-email@example.test"),
            ):
                with self.assertRaisesRegex(GoogleIdentityError, "No se pudo verificar la identidad de Google"):
                    verify_google_identity("sensitive-credential")

        logged = repr(warning.call_args)
        self.assertIn("category=%s exception=%s", logged)
        self.assertIn("key_fetch", logged)
        self.assertIn("PyJWKClientConnectionError", logged)
        self.assertNotIn("sensitive-credential", logged)
        self.assertNotIn("sensitive-token-and-email@example.test", logged)

    @patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-client-id"})
    def test_development_diagnostics_identify_claim_validation_without_details(self):
        import jwt

        app = Flask(__name__)
        app.config["APP_ENV"] = "development"
        with app.app_context(), patch.object(app.logger, "warning") as warning:
            with patch("api.google_identity._jwks.get_signing_key_from_jwt", return_value=SimpleNamespace(key="test-key")):
                with patch("api.google_identity.jwt.decode", side_effect=jwt.InvalidAudienceError("sensitive-audience")):
                    with self.assertRaisesRegex(GoogleIdentityError, "No se pudo verificar la identidad de Google"):
                        verify_google_identity("sensitive-credential")

        logged = repr(warning.call_args)
        self.assertIn("claims_validation", logged)
        self.assertIn("InvalidAudienceError", logged)
        self.assertNotIn("sensitive-credential", logged)
        self.assertNotIn("sensitive-audience", logged)

    @patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-client-id"})
    def test_production_does_not_log_google_verification_diagnostics(self):
        import jwt

        app = Flask(__name__)
        app.config["APP_ENV"] = "production"
        with app.app_context(), patch.object(app.logger, "warning") as warning:
            with patch("api.google_identity._jwks.get_signing_key_from_jwt", return_value=SimpleNamespace(key="test-key")):
                with patch("api.google_identity.jwt.decode", side_effect=jwt.InvalidAudienceError("sensitive-audience")):
                    with self.assertRaisesRegex(GoogleIdentityError, "No se pudo verificar la identidad de Google"):
                        verify_google_identity("sensitive-credential")
        warning.assert_not_called()

    @unittest.skipUnless(importlib.util.find_spec("cryptography"), "RSA test requires PyJWT[crypto]")
    @patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-client-id"})
    def test_real_rsa_verification_rejects_wrong_audience_expiry_and_signature(self):
        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        claims = {
            "iss": "https://accounts.google.com",
            "aud": "test-client-id",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "sub": "google-subject",
            "email": "user@example.test",
            "email_verified": True,
        }
        with patch("api.google_identity._jwks.get_signing_key_from_jwt", return_value=SimpleNamespace(key=private_key.public_key())):
            valid = jwt.encode(claims, private_key, algorithm="RS256")
            self.assertEqual(verify_google_identity(valid)["sub"], "google-subject")
            for overrides in (
                {"aud": "another-client"},
                {"exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
            ):
                with self.assertRaises(GoogleIdentityError):
                    verify_google_identity(jwt.encode({**claims, **overrides}, private_key, algorithm="RS256"))
            with self.assertRaises(GoogleIdentityError):
                verify_google_identity(jwt.encode(claims, other_key, algorithm="RS256"))

    @patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-client-id"})
    @patch("api.google_identity.jwt.decode")
    @patch("api.google_identity._jwks.get_signing_key_from_jwt")
    def test_verified_claims_and_restricted_algorithms(self, signing_key, decode):
        signing_key.return_value.key = "test-key"
        decode.return_value = {"sub": "subject", "email": "USER@example.test", "email_verified": True}
        self.assertEqual(verify_google_identity("test-id-token"), {"sub": "subject", "email": "user@example.test"})
        self.assertEqual(decode.call_args.kwargs["audience"], "test-client-id")
        self.assertEqual(decode.call_args.kwargs["algorithms"], ["RS256"])

    @patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-client-id"})
    @patch("api.google_identity.jwt.decode")
    @patch("api.google_identity._jwks.get_signing_key_from_jwt")
    def test_unverified_email_is_rejected(self, signing_key, decode):
        signing_key.return_value.key = "test-key"
        decode.return_value = {"sub": "subject", "email": "user@example.test", "email_verified": False}
        with self.assertRaises(GoogleIdentityError):
            verify_google_identity("test-id-token")

    @patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-client-id"})
    @patch("api.google_identity.jwt.decode")
    @patch("api.google_identity._jwks.get_signing_key_from_jwt")
    def test_wrong_audience_and_expired_token_are_rejected(self, signing_key, decode):
        import jwt
        signing_key.return_value.key = "test-key"
        for error in (jwt.InvalidAudienceError(), jwt.ExpiredSignatureError()):
            decode.side_effect = error
            with self.assertRaises(GoogleIdentityError):
                verify_google_identity("test-id-token")


if __name__ == "__main__":
    unittest.main()

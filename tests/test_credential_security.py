import unittest
from pathlib import Path
from unittest.mock import patch

import bcrypt
from flask_jwt_extended import decode_token
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from api.credential_security import (
    CredentialRateLimitUnavailable,
    register_credential_revocation,
    replace_password_if_version,
)
from api.jwt_utils import create_user_access_token
from api.models import ExternalIdentity, Users, db
from api.password_recovery_endpoints import auth_bp
from api.routes import api


class CredentialSecurityTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="credential-test-only",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            FRONTEND_URL="http://localhost:3002",
        )
        jwt_manager = JWTManager(self.app)
        db.init_app(self.app)
        register_credential_revocation(jwt_manager)
        self.app.register_blueprint(api, url_prefix="/api")
        self.app.register_blueprint(auth_bp, url_prefix="/api/auth")
        with self.app.app_context():
            db.create_all()
            user = Users(
                email="customer@example.test",
                password=bcrypt.hashpw(b"old-password", bcrypt.gensalt()).decode(),
                is_active=True,
                is_admin=False,
            )
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id
            self.legacy_token = create_access_token(
                identity=str(user.id), additional_claims={"email": user.email, "is_admin": False}
            )
            self.token = create_user_access_token(user)
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _auth(self, token=None):
        return {"Authorization": f"Bearer {token or self.token}"}

    def _change(self, current="old-password", new="new-password", token=None):
        return self.client.post(
            "/api/auth/change-password",
            json={"current_password": current, "new_password": new},
            headers=self._auth(token),
        )

    def test_legacy_token_valid_only_before_version_increment(self):
        self.assertEqual(self.client.get("/api/me", headers=self._auth(self.legacy_token)).status_code, 200)
        self.assertEqual(self._change().status_code, 200)
        self.assertEqual(self.client.get("/api/me", headers=self._auth(self.legacy_token)).status_code, 401)
        self.assertEqual(self.client.get("/api/me", headers=self._auth()).status_code, 401)

    def test_new_login_and_google_style_token_use_current_version(self):
        self.assertEqual(self._change().status_code, 200)
        self.assertEqual(self.client.post("/api/login", json={"email": "customer@example.test", "password": "old-password"}).status_code, 401)
        login = self.client.post("/api/login", json={"email": "customer@example.test", "password": "new-password"})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.get("/api/me", headers=self._auth(login.json["access_token"])).status_code, 200)

    def test_cart_and_checkout_require_current_credential_version(self):
        self.assertEqual(self.client.get("/api/cart", headers=self._auth()).status_code, 200)
        before = self.client.post("/api/checkout/quote", json={}, headers=self._auth())
        self.assertEqual(before.status_code, 200)
        self.assertEqual(self._change().status_code, 200)
        self.assertEqual(self.client.get("/api/cart", headers=self._auth()).status_code, 401)
        self.assertEqual(self.client.post("/api/checkout/quote", json={}, headers=self._auth()).status_code, 401)
        login = self.client.post("/api/login", json={"email": "customer@example.test", "password": "new-password"})
        self.assertEqual(self.client.get("/api/cart", headers=self._auth(login.json["access_token"])).status_code, 200)

    def test_successful_current_password_does_not_consume_failure_allowance(self):
        for _ in range(4):
            self.assertEqual(self._change(current="incorrect").status_code, 403)
        self.assertEqual(self._change(new="short").status_code, 400)
        self.assertEqual(self._change(current="incorrect").status_code, 403)
        self.assertEqual(self._change().status_code, 429)

    def test_google_login_remains_available_after_password_change(self):
        with self.app.app_context():
            db.session.add(ExternalIdentity(
                user_id=self.user_id, provider="google", provider_subject="linked-google-test"
            ))
            db.session.commit()
        self.assertEqual(self._change().status_code, 200)
        with patch("api.routes.verify_google_identity", return_value={
            "sub": "linked-google-test", "email": "customer@example.test"
        }):
            response = self.client.post("/api/auth/google", json={"credential": "mock"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/me", headers=self._auth(response.json["access_token"])).status_code, 200)
        self.assertEqual(self.client.get("/api/me", headers=self._auth()).status_code, 401)

    def test_wrong_current_password_and_length_validation(self):
        self.assertEqual(self._change(current="incorrect").status_code, 403)
        self.assertEqual(self._change(new="short").status_code, 400)
        self.assertEqual(self._change(new="a" * 73).status_code, 400)
        self.assertEqual(self._change(new="á" * 37).status_code, 400)
        self.assertEqual(self._change(new="a" * 8).status_code, 200)

    def test_missing_auth_and_google_only_account(self):
        self.assertEqual(self.client.post("/api/auth/change-password", json={}).status_code, 401)
        with self.app.app_context():
            user = db.session.get(Users, self.user_id)
            user.password = None
            db.session.commit()
        self.assertEqual(self._change().status_code, 403)

    def test_me_rejects_password_without_changing_profile(self):
        response = self.client.patch(
            "/api/me", json={"password": "bypass-password", "firstname": "Changed"}, headers=self._auth()
        )
        self.assertEqual(response.status_code, 400)
        with self.app.app_context():
            user = db.session.get(Users, self.user_id)
            self.assertTrue(bcrypt.checkpw(b"old-password", user.password.encode()))
            self.assertNotEqual(user.firstname, "Changed")

    def test_failed_attempt_limit_and_unavailable_store(self):
        for _ in range(5):
            self.assertEqual(self._change(current="incorrect").status_code, 403)
        self.assertEqual(self._change().status_code, 429)
        with patch("api.routes.reserve_password_attempt", side_effect=CredentialRateLimitUnavailable):
            self.assertEqual(self._change().status_code, 503)

    def test_reset_token_single_use_and_revokes_sessions(self):
        with self.app.app_context():
            reset_token = create_access_token(
                identity="customer@example.test",
                additional_claims={"purpose": "password_reset", "credential_version": 0},
            )
        self.assertEqual(self.client.get("/api/me", headers=self._auth(reset_token)).status_code, 401)
        payload = {"token": reset_token, "password": "reset-password"}
        self.assertEqual(self.client.post("/api/auth/reset-password", json=payload).status_code, 200)
        self.assertEqual(self.client.post("/api/auth/reset-password", json=payload).status_code, 400)
        self.assertEqual(self.client.get("/api/me", headers=self._auth()).status_code, 401)
        self.assertEqual(self.client.post("/api/login", json={"email": "customer@example.test", "password": "reset-password"}).status_code, 200)

    def test_legacy_reset_token_and_concurrent_version_guard(self):
        with self.app.app_context():
            token = create_access_token(
                identity="customer@example.test", additional_claims={"purpose": "password_reset"}
            )
        self.assertEqual(self.client.post("/api/auth/reset-password", json={"token": token, "password": "reset-password"}).status_code, 200)
        with self.app.app_context():
            user = db.session.get(Users, self.user_id)
            self.assertFalse(replace_password_if_version(user, "other-password", 0))
            self.assertEqual(db.session.get(Users, self.user_id).credential_version, 1)

    def test_reset_flow_email_uses_current_credential_version(self):
        with patch("api.password_recovery_endpoints.send_email") as send:
            response = self.client.post("/api/auth/forgot-password", json={"email": "customer@example.test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(send.call_count, 1)
        self.assertNotIn("customer@example.test", response.get_data(as_text=True))
        reset_link = send.call_args.args[2].split("/reset-password?token=")[1].split()[0]
        with self.app.app_context():
            claims = decode_token(reset_link)
        self.assertEqual(claims["credential_version"], 0)
        self.assertEqual(claims["purpose"], "password_reset")


class CredentialMigrationTest(unittest.TestCase):
    def test_additive_revision_is_after_google_identity(self):
        migration = Path(__file__).resolve().parents[1] / "src/migrations/versions/b4c5d6e7f8a9_add_user_credential_version.py"
        source = migration.read_text(encoding="utf-8")
        self.assertIn('down_revision = "c3d4e5f6a7b8"', source)
        self.assertIn('op.add_column(', source)
        self.assertIn('server_default="0"', source)

    def test_legacy_account_page_no_longer_submits_password(self):
        page = Path(__file__).resolve().parents[1] / "src/front/js/pages/AccountPage.jsx"
        source = page.read_text(encoding="utf-8")
        self.assertNotIn("setProfile({ ...profile, password:", source)
        self.assertNotIn("editPassword", source)
        self.assertIn("https://www.metalwolft.com/forgot-password", source)


if __name__ == "__main__":
    unittest.main()

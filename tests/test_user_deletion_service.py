import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flask import Flask
from api.models import db, Users, ExternalIdentity, Orders, Cart
from api.user_deletion_service import UserDeletionBlocked, delete_user_without_history
from api.routes import api
from datetime import timezone

with patch("zoneinfo.ZoneInfo", return_value=timezone.utc):
    from api.admin import UsersAdminView
from flask_jwt_extended import JWTManager
from api.jwt_utils import create_user_access_token


class UserDeletionTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", TESTING=True)
        db.init_app(self.app)
        self.app.config["JWT_SECRET_KEY"] = "test-only-secret"
        JWTManager(self.app)
        self.app.register_blueprint(api, url_prefix="/api")
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _user(self, email="test@example.test", password=None):
        user = Users(email=email, password=password, is_admin=False)
        db.session.add(user)
        db.session.commit()
        return user

    def test_google_account_and_auxiliary_rows_are_removed(self):
        user = self._user()
        user_id = user.id
        db.session.add(ExternalIdentity(user_id=user_id, provider="google", provider_subject="test-sub"))
        db.session.commit()
        delete_user_without_history(user)
        self.assertIsNone(db.session.get(Users, user_id))
        self.assertEqual(ExternalIdentity.query.count(), 0)

    def test_password_account_without_activity_is_removed(self):
        user = self._user(password="test-hash")
        user_id = user.id
        delete_user_without_history(user)
        self.assertIsNone(db.session.get(Users, user_id))

    def test_order_blocks_deletion_and_preserves_identity(self):
        user = self._user()
        db.session.add(ExternalIdentity(user_id=user.id, provider="google", provider_subject="test-sub"))
        db.session.add(Orders(user_id=user.id, total_amount=10, locator="TEST0001"))
        db.session.commit()
        with self.assertRaises(UserDeletionBlocked):
            delete_user_without_history(user)
        self.assertEqual(Users.query.count(), 1)
        self.assertEqual(ExternalIdentity.query.count(), 1)

    def test_error_rolls_back_auxiliary_deletions(self):
        user = self._user()
        db.session.add(ExternalIdentity(user_id=user.id, provider="google", provider_subject="test-sub"))
        db.session.commit()
        with patch.object(db.session, "commit", side_effect=RuntimeError("failure")):
            with self.assertRaises(RuntimeError):
                delete_user_without_history(user)
        self.assertEqual(Users.query.count(), 1)
        self.assertEqual(ExternalIdentity.query.count(), 1)

    def test_admin_view_uses_central_deletion(self):
        user = self._user()
        user_id = user.id
        view = UsersAdminView(Users, db.session)
        with self.app.test_request_context():
            self.assertTrue(view.delete_model(user))
        self.assertIsNone(db.session.get(Users, user_id))

    def test_admin_api_deletes_google_account_and_rejects_order_history(self):
        admin = Users(email="admin@example.test", password="test-hash", is_admin=True)
        db.session.add(admin)
        db.session.commit()
        token = create_user_access_token(admin)
        headers = {"Authorization": f"Bearer {token}"}
        user = self._user()
        user_id = user.id
        db.session.add(ExternalIdentity(user_id=user_id, provider="google", provider_subject="test-sub"))
        db.session.commit()
        response = self.app.test_client().delete(f"/api/users/{user_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ExternalIdentity.query.count(), 0)

        protected = self._user(email="protected@example.test")
        db.session.add(Orders(user_id=protected.id, total_amount=10, locator="TEST0002"))
        db.session.commit()
        response = self.app.test_client().delete(f"/api/users/{protected.id}", headers=headers)
        self.assertEqual(response.status_code, 409)
        self.assertIsNotNone(db.session.get(Users, protected.id))

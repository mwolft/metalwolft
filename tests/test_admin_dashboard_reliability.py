import base64
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flask import Flask

from api import admin as admin_module
from api.models import db


class DashboardReliabilityTest(unittest.TestCase):
    def setUp(self):
        self.original_credentials = (admin_module.ADMIN_USER, admin_module.ADMIN_PW)
        admin_module.ADMIN_USER = "admin-test"
        admin_module.ADMIN_PW = "secret-test"
        self.app = Flask(__name__, template_folder=str(ROOT / "src" / "templates"),
                         static_folder=str(ROOT / "src" / "static"))
        self.app.config.update(TESTING=True, SECRET_KEY="test",
                               SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
                               SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(self.app)
        admin_module.setup_admin(self.app)
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        admin_module.ADMIN_USER, admin_module.ADMIN_PW = self.original_credentials
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def auth(self, username="admin-test", password="secret-test"):
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    def test_basic_auth_requires_configured_credentials(self):
        self.assertEqual(self.client.get("/admin/").status_code, 401)
        self.assertEqual(self.client.get("/admin/", headers=self.auth(password="wrong")).status_code, 401)
        self.assertEqual(self.client.get("/admin/", headers=self.auth()).status_code, 200)
        for username, password in ((None, None), ("admin-test", None), (None, "secret-test"), ("", "secret-test")):
            with self.subTest(username=username, password_present=bool(password)):
                admin_module.ADMIN_USER, admin_module.ADMIN_PW = username, password
                self.assertEqual(self.client.get("/admin/").status_code, 401)
                self.assertEqual(self.client.get("/admin/orders/").status_code, 401)

    def test_unicode_credentials_compare_without_error(self):
        admin_module.ADMIN_USER = "administrador"
        admin_module.ADMIN_PW = "clave-segura-ñ"
        self.assertTrue(admin_module._admin_credentials_valid(
            {"username": "administrador", "password": "clave-segura-ñ"}))
        self.assertFalse(admin_module._admin_credentials_valid(
            {"username": "administrador", "password": "otra-clave"}))

    def test_invalid_year_uses_default_and_dashboard_renders(self):
        for year in ("bad", "10000", "-1", ""):
            with self.subTest(year=year):
                response = self.client.get(f"/admin/?year={year}", headers=self.auth())
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn("Importe de pedidos del mes", html)
                self.assertIn("Importes registrados, no necesariamente cobrados.", html)
                self.assertIn("PENDIENTES DE FABRICAR", html)
                self.assertNotIn("Facturación vs Punto Muerto", html)

    def test_month_windows_clamp_days_and_cross_year(self):
        current_start, current_end, previous_start, previous_end = admin_module._dashboard_month_windows(
            datetime(2026, 3, 31, 15, 20))
        self.assertEqual((current_start, current_end), (datetime(2026, 3, 1), datetime(2026, 3, 31, 15, 20)))
        self.assertEqual((previous_start, previous_end), (datetime(2026, 2, 1), datetime(2026, 2, 28, 15, 20)))
        _, _, previous_start, previous_end = admin_module._dashboard_month_windows(datetime(2026, 1, 31, 10))
        self.assertEqual((previous_start, previous_end), (datetime(2025, 12, 1), datetime(2025, 12, 31, 10)))
        _, _, _, previous_end = admin_module._dashboard_month_windows(datetime(2024, 3, 31, 10))
        self.assertEqual(previous_end, datetime(2024, 2, 29, 10))

    def test_madrid_time_respects_winter_summer_and_aware_input(self):
        self.assertEqual(admin_module._format_madrid_time(datetime(2026, 1, 10, 12)), "10/01 13:00")
        self.assertEqual(admin_module._format_madrid_time(datetime(2026, 7, 10, 12)), "10/07 14:00")


if __name__ == "__main__":
    unittest.main()

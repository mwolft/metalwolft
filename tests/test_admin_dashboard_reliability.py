import base64
import sys
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flask import Flask

from api import admin as admin_module
from api.models import Orders, db


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
                self.assertIn("Importe registrado", html)
                self.assertIn("No representa cobros ni facturación fiscal", html)
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

    def test_commercial_kpis_default_to_history_and_filter_without_changing_queue(self):
        today = datetime.now(timezone.utc).replace(tzinfo=None)
        with self.app.app_context():
            db.session.add_all([
                Orders(locator="DASH000001", order_date=today, total_amount=100, order_status="pendiente"),
                Orders(locator="DASH000002", order_date=today, total_amount=200, order_status="cancelado"),
                Orders(locator="DASH000003", order_date=datetime(2025, 1, 1), total_amount=900),
            ])
            db.session.commit()
        response = self.client.get("/admin/", headers=self.auth())
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("1200.00 €", html)
        self.assertIn("400.00 €", html)
        self.assertIn('class="mw-analytics__value">3</strong>', html)
        self.assertIn('<option value="all" selected>Histórico completo</option>', html)
        day = datetime.now(ZoneInfo("Europe/Madrid")).date().isoformat()
        filtered = self.client.get(f"/admin/?period=custom&date_from={day}&date_to={day}",
                                   headers=self.auth())
        self.assertEqual(filtered.status_code, 200)
        filtered_html = filtered.get_data(as_text=True)
        self.assertIn("300.00 €", filtered_html)
        self.assertIn("150.00 €", filtered_html)
        self.assertIn('class="mw-analytics__value">2</strong>', filtered_html)
        queue_start = '<div class="panel panel-primary admin-production-queue"'
        queue_end = '<section class="mw-analytics'
        self.assertEqual(html.split(queue_start, 1)[1].split(queue_end, 1)[0],
                         filtered_html.split(queue_start, 1)[1].split(queue_end, 1)[0])
        invalid = self.client.get("/admin/?period=custom&date_from=2026-03-20&date_to=2026-03-01",
                                  headers=self.auth())
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("PENDIENTES DE FABRICAR", invalid.get_data(as_text=True))
        combined = self.client.get(
            f"/admin/?year=2025&period=custom&date_from={day}&date_to={day}", headers=self.auth())
        combined_html = combined.get_data(as_text=True)
        self.assertEqual(combined.status_code, 200)
        self.assertIn('name="year" value="2025"', combined_html)
        self.assertIn('name="period" value="custom"', combined_html)
        self.assertIn('id="salesChart-2025"', combined_html)
        self.assertIn("300.00 €", combined_html)
        self.assertIn('href="/admin/manualorderdraft/"', html)
        self.assertIn('href="/admin/libro-aeat"', html)
        self.assertIn('href="/admin/supplierinvoice/upload-and-process/"', html)
        self.assertIn('href="/admin/manualinvoicedraft/new/"', html)
        self.assertIn('class="admin-dashboard__quick-heading">Ventas</h5>', html)
        self.assertIn('class="admin-dashboard__quick-heading">Facturación y contabilidad</h5>', html)
        for title in ("Pedidos manuales", "Libro AEAT", "Factura recibida", "Factura manual"):
            self.assertIn(f'class="admin-dashboard__link-title">{title}</span>', html)
        self.assertEqual(html.count('class="admin-dashboard__card admin-dashboard__link"'), 4)
        self.assertNotIn("Libro AEAT conjunto", html)
        self.assertNotIn("Nueva factura recibida", html)
        self.assertLess(html.index("PENDIENTES DE FABRICAR"), html.index("Actividad comercial"))
        self.assertLess(html.index("Actividad comercial"), html.index("Accesos rápidos"))
        self.assertLess(html.index("Actividad reciente"), html.index("Información general"))
        self.assertNotIn("Punto Muerto", html)


if __name__ == "__main__":
    unittest.main()

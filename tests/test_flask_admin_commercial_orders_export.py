import base64
import sys
import unittest
from datetime import datetime
from io import BytesIO
from pathlib import Path
from datetime import timezone
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flask import Flask
from flask_admin import Admin
from openpyxl import load_workbook

with patch("zoneinfo.ZoneInfo", return_value=timezone.utc):
    from api import admin as admin_module
from api.models import Orders, db


class CommercialOrdersExportHttpTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "test-admin"
        admin_module.ADMIN_PW = "test-password"
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / "src" / "templates"))
        self.app.config.update(SECRET_KEY="test", SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
                               SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(self.app)
        admin = Admin(self.app, url="/admin")
        admin.add_view(admin_module.OrderAdminView(Orders, db.session))
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()
        self.url = next(str(rule) for rule in self.app.url_map.iter_rules()
                        if rule.endpoint.endswith(".export_commercial"))
        credentials = base64.b64encode(b"test-admin:test-password").decode("ascii")
        self.auth = {"Authorization": f"Basic {credentials}"}

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_authentication_and_export(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        response = self.client.get(self.url, headers=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(load_workbook(BytesIO(response.data)).sheetnames, ["Pedidos", "Lineas", "Control"])
        list_url = next(str(rule) for rule in self.app.url_map.iter_rules()
                        if rule.endpoint.endswith(".index_view"))
        listing = self.client.get(list_url, headers=self.auth)
        self.assertEqual(listing.status_code, 200)
        self.assertIn(b"Exportar pedidos y lineas", listing.data)

    def test_date_filters_and_methods(self):
        self.assertEqual(self.client.get(self.url + "?date_from=2026-02-30", headers=self.auth).status_code, 400)
        self.assertEqual(self.client.get(self.url + "?date_from=2026-02-02&date_to=2026-02-01",
                                         headers=self.auth).status_code, 400)
        self.assertEqual(self.client.get(self.url + "?date_from=2026-02-01&date_to=2026-02-28",
                                         headers=self.auth).status_code, 200)
        self.assertEqual(self.client.post(self.url, headers=self.auth).status_code, 405)

    def test_date_filter_includes_only_matching_orders(self):
        with self.app.app_context():
            db.session.add_all([
                Orders(locator="TEST000001", order_date=datetime(2026, 2, 10), total_amount=10),
                Orders(locator="TEST000002", order_date=datetime(2026, 3, 10), total_amount=20),
            ])
            db.session.commit()
        response = self.client.get(self.url + "?date_from=2026-02-01&date_to=2026-02-28",
                                   headers=self.auth)
        self.assertEqual(response.status_code, 200)
        rows = list(load_workbook(BytesIO(response.data))["Pedidos"].values)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][9], 10)


if __name__ == "__main__":
    unittest.main()

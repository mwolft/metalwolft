import base64
import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flask import Flask
from openpyxl import load_workbook
from sqlalchemy import event

from api import admin as admin_module
from api.commercial_analytics_service import commercial_indicators, resolve_commercial_period
from api.commercial_orders_export_service import build_workbook
from api.models import Categories, OrderDetails, Orders, Products, db


class CommercialPeriodTest(unittest.TestCase):
    def test_madrid_boundaries_and_dst(self):
        now = datetime(2026, 7, 10, 10, tzinfo=timezone.utc)
        month = resolve_commercial_period("month", now=now)
        self.assertEqual(month.start_utc, datetime(2026, 6, 30, 22))
        self.assertEqual(month.end_utc, datetime(2026, 7, 10, 10))
        year = resolve_commercial_period("year", now=now)
        self.assertEqual(year.start_utc, datetime(2025, 12, 31, 23))
        previous = resolve_commercial_period("previous_year", now=now)
        self.assertEqual(previous.start_utc, datetime(2024, 12, 31, 23))
        self.assertEqual(previous.end_utc, datetime(2025, 12, 31, 23))
        custom = resolve_commercial_period("custom", "2026-03-28", "2026-03-29")
        self.assertEqual(custom.start_utc, datetime(2026, 3, 27, 23))
        self.assertEqual(custom.end_utc, datetime(2026, 3, 29, 22))
        autumn = resolve_commercial_period("custom", "2026-10-25", "2026-10-25")
        self.assertEqual(autumn.start_utc, datetime(2026, 10, 24, 22))
        self.assertEqual(autumn.end_utc, datetime(2026, 10, 25, 23))
        self.assertIsNone(resolve_commercial_period("all").start_utc)

    def test_invalid_periods(self):
        for kind, start, end in (
            ("unknown", None, None), ("custom", None, None),
            ("custom", "2026-02-30", "2026-03-01"),
            ("custom", "2026-03-10", "2026-03-01"),
            ("custom", "2026-03-01", "9999-12-31"),
        ):
            with self.subTest(kind=kind, start=start, end=end), self.assertRaises(ValueError):
                resolve_commercial_period(kind, start, end)


class CommercialAnalyticsHttpTest(unittest.TestCase):
    def setUp(self):
        self.original_credentials = (admin_module.ADMIN_USER, admin_module.ADMIN_PW)
        admin_module.ADMIN_USER = "analytics-admin"
        admin_module.ADMIN_PW = "analytics-password"
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
        encoded = base64.b64encode(b"analytics-admin:analytics-password").decode()
        self.auth = {"Authorization": f"Basic {encoded}"}
        self.url = "/admin/commercialanalytics/"

    def tearDown(self):
        admin_module.ADMIN_USER, admin_module.ADMIN_PW = self.original_credentials
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_menu_auth_empty_and_invalid_ranges(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.assertEqual(self.client.get(self.url, headers={"Authorization": "Basic YmFkOmJhZA=="}).status_code, 401)
        response = self.client.get(self.url, headers=self.auth)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Analítica comercial", html)
        self.assertIn("No hay pedidos registrados", html)
        self.assertIn('<option value="all" selected>Histórico completo</option>', html)
        menu = self.client.get("/admin/", headers=self.auth).get_data(as_text=True)
        self.assertNotIn(self.url, menu)
        self.assertIsNone(self.app.extensions["admin"][0].get_category_menu_item("Resumen"))
        self.assertEqual(self.client.get(self.url + "?period=custom&date_from=2026-03-20&date_to=2026-03-01",
                                         headers=self.auth).status_code, 400)
        self.assertEqual(self.client.get(self.url + "?period=invalid", headers=self.auth).status_code, 400)
        admin_module.ADMIN_PW = None
        self.assertEqual(self.client.get(self.url, headers=self.auth).status_code, 401)

    def test_aggregates_multiline_physical_units_and_matches_excel(self):
        with self.app.app_context():
            category = Categories(nombre="Prueba", slug="prueba")
            db.session.add(category)
            db.session.flush()
            product = Products(slug="producto-prueba", nombre="Producto prueba", descripcion="Prueba",
                               precio=25, categoria_id=category.id)
            db.session.add(product)
            db.session.flush()
            first = Orders(locator="ANALYTIC01", order_date=datetime(2026, 6, 30, 22, 30),
                           total_amount=100, discount_value=0, shipping_cost=0, order_status="cancelado")
            second = Orders(locator="ANALYTIC02", order_date=datetime(2026, 7, 5, 10),
                            total_amount=50, discount_value=0, shipping_cost=0)
            outside = Orders(locator="ANALYTIC03", order_date=datetime(2026, 6, 30, 21), total_amount=900)
            db.session.add_all([first, second, outside])
            db.session.flush()
            db.session.add_all([
                OrderDetails(order_id=first.id, product_id=product.id, quantity=2, precio_total=25,
                             line_type="physical"),
                OrderDetails(order_id=first.id, product_id=product.id, quantity=3, precio_total=10,
                             line_type="physical"),
                OrderDetails(order_id=first.id, product_id=product.id, quantity=1, precio_total=20,
                             line_type="design_service"),
                OrderDetails(order_id=second.id, product_id=product.id, quantity=1, precio_total=50,
                             line_type="physical"),
            ])
            db.session.commit()
            period = resolve_commercial_period("month", now=datetime(2026, 7, 10, 10, tzinfo=timezone.utc))
            statements = []

            def record_query(connection, cursor, statement, parameters, context, executemany):
                statements.append(statement)

            event.listen(db.engine, "before_cursor_execute", record_query)
            try:
                indicators = commercial_indicators(db.session, period)
            finally:
                event.remove(db.engine, "before_cursor_execute", record_query)
            self.assertEqual(len(statements), 2)
            self.assertEqual(indicators, {"orders": 2, "amount": Decimal("150.00"),
                                          "ticket": Decimal("75.00"), "physical_units": 6})
            exported = build_workbook([first, second])
            rows = list(load_workbook(BytesIO(exported.getvalue()), data_only=True)["Pedidos"].values)[1:]
            self.assertEqual(sum(Decimal(str(row[9])) for row in rows), indicators["amount"])
            self.assertEqual(len(rows), indicators["orders"])
            self.assertEqual(commercial_indicators(db.session, resolve_commercial_period(
                "custom", "2026-08-01", "2026-08-31"))["orders"], 0)
        page = self.client.get(self.url + "?period=custom&date_from=2026-07-01&date_to=2026-07-31",
                               headers=self.auth)
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn("150.00 €", html)
        self.assertIn("75.00 €", html)
        self.assertIn('class="mw-analytics__value">6</strong>', html)
        historical = self.client.get(self.url, headers=self.auth)
        self.assertEqual(historical.status_code, 200)
        self.assertIn("1050.00 €", historical.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()

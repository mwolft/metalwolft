import base64
import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from flask import Flask
from sqlalchemy import event

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from api import admin as admin_module
from api.commercial_analytics_service import (
    commercial_indicators, ranked_physical_models, resolve_ranking_period,
)
from api.models import Categories, OrderDetails, Orders, Products, db


class CommercialModelRankingTest(unittest.TestCase):
    def setUp(self):
        self.original_credentials = (admin_module.ADMIN_USER, admin_module.ADMIN_PW)
        admin_module.ADMIN_USER, admin_module.ADMIN_PW = "ranking-admin", "ranking-secret"
        self.app = Flask(__name__, template_folder=str(ROOT / "src" / "templates"),
                         static_folder=str(ROOT / "src" / "static"))
        self.app.config.update(TESTING=True, SECRET_KEY="test",
                               SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
                               SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(self.app)
        admin_module.setup_admin(self.app)
        with self.app.app_context():
            db.create_all()
            category = Categories(nombre="Prueba", slug="ranking-prueba")
            db.session.add(category)
            db.session.flush()
            first = Products(nombre="Modelo actual A", slug="ranking-a", descripcion="Prueba",
                             precio=10, categoria_id=category.id)
            second = Products(nombre="Modelo actual B", slug="ranking-b", descripcion="Prueba",
                              precio=10, categoria_id=category.id)
            db.session.add_all([first, second])
            db.session.flush()
            year = datetime.now(timezone.utc).year
            current = Orders(locator="RANK001", order_date=datetime(year, 2, 1, 12), total_amount=999)
            another = Orders(locator="RANK002", order_date=datetime(year, 3, 1, 12), total_amount=50)
            previous = Orders(locator="RANK003", order_date=datetime(year - 1, 12, 31, 23), total_amount=40)
            db.session.add_all([current, another, previous])
            db.session.flush()
            db.session.add_all([
                OrderDetails(order_id=current.id, product_id=first.id, quantity=2,
                             precio_total=10, line_type="physical"),
                OrderDetails(order_id=current.id, product_id=first.id, quantity=3,
                             precio_total=10, line_type="physical"),
                OrderDetails(order_id=current.id, product_id=second.id, quantity=1,
                             precio_total=100, line_type="physical"),
                OrderDetails(order_id=current.id, product_id=second.id, quantity=20,
                             precio_total=100, line_type="design_service"),
                OrderDetails(order_id=another.id, product_id=first.id, quantity=1,
                             precio_total=10, line_type="physical"),
                OrderDetails(order_id=previous.id, product_id=second.id, quantity=4,
                             precio_total=5, line_type="physical"),
            ])
            db.session.commit()
            self.first_id, self.second_id, self.year = first.id, second.id, year
        encoded = base64.b64encode(b"ranking-admin:ranking-secret").decode()
        self.auth = {"Authorization": f"Basic {encoded}"}
        self.client = self.app.test_client()

    def tearDown(self):
        admin_module.ADMIN_USER, admin_module.ADMIN_PW = self.original_credentials
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_aggregation_and_kpi_reconciliation(self):
        with self.app.app_context():
            period = resolve_ranking_period("all", [self.year])
            statements = []

            def record(connection, cursor, statement, parameters, context, executemany):
                statements.append(statement)

            event.listen(db.engine, "before_cursor_execute", record)
            try:
                ranking = ranked_physical_models(db.session, period)
            finally:
                event.remove(db.engine, "before_cursor_execute", record)
            self.assertEqual(len(statements), 2)
            self.assertEqual(ranking["total_units"], commercial_indicators(db.session, period)["physical_units"])
            self.assertEqual([row["product_id"] for row in ranking["rows"]],
                             [self.first_id, self.second_id])
            first, second = ranking["rows"]
            self.assertEqual((first["units"], first["orders"], first["amount"]), (6, 2, 60))
            self.assertEqual((second["units"], second["orders"], second["amount"]), (5, 2, 120))
            self.assertEqual(ranked_physical_models(db.session, period, "amount")["rows"][0]["product_id"],
                             self.second_id)
            limited = ranked_physical_models(db.session, period, limit=1)
            self.assertEqual(len(limited["rows"]), 1)
            self.assertEqual(limited["total_units"], 11)

    def test_madrid_year_boundary_empty_and_invalid_filters(self):
        with self.app.app_context():
            this_year = resolve_ranking_period("year", [self.year])
            ranking = ranked_physical_models(db.session, this_year)
            self.assertEqual(ranking["total_units"], 11)
            self.assertEqual(ranking["rows"][1]["orders"], 2)
            previous = resolve_ranking_period("previous_year", [self.year])
            self.assertEqual(ranked_physical_models(db.session, previous)["total_units"], 0)
            older = resolve_ranking_period(f"year:{self.year - 2}", [self.year - 2])
            self.assertEqual(ranked_physical_models(db.session, older)["rows"], [])
            for choice in ("invalid", "year:9999", "year:2025x"):
                with self.assertRaises(ValueError):
                    resolve_ranking_period(choice, [self.year])
            with self.assertRaises(ValueError):
                ranked_physical_models(db.session, this_year, "unknown")

    def test_unit_rounding_matches_excel_and_missing_catalog_name_keeps_id(self):
        with self.app.app_context():
            order = Orders(locator="RANK004", order_date=datetime(self.year, 4, 1, 12), total_amount=0)
            db.session.add(order)
            db.session.flush()
            db.session.add_all([
                OrderDetails(order_id=order.id, product_id=self.first_id, quantity=2,
                             precio_total=10.005, line_type="physical"),
                OrderDetails(order_id=order.id, product_id=99999, quantity=1,
                             precio_total=1, line_type="physical"),
            ])
            db.session.commit()
            rows = ranked_physical_models(db.session, resolve_ranking_period("all", [self.year]))["rows"]
            first = next(row for row in rows if row["product_id"] == self.first_id)
            missing = next(row for row in rows if row["product_id"] == 99999)
            self.assertEqual(first["amount"], Decimal("80.02"))
            self.assertIsNone(missing["current_name"])
            html = self.client.get("/admin/", headers=self.auth).get_data(as_text=True)
            self.assertIn("Producto sin nombre actual", html)
            self.assertIn("ID 99999", html)

    def test_admin_auth_default_sort_and_status(self):
        self.assertEqual(self.client.get("/admin/").status_code, 401)
        html = self.client.get("/admin/", headers=self.auth).get_data(as_text=True)
        self.assertIn("Modelos más vendidos", html)
        self.assertIn('value="all" selected', html)
        self.assertIn("nombre actual del catálogo", html)
        self.assertIn("Total del periodo: 11 rejas físicas", html)
        self.assertLess(html.index("Evolución comercial"), html.index("Modelos más vendidos"))
        self.assertLess(html.index("Modelos más vendidos"), html.index("Actividad reciente"))
        self.assertEqual(self.client.get("/admin/?rank_period=invalid", headers=self.auth).status_code, 400)
        self.assertEqual(self.client.get("/admin/?rank_sort=invalid", headers=self.auth).status_code, 400)


if __name__ == "__main__":
    unittest.main()

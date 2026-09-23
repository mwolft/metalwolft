import base64
import importlib.util
import json
import sys
import unittest
from datetime import datetime
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_DEPS = all(
    has_package(package)
    for package in ("alembic", "flask", "flask_admin", "flask_sqlalchemy", "sqlalchemy", "slugify")
)

if HAS_DEPS:
    from alembic.config import Config
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from alembic.script import ScriptDirectory
    from flask import Flask
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import configure_mappers

    import api.admin as admin_module
    from api.models import GoogleAdsMonthlySpend, Orders, db


class SalesCanvasParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.attributes = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "canvas" and values.get("id", "").startswith("salesChart-"):
            self.attributes = values


@unittest.skipUnless(HAS_DEPS, "Flask-Admin test dependencies are not installed.")
class GoogleAdsMonthlySpendTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"
        configure_mappers()
        self.app = Flask(
            __name__,
            template_folder=str(SRC_DIR / "templates"),
            static_folder=str(SRC_DIR / "static"),
        )
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="google-ads-test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        admin_module.setup_admin(self.app)
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()
        self.auth = {
            "Authorization": f"Basic {base64.b64encode(b'admin:secret').decode('ascii')}"
        }

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _canvas_data(self, year):
        response = self.client.get(f"/admin/?year={year}", headers=self.auth)
        self.assertEqual(response.status_code, 200)
        parser = SalesCanvasParser()
        parser.feed(response.get_data(as_text=True))
        self.assertIsNotNone(parser.attributes)
        return {
            key: json.loads(parser.attributes[f"data-{key}"])
            for key in ("labels", "values", "ads-values")
        }

    def test_database_constraints_allow_zero_and_reject_duplicate_month_invalid_month_and_negative_amount(self):
        with self.app.app_context():
            db.session.add(GoogleAdsMonthlySpend(year=2026, month=1, amount=Decimal("0.00")))
            db.session.commit()
            self.assertEqual(GoogleAdsMonthlySpend.query.one().amount, Decimal("0.00"))

            invalid_records = (
                GoogleAdsMonthlySpend(year=2026, month=1, amount=Decimal("5.00")),
                GoogleAdsMonthlySpend(year=2026, month=0, amount=Decimal("5.00")),
                GoogleAdsMonthlySpend(year=2026, month=13, amount=Decimal("5.00")),
                GoogleAdsMonthlySpend(year=2026, month=2, amount=Decimal("-0.01")),
            )
            for record in invalid_records:
                with self.subTest(month=record.month, amount=record.amount):
                    db.session.add(record)
                    with self.assertRaises(IntegrityError):
                        db.session.flush()
                    db.session.rollback()
            self.assertEqual(GoogleAdsMonthlySpend.query.count(), 1)

    def test_dashboard_keeps_sales_and_distinguishes_missing_month_from_zero(self):
        with self.app.app_context():
            db.session.add_all(
                [
                    GoogleAdsMonthlySpend(year=2026, month=1, amount=Decimal("0.00")),
                    GoogleAdsMonthlySpend(year=2026, month=3, amount=Decimal("120.50")),
                    GoogleAdsMonthlySpend(year=2025, month=1, amount=Decimal("35.25")),
                    Orders(locator="GA2026A", order_date=datetime(2026, 1, 12), total_amount=100.0),
                    Orders(locator="GA2026B", order_date=datetime(2026, 2, 12), total_amount=250.0),
                    Orders(locator="GA2025A", order_date=datetime(2025, 1, 12), total_amount=40.0),
                ]
            )
            db.session.commit()

        current = self._canvas_data(2026)
        self.assertEqual(len(current["labels"]), 12)
        self.assertEqual(current["values"], [100.0, 250.0] + [0] * 10)
        self.assertEqual(current["ads-values"], [0.0, None, 120.5] + [None] * 9)

        previous = self._canvas_data(2025)
        self.assertEqual(previous["values"], [40.0] + [0] * 11)
        self.assertEqual(previous["ads-values"], [35.25] + [None] * 11)

    def test_admin_view_is_protected_and_can_create_edit_and_delete(self):
        url = "/admin/googleadsmonthlyspend/"
        self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.client.get(url, headers=self.auth).status_code, 200)

        created = self.client.post(
            f"{url}new/",
            headers=self.auth,
            data={"year": "2026", "month": "9", "amount": "123.45", "note": "Factura revisada"},
        )
        self.assertEqual(created.status_code, 302)
        with self.app.app_context():
            record = GoogleAdsMonthlySpend.query.one()
            record_id = record.id
            self.assertEqual(record.amount, Decimal("123.45"))

        edited = self.client.post(
            f"{url}edit/?id={record_id}",
            headers=self.auth,
            data={"year": "2026", "month": "9", "amount": "0.00", "note": "Sin gasto"},
        )
        self.assertEqual(edited.status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.get(GoogleAdsMonthlySpend, record_id).amount, Decimal("0.00"))

        deleted = self.client.post(f"{url}delete/", headers=self.auth, data={"id": str(record_id)})
        self.assertEqual(deleted.status_code, 302)
        with self.app.app_context():
            self.assertIsNone(db.session.get(GoogleAdsMonthlySpend, record_id))

    def test_admin_list_orders_year_and_month_descending(self):
        with self.app.app_context():
            db.session.add_all(
                [
                    GoogleAdsMonthlySpend(year=2025, month=12, amount=Decimal("1.00"), note="Registro anterior"),
                    GoogleAdsMonthlySpend(year=2026, month=1, amount=Decimal("2.00"), note="Registro enero"),
                    GoogleAdsMonthlySpend(year=2026, month=9, amount=Decimal("3.00"), note="Registro septiembre"),
                ]
            )
            db.session.commit()

        response = self.client.get("/admin/googleadsmonthlyspend/", headers=self.auth)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertLess(html.index("Registro septiembre"), html.index("Registro enero"))
        self.assertLess(html.index("Registro enero"), html.index("Registro anterior"))

    def test_admin_form_rejects_out_of_range_month_and_negative_amount(self):
        url = "/admin/googleadsmonthlyspend/new/"
        for month, amount in (("13", "10.00"), ("1", "-0.01")):
            with self.subTest(month=month, amount=amount):
                response = self.client.post(
                    url,
                    headers=self.auth,
                    data={"year": "2026", "month": month, "amount": amount},
                )
                self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertEqual(GoogleAdsMonthlySpend.query.count(), 0)

    def test_migration_creates_the_same_database_constraints_and_one_head(self):
        config = Config(str(SRC_DIR / "migrations" / "alembic.ini"))
        config.set_main_option("script_location", str(SRC_DIR / "migrations"))
        script = ScriptDirectory.from_config(config)
        heads = script.get_revisions("heads")
        self.assertEqual(len(heads), 1)
        self.assertEqual(heads[0].revision, "e2f3a4b5c6d7")
        self.assertEqual(heads[0].down_revision, "d1e2f3a4b5c6")

        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            operations = Operations(context)
            migration = script.get_revision("e2f3a4b5c6d7").module
            original_op = migration.op
            try:
                migration.op = operations
                migration.upgrade()
                inspector = inspect(connection)
                columns = {column["name"]: column for column in inspector.get_columns("google_ads_monthly_spend")}
                self.assertEqual(columns["amount"]["type"].as_generic().__class__.__name__, "Numeric")
                self.assertFalse(columns["amount"]["nullable"])
                self.assertEqual(
                    {tuple(item["column_names"]) for item in inspector.get_unique_constraints("google_ads_monthly_spend")},
                    {("year", "month")},
                )
                migration.downgrade()
                self.assertNotIn("google_ads_monthly_spend", inspect(connection).get_table_names())
            finally:
                migration.op = original_op


if __name__ == "__main__":
    unittest.main()

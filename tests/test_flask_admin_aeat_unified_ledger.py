import base64
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_FLASK_ADMIN_DEPS = all(
    has_package(package)
    for package in ("flask", "flask_admin", "flask_sqlalchemy", "sqlalchemy", "slugify")
)

if HAS_FLASK_ADMIN_DEPS:
    from flask import Flask, Response  # noqa: E402
    from flask_admin import Admin  # noqa: E402

    import api.admin as admin_module  # noqa: E402
    from api.aeat_unified_ledger_service import (  # noqa: E402
        AeatUnifiedLedgerExportResult,
        AeatUnifiedLedgerValidationError,
    )
    from api.models import db  # noqa: E402


@unittest.skipUnless(HAS_FLASK_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminAeatUnifiedLedgerTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"
        self.app = Flask(__name__, template_folder=str(SRC_DIR / "templates"))
        self.app.config.update(
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            ACCOUNTING_EXPORT_FOLDER="/safe/accounting",
        )
        db.init_app(self.app)
        self.admin = Admin(
            self.app,
            url="/admin",
            index_view=admin_module.SecureAdminIndexView(),
        )
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()
        self.rule = next(
            rule for rule in self.app.url_map.iter_rules()
            if rule.endpoint.endswith(".unified_aeat_ledger")
        )

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def auth_header(self):
        token = base64.b64encode(b"admin:secret").decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def flashes(self):
        with self.client.session_transaction() as session:
            return session.get("_flashes", [])

    def test_form_and_dashboard_expose_global_year_period_download(self):
        form = self.client.get(self.rule.rule, headers=self.auth_header())
        dashboard = self.client.get("/admin/", headers=self.auth_header())

        self.assertEqual(form.status_code, 200)
        self.assertIn(b'name="year"', form.data)
        self.assertIn(b'name="period"', form.data)
        for period in (b"1T", b"2T", b"3T", b"4T"):
            self.assertIn(period, form.data)
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn(b"DESCARGAR LIBRO AEAT", dashboard.data)
        self.assertIn(self.rule.rule.encode(), dashboard.data)

    def test_post_generates_and_downloads_expected_filename_without_committing(self):
        result = AeatUnifiedLedgerExportResult(
            output_path="/safe/accounting/metalwolft_aeat_2026_2T.xlsx",
            filename="metalwolft_aeat_2026_2T.xlsx",
            sales_row_count=1,
            received_invoice_count=1,
            received_row_count=1,
            generated_at=datetime.now(timezone.utc),
            file_size=1234,
        )
        with (
            patch("api.admin.export_aeat_unified_ledger", return_value=result) as exporter,
            patch("api.admin.send_file", return_value=Response(b"xlsx")) as send_file,
            patch("api.admin.db.session.commit") as commit,
        ):
            response = self.client.post(
                self.rule.rule,
                headers=self.auth_header(),
                data={"year": "2026", "period": "2T"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(exporter.call_args.kwargs["year"], 2026)
        self.assertEqual(exporter.call_args.kwargs["period"], "2T")
        self.assertTrue(exporter.call_args.kwargs["output_path"].endswith("metalwolft_aeat_2026_2T.xlsx"))
        self.assertEqual(send_file.call_args.kwargs["download_name"], "metalwolft_aeat_2026_2T.xlsx")
        commit.assert_not_called()

    def test_domain_error_is_shown_without_internal_traceback(self):
        with patch(
            "api.admin.export_aeat_unified_ledger",
            side_effect=AeatUnifiedLedgerValidationError(
                "La factura rectificativa R2026000001 es histórica y requiere clasificación AEAT manual R1/R4 antes de exportar."
            ),
        ):
            response = self.client.post(
                self.rule.rule,
                headers=self.auth_header(),
                data={"year": "2026", "period": "2T"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("requiere clasificación AEAT manual", self.flashes()[0][1])


if __name__ == "__main__":
    unittest.main()

import base64
import copy
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ADMIN_PATH = SRC_DIR / "api" / "admin.py"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def source():
    return ADMIN_PATH.read_text(encoding="utf-8")


def function_source(function_name):
    text = source()
    start = text.index(f"def {function_name}")
    next_function = text.find("\ndef ", start + 1)
    next_class = text.find("\nclass ", start + 1)
    next_marker = text.find("\n# ==========================", start + 1)
    endings = [position for position in (next_function, next_class, next_marker) if position != -1]
    return text[start:min(endings)] if endings else text[start:]


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
    from api.accounting_excel_service import AccountingExcelExportResult  # noqa: E402
    from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash  # noqa: E402
    from api.models import AccountingEntry, Invoices, db  # noqa: E402


class FlaskAdminInvoiceAccountingSourceTest(unittest.TestCase):
    def test_admin_imports_accounting_services_without_excel_logic_inline(self):
        admin_source = source()

        self.assertIn("AccountingEntry", admin_source)
        self.assertIn("create_accounting_entry", admin_source)
        self.assertIn("export_sales_accounting_entries", admin_source)
        self.assertNotIn("Workbook(", admin_source)
        self.assertNotIn("openpyxl", admin_source)

    def test_record_route_is_post_only_and_rejects_browser_data(self):
        admin_source = source()
        route_source = function_source("record_accounting")

        self.assertIn("@expose('/record-accounting/<int:invoice_id>', methods=['POST'])", admin_source)
        self.assertIn("request.args", route_source)
        self.assertIn("request.form", route_source)
        self.assertIn("request.get_json(silent=True)", route_source)
        self.assertIn("Esta acción no acepta datos contables desde el navegador.", route_source)

    def test_record_route_delegates_to_domain_service_and_controls_transaction(self):
        route_source = function_source("record_accounting")

        self.assertIn("self.session.get(Invoices, invoice_id)", route_source)
        self.assertIn("create_accounting_entry(invoice, db_session=self.session)", route_source)
        self.assertIn("self.session.commit()", route_source)
        self.assertIn("self.session.rollback()", route_source)
        self.assertNotIn("AccountingEntry(", route_source)
        self.assertNotIn("invoice.invoice_number =", route_source)
        self.assertNotIn("invoice.invoice_snapshot =", route_source)
        self.assertNotIn("generate_invoice_pdf(", route_source)
        self.assertNotIn("send_invoice_email", route_source)
        self.assertNotIn("create_pending_submission", route_source)

    def test_export_route_uses_only_accounting_entries_and_does_not_commit(self):
        route_source = function_source("export_accounting")

        self.assertIn("@expose('/export-accounting')", source())
        self.assertIn("self.session.query(AccountingEntry)", route_source)
        self.assertIn("filter_by(entry_type=AccountingEntry.ENTRY_TYPE_SALE)", route_source)
        self.assertIn("AccountingEntry.invoice_date.asc()", route_source)
        self.assertIn("AccountingEntry.invoice_number.asc()", route_source)
        self.assertIn("AccountingEntry.id.asc()", route_source)
        self.assertIn("export_sales_accounting_entries(entries, output_path=output_path, overwrite=True)", route_source)
        self.assertIn("send_file(", route_source)

        for forbidden in (
            "Invoices.query",
            "Orders.query",
            "Users.query",
            "CheckoutSessions.query",
            "invoice_snapshot",
            "db.session.commit",
            "db.session.rollback",
        ):
            self.assertNotIn(forbidden, route_source)


SNAPSHOT = {
    "schema_version": 1,
    "issuer": {"legal_name": "MetalWolft"},
    "customer": {
        "legal_name": "Cliente Test",
        "tax_id": "00000000T",
    },
    "operation": {
        "invoice_type": "ordinary",
        "currency": "EUR",
        "issue_date": "2026-07-18",
        "order_id": 42,
    },
    "payment": {"provider": "stripe"},
    "lines": [{"line_number": 1, "description": "Reja", "quantity": "1"}],
    "totals": {
        "tax_base": "100.00",
        "tax_amount": "21.00",
        "total_amount": "121.00",
    },
}


@unittest.skipUnless(HAS_FLASK_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminInvoiceAccountingHttpTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"

        self.app = Flask(__name__)
        self.app.config.update(
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            ACCOUNTING_EXPORT_FOLDER="/safe/accounting",
        )
        db.init_app(self.app)

        admin = Admin(self.app, url="/admin")
        admin.add_view(admin_module.InvoiceAdminView(Invoices, db.session))

        with self.app.app_context():
            db.create_all()
            self.invoice = Invoices(
                invoice_number="F-2026-000001",
                order_id=42,
                invoice_type="ordinary",
                pdf_path=None,
                amount=121.00,
                client_name="Cliente Test",
                client_address="Calle Test 1",
                client_cif="00000000T",
                order_details=[],
                invoice_snapshot=copy.deepcopy(SNAPSHOT),
                invoice_snapshot_hash=calculate_invoice_snapshot_hash(SNAPSHOT),
                invoice_snapshot_schema_version=1,
                issued_at=datetime(2026, 7, 18, 10, 0, 0),
            )
            db.session.add(self.invoice)
            db.session.commit()
            self.invoice_id = self.invoice.id

        self.client = self.app.test_client()
        self.record_rule = self._rule(".record_accounting")
        self.export_rule = self._rule(".export_accounting")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _rule(self, endpoint_suffix):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(endpoint_suffix):
                return rule
        raise AssertionError(f"Flask Admin route {endpoint_suffix} was not registered")

    def _record_url(self, invoice_id):
        return self.record_rule.rule.replace("<int:invoice_id>", str(invoice_id))

    def _export_url(self):
        return self.export_rule.rule

    def _auth_header(self, username="admin", password="secret"):
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _flashes(self):
        with self.client.session_transaction() as session:
            return session.get("_flashes", [])

    def test_record_accounting_requires_basic_auth(self):
        with patch("api.admin.create_accounting_entry") as creator:
            response = self.client.post(self._record_url(self.invoice_id))

        self.assertEqual(response.status_code, 401)
        creator.assert_not_called()

    def test_record_accounting_rejects_browser_accounting_payload(self):
        response = self.client.post(
            self._record_url(self.invoice_id),
            headers=self._auth_header(),
            json={"tax_base": "0.01", "total_amount": "0.01"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            ("error", "Esta acción no acepta datos contables desde el navegador."),
            self._flashes(),
        )
        with self.app.app_context():
            self.assertEqual(db.session.query(AccountingEntry).count(), 0)

    def test_record_accounting_creates_entry_and_second_call_is_idempotent(self):
        first = self.client.post(
            self._record_url(self.invoice_id),
            headers=self._auth_header(),
        )
        second = self.client.post(
            self._record_url(self.invoice_id),
            headers=self._auth_header(),
        )

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        with self.app.app_context():
            entries = db.session.query(AccountingEntry).all()
            self.assertEqual(len(entries), 1)
            entry = entries[0]
            self.assertEqual(entry.invoice_id, self.invoice_id)
            self.assertEqual(entry.entry_type, AccountingEntry.ENTRY_TYPE_SALE)
            self.assertEqual(entry.invoice_number, "F-2026-000001")
            self.assertEqual(str(entry.taxable_base), "100.00")
            self.assertEqual(str(entry.vat_amount), "21.00")
            self.assertEqual(str(entry.total_amount), "121.00")

        flashes = self._flashes()
        self.assertIn(("success", "Registro contable creado correctamente."), flashes)
        self.assertIn(("success", "La factura ya tenía registro contable."), flashes)

    def test_export_without_entries_redirects_with_safe_message(self):
        with (
            patch("api.admin.export_sales_accounting_entries") as exporter,
            patch("api.admin.send_file") as send_file,
        ):
            response = self.client.get(self._export_url(), headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        self.assertIn(("error", "No hay registros contables de ingresos para exportar."), self._flashes())
        exporter.assert_not_called()
        send_file.assert_not_called()

    def test_export_uses_accounting_entries_and_downloads_xlsx(self):
        self.client.post(self._record_url(self.invoice_id), headers=self._auth_header())
        result = AccountingExcelExportResult(
            output_path="/safe/accounting/ingresos_completo.xlsx",
            filename="ingresos_completo.xlsx",
            row_count=1,
            generated_at=datetime.now(timezone.utc),
            file_size=1234,
        )

        with (
            patch("api.admin.export_sales_accounting_entries", return_value=result) as exporter,
            patch("api.admin.send_file") as send_file,
            patch("api.admin.db.session.commit") as commit,
        ):
            send_file.return_value = Response(b"xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response = self.client.get(self._export_url(), headers=self._auth_header())

        self.assertEqual(response.status_code, 200)
        entries = exporter.call_args.args[0]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].invoice_id, self.invoice_id)
        self.assertTrue(exporter.call_args.kwargs["output_path"].endswith("ingresos_completo.xlsx"))
        self.assertIs(exporter.call_args.kwargs["overwrite"], True)
        self.assertEqual(send_file.call_args.kwargs["download_name"], "ingresos_completo.xlsx")
        self.assertEqual(
            send_file.call_args.kwargs["mimetype"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()

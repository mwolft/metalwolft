import ast
import base64
import copy
import importlib.util
import sys
import unittest
from datetime import datetime
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
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(text, node)
    raise AssertionError(f"{function_name} not found")


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
    from flask import Flask  # noqa: E402
    from flask_admin import Admin  # noqa: E402

    import api.admin as admin_module  # noqa: E402
    from api.invoice_email_service import (  # noqa: E402
        EMAIL_STATUS_FAILED,
        EMAIL_STATUS_SENT,
        InvoiceEmailPdfMissing,
        InvoiceEmailRecipientMissing,
        InvoiceEmailSendError,
    )
    from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash  # noqa: E402
    from api.models import AccountingEntry, Invoices, db  # noqa: E402


SNAPSHOT = {
    "schema_version": 1,
    "issuer": {"legal_name": "MetalWolft", "trade_name": "MetalWolft"},
    "customer": {
        "legal_name": "Cliente Email",
        "tax_id": "00000000T",
        "email": "cliente@example.com",
    },
    "operation": {
        "invoice_type": "ordinary",
        "currency": "EUR",
        "issue_date": "2026-07-18",
        "operation_date": "2026-07-18",
        "order_id": 42,
    },
    "payment": {"provider": "stripe"},
    "lines": [],
    "totals": {
        "tax_base": "100.00",
        "tax_amount": "21.00",
        "total_amount": "121.00",
    },
}


class FlaskAdminInvoiceEmailSourceTest(unittest.TestCase):
    def test_detail_action_is_post_only_and_accepts_no_browser_email_data(self):
        detail_formatter = function_source("_format_admin_invoice_email_detail")
        route_source = function_source("send_invoice_email")

        self.assertIn("view.get_url(\".send_invoice_email\", invoice_id=model.id)", detail_formatter)
        self.assertIn('method="post"', detail_formatter)
        self.assertIn("Enviar factura", detail_formatter)
        self.assertIn("Reenviar factura", detail_formatter)
        self.assertIn("@expose('/send-email/<int:invoice_id>', methods=['POST'])", source())
        self.assertIn("request.args", route_source)
        self.assertIn("request.form", route_source)
        self.assertIn("request.get_json(silent=True)", route_source)
        self.assertIn("Esta acción no acepta datos de email desde el navegador.", route_source)

    def test_route_delegates_to_email_service_and_controls_transaction(self):
        route_source = function_source("send_invoice_email")

        self.assertIn("self.session.get(Invoices, invoice_id)", route_source)
        self.assertIn("adapter = FlaskMailInvoiceAdapter(mail)", route_source)
        self.assertIn("send_invoice_email_v2(", route_source)
        self.assertIn("allow_resend=True", route_source)
        self.assertIn("self.session.commit()", route_source)
        self.assertIn("self.session.rollback()", route_source)
        self.assertIn("_persist_admin_invoice_email_failure(self.session, invoice_id, attempts_before)", route_source)
        self.assertNotIn("Message(", route_source)
        self.assertNotIn("mail.send(", route_source)

    def test_route_does_not_touch_other_documental_or_fiscal_flows(self):
        route_source = function_source("send_invoice_email")

        for forbidden in (
            "generate_invoice_pdf(",
            "issue_invoice_for_order",
            "create_accounting_entry",
            "export_sales_accounting_entries",
            "export_aeat_sales_ledger",
            "create_pending_submission",
            "run_invoice_workflow",
            "invoice.invoice_number =",
            "invoice.invoice_snapshot =",
            "invoice.invoice_snapshot_hash =",
            "invoice.amount =",
            "invoice.order_id =",
        ):
            self.assertNotIn(forbidden, route_source)

    def test_source_imports_required_adapter_service_and_statuses(self):
        admin_source = source()

        for expected in (
            "FlaskMailInvoiceAdapter",
            "FlaskMailInvoiceAdapterError",
            "EMAIL_STATUS_FAILED",
            "EMAIL_STATUS_SENT",
            "InvoiceEmailPdfMissing",
            "InvoiceEmailRecipientMissing",
            "InvoiceEmailSendError",
            "send_invoice_email as send_invoice_email_v2",
            "from api.utils import mail",
        ):
            self.assertIn(expected, admin_source)


@unittest.skipUnless(HAS_FLASK_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminInvoiceEmailHttpTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"

        self.app = Flask(__name__)
        self.app.config.update(
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            INVOICE_FOLDER="/safe/invoices",
        )
        db.init_app(self.app)

        admin = Admin(self.app, url="/admin")
        admin.add_view(admin_module.InvoiceAdminView(Invoices, db.session))

        with self.app.app_context():
            db.create_all()
            self.invoice = Invoices(
                invoice_number="F2026000001",
                order_id=42,
                invoice_type="ordinary",
                pdf_path="/api/download-invoice/invoice_F2026000001.pdf",
                amount=121.00,
                client_name="Cliente Email",
                client_address="Calle Email 1",
                client_cif="00000000T",
                order_details=[],
                invoice_snapshot=copy.deepcopy(SNAPSHOT),
                invoice_snapshot_hash=calculate_invoice_snapshot_hash(SNAPSHOT),
                invoice_snapshot_schema_version=1,
                issued_at=datetime(2026, 7, 18, 10, 0, 0),
                email_attempts=0,
            )
            db.session.add(self.invoice)
            db.session.commit()
            self.invoice_id = self.invoice.id

        self.client = self.app.test_client()
        self.send_rule = self._rule(".send_invoice_email")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _rule(self, endpoint_suffix):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(endpoint_suffix):
                return rule
        raise AssertionError(f"Flask Admin route {endpoint_suffix} was not registered")

    def _send_url(self, invoice_id=None):
        return self.send_rule.rule.replace("<int:invoice_id>", str(invoice_id or self.invoice_id))

    def _auth_header(self, username="admin", password="secret"):
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _flashes(self):
        with self.client.session_transaction() as session:
            return session.get("_flashes", [])

    def _invoice(self):
        return db.session.get(Invoices, self.invoice_id)

    def test_send_invoice_requires_basic_auth(self):
        with patch("api.admin.send_invoice_email_v2") as sender:
            response = self.client.post(self._send_url())

        self.assertEqual(response.status_code, 401)
        sender.assert_not_called()

    def test_send_invoice_rejects_browser_payload(self):
        response = self.client.post(
            self._send_url(),
            headers=self._auth_header(),
            data={"recipient": "other@example.com"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            ("error", "Esta acción no acepta datos de email desde el navegador."),
            self._flashes(),
        )

    def test_send_invoice_success_commits_and_does_not_modify_fiscal_data(self):
        def fake_send(invoice, **kwargs):
            invoice.email_status = EMAIL_STATUS_SENT
            invoice.email_sent_at = datetime(2026, 7, 18, 12, 0, 0)
            invoice.email_attempts = int(invoice.email_attempts or 0) + 1

        with self.app.app_context():
            before = {
                "invoice_number": self._invoice().invoice_number,
                "snapshot": copy.deepcopy(self._invoice().invoice_snapshot),
                "hash": self._invoice().invoice_snapshot_hash,
                "amount": self._invoice().amount,
            }

        with patch("api.admin.send_invoice_email_v2", side_effect=fake_send) as sender:
            response = self.client.post(self._send_url(), headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        self.assertIn(("success", "Factura enviada correctamente."), self._flashes())
        self.assertIs(sender.call_args.kwargs["allow_resend"], True)
        self.assertEqual(sender.call_args.kwargs["invoice_folder"], "/safe/invoices")
        with self.app.app_context():
            invoice = self._invoice()
            self.assertEqual(invoice.email_status, EMAIL_STATUS_SENT)
            self.assertEqual(invoice.email_attempts, 1)
            self.assertEqual(invoice.invoice_number, before["invoice_number"])
            self.assertEqual(invoice.invoice_snapshot, before["snapshot"])
            self.assertEqual(invoice.invoice_snapshot_hash, before["hash"])
            self.assertEqual(invoice.amount, before["amount"])
            self.assertEqual(db.session.query(AccountingEntry).count(), 0)

    def test_resend_is_allowed_and_increments_attempts(self):
        with self.app.app_context():
            invoice = self._invoice()
            invoice.email_status = EMAIL_STATUS_SENT
            invoice.email_attempts = 2
            db.session.commit()

        def fake_resend(invoice, **kwargs):
            invoice.email_attempts = int(invoice.email_attempts or 0) + 1
            invoice.email_status = EMAIL_STATUS_SENT

        with patch("api.admin.send_invoice_email_v2", side_effect=fake_resend):
            response = self.client.post(self._send_url(), headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertEqual(self._invoice().email_attempts, 3)
            self.assertEqual(self._invoice().email_status, EMAIL_STATUS_SENT)

    def test_without_pdf_shows_clear_error_and_does_not_send(self):
        with self.app.app_context():
            self._invoice().pdf_path = None
            db.session.commit()

        with patch("api.admin.send_invoice_email_v2") as sender:
            response = self.client.post(self._send_url(), headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        self.assertIn(("error", "No existe PDF."), self._flashes())
        sender.assert_not_called()

    def test_without_customer_email_shows_clear_error(self):
        with patch("api.admin.send_invoice_email_v2", side_effect=InvoiceEmailRecipientMissing()):
            response = self.client.post(self._send_url(), headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        self.assertIn(("error", "No existe email del cliente."), self._flashes())

    def test_missing_pdf_from_service_shows_clear_error(self):
        with patch("api.admin.send_invoice_email_v2", side_effect=InvoiceEmailPdfMissing()):
            response = self.client.post(self._send_url(), headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        self.assertIn(("error", "No existe PDF."), self._flashes())

    def test_smtp_error_persists_failed_status_and_attempt(self):
        with patch("api.admin.send_invoice_email_v2", side_effect=InvoiceEmailSendError()):
            response = self.client.post(self._send_url(), headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        self.assertIn(("error", "Error SMTP."), self._flashes())
        with self.app.app_context():
            invoice = self._invoice()
            self.assertEqual(invoice.email_status, EMAIL_STATUS_FAILED)
            self.assertEqual(invoice.email_attempts, 1)
            self.assertEqual(invoice.email_last_error, "No se pudo enviar el email de factura.")


if __name__ == "__main__":
    unittest.main()

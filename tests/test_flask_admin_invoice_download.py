import base64
import importlib.util
import sys
import unittest
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
    for package in (
        "flask",
        "flask_admin",
        "flask_sqlalchemy",
        "sqlalchemy",
        "slugify",
    )
)

if HAS_FLASK_ADMIN_DEPS:
    from flask import Flask, Response  # noqa: E402
    from flask_admin import Admin  # noqa: E402

    import api.admin as admin_module  # noqa: E402
    from api.invoice_pdf_download_service import (  # noqa: E402
        InvoicePdfDownloadFileMissing,
        InvoicePdfDownloadInvalidPath,
        InvoicePdfDownloadUnavailable,
        ResolvedInvoicePdfDownload,
    )
    from api.models import Invoices, db  # noqa: E402


@unittest.skipUnless(HAS_FLASK_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminInvoiceDownloadHttpTest(unittest.TestCase):
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

        self.admin = Admin(self.app, url="/admin")
        self.admin.add_view(admin_module.InvoiceAdminView(Invoices, db.session))

        with self.app.app_context():
            db.create_all()
            self.invoice = Invoices(
                invoice_number="F-2026-000001",
                order_id=None,
                invoice_type="ordinary",
                pdf_path="/api/download-invoice/invoice_F2026000001.pdf",
                amount=121.00,
                client_name="Cliente Test",
                client_address="Calle Test 1",
                client_cif="00000000T",
                order_details=[],
            )
            self.invoice_without_pdf = Invoices(
                invoice_number="F-2026-000002",
                order_id=None,
                invoice_type="ordinary",
                pdf_path=None,
                amount=95.00,
                client_name="Cliente Sin PDF",
                client_address="Calle Test 2",
                client_cif=None,
                order_details=[],
            )
            db.session.add_all([self.invoice, self.invoice_without_pdf])
            db.session.commit()
            self.invoice_id = self.invoice.id
            self.invoice_without_pdf_id = self.invoice_without_pdf.id

        self.client = self.app.test_client()
        self.download_rule = self._download_rule()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _download_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".download_pdf"):
                return rule.rule
        raise AssertionError("Flask Admin download_pdf route was not registered")

    def _url(self, invoice_id):
        return self.download_rule.replace("<int:invoice_id>", str(invoice_id))

    def _auth_header(self, username="admin", password="secret"):
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def test_admin_download_requires_basic_auth(self):
        response = self.client.get(self._url(self.invoice_id))

        self.assertEqual(response.status_code, 401)
        self.assertIn("WWW-Authenticate", response.headers)

    def test_admin_download_rejects_invalid_basic_auth(self):
        response = self.client.get(
            self._url(self.invoice_id),
            headers=self._auth_header(password="wrong"),
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("WWW-Authenticate", response.headers)

    def test_admin_download_with_valid_auth_reaches_invoice_lookup(self):
        response = self.client.get(
            self._url(999999),
            headers=self._auth_header(),
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("Factura no encontrada", response.get_data(as_text=True))
        self.assertNotIn("Traceback", response.get_data(as_text=True))
        self.assertNotIn("/safe/invoices", response.get_data(as_text=True))

    def test_admin_download_rejects_invoice_without_pdf(self):
        with patch(
            "api.admin.resolve_invoice_pdf_download",
            side_effect=InvoicePdfDownloadUnavailable("missing"),
        ) as resolver:
            response = self.client.get(
                self._url(self.invoice_without_pdf_id),
                headers=self._auth_header(),
            )

        self.assertEqual(response.status_code, 404)
        self.assertIn("PDF no disponible", response.get_data(as_text=True))
        resolver.assert_called_once()

    def test_admin_download_returns_valid_pdf_without_mutating_invoice_or_committing(self):
        resolved = ResolvedInvoicePdfDownload(
            file_path="/safe/invoices/invoice_F2026000001.pdf",
            filename="invoice_F2026000001.pdf",
            download_name="factura_F-2026-000001.pdf",
        )

        with (
            patch("api.admin.resolve_invoice_pdf_download", return_value=resolved) as resolver,
            patch("api.admin.send_file") as send_file,
            patch("api.admin.db.session.commit") as commit,
        ):
            send_file.return_value = Response(b"%PDF-1.4", mimetype="application/pdf")
            response = self.client.get(
                self._url(self.invoice_id),
                headers=self._auth_header(),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        resolver.assert_called_once()
        send_file.assert_called_once()
        self.assertEqual(send_file.call_args.kwargs["download_name"], "factura_F-2026-000001.pdf")
        commit.assert_not_called()

        with self.app.app_context():
            invoice = db.session.get(Invoices, self.invoice_id)
            self.assertEqual(invoice.pdf_path, "/api/download-invoice/invoice_F2026000001.pdf")
            self.assertEqual(invoice.invoice_number, "F-2026-000001")

    def test_admin_download_missing_file_is_safe_and_does_not_regenerate(self):
        with (
            patch(
                "api.admin.resolve_invoice_pdf_download",
                side_effect=InvoicePdfDownloadFileMissing("missing"),
            ),
            patch("api.admin.render_original_order_invoice_pdf", create=True) as legacy_renderer,
        ):
            response = self.client.get(
                self._url(self.invoice_id),
                headers=self._auth_header(),
            )

        self.assertEqual(response.status_code, 404)
        self.assertIn("Archivo PDF no encontrado", response.get_data(as_text=True))
        legacy_renderer.assert_not_called()

    def test_admin_download_invalid_path_is_rejected_safely(self):
        with patch(
            "api.admin.resolve_invoice_pdf_download",
            side_effect=InvoicePdfDownloadInvalidPath("bad path"),
        ):
            response = self.client.get(
                self._url(self.invoice_id),
                headers=self._auth_header(),
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Ruta de PDF no válida", response.get_data(as_text=True))
        self.assertNotIn("/safe/invoices", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()

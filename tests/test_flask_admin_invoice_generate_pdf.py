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
    from flask import Flask  # noqa: E402
    from flask_admin import Admin  # noqa: E402

    import api.admin as admin_module  # noqa: E402
    from api.invoice_pdf_service import (  # noqa: E402
        InvoicePdfIntegrityError,
        InvoicePdfResult,
        InvoicePdfSnapshotMissing,
        InvoicePdfUnsupportedSchema,
        InvoicePdfWriteError,
    )
    from api.models import Invoices, db  # noqa: E402


SNAPSHOT = {
    "schema_version": 1,
    "issuer": {"legal_name": "MetalWolft"},
    "customer": {"legal_name": "Cliente Test"},
    "operation": {"invoice_type": "ordinary", "currency": "EUR"},
    "lines": [{"line_number": 1, "description": "Reja", "quantity": "1"}],
    "totals": {"total_amount": "121.00"},
}


@unittest.skipUnless(HAS_FLASK_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminInvoiceGeneratePdfHttpTest(unittest.TestCase):
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
            self.without_pdf = self._create_invoice(
                "F-2026-000001",
                pdf_path=None,
                stored_hash="hash-original",
                issued_at=datetime(2026, 7, 18, 10, 0, 0),
            )
            self.with_pdf = self._create_invoice(
                "F-2026-000002",
                pdf_path="/api/download-invoice/invoice_F-2026-000002.pdf",
                stored_hash="hash-existing",
                issued_at=datetime(2026, 7, 18, 11, 0, 0),
            )
            db.session.commit()
            self.without_pdf_id = self.without_pdf.id
            self.with_pdf_id = self.with_pdf.id

        self.client = self.app.test_client()
        self.generate_rule = self._generate_rule()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_invoice(self, invoice_number, *, pdf_path, stored_hash, issued_at):
        invoice = Invoices(
            invoice_number=invoice_number,
            order_id=None,
            invoice_type="ordinary",
            pdf_path=pdf_path,
            amount=121.00,
            client_name="Cliente Test",
            client_address="Calle Test 1",
            client_cif="00000000T",
            order_details=[],
            invoice_snapshot=copy.deepcopy(SNAPSHOT),
            invoice_snapshot_hash=stored_hash,
            invoice_snapshot_schema_version=1,
            issued_at=issued_at,
        )
        db.session.add(invoice)
        return invoice

    def _generate_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".generate_pdf"):
                return rule
        raise AssertionError("Flask Admin generate_pdf route was not registered")

    def _url(self, invoice_id):
        return self.generate_rule.rule.replace("<int:invoice_id>", str(invoice_id))

    def _auth_header(self, username="admin", password="secret"):
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _post(self, invoice_id, *, headers=None, json=None):
        return self.client.post(self._url(invoice_id), headers=headers, json=json)

    def _flashes(self):
        with self.client.session_transaction() as session:
            return session.get("_flashes", [])

    def _result(self, pdf_path="/api/download-invoice/invoice_F-2026-000001.pdf"):
        return InvoicePdfResult(
            pdf_path=pdf_path,
            filename=pdf_path.rsplit("/", 1)[-1],
            generated_at=datetime(2026, 7, 18, 12, 0, 0),
            file_size=1234,
        )

    def test_route_is_registered_as_post_only_and_get_does_not_execute(self):
        self.assertIn("POST", self.generate_rule.methods)
        self.assertNotIn("GET", self.generate_rule.methods)

        with patch("api.admin.generate_invoice_pdf") as generator:
            response = self.client.get(self._url(self.without_pdf_id), headers=self._auth_header())

        self.assertEqual(response.status_code, 405)
        generator.assert_not_called()

    def test_basic_auth_is_required_and_invalid_credentials_do_not_execute(self):
        for headers in (None, self._auth_header(password="wrong")):
            with self.subTest(headers=headers):
                with patch("api.admin.generate_invoice_pdf") as generator:
                    response = self._post(self.without_pdf_id, headers=headers)

                self.assertEqual(response.status_code, 401)
                generator.assert_not_called()

    def test_missing_invoice_redirects_without_generation_or_commit(self):
        with (
            patch("api.admin.generate_invoice_pdf") as generator,
            patch("api.admin.db.session.commit") as commit,
            patch("api.admin.db.session.rollback") as rollback,
        ):
            response = self._post(999999, headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/", response.headers["Location"])
        generator.assert_not_called()
        commit.assert_not_called()
        rollback.assert_not_called()
        self.assertIn(("error", "Factura no encontrada."), self._flashes())

    def test_without_pdf_uses_regenerate_false_ignoring_browser_payload_and_commits_once(self):
        result = self._result()

        def fake_generate(invoice, *, regenerate=False):
            invoice.pdf_path = result.pdf_path
            return result

        with (
            patch("api.admin.generate_invoice_pdf", side_effect=fake_generate) as generator,
            patch("api.admin.db.session.commit") as commit,
            patch("api.admin.db.session.rollback") as rollback,
        ):
            response = self._post(
                self.without_pdf_id,
                headers=self._auth_header(),
                json={"regenerate": True, "pdf_path": "/unsafe.pdf", "output_dir": "/tmp"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("details", response.headers["Location"])
        self.assertEqual(generator.call_args.args[0].id, self.without_pdf_id)
        self.assertEqual(generator.call_args.kwargs, {"regenerate": False})
        commit.assert_called_once()
        rollback.assert_not_called()
        self.assertIn(("success", "PDF generado correctamente."), self._flashes())

    def test_with_pdf_uses_regenerate_true_and_commits_once(self):
        result = self._result("/api/download-invoice/invoice_F-2026-000002.pdf")

        def fake_generate(invoice, *, regenerate=False):
            invoice.pdf_path = result.pdf_path
            return result

        with (
            patch("api.admin.generate_invoice_pdf", side_effect=fake_generate) as generator,
            patch("api.admin.db.session.commit") as commit,
            patch("api.admin.db.session.rollback") as rollback,
        ):
            response = self._post(self.with_pdf_id, headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(generator.call_args.kwargs, {"regenerate": True})
        commit.assert_called_once()
        rollback.assert_not_called()
        self.assertIn(("success", "PDF regenerado correctamente."), self._flashes())

    def test_generation_failure_rolls_back_without_commit_and_sanitizes_error(self):
        with (
            patch("api.admin.generate_invoice_pdf", side_effect=RuntimeError("disk /safe/invoices/secret")),
            patch("api.admin.db.session.commit") as commit,
            patch("api.admin.db.session.rollback") as rollback,
        ):
            response = self._post(self.without_pdf_id, headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        commit.assert_not_called()
        rollback.assert_called_once()
        flashes = self._flashes()
        self.assertIn(("error", "No se pudo generar el PDF."), flashes)
        self.assertNotIn("disk", str(flashes))
        self.assertNotIn("/safe/invoices", str(flashes))

    def test_domain_errors_are_translated_to_safe_messages(self):
        cases = (
            (InvoicePdfSnapshotMissing("snapshot"), "La factura no dispone de un snapshot fiscal válido."),
            (InvoicePdfIntegrityError("hash"), "No se puede generar el PDF porque la integridad fiscal no es válida."),
            (InvoicePdfUnsupportedSchema("schema"), "La versión del snapshot fiscal no está soportada."),
            (InvoicePdfWriteError("No se puede sobrescribir un PDF existente."), "No se puede sobrescribir un PDF que no está asociado a esta factura."),
        )

        for error, message in cases:
            with self.subTest(message=message):
                with (
                    patch("api.admin.generate_invoice_pdf", side_effect=error),
                    patch("api.admin.db.session.commit") as commit,
                    patch("api.admin.db.session.rollback") as rollback,
                ):
                    response = self._post(self.without_pdf_id, headers=self._auth_header())

                self.assertEqual(response.status_code, 302)
                commit.assert_not_called()
                rollback.assert_called_once()
                self.assertIn(("error", message), self._flashes())

    def test_action_preserves_core_fiscal_fields_except_pdf_path(self):
        result = self._result()
        with self.app.app_context():
            invoice = db.session.get(Invoices, self.without_pdf_id)
            original = {
                "invoice_number": invoice.invoice_number,
                "issued_at": invoice.issued_at,
                "invoice_snapshot": copy.deepcopy(invoice.invoice_snapshot),
                "invoice_snapshot_hash": invoice.invoice_snapshot_hash,
            }

        def fake_generate(invoice, *, regenerate=False):
            invoice.pdf_path = result.pdf_path
            return result

        with patch("api.admin.generate_invoice_pdf", side_effect=fake_generate):
            self._post(self.without_pdf_id, headers=self._auth_header())

        with self.app.app_context():
            invoice = db.session.get(Invoices, self.without_pdf_id)
            self.assertEqual(invoice.pdf_path, result.pdf_path)
            for field, expected in original.items():
                self.assertEqual(getattr(invoice, field), expected)


if __name__ == "__main__":
    unittest.main()

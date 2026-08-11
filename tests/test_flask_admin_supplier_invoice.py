import base64
import importlib.util
import sys
import unittest
from datetime import date
from decimal import Decimal
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


HAS_ADMIN_DEPS = all(
    has_package(package)
    for package in ("flask", "flask_admin", "flask_sqlalchemy", "sqlalchemy", "slugify")
)

if HAS_ADMIN_DEPS:
    from flask import Flask  # noqa: E402
    from flask_admin import Admin  # noqa: E402
    from sqlalchemy.orm import configure_mappers  # noqa: E402

    import api.admin as admin_module  # noqa: E402
    from api.models import (  # noqa: E402
        SupplierInvoice,
        SupplierInvoiceReceptionSequence,
        SupplierInvoiceTaxBreakdown,
        db,
    )


@unittest.skipUnless(HAS_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminSupplierInvoiceTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"
        configure_mappers()
        self.app = Flask(__name__, template_folder=str(SRC_DIR / "templates"))
        self.app.config.update(
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.admin = Admin(self.app, url="/admin")
        self.view = admin_module.SupplierInvoiceAdminView(SupplierInvoice, db.session, name="Facturas recibidas")
        self.admin.add_view(self.view)
        with self.app.app_context():
            db.create_all()
            db.session.add(SupplierInvoiceReceptionSequence(id=1, last_number=0))
            self.invoice = self._make_draft()
            db.session.commit()
            self.invoice_id = self.invoice.id
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _make_draft(self):
        invoice = SupplierInvoice(
            supplier_legal_name="Acero Proveedor SL",
            supplier_tax_id="B12345678",
            supplier_invoice_number="P-2026-001",
            issue_date=date(2026, 8, 11),
            concept="Material de taller",
            total_amount=Decimal("121.00"),
        )
        db.session.add(invoice)
        db.session.flush()
        db.session.add(
            SupplierInvoiceTaxBreakdown(
                supplier_invoice_id=invoice.id,
                position=1,
                tax_base=Decimal("100.00"),
                tax_rate=Decimal("21.00"),
                tax_amount=Decimal("21.00"),
                deductible_tax_amount=Decimal("21.00"),
            )
        )
        return invoice

    def _auth_header(self):
        token = base64.b64encode(b"admin:secret").decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _register_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".confirm_register"):
                return rule
        raise AssertionError("Supplier invoice registration route was not registered")

    def _url(self):
        return self._register_rule().rule.replace("<int:supplier_invoice_id>", str(self.invoice_id))

    def _edit_url(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".edit_view"):
                return f"{rule.rule}?id={self.invoice_id}"
        raise AssertionError("Supplier invoice edit route was not registered")

    def test_confirmation_action_registers_only_an_editable_draft(self):
        response = self.client.get(self._url(), headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CONFIRMAR Y REGISTRAR", response.data)

        response = self.client.post(self._url(), headers=self._auth_header())
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            registered = db.session.get(SupplierInvoice, self.invoice_id)
            self.assertEqual(registered.status, SupplierInvoice.STATUS_REGISTERED)
            self.assertEqual(registered.reception_number, 1)

    def test_registered_invoice_cannot_open_edit_or_be_deleted(self):
        self.client.post(self._url(), headers=self._auth_header())
        with self.app.app_context():
            registered = db.session.get(SupplierInvoice, self.invoice_id)
            response = self.client.get(self._edit_url(), headers=self._auth_header())
            self.assertEqual(response.status_code, 302)
        with self.app.test_request_context("/admin/supplierinvoice/"):
            self.assertFalse(self.view.delete_model(registered))
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(SupplierInvoice, self.invoice_id))

    def test_detail_formatter_offers_registration_only_before_registration(self):
        with self.app.app_context():
            view = type("View", (), {"get_url": lambda *_args, **_kwargs: "/register"})()
            before = admin_module._format_supplier_invoice_registration(view, None, self.invoice, None)
            self.assertIn("CONFIRMAR Y REGISTRAR", str(before))
            self.client.post(self._url(), headers=self._auth_header())
            registered = db.session.get(SupplierInvoice, self.invoice_id)
            after = admin_module._format_supplier_invoice_registration(view, None, registered, None)
            self.assertNotIn("CONFIRMAR Y REGISTRAR", str(after))

    def test_date_fields_render_as_native_iso_date_inputs_and_parse_dates(self):
        with self.app.app_context():
            invoice = db.session.get(SupplierInvoice, self.invoice_id)
            with self.app.test_request_context(
                "/admin/supplierinvoice/edit/",
                method="POST",
                data={"issue_date": "2026-07-25", "operation_date": "2026-12-31"},
            ):
                form = self.view.edit_form(invoice)

                self.assertIn("%Y-%m-%d", form.issue_date.format)
                self.assertIn("%Y-%m-%d", form.operation_date.format)
                issue_html = str(form.issue_date())
                operation_html = str(form.operation_date())
                self.assertIn('type="date"', issue_html)
                self.assertIn('type="date"', operation_html)
                self.assertNotIn("data-role=\"datepicker\"", issue_html)
                self.assertNotIn("data-role=\"datepicker\"", operation_html)
                self.assertNotIn("data-date-format", issue_html)
                self.assertNotIn("data-date-format", operation_html)
                for literal_token in ("yyyy", "Tu", "Su"):
                    self.assertNotIn(literal_token, issue_html)
                    self.assertNotIn(literal_token, operation_html)

                self.assertEqual(form.issue_date.data, date(2026, 7, 25))
                self.assertEqual(form.operation_date.data, date(2026, 12, 31))

    def test_create_then_edit_draft_preserves_issue_date_and_allows_empty_operation_date(self):
        with self.app.app_context():
            with self.app.test_request_context(
                "/admin/supplierinvoice/new/",
                method="POST",
                data={
                    "supplier_legal_name": "Proveedor de prueba SL",
                    "supplier_tax_id": "B87654321",
                    "supplier_invoice_number": "P-2026-002",
                    "issue_date": "2026-07-25",
                    "operation_date": "",
                    "concept": "Material auxiliar",
                    "total_amount": "0.00",
                    "currency": "EUR",
                    "fiscal_invoice_type": "F1",
                    "tax_treatment": "domestic_standard",
                    "status": "draft",
                    "source": "manual",
                },
            ):
                form = self.view.create_form()
                self.assertTrue(form.validate())
                invoice = SupplierInvoice()
                form.populate_obj(invoice)
            db.session.add(invoice)
            db.session.commit()

            updated = db.session.get(SupplierInvoice, invoice.id)
            self.assertEqual(updated.issue_date, date(2026, 7, 25))
            self.assertIsNone(updated.operation_date)

            with self.app.test_request_context("/admin/supplierinvoice/edit/"):
                edit_form = self.view.edit_form(updated)
                self.assertEqual(edit_form.issue_date.data, date(2026, 7, 25))
                self.assertIsNone(edit_form.operation_date.data)
                self.assertIn('value="2026-07-25"', str(edit_form.issue_date()))

    def test_issue_date_is_required_while_operation_date_remains_optional(self):
        with self.app.app_context():
            with self.app.test_request_context(
                "/admin/supplierinvoice/new/",
                method="POST",
                data={"issue_date": "", "operation_date": ""},
            ):
                form = self.view.create_form()
                self.assertFalse(form.validate())
                self.assertTrue(form.issue_date.errors)
                self.assertFalse(form.operation_date.errors)


if __name__ == "__main__":
    unittest.main()

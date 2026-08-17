import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.invoice_issue_service import InvoiceIssueError
from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash
from api.manual_invoice_issue_service import issue_manual_invoice
from api.manual_invoice_snapshot_builder import build_manual_invoice_snapshot


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0
        self.rollbacks = 0

    def add(self, value):
        self.added.append(value)

    def flush(self):
        for value in self.added:
            if getattr(value, "id", None) is None:
                value.id = 900

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class FakeInvoice:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.id = None


def issuer():
    return {
        "legal_name": "MetalWolft", "trade_name": "MetalWolft", "tax_id": "B00000000",
        "address": "Calle Taller", "postal_code": "13000", "city": "Ciudad Real",
        "country_code": "ES", "province": None, "email": "facturas@example.test", "phone": None,
    }


def draft(*, total_base=Decimal("100.00"), tax_rate=Decimal("21.00"), email="cliente@example.test"):
    line = SimpleNamespace(id=1, position=1, concept="Servicio manual", tax_base=total_base, tax_rate=tax_rate)
    return SimpleNamespace(
        id=42,
        status="draft",
        issued_invoice_id=None,
        issued_invoice=None,
        client_name="Cliente nacional, S.L.",
        client_tax_id="B12345678",
        client_address="Calle Cliente 1",
        client_postal_code="13001",
        client_city="Ciudad Real",
        client_province="Ciudad Real",
        client_country_code="ES",
        client_email=email,
        issue_date=date(2026, 8, 17),
        operation_date=date(2026, 8, 17),
        external_reference="REF-1",
        currency="EUR",
        lines=[line],
    )


class ManualInvoiceSnapshotTest(unittest.TestCase):
    def test_v2_snapshot_is_compatible_and_has_no_order_or_checkout(self):
        snapshot = build_manual_invoice_snapshot(draft(), issuer(), issue_date=date(2026, 8, 17), actor="admin")

        self.assertEqual(snapshot["schema_version"], 2)
        self.assertEqual(snapshot["operation"]["invoice_type"], "ordinary")
        self.assertIsNone(snapshot["operation"]["order_id"])
        self.assertIsNone(snapshot["references"].get("checkout_session_id"))
        self.assertEqual(snapshot["totals"], {
            "products_amount_before_discount": "100.00",
            "shipping_amount_before_discount": "0.00",
            "total_amount_before_discount": "121.00",
            "discount_amount": "0.00",
            "tax_base": "100.00",
            "tax_amount": "21.00",
            "total_amount": "121.00",
            "rounding_adjustment": "0.00",
        })
        line = snapshot["lines"][0]
        for field in ("unit_price_net", "line_tax_base_before_discount", "discount_tax_base", "tax_base", "tax_amount", "line_total"):
            self.assertIn(field, line)

    def test_snapshot_passes_existing_pdf_email_accounting_and_aeat_validators(self):
        from api.aeat_sales_ledger_service import prepare_aeat_sales_ledger_rows
        from api.invoice_accounting_service import _validated_snapshot as accounting_snapshot
        from api.invoice_accounting_service import _validate_snapshot_hash as accounting_hash
        from api.invoice_email_service import _validated_snapshot as email_snapshot
        from api.invoice_email_service import _validate_snapshot_hash as email_hash
        from api.invoice_pdf_service import _validate_snapshot_contract as pdf_contract
        from api.invoice_pdf_service import _validate_snapshot_hash as pdf_hash

        snapshot = build_manual_invoice_snapshot(draft(), issuer(), issue_date=date(2026, 8, 17))
        invoice = SimpleNamespace(
            id=501,
            invoice_number="F2026000501",
            invoice_type="ordinary",
            issued_at=date(2026, 8, 17),
            invoice_snapshot=snapshot,
            invoice_snapshot_hash=calculate_invoice_snapshot_hash(snapshot),
        )
        pdf_contract(snapshot)
        pdf_hash(invoice, snapshot)
        self.assertIs(email_snapshot(invoice), snapshot)
        email_hash(invoice, snapshot)
        self.assertIs(accounting_snapshot(invoice), snapshot)
        accounting_hash(invoice, snapshot)

        entry = SimpleNamespace(
            id=61,
            entry_type="sale",
            currency="EUR",
            invoice=invoice,
            invoice_number=invoice.invoice_number,
            taxable_base=Decimal("100.00"),
            vat_amount=Decimal("21.00"),
            total_amount=Decimal("121.00"),
        )
        rows = prepare_aeat_sales_ledger_rows([entry])
        self.assertEqual(rows[0]["invoice_type"], "F1")
        self.assertEqual(rows[0]["tax_rate"], Decimal("21.00"))

    def test_rejects_multiple_lines_and_nonpositive_amounts(self):
        invalid = draft()
        invalid.lines.append(SimpleNamespace(id=2, position=2, concept="Otra", tax_base=Decimal("1.00"), tax_rate=Decimal("21.00")))
        with self.assertRaisesRegex(ValueError, "exactamente una linea"):
            build_manual_invoice_snapshot(invalid, issuer(), issue_date=invalid.issue_date)

        with self.assertRaisesRegex(ValueError, "base imponible debe ser mayor"):
            build_manual_invoice_snapshot(draft(total_base=Decimal("0.00")), issuer(), issue_date=date(2026, 8, 17))


class ManualInvoiceIssueServiceTest(unittest.TestCase):
    def test_issues_once_with_null_order_and_fiscal_snapshot(self):
        session = FakeSession()
        target = draft()
        allocation = SimpleNamespace(invoice_number="F2026000099")

        with patch("api.manual_invoice_issue_service._lock_draft_for_update", return_value=target), patch(
            "api.manual_invoice_issue_service.acquire_next_invoice_number", return_value=allocation
        ) as allocate, patch("api.manual_invoice_issue_service._invoice_model", return_value=FakeInvoice):
            result = issue_manual_invoice(db_session=session, draft_id=target.id, issuer=issuer(), actor="admin@example.test")

        self.assertTrue(result.created)
        self.assertEqual(result.invoice_number, "F2026000099")
        self.assertIsNone(result.invoice.order_id)
        self.assertEqual(result.invoice.invoice_type, "ordinary")
        self.assertEqual(result.invoice.invoice_snapshot_schema_version, 2)
        self.assertTrue(result.invoice.invoice_snapshot_hash)
        self.assertEqual(target.status, "issued")
        self.assertEqual(target.issued_invoice_id, result.invoice.id)
        allocate.assert_called_once()
        self.assertEqual(session.commits, 1)

    def test_retry_returns_existing_invoice_without_allocating_number(self):
        session = FakeSession()
        existing = SimpleNamespace(id=77, invoice_number="F2026000099")
        target = draft()
        target.issued_invoice_id = existing.id
        target.issued_invoice = existing

        with patch("api.manual_invoice_issue_service._lock_draft_for_update", return_value=target), patch(
            "api.manual_invoice_issue_service.acquire_next_invoice_number"
        ) as allocate:
            result = issue_manual_invoice(db_session=session, draft_id=target.id, issuer=issuer())

        self.assertFalse(result.created)
        self.assertIs(result.invoice, existing)
        allocate.assert_not_called()

    def test_validation_happens_before_number_allocation(self):
        session = FakeSession()
        target = draft(total_base=Decimal("0.00"))
        with patch("api.manual_invoice_issue_service._lock_draft_for_update", return_value=target), patch(
            "api.manual_invoice_issue_service.acquire_next_invoice_number"
        ) as allocate:
            with self.assertRaisesRegex(ValueError, "base imponible debe ser mayor"):
                issue_manual_invoice(db_session=session, draft_id=target.id, issuer=issuer())
        allocate.assert_not_called()
        self.assertEqual(session.rollbacks, 1)


class ManualInvoiceModelContractTest(unittest.TestCase):
    def test_models_use_numeric_draft_lines_and_keep_invoice_create_disabled(self):
        models = (SRC_DIR / "api" / "models.py").read_text(encoding="utf-8")
        admin = (SRC_DIR / "api" / "admin.py").read_text(encoding="utf-8")
        self.assertIn("class ManualInvoiceDraft(db.Model):", models)
        self.assertIn("class ManualInvoiceDraftLine(db.Model):", models)
        self.assertIn("db.Numeric(12, 2)", models)
        invoice_admin = admin[admin.index("class InvoiceAdminView"):]
        self.assertIn("can_create = False", invoice_admin)


class ManualInvoiceAdminContractTest(unittest.TestCase):
    def test_admin_exposes_draft_workflow_and_dashboard_entry_point(self):
        admin = (SRC_DIR / "api" / "admin.py").read_text(encoding="utf-8")
        dashboard = (SRC_DIR / "templates" / "admin" / "dashboard.html").read_text(encoding="utf-8")
        template = (SRC_DIR / "templates" / "admin" / "manual_invoice_draft_confirm.html").read_text(encoding="utf-8")
        self.assertIn("class ManualInvoiceDraftAdminView", admin)
        self.assertIn('@expose("/confirm-issue/<int:draft_id>", methods=["GET", "POST"])', admin)
        self.assertIn("issue_manual_invoice(", admin)
        self.assertIn("EMITIR FACTURA MANUAL", dashboard)
        self.assertIn("CONFIRMAR EMISIÓN", template)
        self.assertIn("PDF, registrar contabilidad y enviar el email", template)


def _has_admin_dependencies():
    try:
        import flask  # noqa: F401
        import flask_admin  # noqa: F401
        import flask_sqlalchemy  # noqa: F401
        import sqlalchemy  # noqa: F401
    except ImportError:
        return False
    return True


HAS_ADMIN_DEPENDENCIES = _has_admin_dependencies()


@unittest.skipUnless(HAS_ADMIN_DEPENDENCIES, "Flask-Admin dependencies are not installed.")
class ManualInvoiceDraftAdminViewTest(unittest.TestCase):
    def setUp(self):
        from flask import Flask
        from flask_admin import Admin
        from sqlalchemy.orm import configure_mappers

        import api.admin as admin_module
        from api.models import ManualInvoiceDraft, ManualInvoiceDraftLine, db

        self.admin_module = admin_module
        self.ManualInvoiceDraft = ManualInvoiceDraft
        self.ManualInvoiceDraftLine = ManualInvoiceDraftLine
        self.db = db
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
        self.view = admin_module.ManualInvoiceDraftAdminView(
            ManualInvoiceDraft, db.session, name="Facturas manuales"
        )
        self.admin.add_view(self.view)
        with self.app.app_context():
            db.create_all()
            self.draft = ManualInvoiceDraft(
                client_name="Cliente", client_tax_id="B12345678", client_address="Calle 1",
                client_postal_code="13001", client_city="Ciudad Real", issue_date=date(2026, 8, 17),
            )
            db.session.add(self.draft)
            db.session.flush()
            db.session.add(ManualInvoiceDraftLine(
                manual_invoice_draft_id=self.draft.id, concept="Servicio", tax_base=Decimal("100.00"), tax_rate=Decimal("21.00")
            ))
            db.session.commit()
            self.draft_id = self.draft.id
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            self.db.session.remove()
            self.db.drop_all()

    @property
    def auth(self):
        import base64
        return {"Authorization": "Basic " + base64.b64encode(b"admin:secret").decode("ascii")}

    def _route(self, suffix, *, draft_id=None):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint == f"{self.view.endpoint}{suffix}":
                path = rule.rule.replace("<int:id>", str(draft_id)).replace("<int:draft_id>", str(draft_id))
                if suffix == ".edit_view":
                    return f"{path}?id={draft_id}"
                return path
        self.fail(f"Route {suffix} was not registered")

    def test_list_loads_and_draft_has_edit_route(self):
        response = self.client.get(self._route(".index_view"), headers=self.auth)
        self.assertEqual(response.status_code, 200)
        edit_url = self._route(".edit_view", draft_id=self.draft_id)
        self.assertIn(edit_url.encode(), response.data)

    def test_draft_edit_route_accepts_get(self):
        response = self.client.get(self._route(".edit_view", draft_id=self.draft_id), headers=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cliente / raz", response.data)

    def test_issued_and_cancelled_drafts_cannot_be_edited(self):
        with self.app.app_context():
            draft = self.db.session.get(self.ManualInvoiceDraft, self.draft_id)
            draft.status = self.ManualInvoiceDraft.STATUS_ISSUED
            draft.issued_invoice_id = None
            self.db.session.commit()
        response = self.client.get(self._route(".edit_view", draft_id=self.draft_id), headers=self.auth)
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            draft = self.db.session.get(self.ManualInvoiceDraft, self.draft_id)
            draft.status = self.ManualInvoiceDraft.STATUS_CANCELLED
            self.db.session.commit()
        response = self.client.get(self._route(".edit_view", draft_id=self.draft_id), headers=self.auth)
        self.assertEqual(response.status_code, 302)


if __name__ == "__main__":
    unittest.main()

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
    from api.invoice_issue_service import IssuedInvoiceResult  # noqa: E402
    from api.models import Invoices, db  # noqa: E402


V2_SNAPSHOT = {
    "schema_version": 2,
    "operation": {"invoice_type": "ordinary"},
    "lines": [],
    "totals": {"tax_base": "1.00", "tax_amount": "0.21", "total_amount": "1.21"},
}


@unittest.skipUnless(HAS_FLASK_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminInvoiceRectificationHttpTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"
        self.app = Flask(__name__, template_folder=str(SRC_DIR / "templates"))
        self.app.config.update(
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.admin = Admin(self.app, url="/admin")
        self.admin.add_view(admin_module.InvoiceAdminView(Invoices, db.session))

        with self.app.app_context():
            db.create_all()
            self.ordinary = self._create_invoice(
                "F2026000001",
                invoice_type="ordinary",
                snapshot=V2_SNAPSHOT,
                issued_at=datetime(2026, 8, 8, 10, 0, 0),
            )
            self.unissued = self._create_invoice(
                "F2026000002",
                invoice_type="ordinary",
                snapshot=V2_SNAPSHOT,
                issued_at=None,
            )
            self.v1 = self._create_invoice(
                "F2026000003",
                invoice_type="ordinary",
                snapshot={"schema_version": 1},
                issued_at=datetime(2026, 8, 8, 11, 0, 0),
            )
            db.session.commit()
            self.ordinary_id = self.ordinary.id
            self.unissued_id = self.unissued.id
            self.v1_id = self.v1.id

        self.client = self.app.test_client()
        self.rectification_rule = self._rectification_rule()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_invoice(self, invoice_number, *, invoice_type, snapshot, issued_at):
        invoice = Invoices(
            invoice_number=invoice_number,
            invoice_type=invoice_type,
            amount=1.21,
            client_name="Cliente Test",
            client_address="Calle Test 1",
            client_cif="00000000T",
            order_details=[],
            invoice_snapshot=copy.deepcopy(snapshot),
            invoice_snapshot_schema_version=snapshot.get("schema_version"),
            invoice_snapshot_hash="snapshot-hash",
            issued_at=issued_at,
        )
        db.session.add(invoice)
        return invoice

    def _rectification_rule(self):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".issue_total_rectification"):
                return rule
        raise AssertionError("Flask Admin total rectification route was not registered")

    def _url(self, invoice_id):
        return self.rectification_rule.rule.replace("<int:invoice_id>", str(invoice_id))

    def _auth_header(self):
        token = base64.b64encode(b"admin:secret").decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _flashes(self):
        with self.client.session_transaction() as session:
            return session.get("_flashes", [])

    def test_confirmation_is_only_available_for_an_emitted_v2_ordinary_invoice(self):
        response = self.client.get(self._url(self.ordinary_id), headers=self._auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"EMITIR RECTIFICATIVA TOTAL", response.data)
        self.assertIn(b"rectification_reason", response.data)
        self.assertIn(b"Factura emitida por error", response.data)
        self.assertIn(b"rectification_aeat_type", response.data)
        self.assertIn(b"R1", response.data)
        self.assertIn(b"R4", response.data)
        self.assertNotIn(b"R2", response.data)
        self.assertNotIn(b"R3", response.data)
        self.assertNotIn(b"R5", response.data)

        for invoice_id in (self.unissued_id, self.v1_id):
            with self.subTest(invoice_id=invoice_id):
                response = self.client.get(self._url(invoice_id), headers=self._auth_header())
                self.assertEqual(response.status_code, 302)
                self.assertIn(
                    ("error", "Esta factura no puede rectificarse desde administraci\u00f3n."),
                    self._flashes(),
                )

    def test_reason_is_required_before_the_service_is_called(self):
        with patch("api.admin.issue_total_rectification_for_invoice") as issuer:
            response = self.client.post(self._url(self.ordinary_id), headers=self._auth_header(), data={})

        self.assertEqual(response.status_code, 302)
        issuer.assert_not_called()
        self.assertIn(
            ("error", "Selecciona un motivo v\u00e1lido para la rectificaci\u00f3n."),
            self._flashes(),
        )

    def test_aeat_type_is_required_before_the_service_is_called(self):
        with patch("api.admin.issue_total_rectification_for_invoice") as issuer:
            response = self.client.post(
                self._url(self.ordinary_id),
                headers=self._auth_header(),
                data={"rectification_reason": "invoice_error"},
            )

        self.assertEqual(response.status_code, 302)
        issuer.assert_not_called()
        self.assertIn(
            ("error", "Selecciona un tipo fiscal AEAT válido para la rectificación."),
            self._flashes(),
        )

    def test_detail_formatter_shows_the_action_only_for_an_eligible_invoice(self):
        with self.app.app_context():
            view = next(
                view for view in self.admin._views
                if isinstance(view, admin_module.InvoiceAdminView)
            )
            ordinary = db.session.get(Invoices, self.ordinary_id)
            unissued = db.session.get(Invoices, self.unissued_id)
            v1 = db.session.get(Invoices, self.v1_id)
            with self.app.test_request_context("/admin/invoices/details/"):
                eligible_markup = admin_module._format_admin_invoice_type_detail(
                    view, None, ordinary, "invoice_type"
                )
                unissued_markup = admin_module._format_admin_invoice_type_detail(
                    view, None, unissued, "invoice_type"
                )
                v1_markup = admin_module._format_admin_invoice_type_detail(view, None, v1, "invoice_type")

        self.assertIn("EMITIR RECTIFICATIVA TOTAL", str(eligible_markup))
        self.assertNotIn("EMITIR RECTIFICATIVA TOTAL", str(unissued_markup))
        self.assertNotIn("EMITIR RECTIFICATIVA TOTAL", str(v1_markup))

    def test_partial_scope_is_rejected_before_the_service_is_called(self):
        with patch("api.admin.issue_total_rectification_for_invoice") as issuer:
            response = self.client.post(
                self._url(self.ordinary_id),
                headers=self._auth_header(),
                data={
                    "rectification_reason": "invoice_error",
                    "rectification_aeat_type": "R4",
                    "rectification_scope": "partial",
                },
            )

        self.assertEqual(response.status_code, 302)
        issuer.assert_not_called()
        self.assertIn(
            ("error", "La rectificaci\u00f3n parcial todav\u00eda no est\u00e1 soportada."),
            self._flashes(),
        )

    def test_emission_delegates_only_to_the_total_rectification_service(self):
        corrective = Invoices(
            invoice_number="R2026000001",
            invoice_type="corrective",
            original_invoice_id=self.ordinary_id,
            rectification_type="differences",
            rectification_reason="invoice_error",
            rectification_aeat_type="R4",
            amount=-1.21,
            client_name="Cliente Test",
            client_address="Calle Test 1",
            client_cif="00000000T",
            order_details=[],
            invoice_snapshot={"schema_version": 3},
            invoice_snapshot_schema_version=3,
            invoice_snapshot_hash="rectification-hash",
            issued_at=datetime(2026, 8, 8, 12, 0, 0),
        )

        with patch(
            "api.admin.issue_total_rectification_for_invoice",
            return_value=IssuedInvoiceResult(
                invoice=corrective,
                invoice_number="R2026000001",
                created=True,
            ),
        ) as issuer:
            response = self.client.post(
                self._url(self.ordinary_id),
                headers=self._auth_header(),
                data={"rectification_reason": "invoice_error", "rectification_aeat_type": "R4"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("details", response.headers["Location"])
        self.assertEqual(issuer.call_args.kwargs["original_invoice_id"], self.ordinary_id)
        self.assertEqual(issuer.call_args.kwargs["rectification_type"], "differences")
        self.assertEqual(issuer.call_args.kwargs["rectification_reason"], "invoice_error")
        self.assertEqual(issuer.call_args.kwargs["rectification_aeat_type"], "R4")
        self.assertEqual(issuer.call_args.kwargs["rectification_scope"], "total")
        self.assertNotIn("partial", str(issuer.call_args))

    def test_existing_rectification_is_reused_without_calling_the_service(self):
        with self.app.app_context():
            corrective = Invoices(
                invoice_number="R2026000001",
                invoice_type="corrective",
                original_invoice_id=self.ordinary_id,
                rectification_type="differences",
                rectification_reason="invoice_error",
                rectification_aeat_type="R4",
                amount=-1.21,
                client_name="Cliente Test",
                client_address="Calle Test 1",
                client_cif="00000000T",
                order_details=[],
                invoice_snapshot={
                    "schema_version": 3,
                    "operation": {"rectification": {"rectification_scope": "total", "aeat_type": "R4"}},
                },
                invoice_snapshot_schema_version=3,
                invoice_snapshot_hash="rectification-hash",
                issued_at=datetime(2026, 8, 8, 12, 0, 0),
            )
            db.session.add(corrective)
            db.session.commit()
            corrective_id = corrective.id

        with patch("api.admin.issue_total_rectification_for_invoice") as issuer:
            response = self.client.post(
                self._url(self.ordinary_id),
                headers=self._auth_header(),
                data={"rectification_reason": "invoice_error", "rectification_aeat_type": "R4"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn(str(corrective_id), response.headers["Location"])
        issuer.assert_not_called()
        self.assertIn(("info", "La factura ya tiene la rectificativa R2026000001."), self._flashes())

    def test_incompatible_existing_rectification_is_reported_without_calling_the_service(self):
        with self.app.app_context():
            corrective = Invoices(
                invoice_number="R2026000001",
                invoice_type="corrective",
                original_invoice_id=self.ordinary_id,
                rectification_type="differences",
                rectification_reason="return",
                rectification_aeat_type="R4",
                amount=-1.21,
                client_name="Cliente Test",
                client_address="Calle Test 1",
                client_cif="00000000T",
                order_details=[],
                invoice_snapshot={
                    "schema_version": 3,
                    "operation": {"rectification": {"rectification_scope": "total"}},
                },
                invoice_snapshot_schema_version=3,
                invoice_snapshot_hash="rectification-hash",
                issued_at=datetime(2026, 8, 8, 12, 0, 0),
            )
            db.session.add(corrective)
            db.session.commit()

        with patch("api.admin.issue_total_rectification_for_invoice") as issuer:
            response = self.client.post(
                self._url(self.ordinary_id),
                headers=self._auth_header(),
                data={"rectification_reason": "invoice_error", "rectification_aeat_type": "R4"},
            )

        self.assertEqual(response.status_code, 302)
        issuer.assert_not_called()
        self.assertIn(
            ("error", "La factura ya tiene una rectificativa incompatible."),
            self._flashes(),
        )

    def test_detail_formatter_links_both_sides_of_the_rectification(self):
        with self.app.app_context():
            original = db.session.get(Invoices, self.ordinary_id)
            corrective = Invoices(
                invoice_number="R2026000001",
                invoice_type="corrective",
                original_invoice_id=original.id,
                rectification_type="differences",
                rectification_reason="invoice_error",
                rectification_aeat_type="R4",
                amount=-1.21,
                client_name="Cliente Test",
                client_address="Calle Test 1",
                client_cif="00000000T",
                order_details=[],
                invoice_snapshot={"schema_version": 3},
                invoice_snapshot_schema_version=3,
                invoice_snapshot_hash="rectification-hash",
                issued_at=datetime(2026, 8, 8, 12, 0, 0),
            )
            db.session.add(corrective)
            db.session.commit()

            view = next(
                view for view in self.admin._views
                if isinstance(view, admin_module.InvoiceAdminView)
            )
            with self.app.test_request_context("/admin/invoices/details/"):
                original_markup = admin_module._format_admin_invoice_type_detail(view, None, original, "invoice_type")
                corrective_markup = admin_module._format_admin_invoice_type_detail(view, None, corrective, "invoice_type")

        self.assertIn("Ver rectificativa R2026000001", str(original_markup))
        self.assertIn("Ver factura original F2026000001", str(corrective_markup))
        self.assertIn("Tipo fiscal AEAT: R4", str(corrective_markup))

    def test_legacy_rectification_detail_marks_missing_aeat_classification(self):
        with self.app.app_context():
            original = db.session.get(Invoices, self.ordinary_id)
            corrective = Invoices(
                invoice_number="R2026000001",
                invoice_type="corrective",
                original_invoice_id=original.id,
                rectification_type="differences",
                rectification_reason="invoice_error",
                amount=-1.21,
                client_name="Cliente Test",
                client_address="Calle Test 1",
                client_cif="00000000T",
                order_details=[],
                invoice_snapshot={"schema_version": 3},
                invoice_snapshot_schema_version=3,
                invoice_snapshot_hash="rectification-hash",
                issued_at=datetime(2026, 8, 8, 12, 0, 0),
            )
            db.session.add(corrective)
            db.session.commit()

            view = next(view for view in self.admin._views if isinstance(view, admin_module.InvoiceAdminView))
            with self.app.test_request_context("/admin/invoices/details/"):
                markup = admin_module._format_admin_invoice_type_detail(view, None, corrective, "invoice_type")

        self.assertIn("Sin clasificación AEAT", str(markup))


if __name__ == "__main__":
    unittest.main()

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
    from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash  # noqa: E402
    from api.models import Invoices, InvoiceFiscalSubmission, VeriFactuRecord, db  # noqa: E402
    from api.verifactu_record_service import VeriFactuRecordValidationError  # noqa: E402


SNAPSHOT = {
    "schema_version": 1,
    "issuer": {
        "legal_name": "MetalWolft S.L.",
        "tax_id": "B00000000",
        "country_code": "ES",
    },
    "customer": {
        "legal_name": "Cliente Test",
        "tax_id": "00000000T",
        "country_code": "ES",
    },
    "operation": {
        "invoice_type": "ordinary",
        "currency": "EUR",
        "issue_date": "2026-07-19",
        "operation_date": "2026-07-19",
        "order_id": 42,
    },
    "payment": {"provider": "stripe"},
    "lines": [
        {
            "line_number": 1,
            "description": "Reja",
            "quantity": "1",
            "tax_rate": "21.00",
            "tax_base": "100.00",
            "tax_amount": "21.00",
            "total_amount": "121.00",
        }
    ],
    "totals": {
        "tax_base": "100.00",
        "tax_amount": "21.00",
        "total_amount": "121.00",
    },
}


@unittest.skipUnless(HAS_FLASK_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminInvoiceVeriFactuHttpTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"

        self.app = Flask(__name__)
        self.app.config.update(
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            VERIFACTU_SYSTEM_ID="metalwolft-dev-01",
            VERIFACTU_SYSTEM_NAME="MetalWolft",
            VERIFACTU_SYSTEM_VERSION="2026.7",
        )
        db.init_app(self.app)

        admin = Admin(self.app, url="/admin")
        admin.add_view(admin_module.InvoiceAdminView(Invoices, db.session))
        admin.add_view(admin_module.VeriFactuRecordAdminView(VeriFactuRecord, db.session, name="VeriFactu"))

        with self.app.app_context():
            db.create_all()
            self.invoice = self._create_invoice("F2026000003")
            db.session.commit()
            self.invoice_id = self.invoice.id

        self.client = self.app.test_client()
        self.generate_rule = self._rule(".generate_verifactu_record")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_invoice(self, invoice_number):
        snapshot = copy.deepcopy(SNAPSHOT)
        invoice = Invoices(
            invoice_number=invoice_number,
            order_id=42,
            invoice_type="ordinary",
            pdf_path=None,
            amount=121.00,
            client_name="Cliente Test",
            client_address="Calle Test 1",
            client_cif="00000000T",
            order_details=[],
            invoice_snapshot=snapshot,
            invoice_snapshot_hash=calculate_invoice_snapshot_hash(snapshot),
            invoice_snapshot_schema_version=1,
            issued_at=datetime(2026, 7, 19, 10, 30, tzinfo=timezone.utc),
        )
        db.session.add(invoice)
        return invoice

    def _rule(self, endpoint_suffix):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(endpoint_suffix):
                return rule
        raise AssertionError(f"Flask Admin route {endpoint_suffix} was not registered")

    def _url(self, invoice_id):
        return self.generate_rule.rule.replace("<int:invoice_id>", str(invoice_id))

    def _auth_header(self, username="admin", password="secret"):
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _flashes(self):
        with self.client.session_transaction() as session:
            return session.get("_flashes", [])

    def _invoice(self):
        return db.session.get(Invoices, self.invoice_id)

    def _formatter_html(self, invoice):
        class FakeView:
            session = db.session

            def get_url(self, endpoint, **kwargs):
                if endpoint == ".generate_verifactu_record":
                    return f"/admin/invoices/generate-verifactu-record/{kwargs['invoice_id']}"
                if endpoint == "verifacturecord.details_view":
                    return f"/admin/verifacturecord/details/?id={kwargs['id']}"
                raise AssertionError(f"Unexpected endpoint: {endpoint}")

        return str(admin_module._format_admin_invoice_verifactu_detail(
            FakeView(),
            None,
            invoice,
            "verifactu_records",
        ))

    def test_detail_without_record_shows_generate_button(self):
        with self.app.app_context():
            html = self._formatter_html(self._invoice())

        self.assertIn("No generado", html)
        self.assertIn("GENERAR REGISTRO VERIFACTU", html)
        self.assertIn("method=\"post\"", html)

    def test_detail_with_generated_record_hides_create_button(self):
        self.client.post(self._url(self.invoice_id), headers=self._auth_header())

        with self.app.app_context():
            record = db.session.query(VeriFactuRecord).one()
            html = self._formatter_html(self._invoice())

        self.assertEqual(record.status, VeriFactuRecord.STATUS_BUILT)
        self.assertIn("Generado", html)
        self.assertIn(f"ID registro: {record.id}", html)
        self.assertIn(f"Ver registro #{record.id}", html)
        self.assertNotIn("GENERAR REGISTRO VERIFACTU", html)

    def test_detail_with_ready_record_hides_create_button_and_shows_chain_data(self):
        self.client.post(self._url(self.invoice_id), headers=self._auth_header())

        with self.app.app_context():
            record = db.session.query(VeriFactuRecord).one()
            record.status = VeriFactuRecord.STATUS_READY
            record.chain_key = "B00000000|VERI*FACTU|B00000000|metalwolft-dev-01|DEV-001"
            record.chain_sequence = 7
            record.fingerprint = "ABCDEF1234567890"
            record.fingerprint_status = "CALCULATED"
            record.is_first_record = True
            db.session.commit()
            html = self._formatter_html(self._invoice())

        self.assertIn("Preparado", html)
        self.assertIn("Secuencia: 7", html)
        self.assertIn("Huella: ABCDEF123456...", html)
        self.assertNotIn("GENERAR REGISTRO VERIFACTU", html)

    def test_post_creates_single_generated_verifactu_record(self):
        with patch("api.admin.prepare_verifactu_record_for_submission") as prepare:
            response = self.client.post(self._url(self.invoice_id), headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        prepare.assert_not_called()
        with self.app.app_context():
            records = db.session.query(VeriFactuRecord).all()
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record.invoice_id, self.invoice_id)
            self.assertEqual(record.status, VeriFactuRecord.STATUS_BUILT)
            self.assertIsNone(record.fingerprint)
            self.assertIsNone(record.chain_key)
            self.assertIsNone(record.chain_sequence)
            self.assertIsNone(record.official_payload)
            self.assertEqual(db.session.query(InvoiceFiscalSubmission).count(), 0)

        self.assertIn(("success", "Registro VeriFactu generado correctamente."), self._flashes())

    def test_post_repeated_is_idempotent_and_does_not_mutate_existing_record(self):
        first = self.client.post(self._url(self.invoice_id), headers=self._auth_header())
        with self.app.app_context():
            record = db.session.query(VeriFactuRecord).one()
            before = {
                "id": record.id,
                "status": record.status,
                "record_payload": copy.deepcopy(record.record_payload),
                "record_payload_hash": record.record_payload_hash,
                "created_at": record.created_at,
                "fingerprint": record.fingerprint,
            }

        second = self.client.post(self._url(self.invoice_id), headers=self._auth_header())

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        with self.app.app_context():
            records = db.session.query(VeriFactuRecord).all()
            self.assertEqual(len(records), 1)
            record = records[0]
            for field, expected in before.items():
                self.assertEqual(getattr(record, field), expected)

        self.assertIn(("success", "La factura ya tiene un registro VeriFactu generado."), self._flashes())

    def test_post_missing_invoice_redirects_without_generation_or_commit(self):
        with (
            patch("api.admin.create_verifactu_registration_record") as creator,
            patch("api.admin.db.session.commit") as commit,
            patch("api.admin.db.session.rollback") as rollback,
        ):
            response = self.client.post(self._url(999999), headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        creator.assert_not_called()
        commit.assert_not_called()
        rollback.assert_not_called()
        self.assertIn(("error", "Factura no encontrada."), self._flashes())

    def test_post_rolls_back_service_error(self):
        with (
            patch(
                "api.admin.create_verifactu_registration_record",
                side_effect=VeriFactuRecordValidationError("snapshot incompleto"),
            ),
            patch("api.admin.db.session.commit") as commit,
            patch("api.admin.db.session.rollback") as rollback,
        ):
            response = self.client.post(self._url(self.invoice_id), headers=self._auth_header())

        self.assertEqual(response.status_code, 302)
        commit.assert_not_called()
        rollback.assert_called_once()
        self.assertIn(
            ("error", "No se puede generar el registro VeriFactu: snapshot incompleto"),
            self._flashes(),
        )

    def test_post_does_not_modify_invoice_or_create_external_effects(self):
        with self.app.app_context():
            invoice = self._invoice()
            before = {
                "invoice_number": invoice.invoice_number,
                "issued_at": invoice.issued_at,
                "invoice_snapshot": copy.deepcopy(invoice.invoice_snapshot),
                "invoice_snapshot_hash": invoice.invoice_snapshot_hash,
                "amount": invoice.amount,
                "pdf_path": invoice.pdf_path,
            }

        self.client.post(self._url(self.invoice_id), headers=self._auth_header())

        with self.app.app_context():
            invoice = self._invoice()
            for field, expected in before.items():
                self.assertEqual(getattr(invoice, field), expected)
            record = db.session.query(VeriFactuRecord).one()
            self.assertEqual(record.status, VeriFactuRecord.STATUS_BUILT)
            self.assertIsNone(record.fingerprint)
            self.assertEqual(db.session.query(InvoiceFiscalSubmission).count(), 0)


if __name__ == "__main__":
    unittest.main()

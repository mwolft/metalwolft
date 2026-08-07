import ast
import base64
import copy
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ADMIN_PATH = ROOT_DIR / "src/api/admin.py"
MODELS_PATH = ROOT_DIR / "src/api/models.py"
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
    from api.models import (  # noqa: E402
        Invoices,
        InvoiceFiscalSubmission,
        VeriFactuRecord,
        db,
    )
    from api.verifactu_record_service import create_verifactu_registration_record  # noqa: E402


EXPECTED_LIST_COLUMNS = [
    "id",
    "invoice_id",
    "record_type",
    "status",
    "invoice_number",
    "invoice_snapshot_hash",
    "record_payload_hash",
    "fingerprint_status",
    "fingerprint",
    "chain_sequence",
    "previous_record_id",
    "system_id",
    "software_name",
    "software_version",
    "ready_at",
    "created_at",
]

EXPECTED_DETAIL_COLUMNS = [
    "id",
    "invoice_id",
    "provider",
    "mode",
    "record_type",
    "status",
    "schema_version",
    "invoice_number",
    "invoice_issued_at",
    "invoice_snapshot_hash",
    "record_payload_hash",
    "official_payload_schema_version",
    "chain_key",
    "chain_sequence",
    "fingerprint",
    "fingerprint_algorithm",
    "fingerprint_status",
    "fingerprint_input",
    "fingerprint_calculated_at",
    "previous_record_id",
    "previous_fingerprint",
    "is_first_record",
    "system_id",
    "software_name",
    "software_version",
    "installation_id",
    "producer_name",
    "producer_tax_id",
    "generation_timestamp",
    "generation_timezone",
    "ready_at",
    "issuer_tax_id",
    "recipient_tax_id",
    "total_amount",
    "currency",
    "created_at",
    "updated_at",
]


SNAPSHOT = {
    "schema_version": 1,
    "issuer": {
        "legal_name": "MetalWolft S.L.",
        "tax_id": "B00000000",
        "country_code": "ES",
    },
    "customer": {
        "legal_name": "Cliente VeriFactu",
        "tax_id": "00000000T",
        "country_code": "ES",
    },
    "operation": {
        "invoice_type": "ordinary",
        "issue_date": "2026-07-19",
        "operation_date": "2026-07-19",
        "currency": "EUR",
        "order_id": 42,
        "order_locator": "MW-42",
    },
    "payment": {"provider": "stripe", "status": "paid"},
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


def source(path):
    return path.read_text(encoding="utf-8")


def module_ast(path):
    return ast.parse(source(path))


def class_node(path, class_name):
    for node in module_ast(path).body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"{class_name} not found")


def assignment(node, name):
    for statement in node.body:
        if isinstance(statement, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in statement.targets):
                return statement.value
    raise AssertionError(f"{name} assignment not found")


def literal_assignment(node, name):
    return ast.literal_eval(assignment(node, name))


def class_source(class_name):
    text = source(ADMIN_PATH)
    start = text.index(f"class {class_name}")
    next_class = text.find("\nclass ", start + 1)
    marker = text.find("\n# ==========================", start + 1)
    endings = [position for position in (next_class, marker) if position != -1]
    return text[start:min(endings)] if endings else text[start:]


def verifactu_fields():
    fields = set()
    for statement in class_node(MODELS_PATH, "VeriFactuRecord").body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    fields.add(target.id)
    return fields


class FlaskAdminVeriFactuRecordViewTest(unittest.TestCase):
    def setUp(self):
        self.view = class_node(ADMIN_PATH, "VeriFactuRecordAdminView")
        self.view_source = class_source("VeriFactuRecordAdminView")

    def test_view_is_read_only_with_details_enabled(self):
        self.assertIs(literal_assignment(self.view, "can_create"), False)
        self.assertIs(literal_assignment(self.view, "can_edit"), False)
        self.assertIs(literal_assignment(self.view, "can_delete"), False)
        self.assertIs(literal_assignment(self.view, "can_view_details"), True)
        self.assertNotIn("column_editable_list", self.view_source)

    def test_visible_columns_are_safe_and_do_not_expose_raw_payloads(self):
        self.assertEqual(literal_assignment(self.view, "column_list"), EXPECTED_LIST_COLUMNS)
        self.assertEqual(literal_assignment(self.view, "column_details_list"), EXPECTED_DETAIL_COLUMNS)

        exposed = set(EXPECTED_LIST_COLUMNS + EXPECTED_DETAIL_COLUMNS)
        self.assertNotIn("record_payload", exposed)
        self.assertNotIn("official_payload", exposed)
        self.assertNotIn("invoice", exposed)

    def test_configured_columns_exist_on_model(self):
        configured = set(EXPECTED_LIST_COLUMNS + EXPECTED_DETAIL_COLUMNS)
        configured.update(literal_assignment(self.view, "column_searchable_list"))
        configured.update(literal_assignment(self.view, "column_filters"))

        self.assertLessEqual(configured, verifactu_fields())

    def test_setup_admin_registers_read_only_view(self):
        admin_source = source(ADMIN_PATH)

        self.assertIn("VeriFactuRecord", admin_source)
        self.assertIn("VeriFactuRecordAdminView(VeriFactuRecord, db.session, name=\"VeriFactu\")", admin_source)

    def test_view_only_exposes_the_manual_prepare_action(self):
        self.assertIn("@action(", self.view_source)
        self.assertIn("action_prepare_verifactu_records", self.view_source)
        self.assertIn("prepare_verifactu_record_for_submission(", self.view_source)
        self.assertIn("verifactu_system_identity_from_config(current_app.config)", self.view_source)
        self.assertIn("VeriFactuRecordConcurrencyError", self.view_source)
        self.assertIn("self.session.commit()", self.view_source)
        self.assertIn("self.session.rollback()", self.view_source)
        self.assertIn("selected_ids = list(ids or [])", self.view_source)
        self.assertIn("return redirect(self.get_url(\".index_view\"))", self.view_source)
        self.assertIn("record.status == VeriFactuRecord.STATUS_READY", self.view_source)
        self.assertIn("record.status != VeriFactuRecord.STATUS_BUILT", self.view_source)

        for forbidden in (
            "@expose(",
            "create_verifactu",
            "create_pending_submission",
            "mark_sent",
            "mark_accepted",
            "mark_rejected",
            "mark_failed",
            "send_invoice_email",
            "generate_invoice_pdf",
            "issue_invoice_for_order",
        ):
            self.assertNotIn(forbidden, self.view_source)


@unittest.skipUnless(HAS_FLASK_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminVeriFactuRecordActionHttpTest(unittest.TestCase):
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
            VERIFACTU_INSTALLATION_ID="DEV-001",
            VERIFACTU_PRODUCER_NAME="MetalWolft S.L.",
            VERIFACTU_PRODUCER_TAX_ID="B00000000",
        )
        db.init_app(self.app)

        admin = Admin(self.app, url="/admin")
        admin.add_view(admin_module.VeriFactuRecordAdminView(VeriFactuRecord, db.session, name="VeriFactu"))

        with self.app.app_context():
            db.create_all()
            self.record_id = self._create_built_record("F2026000100").id
            db.session.commit()

        self.client = self.app.test_client()
        self.action_url = self._rule(".action_view").rule

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _rule(self, endpoint_suffix):
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(endpoint_suffix):
                return rule
        raise AssertionError(f"Flask Admin route {endpoint_suffix} was not registered")

    def _auth_header(self, username="admin", password="secret"):
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _flashes(self):
        with self.client.session_transaction() as session:
            return session.get("_flashes", [])

    def _post_prepare_action(self, rowids):
        data = {
            "action": "prepare_verifactu_records",
            "url": "/admin/verifacturecord/",
        }
        if rowids:
            data["rowid"] = [str(rowid) for rowid in rowids]
        return self.client.post(self.action_url, data=data, headers=self._auth_header())

    def _create_invoice(self, invoice_number):
        snapshot = copy.deepcopy(SNAPSHOT)
        invoice = Invoices(
            invoice_number=invoice_number,
            invoice_type="ordinary",
            amount=121.00,
            client_name="Cliente VeriFactu",
            client_address="Calle Test 1",
            client_cif="00000000T",
            order_details=[],
            invoice_snapshot=snapshot,
            invoice_snapshot_hash=calculate_invoice_snapshot_hash(snapshot),
            invoice_snapshot_schema_version=1,
            issued_at=datetime(2026, 7, 19, 10, 30, tzinfo=timezone.utc),
        )
        db.session.add(invoice)
        db.session.flush()
        return invoice

    def _create_built_record(self, invoice_number):
        invoice = self._create_invoice(invoice_number)
        result = create_verifactu_registration_record(
            invoice,
            db_session=db.session,
            system_id=self.app.config["VERIFACTU_SYSTEM_ID"],
            software_name=self.app.config["VERIFACTU_SYSTEM_NAME"],
            software_version=self.app.config["VERIFACTU_SYSTEM_VERSION"],
        )
        db.session.flush()
        return result.record

    def _record(self, record_id=None):
        return db.session.get(VeriFactuRecord, record_id or self.record_id)

    def test_action_receives_selected_ids_and_redirects_to_index(self):
        prepared_record_ids = []

        def capture_prepared_record(record, **_kwargs):
            prepared_record_ids.append(record.id)
            return SimpleNamespace(prepared=True)

        with patch(
            "api.admin.prepare_verifactu_record_for_submission",
            side_effect=capture_prepared_record,
        ) as prepare:
            response = self._post_prepare_action([self.record_id])

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/verifacturecord/", response.headers["Location"])
        prepare.assert_called_once()
        self.assertEqual(prepared_record_ids, [self.record_id])

    def test_action_prepares_built_record_and_assigns_chain_data(self):
        with patch.object(admin_module.db.session, "commit", wraps=admin_module.db.session.commit) as commit:
            response = self._post_prepare_action([self.record_id])

        self.assertEqual(response.status_code, 302)
        commit.assert_called_once()
        with self.app.app_context():
            record = self._record()
            self.assertEqual(record.status, VeriFactuRecord.STATUS_READY)
            self.assertEqual(record.chain_sequence, 1)
            self.assertIsNotNone(record.fingerprint)
            self.assertEqual(record.fingerprint_status, "CALCULATED")
            self.assertIs(record.is_first_record, True)
            self.assertEqual(db.session.query(InvoiceFiscalSubmission).count(), 0)
            self.assertIsNone(record.__dict__.get("xml"))

        self.assertIn(("success", "Registros VeriFactu preparados: 1."), self._flashes())

    def test_ready_record_is_idempotent_and_not_recalculated(self):
        self._post_prepare_action([self.record_id])
        with self.app.app_context():
            record = self._record()
            before = {
                "status": record.status,
                "chain_sequence": record.chain_sequence,
                "fingerprint": record.fingerprint,
                "fingerprint_status": record.fingerprint_status,
                "is_first_record": record.is_first_record,
                "ready_at": record.ready_at,
            }

        response = self._post_prepare_action([self.record_id])

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            record = self._record()
            for field, expected in before.items():
                self.assertEqual(getattr(record, field), expected)

        self.assertIn(("warning", "Registros VeriFactu preparados: 0. Ya preparados: 1."), self._flashes())

    def test_invalid_status_is_skipped_without_modification(self):
        with self.app.app_context():
            record = self._record()
            record.status = "FAILED"
            db.session.commit()

        response = self._post_prepare_action([self.record_id])

        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            record = self._record()
            self.assertEqual(record.status, "FAILED")
            self.assertIsNone(record.fingerprint)
            self.assertIsNone(record.chain_sequence)

        self.assertIn(("warning", "Registros VeriFactu preparados: 0. Omitidos por estado no preparable: 1."), self._flashes())

    def test_missing_and_empty_selection_show_clear_flash(self):
        empty_response = self._post_prepare_action([])
        missing_response = self._post_prepare_action([999999])

        self.assertEqual(empty_response.status_code, 302)
        self.assertEqual(missing_response.status_code, 302)
        self.assertIn(("warning", "Selecciona al menos un registro VeriFactu."), self._flashes())
        self.assertIn(("warning", "Registros VeriFactu preparados: 0. No encontrados: 1."), self._flashes())

    def test_service_error_rolls_back_and_flashes_error(self):
        with (
            patch(
                "api.admin.prepare_verifactu_record_for_submission",
                side_effect=admin_module.VeriFactuRecordValidationError("payload incompleto"),
            ),
            patch.object(admin_module.db.session, "rollback", wraps=admin_module.db.session.rollback) as rollback,
        ):
            response = self._post_prepare_action([self.record_id])

        self.assertEqual(response.status_code, 302)
        rollback.assert_called_once()
        with self.app.app_context():
            record = self._record()
            self.assertEqual(record.status, VeriFactuRecord.STATUS_BUILT)
            self.assertIsNone(record.fingerprint)

        self.assertIn(("error", "payload incompleto"), self._flashes())

    def test_action_has_no_xml_submission_or_transmission_side_effects(self):
        with (
            patch("api.admin.create_pending_submission", create=True) as create_pending_submission,
            patch("api.admin.mark_sent", create=True) as mark_sent,
        ):
            response = self._post_prepare_action([self.record_id])

        self.assertEqual(response.status_code, 302)
        create_pending_submission.assert_not_called()
        mark_sent.assert_not_called()
        with self.app.app_context():
            self.assertEqual(db.session.query(InvoiceFiscalSubmission).count(), 0)


if __name__ == "__main__":
    unittest.main()

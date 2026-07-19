import ast
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ADMIN_PATH = ROOT_DIR / "src/api/admin.py"
MODELS_PATH = ROOT_DIR / "src/api/models.py"


EXPECTED_LIST_COLUMNS = [
    "id",
    "invoice_id",
    "record_type",
    "status",
    "invoice_number",
    "invoice_snapshot_hash",
    "record_payload_hash",
    "fingerprint_status",
    "system_id",
    "software_name",
    "software_version",
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
    "fingerprint",
    "fingerprint_algorithm",
    "fingerprint_status",
    "system_id",
    "software_name",
    "software_version",
    "issuer_tax_id",
    "recipient_tax_id",
    "total_amount",
    "currency",
    "created_at",
    "updated_at",
]


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

    def test_visible_columns_are_safe_and_do_not_expose_payload(self):
        self.assertEqual(literal_assignment(self.view, "column_list"), EXPECTED_LIST_COLUMNS)
        self.assertEqual(literal_assignment(self.view, "column_details_list"), EXPECTED_DETAIL_COLUMNS)

        exposed = set(EXPECTED_LIST_COLUMNS + EXPECTED_DETAIL_COLUMNS)
        self.assertNotIn("record_payload", exposed)
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

    def test_view_has_no_actions_or_mutating_domain_calls(self):
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
            "commit(",
            "rollback(",
        ):
            self.assertNotIn(forbidden, self.view_source)


if __name__ == "__main__":
    unittest.main()

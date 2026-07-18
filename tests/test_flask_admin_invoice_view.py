import ast
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ADMIN_PATH = ROOT_DIR / "src/api/admin.py"
MODELS_PATH = ROOT_DIR / "src/api/models.py"

LIST_COLUMNS = [
    "id",
    "invoice_number",
    "invoice_type",
    "order_id",
    "client_name",
    "client_cif",
    "amount",
    "created_at",
    "issued_at",
    "pdf_path",
    "email_status",
    "invoice_snapshot_schema_version",
]

DETAIL_COLUMNS = [
    "id",
    "invoice_number",
    "invoice_type",
    "order_id",
    "client_name",
    "client_address",
    "client_cif",
    "amount",
    "created_at",
    "issued_at",
    "pdf_path",
    "email_status",
    "invoice_snapshot_schema_version",
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


def dict_keys(node, name):
    value = assignment(node, name)
    if not isinstance(value, ast.Dict):
        raise AssertionError(f"{name} is not a dict")
    return [
        key.value
        for key in value.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    ]


def class_source(class_name):
    text = source(ADMIN_PATH)
    start = text.index(f"class {class_name}")
    end = text.index("# ========================== SETUP ADMIN", start)
    return text[start:end]


def function_source(function_name):
    text = source(ADMIN_PATH)
    for node in ast.walk(module_ast(ADMIN_PATH)):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(text, node)
    raise AssertionError(f"{function_name} not found")


def invoice_fields():
    fields = set()
    for statement in class_node(MODELS_PATH, "Invoices").body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    fields.add(target.id)
    return fields


class FlaskAdminInvoiceViewTest(unittest.TestCase):
    def setUp(self):
        self.view = class_node(ADMIN_PATH, "InvoiceAdminView")
        self.view_source = class_source("InvoiceAdminView")

    def test_view_is_read_only_with_details_enabled(self):
        self.assertIs(literal_assignment(self.view, "can_create"), False)
        self.assertIs(literal_assignment(self.view, "can_edit"), False)
        self.assertIs(literal_assignment(self.view, "can_delete"), False)
        self.assertIs(literal_assignment(self.view, "can_view_details"), True)
        self.assertNotIn("column_editable_list", self.view_source)

    def test_list_detail_search_filters_and_sorting_contract(self):
        self.assertEqual(literal_assignment(self.view, "column_list"), LIST_COLUMNS)
        self.assertEqual(literal_assignment(self.view, "column_details_list"), DETAIL_COLUMNS)
        self.assertEqual(
            literal_assignment(self.view, "column_searchable_list"),
            ["invoice_number", "client_name", "client_cif"],
        )
        self.assertEqual(
            literal_assignment(self.view, "column_filters"),
            [
                "invoice_type",
                "email_status",
                "created_at",
                "issued_at",
                "invoice_snapshot_schema_version",
            ],
        )
        self.assertEqual(literal_assignment(self.view, "column_default_sort"), ("created_at", True))

    def test_configured_columns_are_direct_invoice_fields(self):
        configured = set(LIST_COLUMNS + DETAIL_COLUMNS)
        configured.update(literal_assignment(self.view, "column_searchable_list"))
        configured.update(literal_assignment(self.view, "column_filters"))

        self.assertLessEqual(configured, invoice_fields())

    def test_detail_and_list_do_not_expose_sensitive_invoice_payloads(self):
        exposed = set(LIST_COLUMNS + DETAIL_COLUMNS)

        for field in (
            "invoice_snapshot",
            "invoice_snapshot_hash",
            "order_details",
            "email_last_error",
            "issued_by",
        ):
            self.assertNotIn(field, exposed)

    def test_labels_and_formatters_cover_visible_columns(self):
        labels = set(dict_keys(self.view, "column_labels"))
        formatters = set(dict_keys(self.view, "column_formatters"))
        detail_formatters = set(dict_keys(self.view, "column_formatters_detail"))

        self.assertLessEqual(set(LIST_COLUMNS), labels)
        self.assertIn("pdf_path", formatters)
        self.assertIn("pdf_path", detail_formatters)
        self.assertIn("amount", formatters)
        self.assertIn("created_at", formatters)
        self.assertIn("issued_at", formatters)

    def test_no_legacy_number_generation_or_forms_remain(self):
        self.assertNotIn("create_form", self.view_source)
        self.assertNotIn("generate_next_invoice_number", self.view_source)
        self.assertNotIn("form_columns", self.view_source)
        self.assertNotIn("form_extra_fields", self.view_source)

    def test_pdf_indicator_does_not_touch_the_filesystem(self):
        pdf_formatter = function_source("_format_admin_invoice_pdf_available")

        self.assertIn("getattr(model, name", pdf_formatter)
        self.assertIn("view.get_url", pdf_formatter)
        self.assertIn("Descargar PDF", pdf_formatter)
        self.assertNotIn("pdf_path", pdf_formatter)
        for unsafe_access in ("os.path", "exists", "open(", "stat("):
            self.assertNotIn(unsafe_access, pdf_formatter)

    def test_admin_download_route_is_read_only_and_delegates_to_safe_resolver(self):
        download_source = function_source("download_pdf")

        self.assertIn("@expose('/download-pdf/<int:invoice_id>')", self.view_source)
        self.assertIn("self.session.get(Invoices, invoice_id)", download_source)
        self.assertIn("resolve_invoice_pdf_download(", download_source)
        self.assertIn('current_app.config.get("INVOICE_FOLDER")', download_source)
        self.assertIn("send_file(", download_source)

        for forbidden_call in (
            "generate_invoice_pdf",
            "_regenerate_invoice_pdf_to_storage",
            "render_original_order_invoice_pdf",
            "create_accounting_entry",
            "send_invoice_email",
            "create_pending_submission",
            "run_invoice_workflow",
            "db.session.commit",
            "db.session.rollback",
            "self.session.commit",
            "self.session.rollback",
        ):
            self.assertNotIn(forbidden_call, download_source)

    def test_pdf_generation_action_is_detail_only_post_form(self):
        detail_formatter = function_source("_format_admin_invoice_pdf_detail")

        self.assertIn("view.get_url(\".generate_pdf\", invoice_id=model.id)", detail_formatter)
        self.assertIn('method="post"', detail_formatter)
        self.assertIn("Generar PDF", detail_formatter)
        self.assertIn("Regenerar PDF", detail_formatter)
        self.assertIn("¿Seguro que quieres regenerar el PDF existente?", detail_formatter)
        self.assertIn("button_label", detail_formatter)
        self.assertNotIn('name="regenerate"', detail_formatter)
        self.assertNotIn('name="pdf_path"', detail_formatter)
        self.assertNotIn('name="filename"', detail_formatter)
        self.assertNotIn('name="output_dir"', detail_formatter)

    def test_pdf_generation_success_messages_are_contextual(self):
        message_helper = function_source("_admin_invoice_pdf_success_message")

        self.assertIn("El PDF ya estaba generado.", message_helper)
        self.assertIn("PDF regenerado correctamente.", message_helper)
        self.assertIn("PDF generado correctamente.", message_helper)

    def test_pdf_generation_route_delegates_to_v2_service_and_controls_transaction(self):
        route_source = function_source("generate_pdf")

        self.assertIn("@expose('/generate-pdf/<int:invoice_id>', methods=['POST'])", self.view_source)
        self.assertIn("self.session.get(Invoices, invoice_id)", route_source)
        self.assertIn("regenerate = bool(invoice.pdf_path)", route_source)
        self.assertIn("previous_pdf_path = invoice.pdf_path", route_source)
        self.assertIn("generate_invoice_pdf(", route_source)
        self.assertIn("regenerate=regenerate", route_source)
        self.assertIn("self.session.commit()", route_source)
        self.assertIn("self.session.rollback()", route_source)
        self.assertIn("flash(", route_source)
        self.assertIn("redirect(self.get_url(\".details_view\", id=invoice.id))", route_source)
        self.assertNotIn("request.get_json", route_source)
        self.assertNotIn("request.form", route_source)
        self.assertNotIn("output_dir=", route_source)
        self.assertNotIn("db.session.commit", route_source)
        self.assertNotIn("db.session.rollback", route_source)

    def test_pdf_generation_route_does_not_touch_other_documental_flows(self):
        route_source = function_source("generate_pdf")

        for forbidden_call in (
            "issue_invoice_for_order",
            "acquire_next_invoice_number",
            "generate_next_invoice_number",
            "_regenerate_invoice_pdf_to_storage",
            "render_original_order_invoice_pdf",
            "create_accounting_entry",
            "send_invoice_email",
            "create_pending_submission",
            "run_invoice_workflow",
            "CheckoutSessions",
            "Orders",
            "OrderDetails",
        ):
            self.assertNotIn(forbidden_call, route_source)

        for forbidden_assignment in (
            "invoice.invoice_number =",
            "invoice.issued_at =",
            "invoice.invoice_type =",
            "invoice.invoice_snapshot =",
            "invoice.invoice_snapshot_hash =",
            "invoice.amount =",
            "invoice.client_name =",
            "invoice.client_address =",
            "invoice.client_cif =",
            "invoice.order_details =",
            "invoice.order_id =",
        ):
            self.assertNotIn(forbidden_assignment, route_source)

if __name__ == "__main__":
    unittest.main()

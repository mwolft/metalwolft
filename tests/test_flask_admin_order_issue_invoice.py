import ast
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ADMIN_PATH = SRC_DIR / "api" / "admin.py"
ROUTES_PATH = SRC_DIR / "api" / "routes.py"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def source(path):
    return path.read_text(encoding="utf-8")


def module_ast(path):
    return ast.parse(source(path))


def class_node(class_name):
    for node in module_ast(ADMIN_PATH).body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"{class_name} not found")


def class_source(class_name):
    return ast.get_source_segment(source(ADMIN_PATH), class_node(class_name))


def function_source(function_name):
    text = source(ADMIN_PATH)
    for node in ast.walk(module_ast(ADMIN_PATH)):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(text, node)
    raise AssertionError(f"{function_name} not found")


def method_source(class_name, method_name):
    text = source(ADMIN_PATH)
    for statement in class_node(class_name).body:
        if isinstance(statement, ast.FunctionDef) and statement.name == method_name:
            return ast.get_source_segment(text, statement)
    raise AssertionError(f"{method_name} not found in {class_name}")


class FlaskAdminOrderIssueInvoiceSourceTest(unittest.TestCase):
    def setUp(self):
        self.admin_source = source(ADMIN_PATH)
        self.view_source = class_source("OrderAdminView")
        self.issue_source = method_source("OrderAdminView", "issue_invoice")
        self.formatter_source = function_source("_format_order_invoice_detail")

    def test_route_is_post_only_inside_order_admin_view(self):
        self.assertIn("@expose('/issue-invoice/<int:order_id>', methods=['POST'])", self.view_source)
        self.assertIn("def issue_invoice(self, order_id):", self.view_source)
        self.assertNotIn("methods=['GET'", self.issue_source)

    def test_route_does_not_call_rest_endpoint_or_accept_browser_fiscal_data(self):
        self.assertNotIn("from api.routes", self.admin_source)
        self.assertNotIn("requests.", self.issue_source)
        self.assertNotIn("/api/admin/orders", self.issue_source)
        self.assertIn("request.args", self.issue_source)
        self.assertIn("request.form", self.issue_source)
        self.assertIn("request.get_json(silent=True)", self.issue_source)
        self.assertIn("Esta acción no acepta datos fiscales desde el navegador.", self.issue_source)

    def test_new_issue_delegates_once_to_invoice_issue_service(self):
        self.assertIn("order = self.session.get(Orders, order_id)", self.issue_source)
        self.assertIn("select_checkout_session_for_invoice(order)", self.issue_source)
        self.assertIn("build_invoice_issuer_from_config()", self.issue_source)
        self.assertEqual(self.issue_source.count("issue_invoice_for_order("), 1)
        self.assertIn("db_session=self.session", self.issue_source)
        self.assertIn("checkout_session=checkout_session", self.issue_source)
        self.assertIn("order=order", self.issue_source)
        self.assertIn('source="manual"', self.issue_source)
        self.assertIn("actor=invoice_admin_actor_from_basic_auth(request.authorization)", self.issue_source)

    def test_route_does_not_trigger_later_documental_steps_or_checkout(self):
        for forbidden_call in (
            "generate_invoice_pdf(",
            "create_accounting_entry(",
            "send_invoice_email",
            "create_pending_submission(",
            "run_invoice_workflow",
            "_finalize_order_from_checkout_quote",
            "cleanup_cart_lines_from_checkout_quote",
            "render_original_order_invoice_pdf",
        ):
            self.assertNotIn(forbidden_call, self.issue_source)

    def test_route_does_not_commit_or_rollback_around_the_service(self):
        for forbidden_transaction in (
            "self.session.commit",
            "self.session.rollback",
            "db.session.commit",
            "db.session.rollback",
        ):
            self.assertNotIn(forbidden_transaction, self.issue_source)

    def test_idempotence_uses_service_result_not_order_invoice_number(self):
        helper_source = function_source("_admin_issue_invoice_success_message")

        self.assertIn("if result.created:", helper_source)
        self.assertIn("emitida correctamente", helper_source)
        self.assertIn("ya tenía emitida", helper_source)
        self.assertNotIn("order.invoice_number", self.issue_source)
        self.assertNotIn("if order.invoice_number", self.issue_source)

    def test_errors_are_mapped_to_safe_flash_messages_and_logged(self):
        for expected_error in (
            "InvoiceIssueError",
            "InvoiceSnapshotValidationError",
            "InvoiceNumberError",
            "IntegrityError",
            "except Exception:",
        ):
            self.assertIn(expected_error, self.issue_source)

        self.assertIn("current_app.logger.warning", self.issue_source)
        self.assertIn("current_app.logger.exception", self.issue_source)
        self.assertIn("Pedido no encontrado.", self.issue_source)
        self.assertIn("La configuración fiscal del emisor no está completa.", self.issue_source)
        self.assertIn("No se puede emitir la factura para este pedido.", self.issue_source)
        self.assertIn("No se ha podido reservar un número de factura.", self.issue_source)
        self.assertIn("Ya existe una factura ordinaria para este pedido.", self.issue_source)
        self.assertIn("No se ha podido emitir la factura.", self.issue_source)
        self.assertNotIn("str(exc)", self.issue_source)
        self.assertNotIn("traceback", self.issue_source.lower())

    def test_detail_ui_shows_button_only_when_no_ordinary_invoice_exists(self):
        finder_source = function_source("_find_order_ordinary_invoice")

        self.assertIn("view.session.query(Invoices)", finder_source)
        self.assertIn("Invoices.invoice_type == ORDINARY_INVOICE_TYPE", finder_source)
        self.assertIn("invoice = _find_order_ordinary_invoice(view, model)", self.formatter_source)
        self.assertLess(
            self.formatter_source.index("if invoice:"),
            self.formatter_source.index('method="post"'),
        )
        self.assertIn("Factura emitida:", self.formatter_source)
        self.assertIn("Emitir factura", self.formatter_source)
        self.assertIn("Se asignará un número fiscal", self.formatter_source)

    def test_existing_rest_endpoint_still_uses_shared_helpers(self):
        routes = source(ROUTES_PATH)

        self.assertIn("select_checkout_session_for_invoice as _select_checkout_session_for_invoice", routes)
        self.assertIn("build_invoice_issuer_from_config as _build_invoice_issuer_from_config", routes)
        self.assertIn("invoice_admin_actor_from_jwt as _invoice_admin_actor", routes)


if __name__ == "__main__":
    unittest.main()

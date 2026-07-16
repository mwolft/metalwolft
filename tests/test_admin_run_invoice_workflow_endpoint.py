import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def routes_source():
    return (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")


def function_source(function_name):
    source = routes_source()
    start = source.index(f"def {function_name}")
    next_route = source.find("\n@api.route", start + 1)
    next_function = source.find("\ndef ", start + 1)
    endings = [position for position in (next_route, next_function) if position != -1]
    if not endings:
        return source[start:]
    return source[start:min(endings)]


def endpoint_source():
    return function_source("admin_run_invoice_workflow_for_order")


class AdminRunInvoiceWorkflowEndpointSourceTest(unittest.TestCase):
    def test_route_is_post_admin_endpoint_and_requires_jwt(self):
        source = routes_source()
        route_start = source.index("@api.route('/admin/orders/<int:order_id>/run-invoice-workflow', methods=['POST'])")
        route_header = source[route_start:source.index("def admin_run_invoice_workflow_for_order", route_start)]

        self.assertIn("@jwt_required()", route_header)
        self.assertIn("methods=['POST']", route_header)

    def test_non_admin_is_rejected(self):
        source = endpoint_source()

        self.assertIn('if not current_user.get("is_admin"):', source)
        self.assertIn("Access forbidden: Admins only", source)
        self.assertIn("), 403", source)

    def test_empty_body_is_valid_but_documental_body_is_rejected(self):
        source = endpoint_source()

        self.assertIn("request.get_json(silent=True) or {}", source)
        self.assertIn("if request_data:", source)
        self.assertIn("INVOICE_WORKFLOW_BODY_NOT_ALLOWED", source)
        for forbidden in (
            "invoice_number = request_data",
            "issuer = request_data",
            "snapshot = request_data",
            "email = request_data",
            "filename = request_data",
            "regenerate = request_data",
            "amount = request_data",
        ):
            self.assertNotIn(forbidden, source)

    def test_order_not_found_and_not_invoiceable_are_mapped(self):
        source = endpoint_source()

        self.assertIn("order = Orders.query.get(order_id)", source)
        self.assertIn("ORDER_NOT_FOUND", source)
        self.assertIn("), 404", source)
        self.assertIn("_select_checkout_session_for_invoice(order)", source)
        self.assertIn("ORDER_NOT_INVOICEABLE", source)
        self.assertIn("), 409", source)

    def test_endpoint_builds_infrastructure_and_delegates_to_orchestrator(self):
        source = endpoint_source()

        self.assertIn("invoice_folder = current_app.config.get(\"INVOICE_FOLDER\") or os.getenv(\"INVOICE_FOLDER\")", source)
        self.assertIn("issuer=_build_invoice_issuer_from_config()", source)
        self.assertIn("checkout_session=checkout_session", source)
        self.assertIn("actor=_invoice_admin_actor(current_user)", source)
        self.assertIn("invoice_output_dir=invoice_folder", source)
        self.assertIn("mailer=FlaskMailInvoiceAdapter(mail)", source)
        self.assertIn("db_session=db.session", source)
        self.assertIn("run_invoice_workflow_for_order(", source)

    def test_endpoint_does_not_duplicate_workflow_logic(self):
        source = endpoint_source()

        for forbidden in (
            "issue_invoice_for_order(",
            "generate_invoice_pdf(",
            "create_accounting_entry(",
            "create_pending_submission(",
            "send_invoice_email_v2(",
            "Invoices(",
            "AccountingEntry(",
            "InvoiceFiscalSubmission(",
        ):
            self.assertNotIn(forbidden, source)

    def test_response_uses_safe_workflow_result_and_409_for_partial_failure(self):
        source = endpoint_source()

        self.assertIn("return jsonify(result.to_dict()), status_code", source)
        self.assertIn("status_code = 200 if result.completed else 409", source)
        self.assertNotIn("invoice_snapshot", source)
        self.assertNotIn("email_last_error", source)
        self.assertNotIn("pdf_path", source)

    def test_configuration_errors_are_422_and_unexpected_errors_are_sanitized(self):
        source = endpoint_source()

        self.assertIn("except InvoiceSnapshotValidationError:", source)
        self.assertIn("INVOICE_WORKFLOW_CONFIGURATION_INVALID", source)
        self.assertIn("except InvoiceWorkflowConfigurationError:", source)
        self.assertIn("INVOICE_WORKFLOW_CONFIGURATION_MISSING", source)
        self.assertIn("), 422", source)
        self.assertIn("except Exception:", source)
        self.assertIn("INVOICE_WORKFLOW_FAILED", source)
        self.assertIn("), 500", source)
        self.assertNotIn("str(e)", source)
        self.assertNotIn('"error":', source)

    def test_endpoint_rejects_frontend_fiscal_or_email_data(self):
        source = endpoint_source()

        for forbidden in (
            "taxable_base",
            "vat_amount",
            "total_amount = request_data",
            "invoice_snapshot =",
            "client_cif = request_data",
            "recipient =",
            "subject =",
            "output_dir =",
            "filename =",
            "invoice_number =",
        ):
            self.assertNotIn(forbidden, source)

    def test_endpoint_does_not_touch_checkout_or_legacy_flows(self):
        source = endpoint_source()

        for forbidden in (
            "build_checkout_quote",
            "cleanup_cart_lines_from_checkout_quote",
            "stripe.",
            "_paypal_request",
            "render_original_order_invoice_pdf",
            "_regenerate_invoice_pdf_to_storage",
            "send_order_confirmation_email",
        ):
            self.assertNotIn(forbidden, source)

    def test_imports_workflow_service(self):
        source = routes_source()

        self.assertIn("InvoiceWorkflowConfigurationError", source)
        self.assertIn("run_invoice_workflow_for_order", source)


if __name__ == "__main__":
    unittest.main()

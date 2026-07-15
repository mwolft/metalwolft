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


def issue_endpoint_source():
    return function_source("admin_issue_invoice_for_order")


class AdminIssueInvoiceEndpointSourceTest(unittest.TestCase):
    def test_route_is_post_admin_endpoint_and_requires_jwt(self):
        source = routes_source()
        route_start = source.index("@api.route('/admin/orders/<int:order_id>/issue-invoice', methods=['POST'])")
        route_header = source[route_start:source.index("def admin_issue_invoice_for_order", route_start)]

        self.assertIn("@jwt_required()", route_header)
        self.assertIn("methods=['POST']", route_header)

    def test_non_admin_is_rejected(self):
        source = issue_endpoint_source()

        self.assertIn('if not current_user.get("is_admin"):', source)
        self.assertIn("Access forbidden: Admins only", source)
        self.assertIn("), 403", source)

    def test_empty_body_is_valid_but_fiscal_body_is_rejected(self):
        source = issue_endpoint_source()

        self.assertIn("request.get_json(silent=True) or {}", source)
        self.assertIn("if request_data:", source)
        self.assertIn("INVOICE_BODY_NOT_ALLOWED", source)
        self.assertNotIn("invoice_number = request_data", source)
        self.assertNotIn("amount = request_data", source)
        self.assertNotIn("snapshot = request_data", source)

    def test_order_not_found_returns_404(self):
        source = issue_endpoint_source()

        self.assertIn("order = Orders.query.get(order_id)", source)
        self.assertIn("ORDER_NOT_FOUND", source)
        self.assertIn("), 404", source)

    def test_not_invoiceable_order_returns_409(self):
        source = issue_endpoint_source()

        self.assertIn("_select_checkout_session_for_invoice(order)", source)
        self.assertIn("ORDER_NOT_INVOICEABLE", source)
        self.assertIn("), 409", source)

    def test_endpoint_delegates_to_invoice_issue_service(self):
        source = issue_endpoint_source()

        self.assertIn("issue_invoice_for_order(", source)
        self.assertIn("db_session=db.session", source)
        self.assertIn("order_id=order.id", source)
        self.assertIn("checkout_session=checkout_session", source)
        self.assertIn("issuer=_build_invoice_issuer_from_config()", source)
        self.assertIn("actor=_invoice_admin_actor(current_user)", source)
        self.assertIn('source="manual"', source)
        self.assertNotIn("acquire_next_invoice_number", source)
        self.assertNotIn("build_invoice_snapshot", source)
        self.assertNotIn("Invoices(", source)

    def test_idempotent_response_marks_existing_invoice_without_new_number_logic(self):
        source = issue_endpoint_source()

        self.assertIn("already_existed=not result.created", source)
        self.assertNotIn("generate_next_invoice_number", source)

    def test_response_is_safe_and_does_not_include_full_snapshot(self):
        serializer_source = function_source("_serialize_admin_issued_invoice")

        self.assertIn('"id": invoice.id', serializer_source)
        self.assertIn('"order_id": invoice.order_id', serializer_source)
        self.assertIn('"invoice_number": invoice.invoice_number', serializer_source)
        self.assertIn('"invoice_type": invoice.invoice_type', serializer_source)
        self.assertIn('"issued_at": issued_at', serializer_source)
        self.assertIn('"issuance_source": invoice.issuance_source', serializer_source)
        self.assertIn('"invoice_snapshot_schema_version": invoice.invoice_snapshot_schema_version', serializer_source)
        self.assertIn('"invoice_snapshot_hash": invoice.invoice_snapshot_hash', serializer_source)
        self.assertIn('"pdf_available": bool(invoice.pdf_path)', serializer_source)
        self.assertIn('"already_existed": already_existed', serializer_source)
        self.assertNotIn('"invoice_snapshot":', serializer_source)
        self.assertNotIn("invoice.invoice_snapshot,", serializer_source)

    def test_snapshot_number_and_internal_errors_are_mapped_safely(self):
        source = issue_endpoint_source()

        self.assertIn("except InvoiceSnapshotValidationError:", source)
        self.assertIn("INVOICE_SNAPSHOT_INVALID", source)
        self.assertIn("), 422", source)
        self.assertIn("except InvoiceNumberError:", source)
        self.assertIn("INVOICE_NUMBER_UNAVAILABLE", source)
        self.assertIn("except Exception:", source)
        self.assertIn("INVOICE_ISSUE_FAILED", source)
        self.assertNotIn("str(e)", source)

    def test_endpoint_does_not_generate_documents_send_email_or_touch_checkout_flow(self):
        source = issue_endpoint_source()

        self.assertNotIn("render_original_order_invoice_pdf", source)
        self.assertNotIn("_regenerate_invoice_pdf_to_storage", source)
        self.assertNotIn("send_invoice_email", source)
        self.assertNotIn("send_email(", source)
        self.assertNotIn("_finalize_order_from_checkout_quote", source)
        self.assertNotIn("cleanup_cart_lines_from_checkout_quote", source)
        self.assertNotIn("db.session.commit()", source)
        self.assertNotIn("db.session.rollback()", source)

    def test_checkout_session_selector_only_reads_final_checkout_sessions(self):
        source = function_source("_select_checkout_session_for_invoice")
        usability_source = function_source("_is_checkout_session_usable_for_invoice")

        self.assertIn("CheckoutSessions.query.filter_by(order_id=order.id).all()", source)
        self.assertIn("FINAL_CHECKOUT_STATUSES", usability_source)
        self.assertIn("payment_provider == \"stripe\"", usability_source)
        self.assertIn("payment_intent_id", usability_source)
        self.assertIn("payment_provider == \"paypal\"", usability_source)
        self.assertIn("provider_capture_id", usability_source)
        self.assertIn("provider_order_id", usability_source)
        self.assertNotIn(".status =", source)
        self.assertNotIn("db.session.add", source)


if __name__ == "__main__":
    unittest.main()

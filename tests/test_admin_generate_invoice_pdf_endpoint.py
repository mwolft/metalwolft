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
    return function_source("admin_generate_invoice_pdf_v2")


class AdminGenerateInvoicePdfEndpointSourceTest(unittest.TestCase):
    def test_route_is_post_admin_endpoint_and_requires_jwt(self):
        source = routes_source()
        route_start = source.index("@api.route('/admin/invoices/<int:invoice_id>/generate-pdf', methods=['POST'])")
        route_header = source[route_start:source.index("def admin_generate_invoice_pdf_v2", route_start)]

        self.assertIn("@jwt_required()", route_header)
        self.assertIn("methods=['POST']", route_header)

    def test_non_admin_is_rejected(self):
        source = endpoint_source()

        self.assertIn('if not current_user.get("is_admin"):', source)
        self.assertIn("Access forbidden: Admins only", source)
        self.assertIn("), 403", source)

    def test_only_regenerate_body_field_is_allowed(self):
        source = endpoint_source()

        self.assertIn("request.get_json(silent=True) or {}", source)
        self.assertIn('set(request_data) - {"regenerate"}', source)
        self.assertIn("INVOICE_PDF_BODY_NOT_ALLOWED", source)
        self.assertIn("INVALID_REGENERATE_VALUE", source)
        self.assertNotIn("output_dir = request_data", source)
        self.assertNotIn("filename = request_data", source)
        self.assertNotIn("file_path = request_data", source)

    def test_invoice_not_found_returns_404(self):
        source = endpoint_source()

        self.assertIn("invoice = Invoices.query.get(invoice_id)", source)
        self.assertIn("INVOICE_NOT_FOUND", source)
        self.assertIn("), 404", source)

    def test_endpoint_delegates_to_pdf_service_with_configured_folder(self):
        source = endpoint_source()

        self.assertIn("generate_invoice_pdf(", source)
        self.assertIn('current_app.config["INVOICE_FOLDER"]', source)
        self.assertIn("output_dir=invoice_folder", source)
        self.assertIn("regenerate=regenerate", source)
        self.assertNotIn("output_dir=request_data", source)
        self.assertNotIn("filename=request_data", source)

    def test_commit_happens_after_generation_only(self):
        source = endpoint_source()

        generation_position = source.index("result = generate_invoice_pdf(")
        commit_position = source.index("db.session.commit()")
        self.assertGreater(commit_position, generation_position)

    def test_rollbacks_are_present_for_generation_failures(self):
        source = endpoint_source()

        for exception_name in (
            "InvoicePdfSnapshotMissing",
            "InvoicePdfUnsupportedSchema",
            "InvoicePdfIntegrityError",
            "InvoicePdfWriteError",
            "Exception",
        ):
            self.assertIn(f"except {exception_name}", source)
        self.assertGreaterEqual(source.count("db.session.rollback()"), 5)

    def test_missing_snapshot_and_number_are_mapped_safely(self):
        source = endpoint_source()

        self.assertIn("INVOICE_PDF_SNAPSHOT_MISSING", source)
        self.assertIn("INVOICE_PDF_NOT_ISSUED", source)
        self.assertIn("), 422", source)
        self.assertIn("), 409", source)

    def test_unsupported_schema_hash_and_write_conflict_are_mapped(self):
        source = endpoint_source()

        self.assertIn("INVOICE_PDF_SCHEMA_UNSUPPORTED", source)
        self.assertIn("INVOICE_PDF_INTEGRITY_ERROR", source)
        self.assertIn("INVOICE_PDF_FILE_CONFLICT", source)
        self.assertIn("INVOICE_PDF_WRITE_FAILED", source)

    def test_unexpected_errors_are_sanitized(self):
        source = endpoint_source()

        self.assertIn("INVOICE_PDF_GENERATION_FAILED", source)
        self.assertIn("logger.exception", source)
        self.assertNotIn('"error": str(', source)
        self.assertNotIn("traceback", source.lower())

    def test_response_contract_is_safe_and_does_not_expose_absolute_path(self):
        source = function_source("_serialize_admin_generated_invoice_pdf")

        self.assertIn('"id": invoice.id', source)
        self.assertIn('"invoice_number": invoice.invoice_number', source)
        self.assertIn('"pdf_available": bool(invoice.pdf_path)', source)
        self.assertIn('"pdf_path": result.filename', source)
        self.assertIn('"generated": generated', source)
        self.assertIn('"regenerated": regenerated', source)
        self.assertIn('"file_size": result.file_size', source)
        self.assertNotIn("result.pdf_path", source)
        self.assertNotIn("file_path", source)
        self.assertNotIn("current_app.config", source)

    def test_reuse_detection_is_based_on_existing_referenced_file(self):
        source = endpoint_source()
        helper_source = function_source("_invoice_pdf_file_exists")

        self.assertIn("previous_pdf_path = invoice.pdf_path", source)
        self.assertIn("_invoice_pdf_file_exists(invoice_folder, previous_pdf_path)", source)
        self.assertIn("previous_pdf_path == result.pdf_path", source)
        self.assertIn("not regenerate", source)
        self.assertIn("os.path.basename(pdf_path or \"\")", helper_source)
        self.assertIn("os.path.exists(os.path.join(output_dir, filename))", helper_source)

    def test_generated_and_regenerated_flags_follow_regenerate_policy(self):
        source = endpoint_source()

        self.assertIn("generated=not reused_existing", source)
        self.assertIn("regenerated=bool(regenerate)", source)

    def test_endpoint_does_not_issue_invoice_or_consume_number(self):
        source = endpoint_source()

        self.assertNotIn("issue_invoice_for_order", source)
        self.assertNotIn("acquire_next_invoice_number", source)
        self.assertNotIn("generate_next_invoice_number", source)
        self.assertNotIn("Invoices(", source)

    def test_endpoint_does_not_generate_legacy_documents_or_send_email(self):
        source = endpoint_source()

        self.assertNotIn("render_original_order_invoice_pdf", source)
        self.assertNotIn("_regenerate_invoice_pdf_to_storage", source)
        self.assertNotIn("send_invoice_email", source)
        self.assertNotIn("send_email(", source)

    def test_endpoint_does_not_touch_checkout_or_cart(self):
        source = endpoint_source()

        self.assertNotIn("CheckoutSessions", source)
        self.assertNotIn("_finalize_order_from_checkout_quote", source)
        self.assertNotIn("cleanup_cart_lines_from_checkout_quote", source)
        self.assertNotIn("Cart", source)

    def test_endpoint_does_not_modify_fiscal_fields_or_order(self):
        source = endpoint_source()

        self.assertNotIn("invoice.invoice_number =", source)
        self.assertNotIn("invoice.invoice_snapshot =", source)
        self.assertNotIn("invoice.invoice_snapshot_hash =", source)
        self.assertNotIn("invoice.order_id =", source)
        self.assertNotIn("order.", source)

    def test_imports_pdf_service_and_domain_errors(self):
        source = routes_source()

        for imported_name in (
            "InvoicePdfIntegrityError",
            "InvoicePdfSnapshotMissing",
            "InvoicePdfUnsupportedSchema",
            "InvoicePdfWriteError",
            "generate_invoice_pdf",
        ):
            self.assertIn(imported_name, source)

    def test_existing_pdf_is_not_overwritten_without_explicit_regeneration(self):
        source = endpoint_source()

        self.assertIn("previous_file_existed", source)
        self.assertIn("reused_existing", source)
        self.assertIn("INVOICE_PDF_FILE_CONFLICT", source)
        self.assertIn("regenerate=regenerate", source)

    def test_endpoint_keeps_v2_pdf_separate_from_download_legacy_route(self):
        source = endpoint_source()

        self.assertNotIn("send_file", source)
        self.assertNotIn("download_invoice", source)
        self.assertNotIn("download_name", source)


if __name__ == "__main__":
    unittest.main()

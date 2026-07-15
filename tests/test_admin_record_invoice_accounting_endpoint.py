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
    return function_source("admin_record_invoice_accounting")


class AdminRecordInvoiceAccountingEndpointSourceTest(unittest.TestCase):
    def test_route_is_post_admin_endpoint_and_requires_jwt(self):
        source = routes_source()
        route_start = source.index("@api.route('/admin/invoices/<int:invoice_id>/record-accounting', methods=['POST'])")
        route_header = source[route_start:source.index("def admin_record_invoice_accounting", route_start)]

        self.assertIn("@jwt_required()", route_header)
        self.assertIn("methods=['POST']", route_header)

    def test_non_admin_is_rejected(self):
        source = endpoint_source()

        self.assertIn('if not current_user.get("is_admin"):', source)
        self.assertIn("Access forbidden: Admins only", source)
        self.assertIn("), 403", source)

    def test_empty_body_is_valid_but_accounting_body_is_rejected(self):
        source = endpoint_source()

        self.assertIn("request.get_json(silent=True) or {}", source)
        self.assertIn("if request_data:", source)
        self.assertIn("ACCOUNTING_BODY_NOT_ALLOWED", source)
        self.assertNotIn("taxable_base = request_data", source)
        self.assertNotIn("vat_amount = request_data", source)
        self.assertNotIn("invoice_number = request_data", source)
        self.assertNotIn("snapshot = request_data", source)

    def test_invoice_not_found_returns_404(self):
        source = endpoint_source()

        self.assertIn("invoice = Invoices.query.get(invoice_id)", source)
        self.assertIn("INVOICE_NOT_FOUND", source)
        self.assertIn("), 404", source)

    def test_not_issued_invoice_returns_409_before_service_call(self):
        source = endpoint_source()

        self.assertIn("if not invoice.invoice_number or not invoice.issued_at:", source)
        self.assertIn("INVOICE_NOT_ISSUED", source)
        self.assertIn("), 409", source)

    def test_endpoint_delegates_to_accounting_service(self):
        source = endpoint_source()

        self.assertIn("create_accounting_entry(invoice, db_session=db.session)", source)
        self.assertNotIn("AccountingEntry(", source)
        self.assertNotIn("taxable_base=", source)
        self.assertNotIn("vat_amount=", source)
        self.assertNotIn("total_amount=", source)

    def test_endpoint_detects_idempotent_existing_entry_before_call(self):
        source = endpoint_source()

        self.assertIn("existing_entry = AccountingEntry.query.filter_by(", source)
        self.assertIn("invoice_id=invoice.id", source)
        self.assertIn("entry_type=ENTRY_TYPE_SALE", source)
        self.assertIn("already_existed=existing_entry is not None", source)

    def test_commit_happens_after_service_call(self):
        source = endpoint_source()

        service_position = source.index("entry = create_accounting_entry(")
        commit_position = source.index("db.session.commit()")
        self.assertGreater(commit_position, service_position)

    def test_rollbacks_are_present_for_failures(self):
        source = endpoint_source()

        for exception_name in (
            "AccountingEntryValidationError",
            "AccountingEntryUnsupportedSchema",
            "AccountingEntryIntegrityError",
            "IntegrityError",
            "Exception",
        ):
            self.assertIn(f"except {exception_name}", source)
        self.assertGreaterEqual(source.count("db.session.rollback()"), 5)

    def test_snapshot_hash_schema_and_conflict_errors_are_mapped(self):
        source = endpoint_source()

        self.assertIn("ACCOUNTING_ENTRY_SNAPSHOT_INVALID", source)
        self.assertIn("ACCOUNTING_ENTRY_SCHEMA_UNSUPPORTED", source)
        self.assertIn("ACCOUNTING_ENTRY_INTEGRITY_ERROR", source)
        self.assertIn("ACCOUNTING_ENTRY_CONFLICT", source)
        self.assertIn("), 422", source)
        self.assertIn("), 409", source)

    def test_unexpected_errors_are_sanitized(self):
        source = endpoint_source()

        self.assertIn("ACCOUNTING_ENTRY_FAILED", source)
        self.assertIn("logger.exception", source)
        self.assertNotIn('"error": str(', source)
        self.assertNotIn("traceback", source.lower())

    def test_response_contract_does_not_include_snapshot_or_personal_details(self):
        source = function_source("_serialize_admin_accounting_entry")

        for expected in (
            '"id": entry.id',
            '"invoice_id": entry.invoice_id',
            '"invoice_number": entry.invoice_number',
            '"entry_type": entry.entry_type',
            '"status": entry.status',
            '"invoice_date": invoice_date',
            '"taxable_base": _accounting_amount_string(entry.taxable_base)',
            '"vat_amount": _accounting_amount_string(entry.vat_amount)',
            '"total_amount": _accounting_amount_string(entry.total_amount)',
            '"currency": entry.currency',
            '"already_existed": already_existed',
        ):
            self.assertIn(expected, source)

        for forbidden in (
            "invoice_snapshot",
            "customer_name",
            "customer_tax_id",
            "error_message",
            "payment_provider",
        ):
            self.assertNotIn(forbidden, source)

    def test_amount_serializer_returns_decimal_strings(self):
        amount_source = function_source("_accounting_amount_string")
        serializer_source = function_source("_serialize_admin_accounting_entry")

        self.assertIn('return f"{value:.2f}" if value is not None else None', amount_source)
        self.assertIn('"taxable_base": _accounting_amount_string(entry.taxable_base)', serializer_source)
        self.assertIn('"vat_amount": _accounting_amount_string(entry.vat_amount)', serializer_source)
        self.assertIn('"total_amount": _accounting_amount_string(entry.total_amount)', serializer_source)

    def test_endpoint_does_not_modify_invoice_fiscal_fields(self):
        source = endpoint_source()

        for forbidden in (
            "invoice.invoice_number =",
            "invoice.invoice_snapshot =",
            "invoice.invoice_snapshot_hash =",
            "invoice.issued_at =",
        ):
            self.assertNotIn(forbidden, source)

    def test_endpoint_does_not_generate_excel_csv_or_external_files(self):
        source = endpoint_source().lower()

        for forbidden in ("excel", "openpyxl", ".xlsx", "csv", "writer"):
            self.assertNotIn(forbidden, source)

    def test_endpoint_does_not_call_pdf_email_verifactu_or_checkout(self):
        source = endpoint_source()

        for forbidden in (
            "generate_invoice_pdf",
            "render_original_order_invoice_pdf",
            "send_invoice_email",
            "send_email(",
            "InvoiceFiscalSubmission",
            "create_pending_submission",
            "_finalize_order_from_checkout_quote",
            "cleanup_cart_lines_from_checkout_quote",
            "CheckoutSessions",
        ):
            self.assertNotIn(forbidden, source)

    def test_endpoint_is_not_connected_to_invoice_issuance(self):
        source = endpoint_source()

        self.assertNotIn("issue_invoice_for_order", source)
        self.assertNotIn("acquire_next_invoice_number", source)
        self.assertNotIn("generate_next_invoice_number", source)

    def test_imports_accounting_service_and_model(self):
        source = routes_source()

        for expected in (
            "AccountingEntry",
            "ENTRY_TYPE_SALE",
            "AccountingEntryIntegrityError",
            "AccountingEntryUnsupportedSchema",
            "AccountingEntryValidationError",
            "create_accounting_entry",
        ):
            self.assertIn(expected, source)

    def test_second_call_contract_marks_existing_record(self):
        serializer_source = function_source("_serialize_admin_accounting_entry")
        endpoint = endpoint_source()

        self.assertIn('"already_existed": already_existed', serializer_source)
        self.assertIn("already_existed=existing_entry is not None", endpoint)

    def test_endpoint_controls_transaction_not_service(self):
        service_source = (ROOT_DIR / "src/api/invoice_accounting_service.py").read_text(encoding="utf-8")
        endpoint = endpoint_source()

        self.assertIn("db.session.commit()", endpoint)
        self.assertIn("db.session.rollback()", endpoint)
        self.assertNotIn(".commit(", service_source)
        self.assertNotIn(".rollback(", service_source)


if __name__ == "__main__":
    unittest.main()

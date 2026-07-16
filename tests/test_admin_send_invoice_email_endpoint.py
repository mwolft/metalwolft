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
    return function_source("admin_send_invoice_email_v2")


class AdminSendInvoiceEmailEndpointSourceTest(unittest.TestCase):
    def test_route_is_post_admin_endpoint_and_requires_jwt(self):
        source = routes_source()
        route_start = source.index("@api.route('/admin/invoices/<int:invoice_id>/send-email', methods=['POST'])")
        route_header = source[route_start:source.index("def admin_send_invoice_email_v2", route_start)]

        self.assertIn("@jwt_required()", route_header)
        self.assertIn("methods=['POST']", route_header)

    def test_non_admin_is_rejected(self):
        source = endpoint_source()

        self.assertIn('if not current_user.get("is_admin"):', source)
        self.assertIn("Access forbidden: Admins only", source)
        self.assertIn("), 403", source)

    def test_empty_body_is_valid_but_email_body_is_rejected(self):
        source = endpoint_source()

        self.assertIn("request.get_json(silent=True) or {}", source)
        self.assertIn("if request_data:", source)
        self.assertIn("INVOICE_EMAIL_BODY_NOT_ALLOWED", source)
        for forbidden in (
            "recipient = request_data",
            "subject = request_data",
            "body = request_data",
            "pdf_path = request_data",
            "invoice_snapshot = request_data",
            "invoice_number = request_data",
        ):
            self.assertNotIn(forbidden, source)

    def test_invoice_not_found_returns_404(self):
        source = endpoint_source()

        self.assertIn("invoice = Invoices.query.get(invoice_id)", source)
        self.assertIn("INVOICE_NOT_FOUND", source)
        self.assertIn("), 404", source)

    def test_not_issued_invoice_returns_409_before_service_call(self):
        source = endpoint_source()

        self.assertIn("if not invoice.invoice_number or not invoice.issued_at:", source)
        self.assertIn("INVOICE_EMAIL_NOT_ISSUED", source)
        self.assertIn("), 409", source)

    def test_pdf_path_is_required_before_service_call(self):
        source = endpoint_source()

        self.assertIn("if not invoice.pdf_path:", source)
        self.assertIn("INVOICE_EMAIL_PDF_MISSING", source)
        self.assertIn("), 409", source)

    def test_endpoint_uses_flask_mail_adapter_and_invoice_email_service(self):
        source = endpoint_source()

        self.assertIn("adapter = FlaskMailInvoiceAdapter(mail)", source)
        self.assertIn("send_invoice_email_v2(invoice, mailer=adapter)", source)
        self.assertNotIn("Message(", source)
        self.assertNotIn("mail.send(", source)

    def test_success_commits_after_service_call(self):
        source = endpoint_source()

        service_position = source.index("result = send_invoice_email_v2(")
        commit_position = source.index("db.session.commit()")
        self.assertGreater(commit_position, service_position)

    def test_send_error_rolls_back_then_persists_failure_status(self):
        source = endpoint_source()
        helper = function_source("_persist_invoice_email_failure")

        self.assertIn("except (InvoiceEmailSendError, FlaskMailInvoiceAdapterError):", source)
        self.assertIn("db.session.rollback()", source)
        self.assertIn("_persist_invoice_email_failure(invoice_id, attempts_before)", source)
        self.assertIn("failed_invoice.email_status = EMAIL_STATUS_FAILED", helper)
        self.assertIn("failed_invoice.email_attempts = int(attempts_before or 0) + 1", helper)
        self.assertIn('failed_invoice.email_last_error = "No se pudo enviar el email de factura."', helper)
        self.assertIn("db.session.commit()", helper)

    def test_domain_errors_are_mapped_safely(self):
        source = endpoint_source()

        for exception_name in (
            "InvoiceEmailSnapshotMissing",
            "InvoiceEmailUnsupportedSchema",
            "InvoiceEmailIntegrityError",
            "InvoiceEmailRecipientMissing",
            "InvoiceEmailPdfMissing",
            "InvoiceEmailSendError",
            "FlaskMailInvoiceAdapterError",
        ):
            self.assertIn(exception_name, source)

        for code in (
            "INVOICE_EMAIL_SNAPSHOT_MISSING",
            "INVOICE_EMAIL_SCHEMA_UNSUPPORTED",
            "INVOICE_EMAIL_INTEGRITY_ERROR",
            "INVOICE_EMAIL_RECIPIENT_MISSING",
            "INVOICE_EMAIL_PDF_MISSING",
            "INVOICE_EMAIL_SEND_FAILED",
        ):
            self.assertIn(code, source)

        self.assertIn("), 422", source)
        self.assertIn("), 409", source)
        self.assertIn("), 502", source)

    def test_unexpected_errors_are_sanitized(self):
        source = endpoint_source()

        self.assertIn("INVOICE_EMAIL_FAILED", source)
        self.assertIn("logger.exception", source)
        self.assertNotIn('"error": str(', source)
        self.assertNotIn("traceback", source.lower())

    def test_response_contract_is_safe(self):
        source = function_source("_serialize_admin_invoice_email")

        for expected in (
            '"id": invoice.id',
            '"invoice_number": invoice.invoice_number',
            '"recipient": result.recipient',
            '"email_status": invoice.email_status',
            '"email_sent_at": sent_at',
            '"email_attempts": invoice.email_attempts',
            '"already_sent": result.already_sent',
        ):
            self.assertIn(expected, source)

        for forbidden in (
            "invoice_snapshot",
            "body",
            "subject",
            "pdf_path",
            "attachment",
            "email_last_error",
            "smtp",
            "client_address",
            "client_cif",
        ):
            self.assertNotIn(forbidden, source)

    def test_idempotence_is_delegated_to_email_service(self):
        service_source = (SRC_DIR / "api/invoice_email_service.py").read_text(encoding="utf-8")
        endpoint = endpoint_source()

        self.assertIn('getattr(invoice, "email_status", None) == EMAIL_STATUS_SENT', service_source)
        self.assertIn("already_sent=True", service_source)
        self.assertIn("send_invoice_email_v2(invoice, mailer=adapter)", endpoint)
        self.assertNotIn("invoice.email_status = EMAIL_STATUS_SENT", endpoint)

    def test_endpoint_does_not_modify_fiscal_invoice_or_order_fields(self):
        source = endpoint_source()

        for forbidden in (
            "invoice.invoice_number =",
            "invoice.invoice_snapshot =",
            "invoice.invoice_snapshot_hash =",
            "invoice.issued_at =",
            "invoice.order_id =",
            "order.",
        ):
            self.assertNotIn(forbidden, source)

    def test_endpoint_does_not_call_excel_verifactu_pdf_checkout_or_legacy_email(self):
        source = endpoint_source()

        for forbidden in (
            "export_sales_accounting_entries",
            "AccountingEntry",
            "InvoiceFiscalSubmission",
            "create_pending_submission",
            "generate_invoice_pdf",
            "issue_invoice_for_order",
            "build_checkout_quote",
            "send_email(",
        ):
            self.assertNotIn(forbidden, source)

    def test_imports_required_adapter_service_and_errors(self):
        source = routes_source()

        for imported_name in (
            "FlaskMailInvoiceAdapter",
            "FlaskMailInvoiceAdapterError",
            "EMAIL_STATUS_FAILED",
            "InvoiceEmailIntegrityError",
            "InvoiceEmailPdfMissing",
            "InvoiceEmailRecipientMissing",
            "InvoiceEmailSendError",
            "InvoiceEmailSnapshotMissing",
            "InvoiceEmailUnsupportedSchema",
            "send_invoice_email as send_invoice_email_v2",
        ):
            self.assertIn(imported_name, source)

    def test_no_sensitive_failure_details_are_returned(self):
        source = endpoint_source() + function_source("_persist_invoice_email_failure")

        self.assertNotIn("email_last_error", endpoint_source())
        self.assertNotIn("SMTP", source)
        self.assertNotIn("smtp", source)
        self.assertNotIn("Exception as e", source)
        self.assertNotIn("str(e)", source)

    def test_second_call_does_not_bypass_service_or_adapter(self):
        source = endpoint_source()

        self.assertNotIn("if invoice.email_status", source)
        self.assertNotIn("adapter.send(", source)
        self.assertIn("send_invoice_email_v2(invoice, mailer=adapter)", source)


if __name__ == "__main__":
    unittest.main()

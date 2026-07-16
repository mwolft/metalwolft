import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


DOCUMENT_WORKFLOW_CALLS = (
    "issue_invoice_for_order(",
    "run_invoice_workflow_for_order(",
    "generate_invoice_pdf(",
    "create_accounting_entry(",
    "create_pending_submission(",
    "send_invoice_email_v2(",
    "send_invoice_email(",
    "_regenerate_invoice_pdf_to_storage(",
    "render_original_order_invoice_pdf(",
)


def routes_source():
    return (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")


def order_confirmation_source():
    return (ROOT_DIR / "src/api/order_confirmation_email_service.py").read_text(encoding="utf-8")


def function_source(function_name):
    source = routes_source()
    start = source.index(f"def {function_name}")
    next_route = source.find("\n@api.route", start + 1)
    next_function = source.find("\ndef ", start + 1)
    endings = [position for position in (next_route, next_function) if position != -1]
    if not endings:
        return source[start:]
    return source[start:min(endings)]


def finalizer_source():
    source = routes_source()
    start = source.index("def _finalize_order_from_checkout_quote")
    end = source.index("@api.route('/delivery-estimate'", start)
    return source[start:end]


def orders_stripe_fallback_source():
    source = function_source("handle_orders")
    start = source.index("if request.method == 'POST':")
    end = source.index("            if payment_intent_id:", start)
    return source[start:end]


def assert_no_document_workflow(testcase, source):
    for forbidden in DOCUMENT_WORKFLOW_CALLS:
        testcase.assertNotIn(forbidden, source)


class StripeCheckoutInvoiceWorkflowCharacterizationTest(unittest.TestCase):
    def test_stripe_webhook_finalizes_paid_checkout_session_into_order(self):
        source = function_source("stripe_webhook")

        self.assertIn("event_type == 'payment_intent.succeeded'", source)
        self.assertIn("_get_checkout_session_by_payment_intent(", source)
        self.assertIn('checkout_session.status = "paid"', source)
        self.assertIn("order, created = _finalize_order_from_checkout_quote(", source)
        self.assertIn("checkout_session=checkout_session", source)

    def test_stripe_webhook_does_not_start_document_or_invoice_workflow(self):
        source = function_source("stripe_webhook")

        assert_no_document_workflow(self, source)
        self.assertNotIn("Invoices(", source)
        self.assertNotIn("pdf_path", source)
        self.assertNotIn("invoice_number", source)

    def test_stripe_fallback_is_idempotent_when_webhook_already_created_order(self):
        source = orders_stripe_fallback_source()

        self.assertIn("if checkout_session.order_id:", source)
        self.assertIn("existing_order = Orders.query.filter_by(", source)
        self.assertIn('"Order already created for this payment intent."', source)
        self.assertIn("return response, 200", source)
        self.assertIn("new_order, created = _finalize_order_from_checkout_quote(", source)
        self.assertIn("return response, 201 if created else 200", source)

    def test_stripe_fallback_does_not_issue_invoice_or_run_workflow(self):
        source = orders_stripe_fallback_source()

        assert_no_document_workflow(self, source)
        self.assertNotIn("Invoices(", source)
        self.assertNotIn("invoice_number = Invoices.generate_next_invoice_number()", source)
        self.assertNotIn("new_order.invoice_number", source)


class PayPalCheckoutInvoiceWorkflowCharacterizationTest(unittest.TestCase):
    def test_paypal_capture_records_provider_state_but_does_not_create_order(self):
        source = function_source("capture_paypal_order")

        self.assertIn("_paypal_request(", source)
        self.assertIn("checkout_session.provider_order_id", source)
        self.assertIn("checkout_session.provider_capture_id", source)
        self.assertIn("_normalize_checkout_session_status(", source)
        self.assertNotIn("_finalize_order_from_checkout_quote(", source)

    def test_paypal_webhook_is_current_authoritative_order_creation_path(self):
        source = function_source("paypal_webhook")

        self.assertIn('"PAYMENT.CAPTURE.COMPLETED"', source)
        self.assertIn('"PAYMENT.CAPTURE.PENDING"', source)
        self.assertIn("if checkout_session.order_id:", source)
        self.assertIn('checkout_session.status = "order_created"', source)
        self.assertIn("order, created = _finalize_order_from_checkout_quote(", source)
        self.assertIn("checkout_session=checkout_session", source)

    def test_paypal_paths_do_not_start_document_or_invoice_workflow(self):
        capture_source = function_source("capture_paypal_order")
        webhook_source = function_source("paypal_webhook")

        assert_no_document_workflow(self, capture_source)
        assert_no_document_workflow(self, webhook_source)
        self.assertNotIn("Invoices(", capture_source)
        self.assertNotIn("Invoices(", webhook_source)
        self.assertNotIn("pdf_path", capture_source)
        self.assertNotIn("pdf_path", webhook_source)


class CheckoutFinalizerInvoiceWorkflowCharacterizationTest(unittest.TestCase):
    def test_finalizer_creates_order_lines_and_links_checkout_session(self):
        source = finalizer_source()

        self.assertIn("new_order = Orders(", source)
        self.assertIn("new_detail = OrderDetails(", source)
        self.assertIn("db.session.add(new_order)", source)
        self.assertIn("db.session.add(new_detail)", source)
        self.assertIn("checkout_session.order_id = new_order.id", source)
        self.assertIn('checkout_session.status = "order_created"', source)

    def test_finalizer_is_idempotent_by_checkout_session_order_id(self):
        source = finalizer_source()

        self.assertIn("if checkout_session and checkout_session.order_id:", source)
        self.assertIn("existing_order = Orders.query.filter_by(", source)
        self.assertIn("return existing_order, False", source)

    def test_finalizer_commits_order_before_order_confirmation_email(self):
        source = finalizer_source()

        self.assertLess(
            source.index("db.session.commit()"),
            source.index("send_order_confirmation_email("),
        )
        self.assertIn("checkout_quote=checkout_quote", source)
        self.assertIn("customer_firstname=customer_firstname", source)

    def test_finalizer_does_not_depend_on_invoice_pdf_or_document_workflow(self):
        source = finalizer_source()

        assert_no_document_workflow(self, source)
        self.assertNotIn("Invoices(", source)
        self.assertNotIn("invoice_number =", source)
        self.assertNotIn(".invoice_number =", source)
        self.assertNotIn("pdf_path", source)

    def test_finalizer_keeps_order_valid_without_invoice_number(self):
        source = finalizer_source()

        order_constructor = source[source.index("new_order = Orders("):source.index("db.session.add(new_order)")]
        self.assertIn("user_id=user.id", order_constructor)
        self.assertIn("total_amount=0", order_constructor)
        self.assertIn("locator=Orders.generate_locator()", order_constructor)
        self.assertIn('order_status="pendiente"', order_constructor)
        self.assertNotIn("invoice_number", order_constructor)


class CheckoutStatusInvoiceWorkflowCharacterizationTest(unittest.TestCase):
    def test_checkout_status_confirms_order_without_invoice_or_pdf_requirements(self):
        source = function_source("checkout_status")

        self.assertIn("order = checkout_session.order", source)
        self.assertIn('state = "confirmed"', source)
        self.assertIn('"order": order.serialize() if order else None', source)
        self.assertNotIn("Invoices", source)
        self.assertNotIn("invoice_number", source)
        self.assertNotIn("pdf_path", source)

    def test_checkout_status_handles_processing_and_failed_without_invoice_state(self):
        source = function_source("checkout_status")

        self.assertIn('elif session_status in ("payment_failed", "canceled"):', source)
        self.assertIn('state = "failed"', source)
        self.assertIn('state = "processing"', source)
        self.assertIn('"checkout_session_status": session_status', source)
        self.assertIn('"payment_provider": checkout_session.payment_provider', source)


class CheckoutOrderConfirmationEmailCharacterizationTest(unittest.TestCase):
    def test_checkout_email_is_order_confirmation_not_invoice_email(self):
        source = order_confirmation_source()

        self.assertIn("def send_order_confirmation_email(", source)
        self.assertIn('subject=f"Hemos recibido tu pedido {order.locator}"', source)
        self.assertIn("recipients=[user.email, mail_username]", source)
        self.assertIn("Estado del pago: confirmado", source)
        self.assertNotIn("InvoiceEmailMessage", source)
        self.assertNotIn("send_invoice_email", source)
        self.assertNotIn(".attach(", source)
        self.assertNotIn("attachments", source)
        self.assertNotIn("pdf_path", source)


class CheckoutDocumentWorkflowProtectionTest(unittest.TestCase):
    def test_checkout_payment_paths_are_protected_against_accidental_document_workflow(self):
        checkout_sources = {
            "finalizer": finalizer_source(),
            "stripe_webhook": function_source("stripe_webhook"),
            "stripe_fallback": orders_stripe_fallback_source(),
            "paypal_capture": function_source("capture_paypal_order"),
            "paypal_webhook": function_source("paypal_webhook"),
            "checkout_status": function_source("checkout_status"),
            "order_confirmation_email": order_confirmation_source(),
        }

        for name, source in checkout_sources.items():
            with self.subTest(name=name):
                assert_no_document_workflow(self, source)
                self.assertNotIn("create_pending_submission(", source)
                self.assertNotIn("InvoiceFiscalSubmission(", source)
                self.assertNotIn("AccountingEntry(", source)


if __name__ == "__main__":
    unittest.main()

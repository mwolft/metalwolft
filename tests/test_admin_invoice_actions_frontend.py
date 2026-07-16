import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ORDERS_PATH = ROOT_DIR / "src/front/js/component/admin/orders/orders.js"
INVOICES_PATH = ROOT_DIR / "src/front/js/component/admin/invoices/invoices.js"
MODELS_PATH = ROOT_DIR / "src/api/models.py"
CSS_PATH = ROOT_DIR / "src/front/styles/admin-panel.css"


def source(path):
    return path.read_text(encoding="utf-8")


def const_source(path, const_name):
    text = source(path)
    start = text.index(f"const {const_name}")
    next_const = text.find("\nconst ", start + 1)
    next_export = text.find("\nexport ", start + 1)
    endings = [position for position in (next_const, next_export) if position != -1]
    if not endings:
        return text[start:]
    return text[start:min(endings)]


class AdminInvoiceActionsFrontendSourceTest(unittest.TestCase):
    def test_order_issue_button_is_visible_only_without_invoice(self):
        button = const_source(ORDERS_PATH, "IssueInvoiceButton")
        table = const_source(ORDERS_PATH, "OrderListTable")
        orders = source(ORDERS_PATH)
        edit = orders[orders.index("export const OrderEdit"):orders.index("export const OrderCreate")]

        self.assertIn('"Emitir factura"', button)
        self.assertIn("if (record?.invoice_number)", button)
        self.assertIn("return null", button)
        self.assertIn("<IssueInvoiceButton />", table)
        self.assertIn("<IssueInvoiceButton />", edit)

    def test_order_issue_posts_empty_body_and_blocks_double_click(self):
        button = const_source(ORDERS_PATH, "IssueInvoiceButton")

        self.assertIn("/api/admin/orders/${record.id}/issue-invoice", button)
        self.assertIn('method: "POST"', button)
        self.assertIn("Authorization: `Bearer ${token}`", button)
        self.assertIn("if (isIssuing)", button)
        self.assertIn("disabled={isIssuing}", button)
        self.assertNotIn("body:", button)
        self.assertNotIn("JSON.stringify", button)

    def test_order_issue_confirms_notifies_and_refreshes(self):
        button = const_source(ORDERS_PATH, "IssueInvoiceButton")

        self.assertIn("window.confirm", button)
        self.assertIn("notify(`Factura", button)
        self.assertIn("type: \"success\"", button)
        self.assertIn("type: \"error\"", button)
        self.assertIn("refresh()", button)

    def test_invoice_pdf_action_uses_v2_endpoint_and_regenerate_body_only(self):
        button = const_source(INVOICES_PATH, "InvoicePdfActionButton")

        self.assertIn("/api/admin/invoices/${record.id}/generate-pdf", button)
        self.assertIn('method: "POST"', button)
        self.assertIn('body: JSON.stringify({ regenerate: hasPdf })', button)
        self.assertIn('"Content-Type": "application/json"', button)
        self.assertIn("window.confirm", button)
        self.assertIn("disabled={isLoading}", button)
        self.assertIn("refresh()", button)
        self.assertNotIn("output_dir", button)
        self.assertNotIn("filename", button)
        self.assertNotIn("pdf_path", button)

    def test_accounting_action_is_idempotent_in_ui_and_uses_empty_body(self):
        button = const_source(INVOICES_PATH, "RecordAccountingButton")

        self.assertIn("/api/admin/invoices/${record.id}/record-accounting", button)
        self.assertIn("if (record?.accounting_entry_status)", button)
        self.assertIn("Contabilidad:", button)
        self.assertIn("disabled={isLoading}", button)
        self.assertIn("refresh()", button)
        self.assertNotIn("body:", button)
        self.assertNotIn("JSON.stringify", button)

    def test_email_action_requires_pdf_and_hides_after_sent(self):
        button = const_source(INVOICES_PATH, "SendInvoiceEmailButton")

        self.assertIn("/api/admin/invoices/${record.id}/send-email", button)
        self.assertIn('record?.email_status === "sent"', button)
        self.assertIn("Email enviado", button)
        self.assertIn("if (!record.pdf_available)", button)
        self.assertIn("PDF requerido", button)
        self.assertIn("window.confirm", button)
        self.assertIn("disabled={isLoading}", button)
        self.assertNotIn("body:", button)
        self.assertNotIn("JSON.stringify", button)

    def test_invoice_actions_do_not_send_fiscal_or_customer_payloads(self):
        text = "\n".join([
            const_source(ORDERS_PATH, "IssueInvoiceButton"),
            const_source(INVOICES_PATH, "InvoicePdfActionButton"),
            const_source(INVOICES_PATH, "RecordAccountingButton"),
            const_source(INVOICES_PATH, "SendInvoiceEmailButton"),
        ])

        for forbidden in (
            "taxable_base",
            "vat_amount",
            "total_amount",
            "invoice_snapshot",
            "client_cif",
            "client_address",
            "recipient",
            "subject",
            "filename:",
            "output_path",
            "invoice_number:",
        ):
            self.assertNotIn(forbidden, text)

    def test_invoice_list_shows_status_columns_and_actions(self):
        table = const_source(INVOICES_PATH, "InvoiceListTable")

        for expected in (
            "<th>PDF</th>",
            "<th>Contabilidad</th>",
            "<th>Email</th>",
            "<InvoicePdfActionButton />",
            "<RecordAccountingButton />",
            "<SendInvoiceEmailButton />",
            "record.pdf_available",
            "record.accounting_entry_status",
            "record.email_status",
        ):
            self.assertIn(expected, table)

    def test_invoice_edit_exposes_status_fields_and_manual_actions(self):
        text = source(INVOICES_PATH)
        start = text.index("export const InvoiceEdit")
        edit = text[start:]

        for expected in (
            'source="invoice_type"',
            'source="email_status"',
            'source="accounting_entry_status"',
            "<InvoicePdfActionButton />",
            "<RecordAccountingButton />",
            "<SendInvoiceEmailButton />",
        ):
            self.assertIn(expected, edit)

    def test_backend_invoice_admin_serialization_exposes_required_fields(self):
        models = source(MODELS_PATH)
        invoice_class = models[models.index("class Invoices(db.Model):"):models.index("class InvoiceFiscalSubmission(db.Model):")]
        block = invoice_class[
            invoice_class.index("def serialize_admin(self):"):invoice_class.index("def serialize(self):")
        ]

        for expected in (
            '"invoice_type": self.invoice_type',
            '"pdf_available": bool(self.pdf_path)',
            '"invoice_snapshot_schema_version": self.invoice_snapshot_schema_version',
            '"email_status": self.email_status',
            '"email_sent_at": self.email_sent_at.isoformat() if self.email_sent_at else None',
            '"email_attempts": self.email_attempts',
            '"accounting_entry_id": sale_accounting_entry.id if sale_accounting_entry else None',
            '"accounting_entry_status": sale_accounting_entry.status if sale_accounting_entry else None',
        ):
            self.assertIn(expected, block)

    def test_admin_styles_support_success_buttons_and_status_chips(self):
        styles = source(CSS_PATH)

        for expected in (
            ".admin-action-button--success",
            ".admin-status-chip",
            ".admin-status-chip--success",
            ".admin-status-chip--warning",
            ".admin-native-table--invoices",
            "min-width: 1700px",
        ):
            self.assertIn(expected, styles)


if __name__ == "__main__":
    unittest.main()

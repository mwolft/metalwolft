import copy
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


try:
    HAS_FLASK_MAIL = importlib.util.find_spec("flask_mail") is not None
except (ImportError, ValueError):
    HAS_FLASK_MAIL = False

if not HAS_FLASK_MAIL:
    fake_flask_mail = types.ModuleType("flask_mail")

    class ImportOnlyFakeMessage:
        def __init__(self, *args, **kwargs):
            raise AssertionError("Tests patch adapter Message before use")

    fake_flask_mail.Message = ImportOnlyFakeMessage
    sys.modules["flask_mail"] = fake_flask_mail

from api.flask_mail_invoice_adapter import (  # noqa: E402
    FlaskMailInvoiceAdapter,
    FlaskMailInvoiceAdapterError,
)
from api.invoice_email_service import InvoiceEmailAttachment, InvoiceEmailMessage  # noqa: E402


class CapturedFlaskMessage:
    created = []

    def __init__(self, subject=None, recipients=None, body=None, **kwargs):
        self.subject = subject
        self.recipients = recipients or []
        self.body = body
        self.attachments = []
        CapturedFlaskMessage.created.append(self)

    def attach(self, filename=None, content_type=None, data=None, **kwargs):
        self.attachments.append({
            "filename": filename,
            "content_type": content_type,
            "data": data,
        })


class FakeMail:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.sent = []

    def send(self, message):
        if self.fail:
            raise RuntimeError("smtp password leaked in provider error")
        self.sent.append(message)


def invoice_message(**overrides):
    data = {
        "subject": "Factura F2026000001 - MetalWolft",
        "recipients": ("cliente@example.com",),
        "body": "Adjuntamos tu factura.",
        "attachments": (
            InvoiceEmailAttachment(
                filename="invoice_F2026000001.pdf",
                content_type="application/pdf",
                data=b"%PDF-1.4\n%%EOF",
            ),
        ),
    }
    data.update(overrides)
    return InvoiceEmailMessage(**data)


class FlaskMailInvoiceAdapterTest(unittest.TestCase):
    def setUp(self):
        CapturedFlaskMessage.created = []
        self.message_patch = patch(
            "api.flask_mail_invoice_adapter.Message",
            CapturedFlaskMessage,
        )
        self.message_patch.start()

    def tearDown(self):
        self.message_patch.stop()

    def test_converts_subject_recipients_and_body(self):
        mail = FakeMail()
        message = invoice_message()

        FlaskMailInvoiceAdapter(mail).send(message)

        sent = mail.sent[0]
        self.assertEqual(sent.subject, "Factura F2026000001 - MetalWolft")
        self.assertEqual(sent.recipients, ["cliente@example.com"])
        self.assertEqual(sent.body, "Adjuntamos tu factura.")

    def test_attaches_pdf_with_mime_and_bytes(self):
        mail = FakeMail()
        message = invoice_message()

        FlaskMailInvoiceAdapter(mail).send(message)

        attachment = mail.sent[0].attachments[0]
        self.assertEqual(attachment["filename"], "invoice_F2026000001.pdf")
        self.assertEqual(attachment["content_type"], "application/pdf")
        self.assertEqual(attachment["data"], b"%PDF-1.4\n%%EOF")

    def test_calls_mail_send_once(self):
        mail = FakeMail()

        FlaskMailInvoiceAdapter(mail).send(invoice_message())

        self.assertEqual(len(mail.sent), 1)
        self.assertEqual(len(CapturedFlaskMessage.created), 1)

    def test_does_not_modify_invoice_email_message(self):
        mail = FakeMail()
        message = invoice_message()
        before = copy.deepcopy(message)

        FlaskMailInvoiceAdapter(mail).send(message)

        self.assertEqual(message, before)

    def test_missing_message_subject_or_recipients_are_invalid(self):
        adapter = FlaskMailInvoiceAdapter(FakeMail())

        with self.assertRaises(FlaskMailInvoiceAdapterError):
            adapter.send(None)
        with self.assertRaises(FlaskMailInvoiceAdapterError):
            adapter.send(invoice_message(subject=" "))
        with self.assertRaises(FlaskMailInvoiceAdapterError):
            adapter.send(invoice_message(recipients=()))
        with self.assertRaises(FlaskMailInvoiceAdapterError):
            adapter.send(invoice_message(recipients=(" ",)))

    def test_invalid_attachment_is_blocked(self):
        adapter = FlaskMailInvoiceAdapter(FakeMail())

        invalid_attachments = (
            (),
            (InvoiceEmailAttachment("../invoice.pdf", "application/pdf", b"x"),),
            (InvoiceEmailAttachment("folder/invoice.pdf", "application/pdf", b"x"),),
            (InvoiceEmailAttachment("invoice.txt", "application/pdf", b"x"),),
            (InvoiceEmailAttachment("invoice.pdf", "", b"x"),),
            (InvoiceEmailAttachment("invoice.pdf", "application/pdf", b""),),
            (InvoiceEmailAttachment("invoice.pdf", "application/pdf", "not-bytes"),),
        )
        for attachments in invalid_attachments:
            with self.subTest(attachments=attachments):
                with self.assertRaises(FlaskMailInvoiceAdapterError):
                    adapter.send(invoice_message(attachments=attachments))

    def test_smtp_error_is_wrapped_and_cause_is_preserved(self):
        adapter = FlaskMailInvoiceAdapter(FakeMail(fail=True))

        with self.assertRaises(FlaskMailInvoiceAdapterError) as context:
            adapter.send(invoice_message())

        self.assertIsInstance(context.exception.__cause__, RuntimeError)
        self.assertNotIn("smtp password", str(context.exception))

    def test_adapter_can_work_with_fake_mailer(self):
        mail = FakeMail()

        FlaskMailInvoiceAdapter(mail).send(invoice_message())

        self.assertEqual(mail.sent[0].subject, "Factura F2026000001 - MetalWolft")


class FlaskMailInvoiceAdapterSourceTest(unittest.TestCase):
    def test_adapter_is_the_only_layer_importing_flask_mail(self):
        adapter_source = (SRC_DIR / "api/flask_mail_invoice_adapter.py").read_text(encoding="utf-8")
        domain_source = (SRC_DIR / "api/invoice_email_service.py").read_text(encoding="utf-8")

        self.assertIn("from flask_mail import Message", adapter_source)
        self.assertNotIn("flask_mail", domain_source)
        self.assertNotIn("from flask", domain_source)

    def test_adapter_does_not_import_accounting_verifactu_or_domain_services(self):
        source = (SRC_DIR / "api/flask_mail_invoice_adapter.py").read_text(encoding="utf-8")

        for forbidden in (
            "AccountingEntry",
            "export_sales_accounting_entries",
            "InvoiceFiscalSubmission",
            "create_pending_submission",
            "send_invoice_email",
            "current_app",
        ):
            self.assertNotIn(forbidden, source)

    def test_application_context_dependency_is_limited_to_adapter_boundary(self):
        source = (SRC_DIR / "api/flask_mail_invoice_adapter.py").read_text(encoding="utf-8")

        self.assertIn("Message(", source)
        self.assertIn("self.mail.send(flask_message)", source)
        self.assertNotIn("sender=", source)


if __name__ == "__main__":
    unittest.main()

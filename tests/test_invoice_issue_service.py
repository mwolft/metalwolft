import sys
import importlib.util
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import mock_open, patch

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if importlib.util.find_spec("flask_sqlalchemy") is None:
    fake_models = types.ModuleType("api.models")
    fake_models.Invoices = SimpleNamespace(generate_next_invoice_number=lambda: "TEST-001")
    fake_models.Products = SimpleNamespace(query=SimpleNamespace(get=lambda product_id: None))
    sys.modules["api.models"] = fake_models

from api.invoice_email_service import send_invoice_email
from api.invoice_issue_service import issue_invoice_for_order


class FakeDbSession:
    def __init__(self):
        self.added = []

    def add(self, item):
        self.added.append(item)


class FakeInvoice:
    generated_numbers = []

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def generate_next_invoice_number():
        FakeInvoice.generated_numbers.append("NOV-2025-001")
        return "NOV-2025-001"


class FakeProductQuery:
    def get(self, product_id):
        return SimpleNamespace(nombre=f"Producto {product_id}")


class FakeProducts:
    query = FakeProductQuery()


class FakeOrderDetail:
    def __init__(self, order):
        self.order = order

    def serialize(self):
        return {
            "product_id": 7,
            "quantity": 1,
            "invoice_number": self.order.invoice_number,
        }


def customer_context():
    return {
        "firstname": "Sergio",
        "lastname": "Arias",
        "phone": "600000000",
        "shipping_address": "Calle envio",
        "shipping_city": "Ciudad envio",
        "shipping_postal_code": "13000",
        "billing_address": "Calle factura",
        "billing_city": "Ciudad factura",
        "billing_postal_code": "13001",
        "CIF": "00000000T",
    }


def checkout_quote():
    return {
        "discount_percent": 10,
        "lines": [
            {
                "producto_id": 7,
                "quantity": 1,
                "alto": 30,
                "ancho": 30,
                "anclaje": "Sin obra: con agujeros interiores",
                "color": "satinado_blanco",
                "precio_total": 95.0,
            }
        ],
    }


class InvoiceIssueServiceTest(unittest.TestCase):
    def setUp(self):
        FakeInvoice.generated_numbers = []

    def build_order(self):
        order = SimpleNamespace(
            id=123,
            total_amount=116.0,
            shipping_cost=21.0,
            discount_value=0.0,
            discount_code=None,
            invoice_number=None,
            order_details=[],
        )
        order.order_details = [FakeOrderDetail(order)]
        return order

    def test_service_creates_invoice_assigns_order_number_and_returns_paths(self):
        order = self.build_order()
        db_session = FakeDbSession()
        renderer_calls = []

        def fake_renderer(**kwargs):
            renderer_calls.append(kwargs)
            return b"%PDF-test"

        invoice_folder = str(ROOT_DIR / "invoice-test-output")
        opened_file = mock_open()

        with patch("api.invoice_issue_service.Invoices", FakeInvoice), patch(
            "api.invoice_issue_service.Products", FakeProducts
        ), patch("api.invoice_issue_service.os.makedirs") as makedirs, patch(
            "builtins.open", opened_file
        ):
            result = issue_invoice_for_order(
                order=order,
                order_details=checkout_quote()["lines"],
                customer_context=customer_context(),
                checkout_quote=checkout_quote(),
                invoice_folder=invoice_folder,
                db_session=db_session,
                renderer=fake_renderer,
            )

        self.assertEqual(result.invoice_number, "NOV-2025-001")
        self.assertEqual(result.pdf_filename, "invoice_NOV-2025-001.pdf")
        self.assertEqual(result.pdf_path, "/api/download-invoice/invoice_NOV-2025-001.pdf")
        self.assertEqual(order.invoice_number, "NOV-2025-001")
        self.assertEqual(len(db_session.added), 1)
        self.assertEqual(db_session.added[0], result.invoice)
        self.assertEqual(result.invoice.order_id, 123)
        self.assertEqual(result.invoice.amount, 116.0)
        makedirs.assert_called_once_with(invoice_folder, exist_ok=True)
        opened_file.assert_called_once_with(result.file_path, "wb")
        opened_file().write.assert_called_once_with(b"%PDF-test")
        self.assertEqual(renderer_calls[0]["order_details"][0]["product_name"], "Producto 7")

    def test_error_before_commit_is_propagated_without_creating_invoice(self):
        order = self.build_order()
        db_session = FakeDbSession()

        def failing_renderer(**kwargs):
            raise RuntimeError("renderer failed")

        invoice_folder = str(ROOT_DIR / "invoice-test-output")
        with patch("api.invoice_issue_service.Invoices", FakeInvoice), patch(
            "api.invoice_issue_service.Products", FakeProducts
        ), patch("api.invoice_issue_service.os.makedirs"), patch("builtins.open", mock_open()) as opened_file:
            with self.assertRaisesRegex(RuntimeError, "renderer failed"):
                issue_invoice_for_order(
                    order=order,
                    order_details=checkout_quote()["lines"],
                    customer_context=customer_context(),
                    checkout_quote=checkout_quote(),
                    invoice_folder=invoice_folder,
                    db_session=db_session,
                    renderer=failing_renderer,
                )

        self.assertEqual(db_session.added, [])
        self.assertIsNone(order.invoice_number)
        opened_file.assert_not_called()


class InvoiceEmailServiceTest(unittest.TestCase):
    def test_email_service_uses_current_invoice_email_contract(self):
        sent = []
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: None)
        invoice_result = SimpleNamespace(invoice_number="NOV-2025-001", file_path="/tmp/invoice.pdf")
        user = SimpleNamespace(email="cliente@example.com")

        send_invoice_email(
            user=user,
            invoice_result=invoice_result,
            customer_firstname="Sergio",
            customer_lastname="Arias",
            mail_username="admin@example.com",
            logger=logger,
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        )

        self.assertEqual(sent[0]["subject"], "Factura de tu pedido #NOV-2025-001")
        self.assertEqual(sent[0]["recipients"], ["cliente@example.com", "admin@example.com"])
        self.assertIn("Adjuntamos la factura NOV-2025-001", sent[0]["body"])
        self.assertEqual(sent[0]["attachment_path"], "/tmp/invoice.pdf")

    def test_email_error_does_not_escape_service(self):
        errors = []
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: errors.append(args))
        invoice_result = SimpleNamespace(invoice_number="NOV-2025-001", file_path="/tmp/invoice.pdf")
        user = SimpleNamespace(email="cliente@example.com")

        send_invoice_email(
            user=user,
            invoice_result=invoice_result,
            customer_firstname="Sergio",
            customer_lastname="Arias",
            mail_username="admin@example.com",
            logger=logger,
            send_email_func=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("smtp down")),
        )

        self.assertTrue(errors)


class InvoiceFinalizerSourceRegressionTest(unittest.TestCase):
    def test_email_happens_after_main_commit(self):
        source = (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")
        start = source.index("def _finalize_order_from_checkout_quote")
        end = source.index("@api.route('/delivery-estimate'")
        finalizer_source = source[start:end]

        self.assertLess(
            finalizer_source.index("db.session.commit()"),
            finalizer_source.index("send_invoice_email("),
        )

    def test_existing_checkout_session_returns_before_issuing_invoice(self):
        source = (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")
        start = source.index("def _finalize_order_from_checkout_quote")
        end = source.index("@api.route('/delivery-estimate'")
        finalizer_source = source[start:end]

        self.assertLess(
            finalizer_source.index("if checkout_session and checkout_session.order_id:"),
            finalizer_source.index("issue_invoice_for_order("),
        )

    def test_stripe_and_paypal_still_use_shared_finalizer(self):
        source = (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")

        paypal_webhook = source[
            source.index("def paypal_webhook"):source.index("@api.route('/webhook'")
        ]
        stripe_webhook = source[
            source.index("def stripe_webhook"):source.index("@api.route('/checkout/quote'")
        ]

        self.assertIn("_finalize_order_from_checkout_quote(", paypal_webhook)
        self.assertIn("_finalize_order_from_checkout_quote(", stripe_webhook)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.order_confirmation_email_service import send_order_confirmation_email


def checkout_quote():
    return {
        "lines": [
            {
                "product_id": 7,
                "product_name": "Reja fija Pittsburgh",
                "quantity": 2,
                "alto": 30,
                "ancho": 30,
                "anclaje": "Sin obra: con agujeros interiores",
                "color": "satinado_blanco",
                "unit_price": 95.0,
                "line_total": 190.0,
            }
        ],
        "subtotal": 190.0,
        "shipping_cost": 0.0,
        "discount_amount": 9.5,
        "total_amount": 180.5,
    }


class OrderConfirmationEmailServiceTest(unittest.TestCase):
    def test_email_uses_order_confirmation_contract_without_attachment_or_invoice_text(self):
        sent = []
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: None)
        user = SimpleNamespace(email="cliente@example.com")
        order = SimpleNamespace(locator="AB1234", total_amount=180.5)

        send_order_confirmation_email(
            user=user,
            order=order,
            checkout_quote=checkout_quote(),
            customer_firstname="Sergio",
            mail_username="admin@example.com",
            logger=logger,
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        )

        self.assertEqual(sent[0]["subject"], "Hemos recibido tu pedido AB1234")
        self.assertEqual(sent[0]["recipients"], ["cliente@example.com", "admin@example.com"])
        self.assertNotIn("attachment_path", sent[0])
        self.assertNotIn("Factura", sent[0]["subject"])
        self.assertNotIn("factura", sent[0]["body"].lower())
        self.assertIn("Pedido: AB1234", sent[0]["body"])
        self.assertIn("Estado del pago: confirmado", sent[0]["body"])
        self.assertIn("Reja fija Pittsburgh", sent[0]["body"])
        self.assertIn("Cantidad: 2", sent[0]["body"])
        self.assertIn("Total: 180.50 €", sent[0]["body"])

    def test_email_error_does_not_escape_service(self):
        errors = []
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: errors.append(args))
        user = SimpleNamespace(email="cliente@example.com")
        order = SimpleNamespace(locator="AB1234", total_amount=180.5)

        send_order_confirmation_email(
            user=user,
            order=order,
            checkout_quote=checkout_quote(),
            customer_firstname="Sergio",
            mail_username="admin@example.com",
            logger=logger,
            send_email_func=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("smtp down")),
        )

        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()

import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

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
                "screw_option": "long_150",
                "screw_length_mm": 150,
                "screw_supplement": 8.95,
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
    def test_email_uses_multipart_order_contract_without_attachment_or_invoice_text(self):
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
        self.assertIn("Color: Blanco liso", sent[0]["body"])
        self.assertIn("Instalación: Agujeros interiores", sent[0]["body"])
        self.assertIn("Tornillos: 150 mm (+8,95 €)", sent[0]["body"])
        self.assertIn("Envío: GRATIS", sent[0]["body"])
        self.assertIn("TOTAL: 180,50 €", sent[0]["body"])
        self.assertIn("<!doctype html>", sent[0]["html"])
        self.assertIn("Blanco liso", sent[0]["html"])
        self.assertIn("Pago confirmado", sent[0]["html"])

    def test_missing_line_total_is_not_recalculated_from_unit_price(self):
        sent = []
        errors = []
        logger = SimpleNamespace(
            info=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: errors.append(args),
        )
        quote_without_line_total = copy.deepcopy(checkout_quote())
        del quote_without_line_total["lines"][0]["line_total"]

        send_order_confirmation_email(
            user=SimpleNamespace(email="cliente@example.com"),
            order=SimpleNamespace(locator="AB1234", total_amount=180.5),
            checkout_quote=quote_without_line_total,
            customer_firstname="Sergio",
            mail_username="admin@example.com",
            logger=logger,
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        )

        self.assertEqual(sent, [])
        logged_text = " ".join(str(value) for args in errors for value in args)
        self.assertIn("TransactionalEmailRenderError", logged_text)
        self.assertNotIn("95.0", logged_text)

    def test_uses_authoritative_line_total_and_standard_screw_label(self):
        sent = []
        quote = checkout_quote()
        quote["lines"][0].update({
            "unit_price": 1.0,
            "line_total": 191.23,
            "screw_option": "standard",
            "screw_length_mm": 100,
            "screw_supplement": 0,
        })

        send_order_confirmation_email(
            user=SimpleNamespace(email="cliente@example.com"),
            order=SimpleNamespace(locator="AB1234", total_amount=180.5),
            checkout_quote=quote,
            customer_firstname="Sergio",
            mail_username="admin@example.com",
            logger=SimpleNamespace(
                info=lambda *args, **kwargs: None,
                error=lambda *args, **kwargs: None,
            ),
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        )

        self.assertIn("Importe: 191,23 €", sent[0]["body"])
        self.assertIn("Tornillos: 100 mm incluidos", sent[0]["body"])
        self.assertNotIn("Importe: 2,00 €", sent[0]["body"])

    def test_real_flask_mail_mime_contains_plain_text_and_html(self):
        from api import email_routes

        sent = []
        logger = SimpleNamespace(
            info=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: None,
        )
        send_order_confirmation_email(
            user=SimpleNamespace(email="cliente@example.com"),
            order=SimpleNamespace(locator="AB1234", total_amount=180.5),
            checkout_quote=checkout_quote(),
            customer_firstname="Sergio",
            mail_username="admin@example.com",
            logger=logger,
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        )

        app = Flask(__name__)
        app.config.update(
            MAIL_DEFAULT_SENDER="no-reply@metalwolft.com",
            MAIL_SUPPRESS_SEND=True,
        )
        email_routes.mail.init_app(app)
        with app.app_context():
            with patch.object(email_routes.mail, "send") as send:
                self.assertTrue(email_routes.send_email(**sent[0]))
                mime_message = send.call_args.args[0]._message()

        content_types = [part.get_content_type() for part in mime_message.walk()]
        self.assertIn("multipart/alternative", content_types)
        self.assertIn("text/plain", content_types)
        self.assertIn("text/html", content_types)
        self.assertNotIn("application/pdf", content_types)

    def test_email_error_does_not_escape_service_or_log_provider_details(self):
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
            send_email_func=lambda **kwargs: (_ for _ in ()).throw(
                RuntimeError("smtp password secret")
            ),
        )

        self.assertTrue(errors)
        logged_text = " ".join(str(value) for args in errors for value in args)
        self.assertIn("RuntimeError", logged_text)
        self.assertNotIn("smtp password", logged_text)
        self.assertNotIn("secret", logged_text)

    def test_generic_transport_logging_does_not_include_raw_exception(self):
        from api import email_routes

        source = (SRC_DIR / "api/email_routes.py").read_text(encoding="utf-8")
        send_email_source = source[
            source.index("def send_email("):source.index("def get_admin_recipients")
        ]

        self.assertIn("type(exc).__name__", send_email_source)
        self.assertNotIn("str(exc)", send_email_source)
        self.assertNotIn("str(e)", send_email_source)

        app = Flask(__name__)
        app.config.update(
            MAIL_DEFAULT_SENDER="no-reply@metalwolft.com",
            MAIL_SUPPRESS_SEND=True,
        )
        email_routes.mail.init_app(app)
        with app.app_context():
            with patch.object(
                email_routes.mail,
                "send",
                side_effect=RuntimeError("smtp password secret"),
            ), patch.object(app.logger, "error") as log_error:
                self.assertFalse(
                    email_routes.send_email(
                        subject="Pedido",
                        recipients=["cliente@example.com"],
                        body="Texto",
                        html="<p>Texto</p>",
                    )
                )

        logged_text = " ".join(str(value) for value in log_error.call_args.args)
        self.assertIn("RuntimeError", logged_text)
        self.assertNotIn("smtp password", logged_text)
        self.assertNotIn("secret", logged_text)


if __name__ == "__main__":
    unittest.main()

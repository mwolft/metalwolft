import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.cart_reminder_service import (
    CartReminderDeliveryError,
    CartReminderEligibility,
    evaluate_cart_reminder_eligibility,
    send_manual_cart_reminder,
)


def user(**overrides):
    values = {
        "id": 7,
        "email": "cliente@example.com",
        "firstname": "Sergio",
        "is_admin": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def cart_item(**overrides):
    values = {
        "producto_id": 4,
        "product": SimpleNamespace(nombre="Reja fija Albany", imagen=None),
        "alto": 100,
        "ancho": 80,
        "anclaje": "Sin obra: con agujeros interiores",
        "color": "forja_negro",
        "screw_length_mm": 150,
        "screw_supplement": 8.95,
        "precio_total": "139.00",
        "quantity": 2,
        "added_at": "2026-08-09T10:00:00",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class CartReminderEligibilityTest(unittest.TestCase):
    def test_cart_with_email_and_no_later_order_is_eligible(self):
        eligibility = evaluate_cart_reminder_eligibility(
            user=user(),
            cart_items=[cart_item()],
            latest_cart_added_at="2026-08-09T10:00:00",
            later_order=None,
        )

        self.assertTrue(eligibility.eligible)
        self.assertIsNone(eligibility.reason)

    def test_empty_cart_and_missing_email_are_not_eligible(self):
        empty_cart = evaluate_cart_reminder_eligibility(
            user=user(), cart_items=[], latest_cart_added_at=None, later_order=None
        )
        missing_email = evaluate_cart_reminder_eligibility(
            user=user(email=""), cart_items=[cart_item()], latest_cart_added_at=None, later_order=None
        )

        self.assertFalse(empty_cart.eligible)
        self.assertIn("carrito", empty_cart.reason)
        self.assertFalse(missing_email.eligible)
        self.assertIn("email", missing_email.reason)

    def test_later_order_makes_cart_ineligible(self):
        eligibility = evaluate_cart_reminder_eligibility(
            user=user(),
            cart_items=[cart_item()],
            latest_cart_added_at="2026-08-09T10:00:00",
            later_order=SimpleNamespace(id=22),
        )

        self.assertFalse(eligibility.eligible)
        self.assertIn("pedido posterior", eligibility.reason)


class CartReminderDeliveryTest(unittest.TestCase):
    def test_manual_send_uses_saved_cart_values_and_renders_html_text_and_cta(self):
        sent = []
        eligibility = CartReminderEligibility(
            eligible=True,
            reason=None,
            cart_items=(
                cart_item(
                    product=SimpleNamespace(
                        nombre="<Albany>", imagen="https://example.com/albany.jpg"
                    )
                ),
            ),
            latest_cart_added_at=None,
            later_order=None,
        )
        logger = SimpleNamespace(info=lambda *args, **kwargs: None)

        with patch("api.cart_reminder_service.get_cart_reminder_eligibility", return_value=eligibility):
            send_manual_cart_reminder(
                db_session=object(),
                user=user(),
                cart_url="https://www.metalwolft.com/cart",
                logger=logger,
                send_email_func=lambda **kwargs: sent.append(kwargs) or True,
            )

        self.assertEqual(sent[0]["recipients"], ["cliente@example.com"])
        self.assertEqual(sent[0]["subject"], "Tu carrito sigue listo | MetalWolft")
        self.assertIn("RESUMEN DEL CARRITO", sent[0]["body"])
        self.assertIn("278,00", sent[0]["body"])
        self.assertIn("Total: 278,00", sent[0]["body"])
        self.assertIn(">Total</td>", sent[0]["html"])
        self.assertIn("Volver a mi carrito: https://www.metalwolft.com/cart", sent[0]["body"])
        self.assertIn("Volver a mi carrito", sent[0]["html"])
        self.assertIn('href="https://www.metalwolft.com/cart"', sent[0]["html"])
        self.assertIn("&lt;Albany&gt;", sent[0]["html"])
        self.assertNotIn("<Albany>", sent[0]["html"])
        self.assertIn('src="https://example.com/albany.jpg"', sent[0]["html"])

    def test_manual_send_omits_product_image_when_none_is_available(self):
        sent = []
        eligibility = CartReminderEligibility(True, None, (cart_item(),), None, None)
        with patch("api.cart_reminder_service.get_cart_reminder_eligibility", return_value=eligibility):
            send_manual_cart_reminder(
                db_session=object(),
                user=user(),
                cart_url="https://www.metalwolft.com/cart",
                logger=SimpleNamespace(info=lambda *args, **kwargs: None),
                send_email_func=lambda **kwargs: sent.append(kwargs) or True,
            )

        self.assertNotIn('<img src=', sent[0]["html"])

    def test_transport_failure_is_explicit(self):
        eligibility = CartReminderEligibility(True, None, (cart_item(),), None, None)
        with patch("api.cart_reminder_service.get_cart_reminder_eligibility", return_value=eligibility):
            with self.assertRaises(CartReminderDeliveryError):
                send_manual_cart_reminder(
                    db_session=object(),
                    user=user(),
                    cart_url="https://www.metalwolft.com/cart",
                    logger=SimpleNamespace(info=lambda *args, **kwargs: None),
                    send_email_func=lambda **kwargs: False,
                )


class CartReminderAdminSourceTest(unittest.TestCase):
    def test_flask_admin_exposes_cart_action_not_user_action(self):
        source = (SRC_DIR / "api" / "admin.py").read_text(encoding="utf-8")

        self.assertIn("def _format_cart_reminder", source)
        self.assertIn("get_cart_reminder_eligibility", source)
        self.assertIn("class CartAdminView", source)
        self.assertIn("'cart_reminder'", source)
        self.assertIn("@expose('/send-cart-reminder/<int:cart_id>', methods=['POST'])", source)
        self.assertNotIn("def _format_user_cart_reminder", source)
        self.assertNotIn("@expose('/send-cart-reminder/<int:user_id>', methods=['POST'])", source)
        self.assertIn("send_manual_cart_reminder(", source)
        self.assertIn("Enviar recordatorio", source)


if __name__ == "__main__":
    unittest.main()

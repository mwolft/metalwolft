import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.email_routes import OrderUpdateEmailChange, send_order_update_email  # noqa: E402


class OrderStatusEmailTest(unittest.TestCase):
    @staticmethod
    def _logger():
        return SimpleNamespace(
            warning=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: None,
        )

    @staticmethod
    def _order(*, user=None, context=None, checkout_session=None):
        return SimpleNamespace(
            id=42,
            user=user,
            confirmed_order_context=context,
            checkout_session=checkout_session,
            locator="QE2885",
            order_status="pintura",
            estimated_delivery_at=date(2026, 9, 15),
            estimated_delivery_note="Preparación de la expedición",
        )

    @staticmethod
    def _change(
        *,
        old_status="pendiente",
        new_status="pintura",
        old_date=None,
        new_date=date(2026, 9, 15),
        old_note=None,
        new_note="Preparación de la expedición",
        options=None,
    ):
        return OrderUpdateEmailChange(
            old_order_status=old_status,
            new_order_status=new_status,
            old_estimated_delivery_at=old_date,
            new_estimated_delivery_at=new_date,
            old_estimated_delivery_note=old_note,
            new_estimated_delivery_note=new_note,
            status_email_options=options,
        )

    def test_guest_status_update_uses_confirmed_customer_snapshot(self):
        sent = []
        order = self._order(
            context=SimpleNamespace(customer_snapshot={"email": "guest@example.com"}),
        )

        self.assertTrue(send_order_update_email(
            order=order,
            change=self._change(old_date=date(2026, 9, 10), new_date=date(2026, 9, 15)),
            logger=self._logger(),
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        ))

        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["subject"], "Actualización de tu pedido: Pintura")
        self.assertEqual(sent[0]["recipients"], ["guest@example.com"])
        self.assertIn("Estado de tu pedido", sent[0]["html"])
        self.assertIn("QE2885", sent[0]["body"])

    def test_guest_delivery_update_uses_confirmed_customer_snapshot(self):
        sent = []
        order = self._order(
            context=SimpleNamespace(customer_snapshot={"email": "guest@example.com"}),
        )

        self.assertTrue(send_order_update_email(
            order=order,
            change=self._change(
                old_status="pintura",
                new_status="pintura",
                old_date=date(2026, 9, 10),
                new_date=date(2026, 9, 15),
            ),
            logger=self._logger(),
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        ))

        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["subject"], "Actualización: entrega estimada de tu pedido")
        self.assertEqual(sent[0]["recipients"], ["guest@example.com"])
        self.assertIn("Actualización de entrega", sent[0]["html"])

    def test_recipient_priority_is_confirmation_then_checkout_then_user(self):
        sent = []
        confirmation_order = self._order(
            user=SimpleNamespace(email="account@example.com"),
            context=SimpleNamespace(customer_snapshot={"email": "frozen@example.com"}),
        )
        checkout_order = self._order(
            user=SimpleNamespace(email="account@example.com"),
            checkout_session=SimpleNamespace(customer_snapshot={"email": "legacy@example.com"}),
        )
        historical_order = self._order(user=SimpleNamespace(email="account@example.com"))

        for order in (confirmation_order, checkout_order, historical_order):
            self.assertTrue(send_order_update_email(
                order=order,
                change=self._change(old_date=date(2026, 9, 10), new_date=date(2026, 9, 15)),
                logger=self._logger(),
                send_email_func=lambda **kwargs: sent.append(kwargs) or True,
            ))

        self.assertEqual(
            [message["recipients"][0] for message in sent],
            ["frozen@example.com", "legacy@example.com", "account@example.com"],
        )

    def test_same_values_do_not_send_an_email(self):
        sent = []
        order = self._order(user=SimpleNamespace(email="cliente@example.com"))

        self.assertFalse(send_order_update_email(
            order=order,
            change=self._change(
                old_status="pintura",
                new_status="pintura",
                old_date=date(2026, 9, 15),
                new_date=date(2026, 9, 15),
                old_note="Preparación de la expedición",
                new_note="Preparación de la expedición",
            ),
            logger=self._logger(),
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        ))

        self.assertEqual(sent, [])

    def test_status_and_delivery_change_sends_only_status_email(self):
        sent = []
        order = self._order(user=SimpleNamespace(email="cliente@example.com"))

        self.assertTrue(send_order_update_email(
            order=order,
            change=self._change(old_date=date(2026, 9, 10), new_date=date(2026, 9, 15)),
            logger=self._logger(),
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        ))

        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["subject"], "Actualización de tu pedido: Pintura")
        self.assertIn("15/09/2026", sent[0]["body"])

    def test_sent_and_delivered_controls_preserve_selected_guides(self):
        sent = []
        order = self._order(user=SimpleNamespace(email="cliente@example.com"))
        order.order_status = "enviado"

        self.assertTrue(send_order_update_email(
            order=order,
            change=self._change(
                new_status="enviado",
                options={
                    "status": "enviado",
                    "send_email": True,
                    "include_receipt_guide": True,
                    "include_installation_guide": False,
                    "include_incident_form": True,
                },
            ),
            logger=self._logger(),
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        ))
        self.assertIn("Guía de recepción del pedido", sent[0]["body"])
        self.assertIn("Formulario de incidencias", sent[0]["body"])
        self.assertNotIn("Ver guía de instalación", sent[0]["body"])

        order.order_status = "entregado"
        self.assertTrue(send_order_update_email(
            order=order,
            change=self._change(
                old_status="enviado",
                new_status="entregado",
                options={
                    "status": "entregado",
                    "send_email": True,
                    "include_installation_guide": False,
                    "include_maintenance_guide": True,
                },
            ),
            logger=self._logger(),
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        ))
        self.assertIn("Mantenimiento y acabado", sent[1]["body"])
        self.assertNotIn("Guía de instalación:", sent[1]["body"])

    def test_admin_can_suppress_sent_or_delivered_email(self):
        order = self._order(user=SimpleNamespace(email="cliente@example.com"))
        order.order_status = "enviado"

        self.assertFalse(send_order_update_email(
            order=order,
            change=self._change(
                new_status="enviado",
                options={"status": "enviado", "send_email": False},
            ),
            logger=self._logger(),
            send_email_func=lambda **kwargs: (_ for _ in ()).throw(AssertionError("No email expected")),
        ))

    def test_smtp_failure_is_logged_and_does_not_escape(self):
        errors = []
        order = self._order(user=SimpleNamespace(email="cliente@example.com"))
        logger = SimpleNamespace(
            warning=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: errors.append(args),
        )

        self.assertFalse(send_order_update_email(
            order=order,
            change=self._change(old_date=date(2026, 9, 10), new_date=date(2026, 9, 15)),
            logger=logger,
            send_email_func=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("smtp unavailable")),
        ))

        self.assertTrue(errors)
        self.assertIn("RuntimeError", " ".join(str(value) for args in errors for value in args))


if __name__ == "__main__":
    unittest.main()

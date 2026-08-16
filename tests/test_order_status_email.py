import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.email_routes import enviar_correo_cambio_estado_o_entrega  # noqa: E402


class OrderStatusEmailTest(unittest.TestCase):
    def test_status_update_uses_transactional_renderer_without_changing_subject_or_recipient(self):
        target = SimpleNamespace(
            user=SimpleNamespace(email="cliente@example.com"),
            locator="QE2885",
            order_status="pintura",
            estimated_delivery_at=SimpleNamespace(strftime=lambda _: "15/09/2026"),
            estimated_delivery_note="Preparaci\u00f3n de la expedici\u00f3n",
        )
        changed_attribute = SimpleNamespace(
            key="order_status",
            history=SimpleNamespace(has_changes=lambda: True),
        )
        sent = []

        with (
            patch("api.email_routes.sqla_inspect", return_value=SimpleNamespace(attrs=[changed_attribute])),
            patch("api.email_routes.send_email", side_effect=lambda **kwargs: sent.append(kwargs) or True),
        ):
            enviar_correo_cambio_estado_o_entrega(None, None, target)

        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["subject"], "Actualizaci\u00f3n de tu pedido: Pintura")
        self.assertEqual(sent[0]["recipients"], ["cliente@example.com"])
        self.assertIn("Estado de tu pedido", sent[0]["html"])
        self.assertIn("QE2885", sent[0]["body"])
        self.assertIn("15/09/2026", sent[0]["body"])
        self.assertIn("Completado: Recibido", sent[0]["body"])
        self.assertIn("<!doctype html>", sent[0]["html"])

    def test_delivery_update_uses_transactional_renderer_without_changing_subject_or_recipient(self):
        target = SimpleNamespace(
            user=SimpleNamespace(email="cliente@example.com"),
            locator="QE2885",
            order_status="pintura",
            estimated_delivery_at=SimpleNamespace(strftime=lambda _: "15/09/2026"),
            estimated_delivery_note="Preparaci\u00f3n de la expedici\u00f3n",
        )
        changed_attribute = SimpleNamespace(
            key="estimated_delivery_at",
            history=SimpleNamespace(has_changes=lambda: True),
        )
        sent = []

        with (
            patch("api.email_routes.sqla_inspect", return_value=SimpleNamespace(attrs=[changed_attribute])),
            patch("api.email_routes.send_email", side_effect=lambda **kwargs: sent.append(kwargs) or True),
        ):
            enviar_correo_cambio_estado_o_entrega(None, None, target)

        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["subject"], "Actualizaci\u00f3n: entrega estimada de tu pedido")
        self.assertEqual(sent[0]["recipients"], ["cliente@example.com"])
        self.assertIn("Actualizaci\u00f3n de entrega", sent[0]["html"])
        self.assertIn("QE2885", sent[0]["body"])
        self.assertIn("15/09/2026", sent[0]["body"])
        self.assertIn("<!doctype html>", sent[0]["html"])

    def test_sent_status_uses_admin_selected_links(self):
        target = SimpleNamespace(
            user=SimpleNamespace(email="cliente@example.com"),
            locator="QE2885",
            order_status="enviado",
            estimated_delivery_at=None,
            estimated_delivery_note=None,
            _admin_order_status_email_options={
                "status": "enviado",
                "send_email": True,
                "include_receipt_guide": True,
                "include_installation_guide": False,
                "include_incident_form": True,
            },
        )
        changed_attribute = SimpleNamespace(
            key="order_status",
            history=SimpleNamespace(has_changes=lambda: True),
        )
        sent = []

        with (
            patch("api.email_routes.sqla_inspect", return_value=SimpleNamespace(attrs=[changed_attribute])),
            patch("api.email_routes.send_email", side_effect=lambda **kwargs: sent.append(kwargs) or True),
        ):
            enviar_correo_cambio_estado_o_entrega(None, None, target)

        self.assertEqual(len(sent), 1)
        self.assertIn("Guía de recepción del pedido", sent[0]["body"])
        self.assertIn("Formulario de incidencias", sent[0]["body"])
        self.assertNotIn("Ver guía de instalación", sent[0]["body"])
        self.assertFalse(hasattr(target, "_admin_order_status_email_options"))

    def test_sent_status_can_skip_the_standard_email_from_admin(self):
        target = SimpleNamespace(
            user=SimpleNamespace(email="cliente@example.com"),
            locator="QE2885",
            order_status="enviado",
            estimated_delivery_at=None,
            estimated_delivery_note=None,
            _admin_order_status_email_options={"status": "enviado", "send_email": False},
        )
        changed_attribute = SimpleNamespace(
            key="order_status",
            history=SimpleNamespace(has_changes=lambda: True),
        )

        with (
            patch("api.email_routes.sqla_inspect", return_value=SimpleNamespace(attrs=[changed_attribute])),
            patch("api.email_routes.send_email") as send_email,
        ):
            enviar_correo_cambio_estado_o_entrega(None, None, target)

        send_email.assert_not_called()
        self.assertFalse(hasattr(target, "_admin_order_status_email_options"))

    def test_admin_sent_options_do_not_affect_another_status(self):
        target = SimpleNamespace(
            user=SimpleNamespace(email="cliente@example.com"),
            locator="QE2885",
            order_status="pintura",
            estimated_delivery_at=None,
            estimated_delivery_note=None,
            _admin_order_status_email_options={"status": "enviado", "send_email": False},
        )
        changed_attribute = SimpleNamespace(
            key="order_status",
            history=SimpleNamespace(has_changes=lambda: True),
        )
        sent = []

        with (
            patch("api.email_routes.sqla_inspect", return_value=SimpleNamespace(attrs=[changed_attribute])),
            patch("api.email_routes.send_email", side_effect=lambda **kwargs: sent.append(kwargs) or True),
        ):
            enviar_correo_cambio_estado_o_entrega(None, None, target)

        self.assertEqual(len(sent), 1)
        self.assertFalse(hasattr(target, "_admin_order_status_email_options"))

    def test_delivered_status_uses_admin_selected_guides(self):
        target = SimpleNamespace(
            user=SimpleNamespace(email="cliente@example.com"),
            locator="QE2885",
            order_status="entregado",
            estimated_delivery_at=None,
            estimated_delivery_note=None,
            _admin_order_status_email_options={
                "status": "entregado",
                "send_email": True,
                "include_installation_guide": False,
                "include_maintenance_guide": True,
            },
        )
        changed_attribute = SimpleNamespace(
            key="order_status",
            history=SimpleNamespace(has_changes=lambda: True),
        )
        sent = []

        with (
            patch("api.email_routes.sqla_inspect", return_value=SimpleNamespace(attrs=[changed_attribute])),
            patch("api.email_routes.send_email", side_effect=lambda **kwargs: sent.append(kwargs) or True),
        ):
            enviar_correo_cambio_estado_o_entrega(None, None, target)

        self.assertEqual(len(sent), 1)
        self.assertIn("Mantenimiento y acabado", sent[0]["body"])
        self.assertNotIn("Guía de instalación:", sent[0]["body"])
        self.assertFalse(hasattr(target, "_admin_order_status_email_options"))

    def test_delivered_status_can_skip_the_standard_email_from_admin(self):
        target = SimpleNamespace(
            user=SimpleNamespace(email="cliente@example.com"),
            locator="QE2885",
            order_status="entregado",
            estimated_delivery_at=None,
            estimated_delivery_note=None,
            _admin_order_status_email_options={"status": "entregado", "send_email": False},
        )
        changed_attribute = SimpleNamespace(
            key="order_status",
            history=SimpleNamespace(has_changes=lambda: True),
        )

        with (
            patch("api.email_routes.sqla_inspect", return_value=SimpleNamespace(attrs=[changed_attribute])),
            patch("api.email_routes.send_email") as send_email,
        ):
            enviar_correo_cambio_estado_o_entrega(None, None, target)

        send_email.assert_not_called()
        self.assertFalse(hasattr(target, "_admin_order_status_email_options"))


if __name__ == "__main__":
    unittest.main()

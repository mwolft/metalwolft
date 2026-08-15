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


if __name__ == "__main__":
    unittest.main()

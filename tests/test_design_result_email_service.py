import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.design_result_email_service import send_design_result_ready_email  # noqa: E402


class _Logger:
    def __init__(self):
        self.messages = []

    def info(self, *args, **kwargs):
        self.messages.append(("info", args, kwargs))

    def error(self, *args, **kwargs):
        self.messages.append(("error", args, kwargs))


class DesignResultEmailServiceTest(unittest.TestCase):
    def _design_request(self):
        confirmation_context = SimpleNamespace(
            customer_snapshot={
                "firstname": "Ana",
                "email": "frozen-customer@example.test",
            }
        )
        order = SimpleNamespace(
            id=42,
            confirmed_order_context=confirmation_context,
            user=SimpleNamespace(email="live-user@example.test", firstname="Live"),
        )
        return SimpleNamespace(
            reference="DP-0001",
            order=order,
            items=(
                SimpleNamespace(
                    product_name="Reja Maryland",
                    height_cm=120,
                    width_cm=200,
                ),
            ),
        )

    def test_uses_frozen_recipient_and_account_cta_without_attachment(self):
        sent = []
        delivered = send_design_result_ready_email(
            design_request=self._design_request(),
            frontend_url="https://www.metalwolft.com",
            mail_username="admin@example.test",
            logger=_Logger(),
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        )

        self.assertTrue(delivered)
        self.assertEqual(sent[0]["subject"], "Tu diseño previo DP-0001 está listo")
        self.assertEqual(
            sent[0]["recipients"],
            ["frozen-customer@example.test", "admin@example.test"],
        )
        self.assertIn("Alto 120 cm × Ancho 200 cm", sent[0]["body"])
        self.assertIn("/mi-cuenta/pedidos/42", sent[0]["html"])
        self.assertNotIn("attachments", sent[0])
        self.assertNotIn("design-results/", sent[0]["html"])

    def test_smtp_failure_is_best_effort_and_does_not_raise(self):
        logger = _Logger()
        delivered = send_design_result_ready_email(
            design_request=self._design_request(),
            frontend_url="https://www.metalwolft.com",
            mail_username="admin@example.test",
            logger=logger,
            send_email_func=lambda **kwargs: False,
        )

        self.assertFalse(delivered)
        self.assertTrue(any(level == "error" for level, _args, _kwargs in logger.messages))


if __name__ == "__main__":
    unittest.main()

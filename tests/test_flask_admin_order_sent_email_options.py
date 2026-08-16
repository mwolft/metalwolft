import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ADMIN_DEPS = all(
    has_package(package)
    for package in ("flask", "flask_admin", "flask_sqlalchemy", "sqlalchemy", "slugify")
)

if HAS_ADMIN_DEPS:
    from flask import Flask  # noqa: E402
    from sqlalchemy.orm import configure_mappers  # noqa: E402

    import api.admin as admin_module  # noqa: E402
    from api.models import Orders, Users, db  # noqa: E402


@unittest.skipUnless(HAS_ADMIN_DEPS, "Flask Admin test dependencies are not installed.")
class FlaskAdminOrderSentEmailOptionsTest(unittest.TestCase):
    def setUp(self):
        configure_mappers()
        self.app = Flask(__name__)
        self.app.config.update(
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.view = admin_module.OrderAdminView(Orders, db.session)

        with self.app.app_context():
            db.create_all()
            user = Users(email="cliente@example.com", password="secret")
            self.order = Orders(
                user=user,
                total_amount=10,
                locator="QE2885",
                order_status="pendiente",
            )
            db.session.add_all((user, self.order))
            db.session.commit()
            self.order_id = self.order.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _edit_form(
        self,
        *,
        status="enviado",
        sent_master=True,
        receipt=True,
        sent_installation=True,
        incidents=True,
        delivered_master=True,
        delivered_installation=True,
        maintenance=True,
    ):
        order = db.session.get(Orders, self.order_id)
        form = self.view.edit_form(order)
        form.order_status.data = status
        form.send_sent_status_email.data = sent_master
        form.include_receipt_guide_in_sent_email.data = receipt
        form.include_installation_guide_in_sent_email.data = sent_installation
        form.include_incident_form_in_sent_email.data = incidents
        form.send_delivered_status_email.data = delivered_master
        form.include_installation_guide_in_delivered_email.data = delivered_installation
        form.include_maintenance_guide_in_delivered_email.data = maintenance
        return order, form

    def _update(self, form, order):
        sent = []
        with patch("api.email_routes.send_email", side_effect=lambda **kwargs: sent.append(kwargs) or True):
            self.assertTrue(self.view.update_model(form, order))
        return sent

    def test_real_transition_to_sent_forwards_the_selected_links_to_the_renderer(self):
        with self.app.app_context():
            order, form = self._edit_form(receipt=True, sent_installation=False, incidents=True)
            sent = self._update(form, order)

            self.assertEqual(len(sent), 1)
            self.assertEqual(sent[0]["subject"], "Actualización de tu pedido: Enviado")
            self.assertIn("Guía de recepción del pedido", sent[0]["body"])
            self.assertIn("Formulario de incidencias", sent[0]["body"])
            self.assertNotIn("Ver guía de instalación", sent[0]["body"])

    def test_master_false_suppresses_the_status_email_even_with_links_selected(self):
        with self.app.app_context():
            order, form = self._edit_form(sent_master=False, receipt=True, sent_installation=True, incidents=True)
            sent = self._update(form, order)

            self.assertEqual(sent, [])

    def test_real_transition_to_delivered_forwards_installation_and_maintenance_once(self):
        with self.app.app_context():
            order, form = self._edit_form(status="entregado", delivered_installation=True, maintenance=True)
            sent = self._update(form, order)

            self.assertEqual(len(sent), 1)
            self.assertEqual(sent[0]["subject"], "Actualización de tu pedido: Entregado")
            self.assertEqual(sent[0]["body"].count("Guía de instalación:"), 1)
            self.assertEqual(sent[0]["body"].count("Mantenimiento y acabado:"), 1)

    def test_delivered_can_include_only_maintenance(self):
        with self.app.app_context():
            order, form = self._edit_form(
                status="entregado",
                delivered_installation=False,
                maintenance=True,
            )
            sent = self._update(form, order)

            self.assertEqual(len(sent), 1)
            self.assertIn("Mantenimiento y acabado", sent[0]["body"])
            self.assertNotIn("Guía de instalación:", sent[0]["body"])

    def test_delivered_without_guides_omits_the_guidance_block(self):
        with self.app.app_context():
            order, form = self._edit_form(
                status="entregado",
                delivered_installation=False,
                maintenance=False,
            )
            sent = self._update(form, order)

            self.assertEqual(len(sent), 1)
            self.assertNotIn("Ya tienes tu reja", sent[0]["body"])

    def test_delivered_master_false_suppresses_the_status_email(self):
        with self.app.app_context():
            order, form = self._edit_form(
                status="entregado",
                delivered_master=False,
                delivered_installation=True,
                maintenance=True,
            )
            sent = self._update(form, order)

            self.assertEqual(sent, [])

    def test_notification_fields_default_to_true_without_persisting_on_orders(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            form = self.view.edit_form(order)

            for field_name in self.view._ORDER_STATUS_EMAIL_OPTION_FIELDS:
                self.assertTrue(getattr(form, field_name).data)
                self.assertNotIn(field_name, order.__dict__)

    def test_editing_an_already_delivered_order_does_not_recapture_options(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            order.order_status = "entregado"
            with patch("api.email_routes.send_email", return_value=True):
                db.session.commit()

            order, form = self._edit_form(
                status="entregado",
                delivered_master=False,
                maintenance=True,
            )
            sent = self._update(form, order)

            self.assertEqual(sent, [])
            self.assertNotIn("_admin_order_status_email_options", order.__dict__)

    def test_notification_fields_remain_transient_after_an_admin_update(self):
        with self.app.app_context():
            order, form = self._edit_form()
            self._update(form, order)

            for field_name in self.view._ORDER_STATUS_EMAIL_OPTION_FIELDS:
                self.assertNotIn(field_name, order.__dict__)
            self.assertNotIn("_admin_order_status_email_options", order.__dict__)


if __name__ == "__main__":
    unittest.main()

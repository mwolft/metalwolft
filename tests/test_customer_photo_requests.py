import importlib.util
import re
from datetime import datetime, timedelta
from base64 import b64encode
from io import BytesIO
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
HAS_DEPS = all(importlib.util.find_spec(name) for name in ("flask", "flask_admin", "flask_sqlalchemy", "PIL"))

if HAS_DEPS:
    from flask import Flask
    from flask_admin import Admin
    from PIL import Image
    from sqlalchemy.exc import IntegrityError, OperationalError
    from werkzeug.datastructures import FileStorage

    from api.admin import CustomerPhotoRequestAdminView, OrderAdminView
    from api.customer_photo_routes import PhotoUploadRequest, customer_photo_bp
    from api.customer_photo_service import (
        CustomerPhotoError, _verified_test_database, create_photo_request as create_photo_request_service, resolve_photo_request,
        rotate_photo_link,
        review_photo_request, review_deadline_on, madrid_today, _madrid_date, stale_mail_attempts, submit_photos, token_hash, utcnow, validate_image,
    )
    from api.customer_photo_mail import (
        PhotoMailRejected, PhotoMailUncertain, build_photo_confirmation_message,
        build_photo_message, send_photo_message,
    )
    from api.customer_photo_rate_limit import CustomerPhotoRateLimitUnavailable, allow_photo_request
    from api.models import (
        CheckoutSessions, ConfirmedOrderContext, CustomerPhotoRequest,
        CustomerPhotoImage, CustomerPhotoUploadAttempt, CustomerPhotoFollowupNote, Invoices, OrderDetails, Orders, Users, db,
    )

    def create_photo_request(**kwargs):
        kwargs.setdefault("delivered_on", madrid_today())
        return create_photo_request_service(**kwargs)


@unittest.skipUnless(HAS_DEPS, "Backend test dependencies are not installed.")
class CustomerPhotoRequestTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder=str(ROOT / "src" / "templates"))
        self.app.request_class = PhotoUploadRequest
        self.app.config.update(
            SECRET_KEY="test-secret", SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            APP_ENV="development",
            CUSTOMER_PHOTOS_ENABLED=True,
            CUSTOMER_PHOTOS_INCENTIVE_ENABLED=False,
            CUSTOMER_PHOTOS_INCENTIVE_TEST_MODE=False,
            CUSTOMER_PHOTOS_INCENTIVE_TEST_DB_HOST="child.neon.tech",
            CUSTOMER_PHOTOS_INCENTIVE_TEST_EMAILS="cliente@example.test",
            CUSTOMER_PHOTOS_TERMS_VERSION="draft-v1",
            CUSTOMER_PHOTOS_TERMS_TEXT="Borrador de condiciones sometido a aprobación.",
            CUSTOMER_PHOTOS_CONSENT_TEXT="Borrador de autorización comercial.",
            CUSTOMER_PHOTOS_TERMS_URL="https://example.test/condiciones",
            CUSTOMER_PHOTOS_TOKEN_DAYS=30,
            FRONTEND_URL="https://example.test",
            MAIL_SERVER="localhost", MAIL_PORT=1025, MAIL_DEFAULT_SENDER="test@example.test",
        )
        db.init_app(self.app)
        self.app.register_blueprint(customer_photo_bp, url_prefix="/api/customer-photos")
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        user = Users(email="cliente@example.test", password="secret")
        order = Orders(user=user, total_amount=80, locator="AB1234", order_status="enviado")
        order.order_details.append(OrderDetails(product_id=1, quantity=1, precio_total=80, line_type="physical"))
        db.session.add(order)
        db.session.commit()
        self.order_id = order.id
        self.view = OrderAdminView(Orders, db.session)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def order_form(self, mode="none", *, email=True, guides=True):
        order = db.session.get(Orders, self.order_id)
        form = self.view.edit_form(order)
        form.order_status.data = "entregado"
        form.send_delivered_status_email.data = email
        form.include_installation_guide_in_delivered_email.data = guides
        form.include_maintenance_guide_in_delivered_email.data = guides
        form.photo_request_mode.data = mode
        form.photo_actual_delivery_on.data = madrid_today()
        return order, form

    def offer(self, mode="free"):
        order = db.session.get(Orders, self.order_id)
        item, url = create_photo_request(order=order, mode=mode, app=self.app)
        db.session.commit()
        return item, url.split("#", 1)[1]

    def image(self, *, fmt="PNG", mime="image/png", color="red"):
        content = BytesIO()
        Image.new("RGB", (20, 20), color).save(content, format=fmt)
        return FileStorage(stream=BytesIO(content.getvalue()), filename="photo.png", content_type=mime)

    def submit(self, token, *, consent="yes", colors=("red", "blue"), send_message=None):
        return submit_photos(
            token=token, front_photo=self.image(color=colors[0]),
            perspective_photo=self.image(color=colors[1]),
            additional_photos=[self.image(color=color) for color in colors[2:]],
            commercial_consent=consent, app=self.app,
            send_message=send_message or (lambda **_kwargs: None),
        )

    def test_default_and_master_off_leave_email_unchanged_and_create_no_offer(self):
        with self.app.test_request_context(), patch("api.email_routes.send_email", return_value=True) as smtp:
            order, form = self.order_form()
            self.assertEqual(form.photo_request_mode.data, "none")
            self.assertTrue(self.view.update_model(form, order))
            self.assertEqual(CustomerPhotoRequest.query.count(), 0)
            self.assertNotIn("fotografías", smtp.call_args.kwargs["body"].lower())

        db.session.get(Orders, self.order_id).order_status = "enviado"
        db.session.commit()
        with self.app.test_request_context(), patch("api.email_routes.send_email") as smtp:
            order, form = self.order_form("free", email=False)
            self.assertTrue(self.view.update_model(form, order))
            self.assertEqual(CustomerPhotoRequest.query.count(), 0)
            smtp.assert_not_called()

    def test_free_email_without_guides_has_photo_block_and_guest_recipient(self):
        order = db.session.get(Orders, self.order_id)
        order.user_id = None
        order.confirmed_order_context = ConfirmedOrderContext(
            source="admin_external", quote_snapshot={"lines": [{}]},
            customer_snapshot={"email": "invitado@example.test"},
            payment_method="cash", payment_status="confirmed",
            payment_amount=80, currency="EUR", source_manual_draft_id=None,
        )
        db.session.commit()
        with self.app.test_request_context(), patch("api.email_routes.send_email", return_value=True) as smtp:
            order, form = self.order_form("free", guides=False)
            self.assertTrue(self.view.update_model(form, order))
            payload = smtp.call_args.kwargs
            self.assertEqual(payload["recipients"], ["invitado@example.test"])
            self.assertEqual(payload["subject"], "Actualización de tu pedido: Entregado")
            self.assertIn("Ya tienes tu reja", payload["body"])
            self.assertIn("Comparte tus rejas instaladas", payload["html"])
            self.assertIn("/fotos-clientes#", payload["html"])
            item = CustomerPhotoRequest.query.one()
            self.assertEqual(item.mode, "free")
            self.assertIsNotNone(item.email_sent_at)

    def test_free_email_with_guides_keeps_guides_and_adds_photo_block(self):
        with self.app.test_request_context(), patch("api.email_routes.send_email", return_value=True) as smtp:
            order, form = self.order_form("free", guides=True)
            self.assertTrue(self.view.update_model(form, order))
            text = smtp.call_args.kwargs["body"]
            self.assertIn("Guía de instalación:", text)
            self.assertIn("Mantenimiento y acabado:", text)
            self.assertIn("Comparte tus rejas instaladas", text)

    def test_incentive_email_in_development_includes_offer_link_and_terms(self):
        order = db.session.get(Orders, self.order_id)
        checkout = CheckoutSessions(
            user_id=order.user_id, order_id=order.id, status="order_created",
            payment_provider="stripe", payment_intent_id="pi_test",
            public_checkout_token="checkout-incentive", quote_snapshot={"lines": [{}]},
        )
        order.confirmed_order_context = ConfirmedOrderContext(
            source="web_checkout", quote_snapshot={"lines": [{}]},
            customer_snapshot={"email": "cliente@example.test"},
            payment_method="stripe", payment_status="confirmed",
            payment_reference="pi_test", provider_identifiers={"payment_intent_id": "pi_test"},
            payment_amount=80, currency="EUR", source_checkout_session=checkout,
        )
        db.session.commit()
        self.app.config["CUSTOMER_PHOTOS_INCENTIVE_ENABLED"] = True
        with self.app.test_request_context(), patch("api.email_routes.send_email", return_value=True) as smtp:
            order, form = self.order_form("incentive", guides=False)
            self.assertTrue(self.view.update_model(form, order))
        payload = smtp.call_args.kwargs
        self.assertEqual(payload["subject"], "Actualización de tu pedido: Entregado")
        self.assertEqual(payload["recipients"], ["cliente@example.test"])
        for body in (payload["body"], payload["html"]):
            self.assertIn("20 €", body)
            self.assertIn("/fotos-clientes#", body)
            self.assertIn("https://example.test/condiciones", body)
        self.assertEqual(CustomerPhotoRequest.query.one().mode, "incentive")

    def test_same_delivered_status_does_not_create_offer(self):
        order = db.session.get(Orders, self.order_id)
        order.order_status = "entregado"
        db.session.commit()
        with self.app.test_request_context(), patch("api.email_routes.send_email") as smtp:
            order, form = self.order_form("free")
            self.assertTrue(self.view.update_model(form, order))
            smtp.assert_not_called()
        self.assertEqual(CustomerPhotoRequest.query.count(), 0)

    def test_failed_commit_does_not_persist_offer_or_send_email(self):
        with self.app.test_request_context(), patch.object(self.view.session, "commit", side_effect=RuntimeError("db unavailable")), patch(
            "api.admin.send_order_update_email"
        ) as smtp:
            order, form = self.order_form("free")
            self.assertFalse(self.view.update_model(form, order))
            smtp.assert_not_called()
        self.assertEqual(CustomerPhotoRequest.query.count(), 0)

    def test_smtp_failure_leaves_offer_for_explicit_resend_with_rotated_token(self):
        with self.app.test_request_context(), patch("api.email_routes.send_email", return_value=False):
            order, form = self.order_form("free")
            self.assertTrue(self.view.update_model(form, order))
        item = CustomerPhotoRequest.query.one()
        self.assertIsNotNone(item.email_failed_at)
        self.assertIsNone(item.email_sent_at)
        old_hash = item.token_hash
        link = rotate_photo_link(item, app=self.app)
        db.session.commit()
        self.assertNotEqual(old_hash, item.token_hash)
        self.assertEqual(item.token_hash, token_hash(link.split("#", 1)[1]))

    def test_incentive_is_off_by_default_and_manual_is_ineligible(self):
        order = db.session.get(Orders, self.order_id)
        with self.assertRaises(CustomerPhotoError):
            create_photo_request(order=order, mode="incentive", app=self.app)

    def test_simulation_requires_every_gate_and_authorized_recipient(self):
        order = db.session.get(Orders, self.order_id)
        self.app.config.update(CUSTOMER_PHOTOS_INCENTIVE_ENABLED=True, CUSTOMER_PHOTOS_INCENTIVE_TEST_MODE=True)
        with self.assertRaises(CustomerPhotoError):
            create_photo_request(order=order, mode="incentive", app=self.app)
        with patch("api.customer_photo_service._verified_test_database", return_value=True):
            for key, value in (
                ("APP_ENV", "production"),
                ("CUSTOMER_PHOTOS_ENABLED", False),
                ("CUSTOMER_PHOTOS_INCENTIVE_ENABLED", False),
                ("CUSTOMER_PHOTOS_INCENTIVE_TEST_EMAILS", "other@example.test"),
            ):
                original = self.app.config[key]
                self.app.config[key] = value
                with self.assertRaises(CustomerPhotoError):
                    create_photo_request(order=order, mode="incentive", app=self.app)
                self.app.config[key] = original
            item, _ = create_photo_request(order=order, mode="incentive", app=self.app)
        db.session.commit()
        self.assertTrue(db.session.get(CustomerPhotoRequest, item.id).is_simulation)
        self.assertEqual(item.offered_amount, 0)
        self.assertFalse(_verified_test_database(self.app))

    def test_simulation_database_identity_checks_configured_and_live_child(self):
        engine = MagicMock()
        engine.url.render_as_string.return_value = "postgresql://tester:private@child.neon.tech/neondb"
        engine.connect.return_value.__enter__.return_value.execute.return_value.one.return_value = ("neondb", "tester")
        expected = {
            "DATABASE_EXPECTED_HOST": "child.neon.tech",
            "DATABASE_EXPECTED_NAME": "neondb",
            "DATABASE_EXPECTED_USER": "tester",
        }
        with patch("api.customer_photo_service.db") as fake_db, patch.dict(os.environ, expected):
            fake_db.engine = engine
            self.assertTrue(_verified_test_database(self.app))
            engine.connect.return_value.__enter__.return_value.execute.return_value.one.return_value = ("neondb", "other")
            self.assertFalse(_verified_test_database(self.app))
            engine.connect.return_value.__enter__.return_value.execute.return_value.one.return_value = ("neondb", "tester")
            self.app.config["CUSTOMER_PHOTOS_INCENTIVE_TEST_DB_HOST"] = "other.neon.tech"
            self.assertFalse(_verified_test_database(self.app))

    def test_database_rejects_refund_pending_for_simulation(self):
        self.app.config.update(CUSTOMER_PHOTOS_INCENTIVE_ENABLED=True, CUSTOMER_PHOTOS_INCENTIVE_TEST_MODE=True)
        with patch("api.customer_photo_service._verified_test_database", return_value=True):
            item, _ = create_photo_request(
                order=db.session.get(Orders, self.order_id), mode="incentive", app=self.app,
            )
        db.session.commit()
        item.status = "refund_pending"
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        self.assertEqual(db.session.get(CustomerPhotoRequest, item.id).status, "offered")

    def test_simulated_incentive_email_submission_and_review_never_create_refund(self):
        self.app.config.update(CUSTOMER_PHOTOS_INCENTIVE_ENABLED=True, CUSTOMER_PHOTOS_INCENTIVE_TEST_MODE=True)
        with patch("api.customer_photo_service._verified_test_database", return_value=True), self.app.test_request_context(), patch("api.email_routes.send_email", return_value=True) as smtp:
            order, form = self.order_form("incentive", guides=False)
            self.assertTrue(self.view.update_model(form, order))
            payload = smtp.call_args.kwargs
            self.assertIn("SIMULACIÓN — SIN REEMBOLSO", payload["body"])
            self.assertIn("SIMULACIÓN — SIN REEMBOLSO", payload["html"])
            self.assertNotIn("te devolveremos 20 €", payload["body"])
            self.assertNotIn("te devolveremos 20 €", payload["html"])
            self.assertIn("/fotos-clientes#", payload["body"])
        item = CustomerPhotoRequest.query.one()
        self.assertTrue(item.is_simulation)
        token = re.search(r"/fotos-clientes#([A-Za-z0-9_-]+)", payload["body"]).group(1)
        with patch("api.customer_photo_service._verified_test_database", return_value=True):
            details = self.app.test_client().get(
                "/api/customer-photos", headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(details.status_code, 200)
        self.assertTrue(details.json["is_simulation"])
        sent = []
        with patch("api.customer_photo_service._verified_test_database", return_value=True):
            self.submit(token, send_message=lambda **kwargs: sent.append(kwargs["message"]))
        self.assertEqual(len(sent), 2)
        self.assertIn("SIMULACIÓN — SIN REEMBOLSO", sent[0].get_body(preferencelist=("plain",)).get_content())
        self.assertIn("SIMULACIÓN — SIN REEMBOLSO", sent[1].get_content())
        self.app.config["CUSTOMER_PHOTOS_INCENTIVE_TEST_MODE"] = False
        item.mailbox_confirmed_at = utcnow()
        db.session.commit()
        result = review_photo_request(request_id=item.id, decision="approve", note="Prueba", actor="admin", app=self.app)
        db.session.commit()
        self.assertEqual(result.status, "approved")
        self.assertNotEqual(result.status, "refund_pending")
        self.app.config["CUSTOMER_PHOTOS_INCENTIVE_ENABLED"] = True
        with self.assertRaises(CustomerPhotoError):
            create_photo_request(order=order, mode="incentive", app=self.app)

    def test_stripe_requires_matching_payment_intent(self):
        order = db.session.get(Orders, self.order_id)
        checkout = CheckoutSessions(
            user_id=order.user_id, order_id=order.id, status="order_created",
            payment_provider="stripe", payment_intent_id="pi_real",
            public_checkout_token="checkout-token", quote_snapshot={"lines": [{}]},
        )
        order.confirmed_order_context = ConfirmedOrderContext(
            source="web_checkout", quote_snapshot={"lines": [{}]},
            customer_snapshot={"email": "cliente@example.test"},
            payment_method="stripe", payment_status="confirmed",
            payment_reference="pi_real", provider_identifiers={"payment_intent_id": "pi_real"},
            payment_amount=80, currency="EUR", source_checkout_session=checkout,
        )
        db.session.commit()
        self.app.config["CUSTOMER_PHOTOS_INCENTIVE_ENABLED"] = True
        item, _ = create_photo_request(order=order, mode="incentive", app=self.app)
        self.assertEqual(item.offered_amount, 20)
        db.session.rollback()
        self.app.config["APP_ENV"] = "production"
        with self.assertRaises(CustomerPhotoError):
            create_photo_request(order=order, mode="incentive", app=self.app)
        self.app.config["APP_ENV"] = "development"
        checkout.payment_intent_id = "pi_mismatch"
        with self.assertRaises(CustomerPhotoError):
            create_photo_request(order=order, mode="incentive", app=self.app)
        checkout.payment_intent_id = None
        order.confirmed_order_context.payment_reference = None
        order.confirmed_order_context.provider_identifiers = {"payment_intent_id": None}
        with self.assertRaises(CustomerPhotoError):
            create_photo_request(order=order, mode="incentive", app=self.app)

    def test_paypal_order_id_without_capture_is_not_incentive_eligible(self):
        order = db.session.get(Orders, self.order_id)
        checkout = CheckoutSessions(
            user_id=order.user_id, order_id=order.id, status="order_created",
            payment_provider="paypal", provider_order_id="paypal-order",
            public_checkout_token="checkout-token-2", quote_snapshot={"lines": [{}]},
        )
        order.confirmed_order_context = ConfirmedOrderContext(
            source="web_checkout", quote_snapshot={"lines": [{}]},
            customer_snapshot={"email": "cliente@example.test"},
            payment_method="paypal", payment_status="confirmed", payment_reference="paypal-order",
            provider_identifiers={"provider_order_id": "paypal-order"},
            payment_amount=80, currency="EUR", source_checkout_session=checkout,
        )
        db.session.commit()
        self.app.config["CUSTOMER_PHOTOS_INCENTIVE_ENABLED"] = True
        with self.assertRaises(CustomerPhotoError):
            create_photo_request(order=order, mode="incentive", app=self.app)

    def test_paypal_capture_is_incentive_eligible_in_development(self):
        order = db.session.get(Orders, self.order_id)
        checkout = CheckoutSessions(
            user_id=order.user_id, order_id=order.id, status="order_created",
            payment_provider="paypal", provider_order_id="paypal-order",
            provider_capture_id="capture-real", public_checkout_token="checkout-capture",
            quote_snapshot={"lines": [{}]},
        )
        order.confirmed_order_context = ConfirmedOrderContext(
            source="web_checkout", quote_snapshot={"lines": [{}]},
            customer_snapshot={"email": "cliente@example.test"},
            payment_method="paypal", payment_status="confirmed", payment_reference="capture-real",
            provider_identifiers={"provider_order_id": "paypal-order", "provider_capture_id": "capture-real"},
            payment_amount=80, currency="EUR", source_checkout_session=checkout,
        )
        db.session.commit()
        self.app.config["CUSTOMER_PHOTOS_INCENTIVE_ENABLED"] = True
        item, _ = create_photo_request(order=order, mode="incentive", app=self.app)
        self.assertEqual(item.offered_amount, 20)

    def test_token_invalid_expired_revoked_and_single_offer(self):
        item, token = self.offer()
        self.assertEqual(item.token_hash, token_hash(token))
        self.assertNotIn(token, str(item.__dict__))
        self.assertIsNone(resolve_photo_request(token + "x"))
        with self.assertRaises(CustomerPhotoError):
            self.offer()
        item.token_expires_at = utcnow()
        db.session.commit()
        self.assertIsNone(resolve_photo_request(token))
        item.token_expires_at = utcnow().replace(year=utcnow().year + 1)
        item.token_revoked_at = utcnow()
        db.session.commit()
        self.assertIsNone(resolve_photo_request(token))

    def test_five_photos_send_in_one_mail_without_storing_images(self):
        item, token = self.offer()
        sent = []
        result = self.submit(token, consent="no", colors=("red", "blue", "green", "yellow", "black"), send_message=lambda **kwargs: sent.append(kwargs["message"]))
        self.assertEqual(result.status, "received")
        self.assertFalse(result.commercial_consent)
        self.assertEqual(result.consent_text, "Borrador de autorización comercial.")
        self.assertEqual(result.consent_version, "draft-v1")
        self.assertEqual(result.photo_count, 5)
        self.assertEqual(len(sent), 2)
        self.assertEqual(sent[0]["To"], "admin@metalwolft.com")
        self.assertIn("Solicitud: ", sent[0].get_body(preferencelist=("plain",)).get_content())
        self.assertIn("Autorización comercial: No", sent[0].get_body(preferencelist=("plain",)).get_content())
        self.assertEqual(len(list(sent[0].iter_attachments())), 5)
        self.assertNotIn("photo.png", sent[0].as_string())
        self.assertEqual(sent[1]["To"], "cliente@example.test")
        self.assertEqual(sent[1]["Reply-To"], "admin@metalwolft.com")
        confirmation_text = sent[1].get_body(preferencelist=("plain",)).get_content()
        self.assertIn("retirada", confirmation_text)
        self.assertIn("supresión", confirmation_text)
        self.assertEqual(len(list(sent[1].iter_attachments())), 0)
        self.assertEqual(CustomerPhotoImage.query.count(), 0)
        self.assertEqual(CustomerPhotoUploadAttempt.query.count(), 0)
        with self.assertRaises(CustomerPhotoError):
            self.submit(token)
        self.assertEqual(len(sent), 2)

    def test_upload_rejects_missing_consent_mime_and_duplicate_files(self):
        _, token = self.offer()
        with self.assertRaises(CustomerPhotoError):
            self.submit(token, consent="")
        with self.assertRaises(CustomerPhotoError):
            submit_photos(token=token, front_photo=self.image(mime="image/jpeg"), perspective_photo=self.image(), additional_photos=[], commercial_consent="yes", app=self.app)
        with self.assertRaises(CustomerPhotoError):
            self.submit(token, colors=("red", "red"))
        with self.assertRaises(CustomerPhotoError):
            self.submit(token, colors=("red", "blue", "green", "yellow", "black", "white"))

    def test_both_required_perspectives_are_enforced(self):
        _, token = self.offer()
        for front, perspective, expected in (
            (None, self.image(color="blue"), "frontal"),
            (self.image(), None, "perspectiva"),
        ):
            with self.subTest(expected=expected), self.assertRaisesRegex(CustomerPhotoError, expected):
                submit_photos(token=token, front_photo=front, perspective_photo=perspective,
                              additional_photos=[], commercial_consent="yes", app=self.app)
        self.assertEqual(CustomerPhotoRequest.query.first().status, "offered")

    def test_public_upload_requires_two_distinct_photo_fields(self):
        item, token = self.offer()
        client = self.app.test_client()
        with patch("api.customer_photo_service.send_photo_message") as smtp:
            for field, expected in (("front_photo", "perspectiva"), ("perspective_photo", "frontal")):
                with self.subTest(field=field):
                    response = client.post(
                        "/api/customer-photos", headers={"Authorization": f"Bearer {token}"},
                        data={"commercial_consent": "yes", field: (BytesIO(self.image().stream.read()), "reja.png", "image/png")},
                        content_type="multipart/form-data",
                    )
                    self.assertEqual(response.status_code, 400)
                    self.assertIn(expected, response.json["error"])
            smtp.assert_not_called()
        self.assertEqual(db.session.get(CustomerPhotoRequest, item.id).status, "offered")

    def test_large_image_is_resized_in_memory_and_oversize_mail_is_rejected(self):
        large = BytesIO()
        Image.new("RGB", (3200, 2500), "red").save(large, format="JPEG")
        file = FileStorage(stream=BytesIO(large.getvalue()), filename="private-name.jpg", content_type="image/jpeg")
        mime, content, _digest, extension = validate_image(file)
        with Image.open(BytesIO(content)) as normalized:
            self.assertLessEqual(max(normalized.size), 2400)
        with patch("api.customer_photo_mail.MAX_MIME_BYTES", 100):
            with self.assertRaises(PhotoMailRejected):
                build_photo_message(
                    app=self.app, order_reference="AB1234", request_id=1,
                    attempt_id="abc", date=utcnow(), consent=True,
                    photos=[(mime, content, "hash", extension)],
                )

    def test_smtp_adapter_sends_one_message_and_classifies_rejection(self):
        photo = validate_image(self.image(fmt="JPEG", mime="image/jpeg"))
        message = build_photo_message(
            app=self.app, order_reference="AB1234", request_id=1,
            attempt_id="abc", date=utcnow(), consent=True, photos=[photo],
        )
        with patch("api.customer_photo_mail.smtplib.SMTP") as smtp_class:
            send_photo_message(app=self.app, message=message)
            smtp_class.return_value.__enter__.return_value.send_message.assert_called_once_with(message)
        with patch("api.customer_photo_mail.smtplib.SMTP") as smtp_class:
            from smtplib import SMTPDataError
            smtp_class.return_value.__enter__.return_value.send_message.side_effect = SMTPDataError(552, b"too large")
            with self.assertRaises(PhotoMailRejected):
                send_photo_message(app=self.app, message=message)

    def test_definitive_smtp_rejection_allows_explicit_retry(self):
        item, token = self.offer()
        def reject(**_kwargs):
            raise PhotoMailRejected("Rejected")
        with self.assertRaises(PhotoMailRejected):
            self.submit(token, send_message=reject)
        self.assertEqual(db.session.get(CustomerPhotoRequest, item.id).status, "offered")
        self.assertEqual(item.delivery_status, "rejected")
        self.assertIsNone(item.commercial_consent)
        self.assertEqual(CustomerPhotoImage.query.count(), 0)
        self.submit(token)
        self.assertEqual(item.status, "received")

    def test_confirmation_failure_does_not_undo_accepted_submission_or_resend_photos(self):
        item, token = self.offer()
        sent = []
        def send(**kwargs):
            sent.append(kwargs["message"])
            if len(sent) == 2:
                raise PhotoMailUncertain("confirmation timeout")
        with patch.object(self.app.logger, "exception"):
            self.submit(token, send_message=send)
        self.assertEqual(item.status, "received")
        self.assertEqual(item.delivery_status, "accepted")
        self.assertEqual(len(sent), 2)
        with self.assertRaises(CustomerPhotoError):
            self.submit(token)

    def test_token_cannot_rotate_during_smtp_send(self):
        item, token = self.offer()
        def check_during_send(**_kwargs):
            locked = db.session.query(CustomerPhotoRequest).filter_by(id=item.id).with_for_update().one()
            with self.assertRaises(CustomerPhotoError):
                rotate_photo_link(locked, app=self.app)
            with self.assertRaises(CustomerPhotoError):
                self.submit(token)
        self.submit(token, send_message=check_during_send)
        self.assertEqual(item.status, "received")
        self.assertEqual(CustomerPhotoImage.query.count(), 0)

    def test_uncertain_smtp_is_not_retried_and_requires_reconciliation(self):
        item, token = self.offer()
        def uncertain(**_kwargs):
            raise PhotoMailUncertain("timeout")
        with self.assertRaises(PhotoMailUncertain):
            self.submit(token, send_message=uncertain)
        self.assertEqual(item.delivery_status, "unknown")
        self.assertEqual(item.status, "offered")
        with self.assertRaises(CustomerPhotoError):
            self.submit(token)
        with self.assertRaises(CustomerPhotoError):
            rotate_photo_link(item, app=self.app)
        self.assertEqual(stale_mail_attempts(now=utcnow() + timedelta(hours=1)), [item])

    def test_production_blocks_incentive_resend_upload_and_approval(self):
        self.app.config["CUSTOMER_PHOTOS_INCENTIVE_ENABLED"] = True
        item, token = self.offer()
        item.mode = "incentive"
        item.offered_amount = 20
        db.session.commit()
        self.app.config["APP_ENV"] = "production"
        with self.assertRaises(CustomerPhotoError):
            rotate_photo_link(item, app=self.app)
        with self.assertRaises(CustomerPhotoError):
            self.submit(token)
        self.app.config["APP_ENV"] = "development"
        self.submit(token)
        item.mailbox_confirmed_at = utcnow()
        db.session.commit()
        self.app.config["APP_ENV"] = "production"
        with self.assertRaises(CustomerPhotoError):
            review_photo_request(request_id=item.id, decision="approve", note="", actor="admin", app=self.app)
        self.assertEqual(item.status, "received")

    def test_review_is_explicit_and_never_pays(self):
        item, token = self.offer()
        self.submit(token)
        with self.assertRaises(CustomerPhotoError):
            review_photo_request(request_id=item.id, decision="approve", note="Adecuadas", actor="admin", app=self.app)
        item.mailbox_confirmed_at = utcnow()
        db.session.commit()
        reviewed = review_photo_request(request_id=item.id, decision="approve", note="Adecuadas", actor="admin", app=self.app)
        db.session.commit()
        self.assertEqual(reviewed.status, "approved")
        self.assertEqual(CustomerPhotoImage.query.count(), 0)
        with self.assertRaises(CustomerPhotoError):
            review_photo_request(request_id=item.id, decision="approve", note="", actor="admin", app=self.app)

    def test_incentive_approval_only_marks_refund_pending(self):
        self.app.config["CUSTOMER_PHOTOS_INCENTIVE_ENABLED"] = True
        item, token = self.offer()
        item.mode = "incentive"
        item.offered_amount = 20
        db.session.commit()
        self.submit(token)
        item.mailbox_confirmed_at = utcnow()
        db.session.commit()
        reviewed = review_photo_request(request_id=item.id, decision="approve", note="Aptas", actor="admin", app=self.app)
        db.session.commit()
        self.assertEqual(reviewed.status, "refund_pending")

    def test_invalid_recipient_blocks_offer(self):
        order = db.session.get(Orders, self.order_id)
        order.user.email = "not-an-email"
        with self.assertRaises(CustomerPhotoError):
            create_photo_request(order=order, mode="free", app=self.app)

    def test_admin_review_requires_authentication(self):
        admin = Admin(self.app)
        admin.add_view(CustomerPhotoRequestAdminView(CustomerPhotoRequest, db.session, endpoint="photo-review-test"))
        item, token = self.offer()
        self.assertTrue(token)
        client = self.app.test_client()
        response = client.get(f"/admin/photo-review-test/review/{item.id}")
        self.assertEqual(response.status_code, 401)
        credentials = b64encode(b"photo-admin:secret").decode("ascii")
        with patch("api.admin.ADMIN_USER", "photo-admin"), patch("api.admin.ADMIN_PW", "secret"):
            response = client.get(
                f"/admin/photo-review-test/review/{item.id}",
                headers={"Authorization": f"Basic {credentials}"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Fotograf", response.data)

    def test_admin_reconciles_received_mail_before_review(self):
        admin = Admin(self.app)
        admin.add_view(CustomerPhotoRequestAdminView(CustomerPhotoRequest, db.session, endpoint="photo-review-mail"))
        item, token = self.offer()
        self.submit(token)
        client = self.app.test_client()
        credentials = b64encode(b"photo-admin:secret").decode("ascii")
        url = f"/admin/photo-review-mail/review/{item.id}"
        with patch("api.admin.ADMIN_USER", "photo-admin"), patch("api.admin.ADMIN_PW", "secret"), patch("api.admin._valid_work_order_csrf_token", return_value=True):
            denied = client.post(url, headers={"Authorization": f"Basic {credentials}"}, data={"decision": "confirm_mail"})
            self.assertEqual(denied.status_code, 302)
            self.assertIsNone(db.session.get(CustomerPhotoRequest, item.id).mailbox_confirmed_at)
            response = client.post(url, headers={"Authorization": f"Basic {credentials}"}, data={"decision": "confirm_mail", "mail_verified": "yes"})
            self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(db.session.get(CustomerPhotoRequest, item.id).mailbox_confirmed_at)

    def test_new_offer_freezes_real_delivery_date_and_expires_after_thirty_days(self):
        order = db.session.get(Orders, self.order_id)
        with self.assertRaisesRegex(CustomerPhotoError, "fecha real"):
            create_photo_request_service(order=order, mode="free", app=self.app)
        with self.assertRaisesRegex(CustomerPhotoError, "futura"):
            create_photo_request_service(order=order, mode="free", app=self.app, delivered_on=madrid_today() + timedelta(days=1))
        with self.assertRaisesRegex(CustomerPhotoError, "30 días"):
            create_photo_request_service(order=order, mode="free", app=self.app, delivered_on=madrid_today() - timedelta(days=31))
        delivered = madrid_today() - timedelta(days=15)
        item, token_url = create_photo_request_service(order=order, mode="free", app=self.app, delivered_on=delivered)
        db.session.commit()
        self.assertEqual(item.actual_delivery_on, delivered)
        self.assertEqual(item.participation_deadline_on, delivered + timedelta(days=30))
        self.assertEqual(_madrid_date(item.token_expires_at), delivered + timedelta(days=31))
        self.assertTrue(token_url.endswith(token_url.split("#", 1)[1]))

    def test_historical_offer_without_delivery_date_is_not_retroactively_expired(self):
        item, token = self.offer()
        item.actual_delivery_on = None
        item.participation_deadline_on = None
        item.receipt_accredited_on = None
        db.session.commit()
        self.assertEqual(resolve_photo_request(token).id, item.id)
        self.assertIsNone(review_deadline_on(item))

    def test_review_deadline_requires_accredited_receipt(self):
        item, token = self.offer()
        self.assertIsNone(review_deadline_on(item))
        self.submit(token)
        item = db.session.get(CustomerPhotoRequest, item.id)
        self.assertEqual(item.receipt_accredited_on, madrid_today())
        self.assertEqual(review_deadline_on(item), madrid_today() + timedelta(days=7))
        item.delivery_status = "unknown"
        self.assertIsNone(review_deadline_on(item))

    def test_uncertain_mail_deadline_starts_when_admin_confirms_inbox(self):
        admin = Admin(self.app)
        admin.add_view(CustomerPhotoRequestAdminView(CustomerPhotoRequest, db.session, endpoint="photo-review-uncertain"))
        item, _ = self.offer()
        item.delivery_status = "unknown"
        item.delivery_started_at = utcnow() - timedelta(hours=1)
        db.session.commit()
        self.assertIsNone(review_deadline_on(item))
        credentials = b64encode(b"photo-admin:secret").decode("ascii")
        with patch("api.admin.ADMIN_USER", "photo-admin"), patch("api.admin.ADMIN_PW", "secret"), patch("api.admin._valid_work_order_csrf_token", return_value=True):
            denied = self.app.test_client().post(
                f"/admin/photo-review-uncertain/review/{item.id}",
                headers={"Authorization": f"Basic {credentials}"},
                data={"decision": "confirm_mail", "mail_verified": "yes"},
            )
            self.assertEqual(denied.status_code, 302)
            self.assertIsNone(item.receipt_accredited_on)
            response = self.app.test_client().post(
                f"/admin/photo-review-uncertain/review/{item.id}",
                headers={"Authorization": f"Basic {credentials}"},
                data={"decision": "confirm_mail", "mail_verified": "yes", "mail_received_on": madrid_today().isoformat()},
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(item.receipt_accredited_on, madrid_today())
        self.assertEqual(review_deadline_on(item), madrid_today() + timedelta(days=7))
        self.assertEqual(item.status, "received")

    def test_correction_notes_append_without_changing_original_review_history(self):
        admin = Admin(self.app)
        admin.add_view(CustomerPhotoRequestAdminView(CustomerPhotoRequest, db.session, endpoint="photo-review-notes"))
        item, token = self.offer()
        self.submit(token)
        item.mailbox_confirmed_at = utcnow()
        item.receipt_accredited_on = madrid_today() - timedelta(days=3)
        db.session.commit()
        self.assertEqual(review_deadline_on(item), madrid_today() + timedelta(days=4))
        credentials = b64encode(b"photo-admin:secret").decode("ascii")
        url = f"/admin/photo-review-notes/review/{item.id}"
        with patch("api.admin.ADMIN_USER", "photo-admin"), patch("api.admin.ADMIN_PW", "secret"), patch("api.admin._valid_work_order_csrf_token", return_value=True):
            client = self.app.test_client()
            for kind, note in (("correction_requested", "Falta detalle lateral"), ("correction_received", "Recibida por correo")):
                response = client.post(url, headers={"Authorization": f"Basic {credentials}"},
                                       data={"decision": "note_correction", "correction_kind": kind, "note": note,
                                             "correction_received_on": madrid_today().isoformat() if kind == "correction_received" else ""})
                self.assertEqual(response.status_code, 302)
            response = client.get(url, headers={"Authorization": f"Basic {credentials}"})
            self.assertIn(b"L\xc3\xadmite de revisi\xc3\xb3n", response.data)
        self.assertEqual([note.kind for note in CustomerPhotoFollowupNote.query.order_by(CustomerPhotoFollowupNote.id)],
                         ["correction_requested", "correction_received"])
        self.assertEqual(review_deadline_on(item), madrid_today() + timedelta(days=7))
        self.assertIsNone(item.review_note)
        review_photo_request(request_id=item.id, decision="approve", note="Apta", actor="admin", app=self.app)
        db.session.commit()
        self.assertEqual(CustomerPhotoFollowupNote.query.count(), 2)
        self.assertEqual(item.review_note, "Apta")

    def test_overdue_review_is_highlighted_without_automatic_decision(self):
        admin = Admin(self.app)
        admin.add_view(CustomerPhotoRequestAdminView(CustomerPhotoRequest, db.session, endpoint="photo-review-overdue"))
        item, token = self.offer()
        self.submit(token)
        item.mailbox_confirmed_at = utcnow()
        item.receipt_accredited_on = madrid_today() - timedelta(days=8)
        db.session.commit()
        credentials = b64encode(b"photo-admin:secret").decode("ascii")
        with patch("api.admin.ADMIN_USER", "photo-admin"), patch("api.admin.ADMIN_PW", "secret"):
            client = self.app.test_client()
            response = client.get(
                f"/admin/photo-review-overdue/review/{item.id}",
                headers={"Authorization": f"Basic {credentials}"},
            )
            listing = client.get("/admin/photo-review-overdue/", headers={"Authorization": f"Basic {credentials}"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PLAZO VENCIDO", response.data)
        self.assertEqual(listing.status_code, 200)
        self.assertIn(b"VENCIDO", listing.data)
        self.assertEqual(item.status, "received")

    def test_reject_requires_note_and_consent_can_be_revoked(self):
        admin = Admin(self.app)
        admin.add_view(CustomerPhotoRequestAdminView(CustomerPhotoRequest, db.session, endpoint="photo-review-revoke"))
        item, token = self.offer()
        self.submit(token)
        item.mailbox_confirmed_at = utcnow()
        db.session.commit()
        with self.assertRaises(CustomerPhotoError):
            review_photo_request(request_id=item.id, decision="reject", note="", actor="admin")
        self.assertEqual(self.app.test_client().post(
            "/api/customer-photos/consent/revoke", headers={"Authorization": f"Bearer {token}"},
        ).status_code, 404)
        credentials = b64encode(b"photo-admin:secret").decode("ascii")
        with patch("api.admin.ADMIN_USER", "photo-admin"), patch("api.admin.ADMIN_PW", "secret"), patch("api.admin._valid_work_order_csrf_token", return_value=True):
            response = self.app.test_client().post(
                f"/admin/photo-review-revoke/review/{item.id}",
                headers={"Authorization": f"Basic {credentials}"}, data={"decision": "revoke"},
            )
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(item.consent_revoked_at)
        self.assertEqual(item.status, "revoked")
        self.assertEqual(item.consent_version, "draft-v1")
        self.assertEqual(item.photo_count, 2)

    def test_rate_limiter_blocks_repeated_requests(self):
        start = datetime(2026, 10, 9, 12, 0)
        self.assertTrue(allow_photo_request("test", limit=2, now=start))
        db.session.remove()
        self.assertTrue(allow_photo_request("test", limit=2, now=start))
        self.assertFalse(allow_photo_request("test", limit=2, now=start))
        self.assertTrue(allow_photo_request("other", limit=2, now=start))
        self.assertTrue(allow_photo_request("test", limit=2, now=start + timedelta(minutes=11)))

    def test_rate_limiter_fails_closed_when_database_unavailable(self):
        with patch.object(db.session, "execute", side_effect=OperationalError("query", {}, Exception("offline"))):
            with self.assertRaises(CustomerPhotoRateLimitUnavailable):
                allow_photo_request("unavailable", limit=2)

    def test_public_api_does_not_disclose_order_and_blocks_cross_access(self):
        _, token = self.offer()
        client = self.app.test_client()
        response = client.get("/api/customer-photos", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("order_id", response.json)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(client.get("/api/customer-photos", headers={"Authorization": "Bearer wrong"}).status_code, 404)

    def test_public_upload_is_private_single_use_and_has_no_fiscal_side_effects(self):
        item, token = self.offer()
        image = self.image()
        content = image.stream.read()
        client = self.app.test_client()
        with patch("api.customer_photo_service.send_photo_message") as smtp:
            response = client.post(
                "/api/customer-photos",
                headers={"Authorization": f"Bearer {token}"},
                data={
                    "commercial_consent": "yes",
                    "front_photo": (BytesIO(content), "frontal.png", "image/png"),
                    "perspective_photo": (BytesIO(self.image(color="blue").stream.read()), "lateral.png", "image/png"),
                },
                content_type="multipart/form-data",
            )
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("order_id", response.json)
        self.assertEqual(smtp.call_count, 2)
        self.assertEqual(db.session.get(CustomerPhotoRequest, item.id).status, "received")
        self.assertEqual(db.session.get(Orders, self.order_id).order_status, "enviado")
        self.assertEqual(Invoices.query.count(), 0)
        second = client.post(
                "/api/customer-photos",
                headers={"Authorization": f"Bearer {token}"},
                data={"commercial_consent": "yes", "front_photo": (BytesIO(content), "reja.png", "image/png")},
                content_type="multipart/form-data",
        )
        self.assertEqual(second.status_code, 400)
        self.assertEqual(CustomerPhotoImage.query.count(), 0)

    def test_photo_multipart_stream_stays_in_memory(self):
        with self.app.test_request_context("/api/customer-photos", method="POST") as context:
            stream = context.request._get_file_stream(1024, "image/jpeg", "photo.jpg")
            self.assertIsInstance(stream, BytesIO)


if __name__ == "__main__":
    unittest.main()

import importlib.util
from datetime import datetime, timedelta
from base64 import b64encode
from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
HAS_DEPS = all(importlib.util.find_spec(name) for name in ("flask", "flask_admin", "flask_sqlalchemy", "PIL"))

if HAS_DEPS:
    from flask import Flask
    from flask_admin import Admin
    from PIL import Image
    from sqlalchemy.exc import OperationalError
    from werkzeug.datastructures import FileStorage

    from api.admin import CustomerPhotoRequestAdminView, OrderAdminView
    from api.customer_photo_routes import customer_photo_bp
    from api.customer_photo_service import (
        CustomerPhotoError, create_photo_request, resolve_photo_request,
        rotate_photo_link,
        review_photo_request, stale_upload_attempts, submit_photos, token_hash, utcnow,
    )
    from api.customer_photo_rate_limit import CustomerPhotoRateLimitUnavailable, allow_photo_request
    from api.models import (
        CheckoutSessions, ConfirmedOrderContext, CustomerPhotoRequest,
        CustomerPhotoImage, CustomerPhotoUploadAttempt, Invoices, OrderDetails, Orders, Users, db,
    )


class FakeStorage:
    def __init__(self, *, fail=False):
        self.objects = {}
        self.fail = fail

    def put_object(self, *, storage_key, content, mime_type):
        if self.fail:
            raise RuntimeError("R2 failed")
        self.objects[storage_key] = content

    def delete_object(self, *, storage_key):
        self.objects.pop(storage_key, None)


@unittest.skipUnless(HAS_DEPS, "Backend test dependencies are not installed.")
class CustomerPhotoRequestTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder=str(ROOT / "src" / "templates"))
        self.app.config.update(
            SECRET_KEY="test-secret", SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            APP_ENV="development",
            CUSTOMER_PHOTOS_ENABLED=True,
            CUSTOMER_PHOTOS_INCENTIVE_ENABLED=False,
            CUSTOMER_PHOTOS_TERMS_VERSION="draft-v1",
            CUSTOMER_PHOTOS_TERMS_TEXT="Borrador de condiciones sometido a aprobación.",
            CUSTOMER_PHOTOS_CONSENT_TEXT="Borrador de autorización comercial.",
            CUSTOMER_PHOTOS_TERMS_URL="https://example.test/condiciones",
            CUSTOMER_PHOTOS_TOKEN_DAYS=30,
            FRONTEND_URL="https://example.test",
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

    def test_upload_private_images_consent_and_duplicate_protection(self):
        item, token = self.offer()
        storage = FakeStorage()
        result = submit_photos(
            token=token, files=[self.image(color="red"), self.image(color="blue")],
            commercial_consent="no", app=self.app, storage=storage,
        )
        self.assertEqual(result.status, "received")
        self.assertFalse(result.commercial_consent)
        self.assertEqual(result.consent_text, "Borrador de autorización comercial.")
        self.assertEqual(result.consent_version, "draft-v1")
        self.assertEqual(len(result.images), 2)
        self.assertEqual(len(storage.objects), 2)
        with self.assertRaises(CustomerPhotoError):
            submit_photos(token=token, files=[self.image()], commercial_consent="yes", app=self.app, storage=storage)

    def test_upload_rejects_missing_consent_mime_and_duplicate_files(self):
        _, token = self.offer()
        with self.assertRaises(CustomerPhotoError):
            submit_photos(token=token, files=[self.image()], commercial_consent="", app=self.app, storage=FakeStorage())
        with self.assertRaises(CustomerPhotoError):
            submit_photos(token=token, files=[self.image(mime="image/jpeg")], commercial_consent="yes", app=self.app, storage=FakeStorage())
        with self.assertRaises(CustomerPhotoError):
            submit_photos(token=token, files=[self.image(), self.image()], commercial_consent="yes", app=self.app, storage=FakeStorage())

    def test_storage_failure_does_not_accept_submission(self):
        item, token = self.offer()
        with self.assertRaises(RuntimeError):
            submit_photos(token=token, files=[self.image()], commercial_consent="yes", app=self.app, storage=FakeStorage(fail=True))
        self.assertEqual(db.session.get(CustomerPhotoRequest, item.id).status, "offered")
        self.assertEqual(CustomerPhotoImage.query.count(), 0)
        self.assertEqual(CustomerPhotoUploadAttempt.query.count(), 0)

    def test_token_rotated_during_r2_upload_cannot_confirm(self):
        item, token = self.offer()
        storage = FakeStorage()
        original_put = storage.put_object

        def rotate_during_upload(**kwargs):
            original_put(**kwargs)
            locked = db.session.query(CustomerPhotoRequest).filter_by(id=item.id).with_for_update().one()
            rotate_photo_link(locked, app=self.app)
            db.session.commit()

        storage.put_object = rotate_during_upload
        with self.assertRaises(CustomerPhotoError):
            submit_photos(token=token, files=[self.image()], commercial_consent="yes", app=self.app, storage=storage)
        self.assertEqual(db.session.get(CustomerPhotoRequest, item.id).status, "offered")
        self.assertEqual(CustomerPhotoImage.query.count(), 0)
        self.assertEqual(CustomerPhotoUploadAttempt.query.count(), 0)
        self.assertEqual(storage.objects, {})

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
            submit_photos(token=token, files=[self.image()], commercial_consent="yes", app=self.app, storage=FakeStorage())
        self.assertEqual(CustomerPhotoUploadAttempt.query.count(), 0)
        self.app.config["APP_ENV"] = "development"
        submit_photos(token=token, files=[self.image()], commercial_consent="yes", app=self.app, storage=FakeStorage())
        self.app.config["APP_ENV"] = "production"
        with self.assertRaises(CustomerPhotoError):
            review_photo_request(request_id=item.id, decision="approve", note="", actor="admin", app=self.app)
        self.assertEqual(item.status, "received")

    def test_stale_reservation_is_reported_without_deletion(self):
        item, _ = self.offer()
        attempt = CustomerPhotoUploadAttempt(request_id=item.id, storage_key="customer-photos/test/orphan.jpg")
        db.session.add(attempt)
        db.session.commit()
        self.assertEqual(stale_upload_attempts(now=utcnow() + timedelta(days=2)), [attempt])
        self.assertEqual(CustomerPhotoUploadAttempt.query.count(), 1)

    def test_review_is_explicit_and_never_pays(self):
        item, token = self.offer()
        submit_photos(token=token, files=[self.image()], commercial_consent="yes", app=self.app, storage=FakeStorage())
        reviewed = review_photo_request(request_id=item.id, decision="approve", note="Adecuadas", actor="admin", app=self.app)
        db.session.commit()
        self.assertEqual(reviewed.status, "approved")
        self.assertEqual(reviewed.images[0].review_status, "approved")
        with self.assertRaises(CustomerPhotoError):
            review_photo_request(request_id=item.id, decision="approve", note="", actor="admin", app=self.app)

    def test_incentive_approval_only_marks_refund_pending(self):
        self.app.config["CUSTOMER_PHOTOS_INCENTIVE_ENABLED"] = True
        item, token = self.offer()
        item.mode = "incentive"
        item.offered_amount = 20
        db.session.commit()
        submit_photos(token=token, files=[self.image()], commercial_consent="yes", app=self.app, storage=FakeStorage())
        with patch("api.customer_photo_service.get_private_object_storage") as storage:
            reviewed = review_photo_request(request_id=item.id, decision="approve", note="Aptas", actor="admin", app=self.app)
            db.session.commit()
            storage.assert_not_called()
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

    def test_reject_requires_note_and_consent_can_be_revoked(self):
        item, token = self.offer()
        submit_photos(token=token, files=[self.image()], commercial_consent="yes", app=self.app, storage=FakeStorage())
        with self.assertRaises(CustomerPhotoError):
            review_photo_request(request_id=item.id, decision="reject", note="", actor="admin")
        response = self.app.test_client().post(
            "/api/customer-photos/consent/revoke", headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(item.consent_revoked_at)
        reviewed = review_photo_request(request_id=item.id, decision="reject", note="No coincide", actor="admin")
        db.session.commit()
        self.assertEqual(reviewed.status, "rejected")

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
        storage = FakeStorage()
        client = self.app.test_client()
        with patch("api.customer_photo_service.get_private_object_storage", return_value=storage):
            response = client.post(
                "/api/customer-photos",
                headers={"Authorization": f"Bearer {token}"},
                data={
                    "commercial_consent": "yes",
                    "photos": (BytesIO(content), "reja.png", "image/png"),
                },
                content_type="multipart/form-data",
            )
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("order_id", response.json)
        self.assertEqual(len(storage.objects), 1)
        self.assertEqual(db.session.get(CustomerPhotoRequest, item.id).status, "received")
        self.assertEqual(db.session.get(Orders, self.order_id).order_status, "enviado")
        self.assertEqual(Invoices.query.count(), 0)
        with patch("api.customer_photo_service.get_private_object_storage", return_value=storage):
            second = client.post(
                "/api/customer-photos",
                headers={"Authorization": f"Bearer {token}"},
                data={"commercial_consent": "yes", "photos": (BytesIO(content), "reja.png", "image/png")},
                content_type="multipart/form-data",
            )
        self.assertEqual(second.status_code, 400)
        self.assertEqual(CustomerPhotoImage.query.count(), 1)


if __name__ == "__main__":
    unittest.main()

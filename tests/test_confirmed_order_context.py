import re
import sys
import unittest
import importlib.util
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


HAS_DEPS = all(
    importlib.util.find_spec(package) is not None
    for package in ("flask", "flask_sqlalchemy", "sqlalchemy", "slugify")
)


if HAS_DEPS:
    from flask import Flask
    from sqlalchemy.exc import IntegrityError

    from api.confirmed_order_context_service import (
        ConfirmedOrderInput,
        ConfirmedOrderContextError,
        build_web_checkout_confirmation_input,
        persist_confirmed_order_context,
    )
    from api.models import (
        Categories,
        CheckoutSessions,
        ConfirmedOrderContext,
        OrderDetails,
        Orders,
        Products,
        Users,
        db,
    )
    from api.routes import _finalize_order_from_checkout_quote


@unittest.skipUnless(HAS_DEPS, "Flask/SQLAlchemy test dependencies are not installed.")
class ConfirmedOrderContextTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            ENABLE_INVOICE_WORKFLOW_AFTER_CHECKOUT=False,
            MAIL_USERNAME="no-reply@example.test",
        )
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            category = Categories(nombre="Rejas", descripcion="Tests", slug="rejas")
            db.session.add(category)
            db.session.flush()
            product = Products(
                nombre="Reja fija Essex",
                descripcion="Modelo de pruebas",
                precio=100,
                categoria_id=category.id,
                slug="reja-fija-essex",
            )
            second_product = Products(
                nombre="Reja fija Albany",
                descripcion="Segundo modelo de pruebas",
                precio=75,
                categoria_id=category.id,
                slug="reja-fija-albany",
            )
            user = Users(email="cliente@example.test", password="x")
            db.session.add_all([product, second_product, user])
            db.session.commit()
            self.product_id = product.id
            self.second_product_id = second_product.id
            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def customer_snapshot(self):
        return {
            "firstname": "Ana",
            "lastname": "Cliente",
            "email": "cliente@example.test",
            "phone": "600000000",
            "legal_name": "Ana Cliente",
            "tax_id": "00000000T",
            "billing_address": "Calle Fiscal 1",
            "billing_postal_code": "13001",
            "billing_city": "Ciudad Real",
            "shipping_address": "Calle Entrega 1",
            "shipping_postal_code": "13001",
            "shipping_city": "Ciudad Real",
        }

    def checkout_quote(self):
        return {
            "currency": "EUR",
            "lines": [
                {
                    "product_id": self.product_id,
                    "product_name": "Reja fija Essex",
                    "quantity": 1,
                    "alto": 118,
                    "ancho": 122,
                    "anclaje": "Sin obra: con agujeros interiores",
                    "color": "satinado_blanco",
                    "screw_option": "standard",
                    "unit_price": 100.00,
                    "line_total": 100.00,
                    "shipping_type": "normal",
                    "shipping_cost": 0.0,
                }
            ],
            "subtotal": 100.00,
            "shipping_cost": 0.0,
            "discount_percent": 0.0,
            "discount_amount": 0.0,
            "total_amount": 100.00,
        }

    def paid_checkout_session(self, *, provider, payment_reference, quote=None, customer=None):
        quote = deepcopy(quote or self.checkout_quote())
        customer = deepcopy(customer or self.customer_snapshot())
        values = {
            "user_id": self.user_id,
            "payment_provider": provider,
            "status": "paid",
            "public_checkout_token": f"{provider}-confirmed-context-token",
            "subtotal": quote["subtotal"],
            "shipping_cost": quote["shipping_cost"],
            "discount_amount": quote["discount_amount"],
            "total_amount": quote["total_amount"],
            "quote_snapshot": deepcopy(quote),
            "customer_snapshot": deepcopy(customer),
        }
        if provider == "stripe":
            values["payment_intent_id"] = payment_reference
        else:
            values["provider_order_id"] = "ORDER-REAL-001"
            values["provider_capture_id"] = payment_reference

        checkout_session = CheckoutSessions(**values)
        db.session.add(checkout_session)
        db.session.commit()
        return checkout_session, quote, customer

    def finalize(self, checkout_session):
        return _finalize_order_from_checkout_quote(
            user=db.session.get(Users, self.user_id),
            checkout_quote=checkout_session.quote_snapshot,
            customer_snapshot=checkout_session.customer_snapshot,
            checkout_session=checkout_session,
        )

    def persisted_order(self, locator):
        order = Orders(
            user_id=self.user_id,
            total_amount=100.0,
            locator=locator,
            order_status="pendiente",
        )
        db.session.add(order)
        db.session.flush()
        return order

    def external_confirmation(
        self,
        *,
        source="admin_external",
        payment_method="cash",
        payment_status="confirmed",
        payment_reference=None,
        provider_identifiers=None,
        payment_confirmed_at=datetime(2026, 9, 10, 9, 45),
        confirmed_by="admin@example.test",
        internal_note="Pago externo confirmado por administración.",
    ):
        return ConfirmedOrderInput(
            source=source,
            payment_method=payment_method,
            payment_status=payment_status,
            payment_reference=payment_reference,
            provider_identifiers=provider_identifiers,
            payment_confirmed_at=payment_confirmed_at,
            payment_amount=Decimal("100.00"),
            currency="EUR",
            confirmed_by=confirmed_by,
            internal_note=internal_note,
        )

    def test_stripe_checkout_creates_one_frozen_context_from_authoritative_snapshots(self):
        with self.app.app_context(), patch("api.routes.send_order_confirmation_email"):
            checkout_session, quote, customer = self.paid_checkout_session(
                provider="stripe",
                payment_reference="pi_real_confirmed_001",
            )

            order, created = self.finalize(checkout_session)

            self.assertTrue(created)
            context = ConfirmedOrderContext.query.one()
            self.assertEqual(context.source, "web_checkout")
            self.assertEqual(context.order_id, order.id)
            self.assertEqual(context.source_checkout_session_id, checkout_session.id)
            self.assertIsNone(context.source_manual_draft_id)
            self.assertEqual(context.quote_snapshot, quote)
            self.assertEqual(context.customer_snapshot, customer)
            self.assertEqual(context.payment_method, "stripe")
            self.assertEqual(context.payment_status, "confirmed")
            self.assertEqual(context.payment_reference, "pi_real_confirmed_001")
            self.assertEqual(
                context.provider_identifiers,
                {"payment_intent_id": "pi_real_confirmed_001"},
            )
            self.assertEqual(context.payment_amount, Decimal("100.00"))
            self.assertEqual(context.currency, "EUR")
            self.assertIsNone(context.payment_confirmed_at)
            self.assertIsNotNone(context.confirmed_at)
            self.assertEqual(checkout_session.order_id, order.id)
            self.assertEqual(checkout_session.status, "order_created")

    def test_paypal_checkout_uses_the_real_capture_reference(self):
        with self.app.app_context(), patch("api.routes.send_order_confirmation_email"):
            checkout_session, _, _ = self.paid_checkout_session(
                provider="paypal",
                payment_reference="CAPTURE-REAL-001",
            )

            order, created = self.finalize(checkout_session)

            self.assertTrue(created)
            context = ConfirmedOrderContext.query.one()
            self.assertEqual(context.order_id, order.id)
            self.assertEqual(context.payment_method, "paypal")
            self.assertEqual(context.payment_status, "confirmed")
            self.assertEqual(context.payment_reference, "CAPTURE-REAL-001")
            self.assertEqual(
                context.provider_identifiers,
                {
                    "provider_order_id": "ORDER-REAL-001",
                    "provider_capture_id": "CAPTURE-REAL-001",
                },
            )

    def test_web_checkout_adapter_builds_neutral_confirmation_input(self):
        with self.app.app_context():
            checkout_session, _, _ = self.paid_checkout_session(
                provider="stripe",
                payment_reference="pi_neutral_confirmation_input",
            )

            confirmation = build_web_checkout_confirmation_input(checkout_session)

            self.assertEqual(confirmation.source, "web_checkout")
            self.assertEqual(confirmation.payment_method, "stripe")
            self.assertEqual(confirmation.payment_status, "confirmed")
            self.assertEqual(confirmation.payment_reference, "pi_neutral_confirmation_input")
            self.assertEqual(
                confirmation.provider_identifiers,
                {"payment_intent_id": "pi_neutral_confirmation_input"},
            )
            self.assertEqual(confirmation.payment_amount, Decimal("100.00"))
            self.assertEqual(confirmation.currency, "EUR")
            self.assertEqual(confirmation.source_checkout_session_id, checkout_session.id)
            self.assertIsNone(confirmation.source_manual_draft_id)
            self.assertIsNone(confirmation.payment_confirmed_at)

    def test_web_checkout_requires_real_stripe_and_paypal_references(self):
        with self.app.app_context():
            stripe_session, _, _ = self.paid_checkout_session(
                provider="stripe",
                payment_reference="pi_reference_required",
            )
            stripe_session.payment_intent_id = None
            with self.assertRaisesRegex(ConfirmedOrderContextError, "referencia"):
                build_web_checkout_confirmation_input(stripe_session)

            paypal_session, _, _ = self.paid_checkout_session(
                provider="paypal",
                payment_reference="CAPTURE-reference-required",
            )
            paypal_session.provider_order_id = None
            paypal_session.provider_capture_id = None
            with self.assertRaisesRegex(ConfirmedOrderContextError, "referencia"):
                build_web_checkout_confirmation_input(paypal_session)

    def test_future_external_cash_without_reference_requires_actor_and_note(self):
        with self.app.app_context():
            for index, values in enumerate(
                (
                    {"confirmed_by": None, "internal_note": "Confirmado internamente."},
                    {"confirmed_by": "admin@example.test", "internal_note": None},
                ),
                start=1,
            ):
                order = self.persisted_order(f"CX10{index:02d}")
                with self.assertRaisesRegex(ConfirmedOrderContextError, "requiere"):
                    persist_confirmed_order_context(
                        db_session=db.session,
                        order=order,
                        quote_snapshot=self.checkout_quote(),
                        customer_snapshot=self.customer_snapshot(),
                        confirmation=self.external_confirmation(**values),
                    )

    def test_external_payment_evidence_requires_real_date_and_actor_for_every_method(self):
        with self.app.app_context():
            invalid_inputs = (
                self.external_confirmation(
                    payment_method="bank_transfer",
                    payment_reference="TRF-2026-0001",
                    payment_confirmed_at=None,
                ),
                self.external_confirmation(
                    payment_method="bank_transfer",
                    payment_reference="TRF-2026-0001",
                    confirmed_by=" ",
                ),
            )
            for index, confirmation in enumerate(invalid_inputs, start=1):
                with self.subTest(confirmation=confirmation):
                    order = self.persisted_order(f"CX15{index:02d}")
                    with self.assertRaisesRegex(ConfirmedOrderContextError, "requiere"):
                        persist_confirmed_order_context(
                            db_session=db.session,
                            order=order,
                            quote_snapshot=self.checkout_quote(),
                            customer_snapshot=self.customer_snapshot(),
                            confirmation=confirmation,
                        )

    def test_future_external_other_without_reference_requires_actor_and_note(self):
        with self.app.app_context():
            order = self.persisted_order("CX1101")
            confirmation = self.external_confirmation(
                payment_method="external_other",
                confirmed_by=None,
                internal_note=None,
            )

            with self.assertRaisesRegex(ConfirmedOrderContextError, "requiere"):
                persist_confirmed_order_context(
                    db_session=db.session,
                    order=order,
                    quote_snapshot=self.checkout_quote(),
                    customer_snapshot=self.customer_snapshot(),
                    confirmation=confirmation,
                )

    def test_future_external_stripe_and_paypal_require_real_references(self):
        with self.app.app_context():
            for index, payment_method in enumerate(("stripe", "paypal"), start=1):
                order = self.persisted_order(f"CX11{index + 1:02d}")
                confirmation = self.external_confirmation(
                    payment_method=payment_method,
                    payment_reference=None,
                )
                with self.assertRaisesRegex(ConfirmedOrderContextError, "requieren"):
                    persist_confirmed_order_context(
                        db_session=db.session,
                        order=order,
                        quote_snapshot=self.checkout_quote(),
                        customer_snapshot=self.customer_snapshot(),
                        confirmation=confirmation,
                    )

    def test_payment_reference_is_nullable_for_auditable_external_cash(self):
        with self.app.app_context():
            order = self.persisted_order("CX1201")
            context, created = persist_confirmed_order_context(
                db_session=db.session,
                order=order,
                quote_snapshot=self.checkout_quote(),
                customer_snapshot=self.customer_snapshot(),
                confirmation=self.external_confirmation(),
            )
            db.session.commit()

            self.assertTrue(created)
            self.assertTrue(ConfirmedOrderContext.__table__.c.payment_reference.nullable)
            self.assertEqual(context.source, "admin_external")
            self.assertEqual(context.payment_method, "cash")
            self.assertEqual(context.payment_status, "confirmed")
            self.assertIsNone(context.payment_reference)
            self.assertIsNone(context.provider_identifiers)

    def test_service_rejects_invalid_confirmation_vocabularies(self):
        with self.app.app_context():
            invalid_inputs = (
                {"source": "unknown"},
                {"payment_method": "wire"},
                {"payment_status": "pending"},
            )
            for index, values in enumerate(invalid_inputs, start=1):
                order = self.persisted_order(f"CX13{index:02d}")
                with self.assertRaisesRegex(ConfirmedOrderContextError, "no es válido"):
                    persist_confirmed_order_context(
                        db_session=db.session,
                        order=order,
                        quote_snapshot=self.checkout_quote(),
                        customer_snapshot=self.customer_snapshot(),
                        confirmation=self.external_confirmation(**values),
                    )

    def test_database_checks_reject_invalid_confirmation_vocabularies(self):
        with self.app.app_context():
            invalid_values = (
                {"source": "unknown", "payment_method": "cash", "payment_status": "confirmed"},
                {"source": "admin_external", "payment_method": "wire", "payment_status": "confirmed"},
                {"source": "admin_external", "payment_method": "cash", "payment_status": "pending"},
            )
            for index, values in enumerate(invalid_values, start=1):
                order = self.persisted_order(f"CX14{index:02d}")
                db.session.add(
                    ConfirmedOrderContext(
                        order_id=order.id,
                        quote_snapshot=self.checkout_quote(),
                        customer_snapshot=self.customer_snapshot(),
                        payment_amount=Decimal("100.00"),
                        currency="EUR",
                        payment_reference=None,
                        **values,
                    )
                )
                with self.assertRaises(IntegrityError):
                    db.session.commit()
                db.session.rollback()

    def test_physical_order_characterizes_the_frozen_operational_fields(self):
        with self.app.app_context(), patch("api.routes.send_order_confirmation_email"):
            checkout_session, quote, customer = self.paid_checkout_session(
                provider="stripe",
                payment_reference="pi_physical_characterization",
            )

            order, created = self.finalize(checkout_session)

            self.assertTrue(created)
            self.assertEqual(order.user_id, self.user_id)
            self.assertRegex(order.locator, re.compile(r"^[A-Z]{2}\d{4}$"))
            self.assertEqual(order.order_status, "pendiente")
            self.assertEqual(order.total_amount, quote["total_amount"])
            self.assertEqual(order.shipping_cost, quote["shipping_cost"])
            self.assertEqual(order.discount_code, quote["discount_code"] if "discount_code" in quote else None)
            self.assertEqual(order.discount_value, quote["discount_amount"])
            self.assertIsNone(order.invoice_number)
            self.assertIsNone(order.estimated_delivery_at)
            self.assertIsNone(order.estimated_delivery_note)
            self.assertIsNotNone(order.order_date)

            detail = OrderDetails.query.one()
            line = quote["lines"][0]
            self.assertEqual(detail.product_id, line["product_id"])
            self.assertEqual(detail.quantity, line["quantity"])
            self.assertEqual(detail.line_type, "physical")
            self.assertEqual(detail.alto, line["alto"])
            self.assertEqual(detail.ancho, line["ancho"])
            self.assertEqual(detail.anclaje, line["anclaje"])
            self.assertEqual(detail.color, line["color"])
            self.assertEqual(detail.screw_option, line["screw_option"])
            self.assertEqual(detail.screw_length_mm, 80)
            self.assertEqual(detail.screw_supplement, 0.0)
            self.assertEqual(detail.precio_total, line["unit_price"])
            self.assertEqual(detail.shipping_type, line["shipping_type"])
            self.assertEqual(detail.shipping_cost, line["shipping_cost"])
            self.assertEqual(detail.firstname, customer["firstname"])
            self.assertEqual(detail.lastname, customer["lastname"])
            self.assertEqual(detail.shipping_address, customer["shipping_address"])
            self.assertEqual(detail.shipping_city, customer["shipping_city"])
            self.assertEqual(detail.shipping_postal_code, customer["shipping_postal_code"])
            self.assertEqual(detail.billing_address, customer["billing_address"])
            self.assertEqual(detail.billing_city, customer["billing_city"])
            self.assertEqual(detail.billing_postal_code, customer["billing_postal_code"])
            self.assertEqual(detail.CIF, customer.get("CIF"))

    def test_multiple_physical_quote_lines_preserve_each_configuration(self):
        quote = self.checkout_quote()
        quote["lines"].append({
            "product_id": self.second_product_id,
            "product_name": "Reja fija Albany",
            "quantity": 2,
            "alto": 150,
            "ancho": 100,
            "anclaje": "Sin obra: con pletinas",
            "color": "forja_negro",
            "screw_option": "long_150",
            "unit_price": 75.0,
            "line_total": 150.0,
            "shipping_type": "normal",
            "shipping_cost": 9.95,
        })
        quote.update({
            "subtotal": 250.0,
            "shipping_cost": 9.95,
            "discount_code": "ACUERDO10",
            "discount_percent": 0.0,
            "discount_amount": 10.0,
            "total_amount": 249.95,
        })

        with self.app.app_context(), patch("api.routes.send_order_confirmation_email"):
            checkout_session, _, _ = self.paid_checkout_session(
                provider="stripe",
                payment_reference="pi_multiple_lines",
                quote=quote,
            )

            order, created = self.finalize(checkout_session)

            self.assertTrue(created)
            self.assertEqual(order.total_amount, 249.95)
            self.assertEqual(order.shipping_cost, 9.95)
            self.assertEqual(order.discount_code, "ACUERDO10")
            self.assertEqual(order.discount_value, 10.0)
            details = {detail.product_id: detail for detail in OrderDetails.query.all()}
            self.assertEqual(set(details), {self.product_id, self.second_product_id})
            self.assertEqual(details[self.product_id].quantity, 1)
            self.assertEqual(details[self.second_product_id].quantity, 2)
            self.assertEqual(details[self.second_product_id].alto, 150)
            self.assertEqual(details[self.second_product_id].ancho, 100)
            self.assertEqual(details[self.second_product_id].anclaje, "Sin obra: con pletinas")
            self.assertEqual(details[self.second_product_id].color, "forja_negro")
            self.assertEqual(details[self.second_product_id].screw_option, "long_150")
            self.assertEqual(details[self.second_product_id].screw_length_mm, 150)
            self.assertEqual(details[self.second_product_id].screw_supplement, 8.95)

    def test_identical_physical_quote_lines_keep_the_existing_grouping(self):
        quote = self.checkout_quote()
        quote["lines"].append(deepcopy(quote["lines"][0]))
        quote.update({
            "subtotal": 200.0,
            "shipping_cost": 0.0,
            "discount_amount": 0.0,
            "total_amount": 200.0,
        })

        with self.app.app_context(), patch("api.routes.send_order_confirmation_email"):
            checkout_session, _, _ = self.paid_checkout_session(
                provider="stripe",
                payment_reference="pi_grouped_lines",
                quote=quote,
            )

            order, created = self.finalize(checkout_session)

            self.assertTrue(created)
            self.assertEqual(order.total_amount, 200.0)
            details = OrderDetails.query.all()
            self.assertEqual(len(details), 1)
            self.assertEqual(details[0].quantity, 2)
            self.assertEqual(details[0].precio_total, 100.0)

    def test_finalizer_retry_keeps_one_order_and_one_context(self):
        with self.app.app_context(), patch("api.routes.send_order_confirmation_email"):
            checkout_session, _, _ = self.paid_checkout_session(
                provider="stripe",
                payment_reference="pi_real_confirmed_retry",
            )

            order, created = self.finalize(checkout_session)
            retried_order, retried_created = self.finalize(checkout_session)

            self.assertTrue(created)
            self.assertFalse(retried_created)
            self.assertEqual(retried_order.id, order.id)
            self.assertEqual(Orders.query.count(), 1)
            self.assertEqual(ConfirmedOrderContext.query.count(), 1)

    def test_context_creation_failure_rolls_back_the_new_order(self):
        with self.app.app_context(), patch("api.routes.send_order_confirmation_email"):
            checkout_session, _, _ = self.paid_checkout_session(
                provider="stripe",
                payment_reference="pi_real_confirmed_rollback",
            )

            with patch(
                "api.order_creation_service.persist_confirmed_order_context",
                side_effect=ConfirmedOrderContextError("context failure"),
            ):
                with self.assertRaisesRegex(ConfirmedOrderContextError, "context failure"):
                    self.finalize(checkout_session)

            self.assertEqual(Orders.query.count(), 0)
            self.assertEqual(OrderDetails.query.count(), 0)
            self.assertEqual(ConfirmedOrderContext.query.count(), 0)
            restored_session = db.session.get(CheckoutSessions, checkout_session.id)
            self.assertIsNone(restored_session.order_id)
            self.assertEqual(restored_session.status, "paid")

    def test_historical_order_remains_valid_without_a_confirmed_context(self):
        with self.app.app_context():
            historical_order = Orders(
                user_id=self.user_id,
                total_amount=50.0,
                locator="HX0001",
                order_status="pendiente",
            )
            db.session.add(historical_order)
            db.session.commit()

            persisted_order = db.session.get(Orders, historical_order.id)
            self.assertIsNone(persisted_order.confirmed_order_context)
            self.assertEqual(ConfirmedOrderContext.query.count(), 0)

    def test_confirmed_context_is_immutable_including_new_audit_fields(self):
        with self.app.app_context(), patch("api.routes.send_order_confirmation_email"):
            checkout_session, _, _ = self.paid_checkout_session(
                provider="stripe",
                payment_reference="pi_real_confirmed_immutable",
            )
            self.finalize(checkout_session)

            context = ConfirmedOrderContext.query.one()
            context.internal_note = "No debe editarse"
            with self.assertRaisesRegex(ValueError, "inmutable"):
                db.session.commit()
            db.session.rollback()

            db.session.refresh(context)
            context.payment_status = "cancelled"
            with self.assertRaisesRegex(ValueError, "inmutable"):
                db.session.commit()
            db.session.rollback()

            db.session.refresh(context)
            context.provider_identifiers = {"payment_intent_id": "pi_tampered"}
            with self.assertRaisesRegex(ValueError, "inmutable"):
                db.session.commit()
            db.session.rollback()


if __name__ == "__main__":
    unittest.main()

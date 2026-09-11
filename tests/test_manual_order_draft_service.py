import importlib.util
import sys
import unittest
from copy import deepcopy
from datetime import date, datetime, timezone
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
    from sqlalchemy import text

    from api.manual_order_draft_service import (
        ManualOrderDraftNotEditableError,
        ManualOrderDraftQuoteError,
        ManualOrderDraftValidationError,
        build_manual_order_draft_fingerprint,
        build_manual_order_draft_quote_input,
        invalidate_manual_order_draft_review,
        is_manual_order_draft_review_current,
        manual_order_draft_quote_snapshots_match,
        review_manual_order_draft,
    )
    from api.models import (
        Categories,
        CheckoutSessions,
        ManualOrderDraft,
        ManualOrderDraftLine,
        Orders,
        Products,
        Users,
        db,
    )


@unittest.skipUnless(HAS_DEPS, "Flask/SQLAlchemy test dependencies are not installed.")
class ManualOrderDraftReviewServiceTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            db.session.execute(text("PRAGMA foreign_keys=ON"))

            category = Categories(nombre="Rejas", descripcion="Tests", slug="rejas")
            user = Users(
                email="cliente@example.test",
                password="x",
                firstname="Perfil",
                lastname="Original",
                phone="611 111 111",
                billing_address="Dirección perfil 1",
                billing_city="Ciudad Real",
                billing_postal_code="13001",
                shipping_address="Entrega perfil 1",
                shipping_city="Ciudad Real",
                shipping_postal_code="13001",
                CIF="00000000T",
            )
            db.session.add_all([category, user])
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
                precio=90,
                categoria_id=category.id,
                slug="reja-fija-albany",
            )
            db.session.add_all([product, second_product])
            db.session.commit()
            self.user_id = user.id
            self.product_id = product.id
            self.second_product_id = second_product.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def customer_draft(self, **overrides):
        customer = {
            "firstname": "Ana",
            "lastname": "Cliente",
            "email": "CLIENTE@example.test",
            "phone": "600 000 000",
            "legal_name": "Ana Cliente",
            "tax_id": "00000000T",
            "billing_address": "Calle Fiscal 1",
            "billing_postal_code": "13001",
            "billing_city": "Ciudad Real",
            "shipping_address": "Calle Entrega 1",
            "shipping_postal_code": "13001",
            "shipping_city": "Ciudad Real",
        }
        customer.update(overrides)
        return customer

    def create_draft(self, *, lines=None, customer=None, **overrides):
        values = {
            "user_id": self.user_id,
            "customer_draft": customer or self.customer_draft(),
        }
        values.update(overrides)
        draft = ManualOrderDraft(**values)
        if lines is None:
            lines = [
                ManualOrderDraftLine(
                    position=0,
                    product_id=self.product_id,
                    quantity=1,
                    alto=118,
                    ancho=122,
                    anclaje="Sin obra: con agujeros interiores",
                    color="satinado_blanco",
                    screw_option="standard",
                )
            ]
        draft.lines.extend(lines)
        db.session.add(draft)
        db.session.commit()
        return draft

    def test_valid_draft_uses_the_real_quote_engine_and_stores_its_snapshot(self):
        with self.app.app_context():
            draft = self.create_draft()

            quote = review_manual_order_draft(db_session=db.session, draft=draft)

            self.assertEqual(quote, draft.last_quote_snapshot)
            self.assertEqual(quote["lines"][0]["product_id"], self.product_id)
            self.assertEqual(quote["lines"][0]["quantity"], 1)
            self.assertIn("subtotal", quote)
            self.assertIn("shipping_cost", quote)
            self.assertIn("discount_amount", quote)
            self.assertIn("total_amount", quote)
            self.assertEqual(draft.customer_draft["email"], "cliente@example.test")
            self.assertEqual(len(draft.quote_fingerprint), 64)
            self.assertTrue(is_manual_order_draft_review_current(draft))
            self.assertEqual(Orders.query.count(), 0)
            self.assertEqual(CheckoutSessions.query.count(), 0)

    def test_review_does_not_commit_or_change_the_user_profile(self):
        with self.app.app_context():
            draft = self.create_draft()
            user = db.session.get(Users, self.user_id)
            original_profile = {
                "firstname": user.firstname,
                "lastname": user.lastname,
                "phone": user.phone,
                "billing_address": user.billing_address,
                "shipping_address": user.shipping_address,
                "CIF": user.CIF,
            }

            with patch.object(db.session, "commit") as commit:
                review_manual_order_draft(db_session=db.session, draft=draft)

            commit.assert_not_called()
            self.assertEqual(
                {
                    "firstname": user.firstname,
                    "lastname": user.lastname,
                    "phone": user.phone,
                    "billing_address": user.billing_address,
                    "shipping_address": user.shipping_address,
                    "CIF": user.CIF,
                },
                original_profile,
            )
            db.session.rollback()

    def test_non_editable_drafts_are_rejected(self):
        with self.app.app_context():
            for status in (ManualOrderDraft.STATUS_ISSUED, ManualOrderDraft.STATUS_CANCELLED):
                with self.subTest(status=status):
                    draft = self.create_draft(status=status)
                    with self.assertRaises(ManualOrderDraftNotEditableError):
                        review_manual_order_draft(db_session=db.session, draft=draft)

    def test_draft_without_lines_is_rejected(self):
        with self.app.app_context():
            draft = self.create_draft(lines=[])

            with self.assertRaisesRegex(ManualOrderDraftValidationError, "al menos una"):
                review_manual_order_draft(db_session=db.session, draft=draft)

    def test_invalid_user_and_customer_email_mismatch_are_rejected(self):
        with self.app.app_context():
            invalid_user_draft = ManualOrderDraft(
                user_id=999999,
                status=ManualOrderDraft.STATUS_DRAFT,
                customer_draft=self.customer_draft(),
            )
            invalid_user_draft.lines.append(
                ManualOrderDraftLine(
                    position=0,
                    product_id=self.product_id,
                    quantity=1,
                    alto=118,
                    ancho=122,
                    anclaje="Sin obra: con agujeros interiores",
                    color="satinado_blanco",
                    screw_option="standard",
                )
            )
            with self.assertRaisesRegex(ManualOrderDraftValidationError, "no existe"):
                review_manual_order_draft(db_session=db.session, draft=invalid_user_draft)

            draft = self.create_draft(customer=self.customer_draft(email="other@example.test"))
            with self.assertRaisesRegex(ManualOrderDraftValidationError, "debe coincidir"):
                review_manual_order_draft(db_session=db.session, draft=draft)

    def test_adapter_orders_configurations_and_excludes_client_prices(self):
        with self.app.app_context():
            draft = self.create_draft(
                lines=[
                    ManualOrderDraftLine(
                        position=1,
                        product_id=self.product_id,
                        quantity=2,
                        alto=100,
                        ancho=120,
                        anclaje="Sin obra: con agujeros interiores",
                        color="satinado_blanco",
                        screw_option="long_150",
                    ),
                    ManualOrderDraftLine(
                        position=0,
                        product_id=self.second_product_id,
                        quantity=1,
                        alto=110,
                        ancho=115,
                        anclaje="Sin obra: con pletinas",
                        color="satinado_blanco",
                        screw_option="standard",
                    ),
                ]
            )
            draft.lines[0].precio_total = 0.01

            raw_products = build_manual_order_draft_quote_input(draft)

            self.assertEqual([line["product_id"] for line in raw_products], [
                self.second_product_id,
                self.product_id,
            ])
            self.assertEqual(raw_products[1]["screw_option"], "long_150")
            self.assertNotIn("precio_total", raw_products[0])
            self.assertNotIn("price", raw_products[0])

    def test_review_calls_build_checkout_quote_with_only_adapter_input(self):
        with self.app.app_context():
            draft = self.create_draft()
            expected_quote = {
                "lines": [{"product_id": self.product_id, "quantity": 1}],
                "subtotal": 100.0,
                "shipping_cost": 0.0,
                "discount_code": None,
                "discount_code_valid": False,
                "discount_percent": 0.0,
                "discount_amount": 0.0,
                "total_amount": 100.0,
                "comparison": {"has_difference": False},
            }
            expected_input = build_manual_order_draft_quote_input(draft)

            with patch(
                "api.manual_order_draft_service.build_checkout_quote",
                return_value=deepcopy(expected_quote),
            ) as quote_builder:
                review_manual_order_draft(db_session=db.session, draft=draft)

            quote_builder.assert_called_once_with(
                raw_products=expected_input,
                discount_code=None,
            )

    def test_client_controlled_price_cannot_influence_the_reviewed_quote(self):
        with self.app.app_context():
            draft = self.create_draft()
            draft.lines[0].precio_total = 0.01
            draft.last_quote_snapshot = {"total_amount": 0.01}

            quote = review_manual_order_draft(db_session=db.session, draft=draft)

            self.assertNotEqual(quote["lines"][0]["unit_price"], 0.01)
            self.assertNotEqual(quote["total_amount"], 0.01)

    def test_discount_codes_are_processed_by_the_canonical_engine(self):
        with self.app.app_context():
            draft = self.create_draft(discount_code=" rejas10 ")

            quote = review_manual_order_draft(db_session=db.session, draft=draft)

            self.assertEqual(draft.discount_code, "REJAS10")
            self.assertEqual(quote["discount_code"], "REJAS10")
            self.assertTrue(quote["discount_code_valid"])
            self.assertEqual(quote["discount_percent"], 10.0)

            draft.discount_code = "NO-EXISTE"
            with self.assertRaisesRegex(ManualOrderDraftQuoteError, "descuento"):
                review_manual_order_draft(db_session=db.session, draft=draft)

    def test_fingerprint_is_stable_for_equivalent_json_decimal_and_dates(self):
        with self.app.app_context():
            draft = self.create_draft(
                estimated_delivery_at=date(2026, 9, 30),
                estimated_delivery_note="Entrega planificada",
            )
            quote_a = {
                "total_amount": Decimal("100.00"),
                "metadata": {
                    "reviewed_at": datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc),
                    "currency": "EUR",
                },
            }
            quote_b = {
                "metadata": {
                    "currency": "EUR",
                    "reviewed_at": datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc),
                },
                "total_amount": Decimal("100.00"),
            }

            fingerprint_a = build_manual_order_draft_fingerprint(
                draft,
                quote_snapshot=quote_a,
            )
            fingerprint_b = build_manual_order_draft_fingerprint(
                draft,
                quote_snapshot=quote_b,
            )

            self.assertEqual(fingerprint_a, fingerprint_b)
            self.assertTrue(manual_order_draft_quote_snapshots_match(quote_a, quote_b))

    def test_review_current_detects_all_relevant_editable_changes(self):
        with self.app.app_context():
            draft = self.create_draft(
                estimated_delivery_at=date(2026, 9, 30),
                estimated_delivery_note="Entrega inicial",
            )
            review_manual_order_draft(db_session=db.session, draft=draft)
            self.assertTrue(is_manual_order_draft_review_current(draft))

            changes = (
                ("quantity", 2),
                ("alto", 119),
                ("ancho", 123),
            )
            for field, value in changes:
                with self.subTest(field=field):
                    original = getattr(draft.lines[0], field)
                    setattr(draft.lines[0], field, value)
                    self.assertFalse(is_manual_order_draft_review_current(draft))
                    setattr(draft.lines[0], field, original)

            customer = dict(draft.customer_draft)
            customer["billing_city"] = "Miguelturra"
            draft.customer_draft = customer
            self.assertFalse(is_manual_order_draft_review_current(draft))
            draft.customer_draft["billing_city"] = "Ciudad Real"

            draft.discount_code = "REJAS10"
            self.assertFalse(is_manual_order_draft_review_current(draft))
            draft.discount_code = None

            draft.estimated_delivery_at = date(2026, 10, 1)
            self.assertFalse(is_manual_order_draft_review_current(draft))
            draft.estimated_delivery_at = date(2026, 9, 30)

            draft.estimated_delivery_note = "Entrega actualizada"
            self.assertFalse(is_manual_order_draft_review_current(draft))

    def test_invalidation_clears_review_and_a_new_review_restores_it(self):
        with self.app.app_context():
            draft = self.create_draft()
            review_manual_order_draft(db_session=db.session, draft=draft)

            invalidate_manual_order_draft_review(draft)

            self.assertIsNone(draft.last_quote_snapshot)
            self.assertIsNone(draft.quote_fingerprint)
            self.assertFalse(is_manual_order_draft_review_current(draft))

            review_manual_order_draft(db_session=db.session, draft=draft)
            self.assertIsNotNone(draft.last_quote_snapshot)
            self.assertTrue(is_manual_order_draft_review_current(draft))

    def test_invalid_configuration_is_reported_as_quote_error(self):
        with self.app.app_context():
            draft = self.create_draft()
            draft.lines[0].alto = 10

            with self.assertRaises(ManualOrderDraftQuoteError):
                review_manual_order_draft(db_session=db.session, draft=draft)


if __name__ == "__main__":
    unittest.main()

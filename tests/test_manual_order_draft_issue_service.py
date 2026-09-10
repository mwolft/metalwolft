import importlib.util
import sys
import unittest
import uuid
from copy import deepcopy
from datetime import date, datetime
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
    from sqlalchemy.exc import IntegrityError

    from api.invoice_confirmation_context import (
        build_invoice_confirmation_context_from_confirmed_order_context,
    )
    from api.manual_order_draft_issue_service import (
        ManualOrderDraftCancelledError,
        ManualOrderDraftIssuedIntegrityError,
        ManualOrderDraftPaymentEvidenceError,
        ManualOrderDraftOrderCreationError,
        ManualOrderDraftNotFoundError,
        ManualOrderDraftCustomerError,
        ManualOrderDraftQuoteChangedError,
        ManualOrderDraftReviewRequiredError,
        ManualOrderDraftReviewStaleError,
        issue_manual_order_draft,
    )
    from api.manual_order_draft_service import review_manual_order_draft
    from api.models import (
        Categories,
        CheckoutSessions,
        ConfirmedOrderContext,
        Invoices,
        ManualOrderDraft,
        ManualOrderDraftLine,
        OrderDetails,
        Orders,
        Products,
        Users,
        WorkOrder,
        db,
    )


@unittest.skipUnless(HAS_DEPS, "Flask/SQLAlchemy test dependencies are not installed.")
class ManualOrderDraftIssueServiceTest(unittest.TestCase):
    ACTOR = "flask_admin:sergio"

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
            db.session.add_all((category, user))
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
            db.session.add_all((product, second_product))
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
            "payment_method": "bank_transfer",
            "payment_reference": "TRF-2026-0001",
            "payment_confirmed_at": datetime(2026, 9, 10, 9, 45),
            "payment_note": "Transferencia contrastada con el extracto bancario.",
            "internal_note": "Pedido acordado fuera de la web.",
            "estimated_delivery_at": date(2026, 9, 30),
            "estimated_delivery_note": "Entrega acordada con el cliente.",
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

    def review(self, draft):
        quote = review_manual_order_draft(db_session=db.session, draft=draft)
        db.session.commit()
        return quote

    def issue(self, draft, *, actor=ACTOR):
        return issue_manual_order_draft(
            db_session=db.session,
            draft_id=draft.id,
            actor=actor,
        )

    def test_bank_transfer_creates_one_canonical_order_and_context(self):
        with self.app.app_context():
            draft = self.create_draft()
            reviewed_quote = self.review(draft)
            original_user = db.session.get(Users, self.user_id)
            original_profile = (
                original_user.firstname,
                original_user.lastname,
                original_user.phone,
                original_user.billing_address,
            )

            with patch.object(db.session, "commit") as commit:
                order = self.issue(draft)

            commit.assert_not_called()
            self.assertEqual(Orders.query.count(), 1)
            self.assertEqual(OrderDetails.query.count(), 1)
            self.assertEqual(ConfirmedOrderContext.query.count(), 1)
            self.assertEqual(CheckoutSessions.query.count(), 0)
            self.assertEqual(Invoices.query.count(), 0)
            self.assertEqual(WorkOrder.query.count(), 0)

            detail = OrderDetails.query.one()
            context = ConfirmedOrderContext.query.one()
            self.assertEqual(order.user_id, self.user_id)
            self.assertEqual(order.order_status, "pendiente")
            self.assertEqual(order.total_amount, reviewed_quote["total_amount"])
            self.assertEqual(order.shipping_cost, reviewed_quote["shipping_cost"])
            self.assertEqual(order.discount_code, reviewed_quote["discount_code"])
            self.assertEqual(order.discount_value, reviewed_quote["discount_amount"])
            self.assertEqual(order.estimated_delivery_at, date(2026, 9, 30))
            self.assertEqual(order.estimated_delivery_note, "Entrega acordada con el cliente.")
            self.assertEqual(detail.product_id, self.product_id)
            self.assertEqual(detail.quantity, 1)
            self.assertEqual(detail.alto, 118)
            self.assertEqual(detail.ancho, 122)
            self.assertEqual(detail.anclaje, "Sin obra: con agujeros interiores")
            self.assertEqual(detail.color, "satinado_blanco")
            self.assertEqual(detail.screw_option, "standard")
            self.assertEqual(context.order_id, order.id)
            self.assertEqual(context.source, "admin_external")
            self.assertEqual(context.source_manual_draft_id, draft.id)
            self.assertEqual(context.quote_snapshot, reviewed_quote)
            self.assertEqual(context.customer_snapshot, draft.customer_draft)
            self.assertEqual(context.payment_method, "bank_transfer")
            self.assertEqual(context.payment_reference, "TRF-2026-0001")
            self.assertEqual(context.payment_amount, Decimal(str(reviewed_quote["total_amount"])))
            self.assertEqual(context.currency, "EUR")
            self.assertEqual(context.confirmed_by, self.ACTOR)
            self.assertEqual(context.internal_note, "Pedido acordado fuera de la web.")
            self.assertIsNone(context.provider_identifiers)
            self.assertEqual(draft.status, ManualOrderDraft.STATUS_ISSUED)
            self.assertEqual(draft.issued_order_id, order.id)
            self.assertTrue(draft.issuance_key)
            self.assertIsInstance(uuid.UUID(draft.issuance_key), uuid.UUID)
            self.assertEqual(
                (
                    original_user.firstname,
                    original_user.lastname,
                    original_user.phone,
                    original_user.billing_address,
                ),
                original_profile,
            )
            db.session.rollback()

    def test_multiple_draft_lines_create_multiple_order_details(self):
        with self.app.app_context():
            draft = self.create_draft(
                lines=[
                    ManualOrderDraftLine(
                        position=0,
                        product_id=self.product_id,
                        quantity=1,
                        alto=118,
                        ancho=122,
                        anclaje="Sin obra: con agujeros interiores",
                        color="satinado_blanco",
                        screw_option="standard",
                    ),
                    ManualOrderDraftLine(
                        position=1,
                        product_id=self.second_product_id,
                        quantity=2,
                        alto=100,
                        ancho=120,
                        anclaje="Sin obra: con pletinas",
                        color="satinado_blanco",
                        screw_option="long_150",
                    ),
                ]
            )
            self.review(draft)

            order = self.issue(draft)

            details = OrderDetails.query.filter_by(order_id=order.id).order_by(OrderDetails.id).all()
            self.assertEqual(len(details), 2)
            self.assertEqual(
                [(detail.product_id, detail.quantity, detail.alto, detail.ancho) for detail in details],
                [
                    (self.product_id, 1, 118, 122),
                    (self.second_product_id, 2, 100, 120),
                ],
            )

    def test_cash_and_external_other_accept_only_their_valid_evidence(self):
        with self.app.app_context():
            valid_cases = (
                {
                    "payment_method": "cash",
                    "payment_reference": None,
                    "internal_note": None,
                    "payment_note": "Cobro en efectivo registrado en caja.",
                },
                {
                    "payment_method": "external_other",
                    "payment_reference": "RECIBO-EXTERNO-001",
                    "internal_note": None,
                    "payment_note": None,
                },
                {
                    "payment_method": "external_other",
                    "payment_reference": None,
                    "internal_note": "Pago confirmado con justificante firmado.",
                    "payment_note": None,
                },
            )

            for index, values in enumerate(valid_cases, start=1):
                with self.subTest(values=values):
                    draft = self.create_draft(**values)
                    self.review(draft)

                    order = self.issue(draft)
                    context = order.confirmed_order_context

                    self.assertEqual(context.source, "admin_external")
                    self.assertEqual(context.payment_method, values["payment_method"])
                    self.assertEqual(context.confirmed_by, self.ACTOR)
                    if values["payment_method"] == "cash":
                        self.assertEqual(
                            context.internal_note,
                            "Cobro en efectivo registrado en caja.",
                        )
                    db.session.commit()

    def test_rejects_incomplete_external_payment_evidence_before_creating_order(self):
        with self.app.app_context():
            invalid_cases = (
                {"payment_method": "bank_transfer", "payment_reference": None},
                {"payment_method": "bank_transfer", "payment_reference": " "},
                {
                    "payment_method": "cash",
                    "payment_reference": None,
                    "payment_note": " ",
                    "internal_note": None,
                },
                {
                    "payment_method": "external_other",
                    "payment_reference": None,
                    "payment_note": None,
                    "internal_note": None,
                },
                {"payment_confirmed_at": None},
            )

            for values in invalid_cases:
                with self.subTest(values=values):
                    draft = self.create_draft(**values)
                    self.review(draft)

                    with self.assertRaises(ManualOrderDraftPaymentEvidenceError):
                        self.issue(draft)

                    self.assertEqual(Orders.query.count(), 0)
                    self.assertEqual(ConfirmedOrderContext.query.count(), 0)
                    db.session.rollback()

    def test_actor_must_be_explicit_and_nonempty(self):
        with self.app.app_context():
            draft = self.create_draft()
            self.review(draft)

            with self.assertRaises(ManualOrderDraftPaymentEvidenceError):
                self.issue(draft, actor=" ")

            self.assertEqual(Orders.query.count(), 0)
            self.assertEqual(ConfirmedOrderContext.query.count(), 0)

    def test_missing_draft_invalid_customer_and_canonical_failure_have_domain_errors(self):
        with self.app.app_context():
            with self.assertRaises(ManualOrderDraftNotFoundError):
                issue_manual_order_draft(
                    db_session=db.session,
                    draft_id=999999,
                    actor=self.ACTOR,
                )

            invalid_customer = self.create_draft(
                customer=self.customer_draft(email="other@example.test"),
            )
            with self.assertRaises(ManualOrderDraftCustomerError):
                self.issue(invalid_customer)

            draft = self.create_draft()
            self.review(draft)
            with patch(
                "api.manual_order_draft_issue_service.create_order_from_confirmed_input",
                side_effect=ValueError("configuración canónica inválida"),
            ):
                with self.assertRaises(ManualOrderDraftOrderCreationError):
                    self.issue(draft)
            self.assertEqual(Orders.query.count(), 0)
            self.assertEqual(ConfirmedOrderContext.query.count(), 0)

    def test_review_is_required_and_stale_edits_are_rejected(self):
        with self.app.app_context():
            missing_review = self.create_draft()
            with self.assertRaises(ManualOrderDraftReviewRequiredError):
                self.issue(missing_review)

            missing_fingerprint = self.create_draft()
            self.review(missing_fingerprint)
            missing_fingerprint.quote_fingerprint = None
            with self.assertRaises(ManualOrderDraftReviewRequiredError):
                self.issue(missing_fingerprint)
            db.session.rollback()

            for mutation in (
                lambda draft: setattr(draft.lines[0], "quantity", 2),
                lambda draft: setattr(
                    draft,
                    "customer_draft",
                    {**draft.customer_draft, "billing_city": "Miguelturra"},
                ),
            ):
                with self.subTest(mutation=mutation):
                    draft = self.create_draft()
                    self.review(draft)
                    mutation(draft)

                    with self.assertRaises(ManualOrderDraftReviewStaleError):
                        self.issue(draft)

                    self.assertEqual(Orders.query.count(), 0)
                    db.session.rollback()

    def test_external_quote_changes_block_emission_without_replacing_review(self):
        with self.app.app_context():
            scenarios = ("price", "shipping", "discount", "availability")
            for scenario in scenarios:
                with self.subTest(scenario=scenario):
                    draft = self.create_draft(
                        discount_code="REJAS10" if scenario == "discount" else None,
                    )
                    reviewed_quote = deepcopy(self.review(draft))
                    reviewed_fingerprint = draft.quote_fingerprint

                    if scenario == "price":
                        product = db.session.get(Products, self.product_id)
                        product.precio = 120
                        db.session.flush()
                        expected_error = ManualOrderDraftQuoteChangedError
                    elif scenario == "shipping":
                        expected_error = ManualOrderDraftQuoteChangedError
                    elif scenario == "discount":
                        expected_error = ManualOrderDraftQuoteChangedError
                    else:
                        product = db.session.get(Products, self.product_id)
                        product.available_for_sale = False
                        db.session.flush()
                        expected_error = ManualOrderDraftQuoteChangedError

                    if scenario == "shipping":
                        patcher = patch("api.checkout_service.STANDARD_SHIPPING_COST", 25.0)
                    elif scenario == "discount":
                        patcher = patch.dict("api.checkout_service.DISCOUNT_CODES", {}, clear=True)
                    else:
                        patcher = None

                    if patcher is None:
                        with self.assertRaises(expected_error):
                            self.issue(draft)
                    else:
                        with patcher:
                            with self.assertRaises(expected_error):
                                self.issue(draft)

                    self.assertEqual(draft.last_quote_snapshot, reviewed_quote)
                    self.assertEqual(draft.quote_fingerprint, reviewed_fingerprint)
                    self.assertEqual(Orders.query.count(), 0)
                    self.assertEqual(ConfirmedOrderContext.query.count(), 0)
                    db.session.rollback()

    def test_issued_draft_returns_its_existing_order_without_duplicates(self):
        with self.app.app_context():
            draft = self.create_draft()
            self.review(draft)
            first_order = self.issue(draft)
            db.session.commit()
            issuance_key = draft.issuance_key

            second_order = self.issue(draft, actor="otro-actor")

            self.assertEqual(second_order.id, first_order.id)
            self.assertEqual(draft.issuance_key, issuance_key)
            self.assertEqual(Orders.query.count(), 1)
            self.assertEqual(ConfirmedOrderContext.query.count(), 1)

    def test_caller_rollback_removes_the_entire_emission_atomically(self):
        with self.app.app_context():
            draft = self.create_draft()
            self.review(draft)

            self.issue(draft)
            self.assertEqual(Orders.query.count(), 1)
            self.assertEqual(ConfirmedOrderContext.query.count(), 1)

            db.session.rollback()
            restored_draft = db.session.get(ManualOrderDraft, draft.id)
            self.assertEqual(Orders.query.count(), 0)
            self.assertEqual(ConfirmedOrderContext.query.count(), 0)
            self.assertEqual(restored_draft.status, ManualOrderDraft.STATUS_DRAFT)
            self.assertIsNone(restored_draft.issued_order_id)
            self.assertIsNone(restored_draft.issuance_key)

    def test_cancelled_or_inconsistent_issued_drafts_are_rejected(self):
        with self.app.app_context():
            cancelled = self.create_draft(status=ManualOrderDraft.STATUS_CANCELLED)
            with self.assertRaises(ManualOrderDraftCancelledError):
                self.issue(cancelled)

            inconsistent = self.create_draft(status=ManualOrderDraft.STATUS_ISSUED)
            with self.assertRaises(ManualOrderDraftIssuedIntegrityError):
                self.issue(inconsistent)

    def test_source_manual_draft_uniqueness_is_a_database_barrier(self):
        with self.app.app_context():
            draft = self.create_draft()
            quote = self.review(draft)
            order = self.issue(draft)
            db.session.commit()

            duplicate_order = Orders(
                user_id=self.user_id,
                total_amount=quote["total_amount"],
                locator="MO9001",
                order_status="pendiente",
            )
            db.session.add(duplicate_order)
            db.session.flush()
            db.session.add(
                ConfirmedOrderContext(
                    order_id=duplicate_order.id,
                    source="admin_external",
                    quote_snapshot=quote,
                    customer_snapshot=draft.customer_draft,
                    payment_method="bank_transfer",
                    payment_status="confirmed",
                    payment_reference="TRF-OTHER-001",
                    payment_confirmed_at=datetime(2026, 9, 10, 10, 0),
                    payment_amount=Decimal(str(quote["total_amount"])),
                    currency="EUR",
                    confirmed_by=self.ACTOR,
                    source_manual_draft_id=draft.id,
                    internal_note="Duplicado intencionado para comprobar la restricción.",
                )
            )

            with self.assertRaises(IntegrityError):
                db.session.flush()
            db.session.rollback()
            self.assertEqual(order.id, draft.issued_order_id)

    def test_manual_orders_produce_invoice_valid_contexts_without_checkout(self):
        with self.app.app_context():
            cases = (
                {
                    "payment_method": "bank_transfer",
                    "payment_reference": "TRF-2026-0901",
                },
                {
                    "payment_method": "cash",
                    "payment_reference": None,
                    "internal_note": None,
                    "payment_note": "Cobro en efectivo registrado en caja.",
                },
                {
                    "payment_method": "external_other",
                    "payment_reference": None,
                    "internal_note": "Pago confirmado con justificante firmado.",
                },
            )
            for values in cases:
                with self.subTest(values=values):
                    draft = self.create_draft(**values)
                    self.review(draft)
                    order = self.issue(draft)
                    context = build_invoice_confirmation_context_from_confirmed_order_context(
                        order=order,
                        confirmed_order_context=order.confirmed_order_context,
                    )

                    self.assertEqual(context.source, "admin_external")
                    self.assertEqual(context.source_checkout_session_id, None)
                    self.assertEqual(context.source_manual_draft_id, draft.id)
                    self.assertEqual(context.payment_amount, Decimal(str(order.total_amount)))
                    self.assertIsNone(getattr(order, "checkout_session", None))
                    db.session.commit()

    def test_issue_service_uses_row_lock_and_never_commits_or_rolls_back(self):
        source = (SRC_DIR / "api/manual_order_draft_issue_service.py").read_text(
            encoding="utf-8"
        )

        self.assertIn(".with_for_update()", source)
        self.assertNotIn("db_session.commit(", source)
        self.assertNotIn("db_session.rollback(", source)
        self.assertNotIn("CheckoutSessions(", source)
        self.assertNotIn("Invoices(", source)
        self.assertNotIn("WorkOrder(", source)
        self.assertNotIn("cleanup_cart", source)
        self.assertNotIn("send_order_confirmation_email", source)
        self.assertNotIn("handle_post_order_invoice_workflow", source)


if __name__ == "__main__":
    unittest.main()

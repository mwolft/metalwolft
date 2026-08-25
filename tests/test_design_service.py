import sys
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.design_service import (  # noqa: E402
    SERVICE_LINE_TYPE,
    DesignServiceUnavailable,
    DesignServiceValidationError,
    assert_order_accepts_physical_detail,
    build_design_checkout_quote,
    build_design_service_quote,
    create_design_request,
    order_contains_design_service,
    transition_design_request_status,
)
from api.admin import DesignRequestAdminView  # noqa: E402
from api.models import DesignRequest, OrderDetails  # noqa: E402
from api.routes import _assert_homogeneous_order_details, _build_order_details_from_checkout_quote  # noqa: E402
from api.invoice_snapshot_builder import build_invoice_snapshot  # noqa: E402
from api.work_order_service import generate_work_order_pdf  # noqa: E402


class _QuoteSession:
    def __init__(self, config, products):
        self.config = config
        self.products = {product.id: product for product in products}

    def get(self, model, identity):
        if model.__name__ == "DesignServiceConfig":
            return self.config
        if model.__name__ == "Products":
            return self.products.get(identity)
        return None


class _CreateSession(_QuoteSession):
    def __init__(self, config, products, existing=None):
        super().__init__(config, products)
        self.added = []
        self.existing = existing

    def query(self, _model):
        return self

    def filter_by(self, **_kwargs):
        return self

    def one_or_none(self):
        return self.existing

    def add(self, value):
        self.added.append(value)
        if value.__class__.__name__ == "DesignRequest" and value.id is None:
            value.id = 31

    def flush(self):
        return None


def _items():
    return [
        {"product_id": 7, "width_cm": 200, "height_cm": 120},
        {"product_id": 7, "width_cm": 150, "height_cm": 120},
        {"product_id": 8, "width_cm": 100, "height_cm": 80},
    ]


def _tiers():
    return [
        SimpleNamespace(min_design_count=2, unit_price_gross=Decimal("22.45")),
        SimpleNamespace(min_design_count=3, unit_price_gross=Decimal("19.95")),
        SimpleNamespace(min_design_count=4, unit_price_gross=Decimal("17.95")),
    ]


class DesignServiceQuoteTest(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(
            is_active=True,
            base_price_gross=Decimal("24.95"),
            currency="EUR",
            lead_time_hours=24,
            price_tiers=_tiers(),
        )
        self.products = [
            SimpleNamespace(id=7, nombre="Reja Maryland", available_for_sale=True),
            SimpleNamespace(id=8, nombre="Reja Vermont", available_for_sale=True),
        ]
        self.session = _QuoteSession(self.config, self.products)

    @patch("api.design_service.ensure_product_available_for_sale")
    def test_one_design_uses_authoritative_2495_price_without_shipping_or_anchorage(self, _availability):
        quote = build_design_service_quote(
            db_session=self.session,
            items=[{"product_id": 7, "width_cm": 200, "height_cm": 120}],
        )

        self.assertEqual(quote["total_amount"], "24.95")
        self.assertEqual(quote["tax_base"], "20.62")
        self.assertEqual(quote["tax_amount"], "4.33")
        self.assertFalse(quote["requires_shipping"])
        self.assertEqual(quote["shipping_cost"], "0.00")
        self.assertNotIn("anclaje", quote["lines"][0])
        self.assertNotIn("screw_option", quote["lines"][0])

    @patch("api.design_service.ensure_product_available_for_sale")
    def test_multiple_designs_use_matching_tier_and_freeze_a_discount(self, _availability):
        quote = build_design_service_quote(db_session=self.session, items=_items())

        self.assertEqual(quote["subtotal"], "74.85")
        self.assertEqual(quote["discount_amount"], "15.00")
        self.assertEqual(quote["total_amount"], "59.85")
        self.assertEqual(quote["pricing_tier_min_design_count"], 3)
        self.assertEqual(len(quote["lines"]), 3)

    @patch("api.design_service.ensure_product_available_for_sale")
    def test_safe_fallback_charges_base_price_when_no_tier_matches(self, _availability):
        self.config.price_tiers = [SimpleNamespace(min_design_count=6, unit_price_gross=Decimal("20.00"))]
        quote = build_design_service_quote(db_session=self.session, items=_items())
        self.assertEqual(quote["total_amount"], "74.85")
        self.assertEqual(quote["discount_amount"], "0.00")

    @patch("api.design_service.ensure_product_available_for_sale")
    def test_exact_duplicates_are_deduplicated_but_different_measurements_and_models_are_valid(self, _availability):
        duplicate_quote = build_design_service_quote(
            db_session=self.session,
            items=[
                {"product_id": 7, "width_cm": 200, "height_cm": 120},
                {"product_id": 7, "width_cm": 200, "height_cm": 120},
                {"product_id": 7, "width_cm": 200, "height_cm": 120},
            ],
        )
        self.assertEqual(len(duplicate_quote["items"]), 1)
        self.assertEqual(duplicate_quote["total_amount"], "24.95")
        quote = build_design_service_quote(db_session=self.session, items=_items())
        self.assertEqual([line["product_name"] for line in quote["lines"]], [
            "Reja Maryland", "Reja Maryland", "Reja Vermont",
        ])

    def test_inactive_service_is_rejected(self):
        self.config.is_active = False
        with self.assertRaises(DesignServiceUnavailable):
            build_design_service_quote(db_session=self.session, items=_items())

    @patch("api.design_service.ensure_product_available_for_sale")
    def test_creation_freezes_price_lead_time_and_model_name(self, _availability):
        session = _CreateSession(self.config, self.products)
        result = create_design_request(
            db_session=session,
            user_id=4,
            items=_items(),
            creation_key="design-request-key-1",
        )

        request = result.design_request
        created_items = [item for item in session.added if item.__class__.__name__ == "DesignRequestItem"]
        self.assertTrue(result.created)
        self.assertEqual(request.price_gross, Decimal("59.85"))
        self.assertEqual(request.lead_time_hours, 24)
        self.assertEqual([item.product_name for item in created_items], [
            "Reja Maryland", "Reja Maryland", "Reja Vermont",
        ])
        self.assertFalse(hasattr(request, "anchorage_type"))

    @patch("api.design_service.ensure_product_available_for_sale")
    def test_initial_price_table_applies_the_highest_matching_tier(self, _availability):
        expected = {
            1: "24.95",
            2: "44.90",
            3: "59.85",
            4: "71.80",
            5: "89.75",
        }
        for count, total in expected.items():
            items = [
                {"product_id": 7, "width_cm": 100 + index, "height_cm": 120}
                for index in range(count)
            ]
            quote = build_design_service_quote(db_session=self.session, items=items)
            self.assertEqual(quote["total_amount"], total)

    def test_same_user_key_is_idempotent(self):
        existing = SimpleNamespace(id=31, creation_key="design-request-key-1")
        session = _CreateSession(self.config, self.products, existing=existing)
        result = create_design_request(
            db_session=session,
            user_id=4,
            items=_items(),
            creation_key="design-request-key-1",
        )
        self.assertFalse(result.created)
        self.assertIs(result.design_request, existing)

    def test_idempotency_is_scoped_to_user_in_the_database_contract(self):
        unique_constraints = {
            constraint.name: tuple(column.name for column in constraint.columns)
            for constraint in DesignRequest.__table__.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
        }
        self.assertEqual(
            unique_constraints["uq_design_requests_user_creation_key"],
            ("user_id", "creation_key"),
        )


class DesignServiceCheckoutAndSnapshotTest(unittest.TestCase):
    def _request(self):
        return SimpleNamespace(
            id=3,
            user_id=4,
            status="pending_payment",
            subtotal_gross=Decimal("74.85"),
            price_gross=Decimal("59.85"),
            discount_amount=Decimal("15.00"),
            pricing_tier_min_design_count=3,
            lead_time_hours=24,
            items=[
                SimpleNamespace(id=1, product_id=7, product_name="Reja Maryland", width_cm=Decimal("200"), height_cm=Decimal("120")),
                SimpleNamespace(id=2, product_id=7, product_name="Reja Maryland", width_cm=Decimal("150"), height_cm=Decimal("120")),
                SimpleNamespace(id=3, product_id=8, product_name="Reja Vermont", width_cm=Decimal("100"), height_cm=Decimal("80")),
            ],
        )

    def test_checkout_quote_uses_only_frozen_items_and_has_no_shipping(self):
        quote = build_design_checkout_quote(design_request=self._request(), user_id=4)
        self.assertEqual(quote["design_request_id"], 3)
        self.assertEqual(len(quote["lines"]), 3)
        self.assertTrue(all("anclaje" not in line for line in quote["lines"]))
        self.assertFalse(quote["requires_shipping"])

        order_details = _build_order_details_from_checkout_quote(quote)
        self.assertTrue(all(detail["screw_option"] == "not_applicable" for detail in order_details))
        self.assertTrue(all(detail["anclaje"] is None for detail in order_details))

    def test_multidesign_snapshot_is_fiscal_and_omits_physical_attributes(self):
        quote = build_design_checkout_quote(design_request=self._request(), user_id=4)
        checkout_session = SimpleNamespace(
            id=8, order_id=9, status="order_created", payment_provider="stripe",
            payment_intent_id="pi_design_test", provider_order_id=None, provider_capture_id=None,
            quote_snapshot=quote,
            customer_snapshot={
                "firstname": "Ana", "lastname": "Cliente", "email": "ana@example.com",
                "billing_address": "Calle Fiscal 1", "billing_postal_code": "13001",
                "billing_city": "Ciudad Real", "CIF": "00000000T",
            },
            user=SimpleNamespace(email="ana@example.com"),
        )
        snapshot = build_invoice_snapshot(
            SimpleNamespace(id=9, locator="DP123", order_date=datetime(2026, 8, 25), user=checkout_session.user),
            checkout_session,
            {"legal_name": "MetalWolft SL", "tax_id": "B00000000", "address": "Calle Taller 1", "postal_code": "13000", "city": "Ciudad Real", "country_code": "ES"},
            issue_date=datetime(2026, 8, 25),
        )
        self.assertEqual(len(snapshot["lines"]), 3)
        self.assertEqual(snapshot["totals"]["products_amount_before_discount"], "74.85")
        self.assertEqual(snapshot["totals"]["discount_amount"], "15.00")
        self.assertEqual(snapshot["totals"]["total_amount"], "59.85")
        self.assertEqual(sum(Decimal(line["tax_base"]) + Decimal(line["tax_amount"]) for line in snapshot["lines"]), Decimal("59.85"))
        self.assertTrue(all(line["line_type"] == SERVICE_LINE_TYPE for line in snapshot["lines"]))
        self.assertTrue(all("anchoring" not in line["configuration"] for line in snapshot["lines"]))
        self.assertTrue(all("screw_option" not in line["configuration"] for line in snapshot["lines"]))


class DesignServiceOperationalIsolationTest(unittest.TestCase):
    def test_design_service_order_has_no_work_order(self):
        order = SimpleNamespace(order_details=[SimpleNamespace(line_type=SERVICE_LINE_TYPE)])
        self.assertTrue(order_contains_design_service(order))
        with self.assertRaises(ValueError):
            generate_work_order_pdf(order)

    def test_delivered_requires_a_result_and_cancellation_is_not_a_transition(self):
        request = SimpleNamespace(status="in_progress", result_storage_key=None)
        with self.assertRaises(DesignServiceValidationError):
            transition_design_request_status(design_request=request, new_status="delivered")

        request = SimpleNamespace(status="pending", result_storage_key="private/design.pdf", started_at=None, delivered_at=None)
        with self.assertRaises(DesignServiceValidationError):
            transition_design_request_status(design_request=request, new_status="cancelled")

    def test_admin_does_not_offer_cancellation_and_legacy_details_default_to_physical(self):
        allowed_statuses = set().union(*DesignRequestAdminView._ALLOWED_TRANSITIONS.values())
        self.assertNotIn("cancelled", allowed_statuses)
        self.assertEqual(OrderDetails.__table__.c.line_type.server_default.arg, "physical")

    def test_mixed_order_lines_are_rejected_before_order_creation(self):
        with self.assertRaisesRegex(ValueError, "no puede mezclar"):
            _assert_homogeneous_order_details([
                {"line_type": "physical"},
                {"line_type": SERVICE_LINE_TYPE},
            ])

    def test_physical_detail_cannot_be_added_to_a_design_order(self):
        order = SimpleNamespace(
            order_details=[SimpleNamespace(line_type=SERVICE_LINE_TYPE)],
            design_request=SimpleNamespace(id=3),
        )
        with self.assertRaises(DesignServiceValidationError):
            assert_order_accepts_physical_detail(order)

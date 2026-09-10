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


from api.invoice_admin_helpers import (  # noqa: E402
    select_invoice_confirmation_context_for_invoice,
)
from api.invoice_confirmation_context import (  # noqa: E402
    InvoiceConfirmationContextError,
    build_invoice_confirmation_context_from_confirmed_order_context,
)
from api.invoice_snapshot_builder import (  # noqa: E402
    build_invoice_snapshot,
)
from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash  # noqa: E402


def make_quote():
    return {
        "lines": [
            {
                "product_id": 7,
                "producto_id": 7,
                "product_name": "Reja fija Essex",
                "quantity": 1,
                "alto": 109,
                "ancho": 198,
                "anclaje": "Sin obra: con agujeros interiores",
                "color": "satinado_blanco",
                "unit_price": 95.0,
                "line_total": 95.0,
                "shipping_type": "normal",
                "shipping_cost": 0.0,
            }
        ],
        "subtotal": 95.0,
        "shipping_cost": 21.0,
        "discount_code": None,
        "discount_code_valid": False,
        "discount_percent": 0.0,
        "discount_amount": 0.0,
        "total_amount": 116.0,
        "currency": "EUR",
    }


def make_customer():
    return {
        "firstname": "Sergio",
        "lastname": "Arias",
        "email": "cliente@example.com",
        "phone": "600000000",
        "billing_address": "Calle Factura 3",
        "billing_city": "Ciudad Real",
        "billing_postal_code": "13001",
        "CIF": "00000000T",
    }


def make_order(**overrides):
    data = {
        "id": 123,
        "locator": "VO1234",
        "order_date": datetime(2026, 9, 10, 10, 30),
        "user": SimpleNamespace(email="cliente@example.com"),
        "confirmed_order_context": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_issuer():
    return {
        "legal_name": "MetalWolft Legal",
        "trade_name": "MetalWolft",
        "tax_id": "B00000000",
        "address": "Calle Taller 1",
        "postal_code": "13000",
        "city": "Ciudad Real",
        "country_code": "ES",
    }


def make_confirmed_context(**overrides):
    data = {
        "id": 44,
        "order_id": 123,
        "source": "web_checkout",
        "quote_snapshot": make_quote(),
        "customer_snapshot": make_customer(),
        "payment_method": "stripe",
        "payment_status": "confirmed",
        "payment_reference": "pi_real_123",
        "provider_identifiers": {"payment_intent_id": "pi_real_123"},
        "payment_confirmed_at": None,
        "payment_amount": Decimal("116.00"),
        "currency": "EUR",
        "confirmed_by": None,
        "source_checkout_session_id": 56,
        "source_manual_draft_id": None,
        "internal_note": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_legacy_checkout_session(**overrides):
    data = {
        "id": 56,
        "order_id": 123,
        "status": "order_created",
        "payment_provider": "stripe",
        "payment_intent_id": "pi_real_123",
        "provider_order_id": None,
        "provider_capture_id": None,
        "quote_snapshot": make_quote(),
        "customer_snapshot": make_customer(),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class InvoiceConfirmationContextTest(unittest.TestCase):
    def test_web_context_preserves_the_legacy_v2_snapshot_shape(self):
        order = make_order()
        legacy_snapshot = build_invoice_snapshot(
            order,
            make_legacy_checkout_session(),
            make_issuer(),
            issue_date=datetime(2026, 9, 10, 11, 0),
            source="manual",
            actor={"email": "admin@example.com"},
        )
        context = build_invoice_confirmation_context_from_confirmed_order_context(
            order=order,
            confirmed_order_context=make_confirmed_context(),
        )
        coc_snapshot = build_invoice_snapshot(
            order,
            context,
            make_issuer(),
            issue_date=datetime(2026, 9, 10, 11, 0),
            source="manual",
            actor={"email": "admin@example.com"},
        )

        self.assertEqual(coc_snapshot["schema_version"], 2)
        self.assertEqual(coc_snapshot["metadata"]["generator"], legacy_snapshot["metadata"]["generator"])
        self.assertEqual(coc_snapshot["issuer"], legacy_snapshot["issuer"])
        self.assertEqual(coc_snapshot["customer"], legacy_snapshot["customer"])
        self.assertEqual(coc_snapshot["operation"], legacy_snapshot["operation"])
        self.assertEqual(coc_snapshot["lines"], legacy_snapshot["lines"])
        self.assertEqual(coc_snapshot["totals"], legacy_snapshot["totals"])
        self.assertEqual(coc_snapshot["payment"], legacy_snapshot["payment"])
        self.assertEqual(coc_snapshot["references"], legacy_snapshot["references"])

    def test_admin_external_context_builds_v2_without_checkout_identifiers(self):
        order = make_order()
        confirmed_context = make_confirmed_context(
            id=45,
            source="admin_external",
            payment_method="bank_transfer",
            payment_reference="TRF-2026-0001",
            provider_identifiers=None,
            payment_confirmed_at=datetime(2026, 9, 10, 9, 45),
            confirmed_by="flask_admin:sergio",
            source_checkout_session_id=None,
            internal_note="Transferencia confirmada con extracto bancario.",
        )
        context = build_invoice_confirmation_context_from_confirmed_order_context(
            order=order,
            confirmed_order_context=confirmed_context,
        )

        snapshot = build_invoice_snapshot(
            order,
            context,
            make_issuer(),
            issue_date=datetime(2026, 9, 10, 11, 0),
        )

        self.assertEqual(snapshot["schema_version"], 2)
        self.assertEqual(snapshot["payment"]["provider"], "bank_transfer")
        self.assertEqual(snapshot["payment"]["provider_reference"], "TRF-2026-0001")
        self.assertEqual(snapshot["payment"]["paid_at"], "2026-09-10T09:45:00")
        self.assertNotIn("checkout_session_id", snapshot["references"])
        self.assertEqual(snapshot["references"]["confirmation_context_id"], 45)
        self.assertEqual(snapshot["references"]["confirmation_source"], "admin_external")
        self.assertNotIn("payment_intent_id", str(snapshot))
        self.assertNotIn("provider_capture_id", str(snapshot))
        self.assertTrue(calculate_invoice_snapshot_hash(snapshot))

    def test_paypal_context_uses_the_real_capture_reference(self):
        order = make_order()
        context = build_invoice_confirmation_context_from_confirmed_order_context(
            order=order,
            confirmed_order_context=make_confirmed_context(
                payment_method="paypal",
                payment_reference="CAPTURE-123",
                provider_identifiers={
                    "provider_order_id": "ORDER-123",
                    "provider_capture_id": "CAPTURE-123",
                },
            ),
        )

        snapshot = build_invoice_snapshot(
            order,
            context,
            make_issuer(),
            issue_date=datetime(2026, 9, 10, 11, 0),
        )

        self.assertEqual(snapshot["payment"]["provider"], "paypal")
        self.assertEqual(snapshot["payment"]["provider_reference"], "CAPTURE-123")
        self.assertEqual(snapshot["references"]["checkout_session_id"], 56)

    def test_invalid_context_never_falls_back_to_legacy_checkout(self):
        invalid_context = make_confirmed_context(payment_amount=Decimal("99.00"))
        order = make_order(confirmed_order_context=invalid_context)

        with patch(
            "api.invoice_admin_helpers._select_legacy_checkout_confirmation_context_for_invoice"
        ) as legacy_selector:
            selected_context, error = select_invoice_confirmation_context_for_invoice(order)

        self.assertIsNone(selected_context)
        self.assertEqual(error, "El contexto confirmado del pedido no es valido para facturacion.")
        legacy_selector.assert_not_called()

    def test_order_without_context_uses_the_legacy_selector(self):
        order = make_order()
        expected_context = object()

        with patch(
            "api.invoice_admin_helpers._select_legacy_checkout_confirmation_context_for_invoice",
            return_value=(expected_context, None),
        ) as legacy_selector:
            selected_context, error = select_invoice_confirmation_context_for_invoice(order)

        self.assertIs(selected_context, expected_context)
        self.assertIsNone(error)
        legacy_selector.assert_called_once_with(order)

    def test_payment_amount_and_currency_must_match_the_frozen_quote(self):
        order = make_order()
        for overrides in (
            {"payment_amount": Decimal("115.99")},
            {"currency": "USD"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(InvoiceConfirmationContextError):
                    build_invoice_confirmation_context_from_confirmed_order_context(
                        order=order,
                        confirmed_order_context=make_confirmed_context(**overrides),
                    )

    def test_fiscal_customer_validation_blocks_incomplete_context(self):
        customer = make_customer()
        customer.pop("CIF")
        order = make_order(
            confirmed_order_context=make_confirmed_context(customer_snapshot=customer),
        )

        selected_context, error = select_invoice_confirmation_context_for_invoice(order)

        self.assertIsNone(selected_context)
        self.assertEqual(error, "El contexto confirmado del pedido no es valido para facturacion.")

    def test_external_payment_evidence_rules_are_enforced(self):
        order = make_order()
        valid_cash = make_confirmed_context(
            source="admin_external",
            payment_method="cash",
            payment_reference=None,
            provider_identifiers=None,
            payment_confirmed_at=datetime(2026, 9, 10, 9, 45),
            confirmed_by="flask_admin:sergio",
            source_checkout_session_id=None,
            internal_note="Cobro en efectivo registrado en caja.",
        )
        build_invoice_confirmation_context_from_confirmed_order_context(
            order=order,
            confirmed_order_context=valid_cash,
        )
        valid_other = make_confirmed_context(
            source="admin_external",
            payment_method="external_other",
            payment_reference=None,
            provider_identifiers=None,
            payment_confirmed_at=datetime(2026, 9, 10, 9, 45),
            confirmed_by="flask_admin:sergio",
            source_checkout_session_id=None,
            internal_note="Pago externo confirmado con justificante firmado.",
        )
        build_invoice_confirmation_context_from_confirmed_order_context(
            order=order,
            confirmed_order_context=valid_other,
        )

        invalid_contexts = (
            make_confirmed_context(
                source="admin_external",
                payment_method="bank_transfer",
                payment_reference=None,
                provider_identifiers=None,
                payment_confirmed_at=datetime(2026, 9, 10, 9, 45),
                confirmed_by="flask_admin:sergio",
                source_checkout_session_id=None,
                internal_note="Transferencia.",
            ),
            make_confirmed_context(
                source="admin_external",
                payment_method="cash",
                payment_reference=None,
                provider_identifiers=None,
                payment_confirmed_at=datetime(2026, 9, 10, 9, 45),
                confirmed_by="flask_admin:sergio",
                source_checkout_session_id=None,
                internal_note=None,
            ),
            make_confirmed_context(
                source="admin_external",
                payment_method="external_other",
                payment_reference=None,
                provider_identifiers=None,
                payment_confirmed_at=datetime(2026, 9, 10, 9, 45),
                confirmed_by="flask_admin:sergio",
                source_checkout_session_id=None,
                internal_note=None,
            ),
        )
        for invalid_context in invalid_contexts:
            with self.subTest(payment_method=invalid_context.payment_method):
                with self.assertRaises(InvoiceConfirmationContextError):
                    build_invoice_confirmation_context_from_confirmed_order_context(
                        order=order,
                        confirmed_order_context=invalid_context,
                    )


if __name__ == "__main__":
    unittest.main()

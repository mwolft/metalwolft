import copy
import sys
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.invoice_snapshot_builder import (  # noqa: E402
    InvoiceSnapshotValidationError,
    build_invoice_snapshot,
    build_rectification_snapshot_from_invoice,
)


def issuer(overrides=None):
    data = {
        "legal_name": "MetalWolft Legal",
        "trade_name": "MetalWolft",
        "tax_id": "B00000000",
        "address": "Calle Taller 1",
        "postal_code": "13000",
        "city": "Ciudad Real",
        "province": "Ciudad Real",
        "country_code": "ES",
        "email": None,
        "phone": None,
    }
    data.update(overrides or {})
    return data


def customer_snapshot(overrides=None):
    data = {
        "firstname": "Sergio",
        "lastname": "Arias",
        "phone": "600000000",
        "shipping_address": "Calle Envio 2",
        "shipping_city": "Ciudad Real",
        "shipping_postal_code": "13000",
        "billing_address": "Calle Factura 3",
        "billing_city": "Ciudad Real",
        "billing_postal_code": "13001",
        "CIF": "00000000T",
    }
    data.update(overrides or {})
    return data


def quote(overrides=None):
    data = {
        "lines": [
            {
                "product_id": 7,
                "producto_id": 7,
                "product_name": "Reja fija Pittsburgh",
                "quantity": 1,
                "alto": 30,
                "ancho": 30,
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
    }
    data.update(overrides or {})
    return data


def quote_line(product_id, amount, name=None):
    return {
        "product_id": product_id,
        "producto_id": product_id,
        "product_name": name or f"Producto {product_id}",
        "quantity": 1,
        "alto": 30,
        "ancho": 30,
        "anclaje": "Sin obra: con agujeros interiores",
        "color": "satinado_blanco",
        "unit_price": amount,
        "line_total": amount,
    }


def order(overrides=None):
    data = {
        "id": 123,
        "locator": "AB1234",
        "order_date": datetime(2026, 7, 15, 10, 30),
        "user": SimpleNamespace(email="cliente@example.com"),
    }
    data.update(overrides or {})
    return SimpleNamespace(**data)


def checkout_session(overrides=None):
    data = {
        "id": 10,
        "order_id": 123,
        "payment_provider": "stripe",
        "payment_intent_id": "pi_test",
        "provider_order_id": None,
        "provider_capture_id": None,
        "status": "order_created",
        "quote_snapshot": quote(),
        "customer_snapshot": customer_snapshot(),
        "user": SimpleNamespace(email="cliente@example.com"),
    }
    data.update(overrides or {})
    return SimpleNamespace(**data)


def build(**overrides):
    return build_invoice_snapshot(
        overrides.get("order", order()),
        overrides.get("checkout_session", checkout_session()),
        overrides.get("issuer", issuer()),
        issue_date=overrides.get("issue_date", datetime(2026, 7, 16, 9, 0)),
        source=overrides.get("source", "manual"),
        actor=overrides.get("actor"),
    )


def corrective_invoice(overrides=None):
    original_snapshot = build()
    data = {
        "id": 2001,
        "invoice_number": "F2026000001",
        "issued_at": datetime(2026, 7, 16, 10, 0),
        "invoice_type": "ordinary",
        "invoice_snapshot": original_snapshot,
    }
    data.update(overrides or {})
    return SimpleNamespace(**data)


def assert_no_floats(testcase, value):
    if isinstance(value, float):
        testcase.fail(f"Snapshot contains float value: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_floats(testcase, child)
    if isinstance(value, list):
        for child in value:
            assert_no_floats(testcase, child)


def money(value):
    return Decimal(str(value))


def assert_fiscal_totals(testcase, snapshot):
    lines = snapshot["lines"]
    totals = snapshot["totals"]
    testcase.assertEqual(
        sum(money(line["line_amount_before_discount"]) for line in lines),
        money(totals["total_amount_before_discount"]),
    )
    testcase.assertEqual(
        sum(money(line["discount_amount"]) for line in lines),
        money(totals["discount_amount"]),
    )
    testcase.assertEqual(
        sum(money(line["line_total"]) for line in lines),
        money(totals["total_amount"]),
    )
    testcase.assertEqual(
        sum(money(line["tax_base"]) for line in lines),
        money(totals["tax_base"]),
    )
    testcase.assertEqual(
        sum(money(line["tax_amount"]) for line in lines),
        money(totals["tax_amount"]),
    )
    testcase.assertEqual(
        money(totals["tax_base"]) + money(totals["tax_amount"]),
        money(totals["total_amount"]),
    )
    for line in lines:
        testcase.assertEqual(
            money(line["tax_base"]) + money(line["tax_amount"]),
            money(line["line_total"]),
        )
        testcase.assertEqual(
            money(line["line_tax_base_before_discount"]) - money(line["discount_tax_base"]),
            money(line["tax_base"]),
        )


class InvoiceSnapshotBuilderTest(unittest.TestCase):
    def assert_validation_error(self, field, **overrides):
        with self.assertRaises(InvoiceSnapshotValidationError) as error:
            build(**overrides)
        self.assertEqual(error.exception.field, field)

    def test_builds_valid_stripe_snapshot_without_discount(self):
        snapshot = build()

        self.assertEqual(snapshot["schema_version"], 2)
        self.assertEqual(snapshot["metadata"]["generator"], "invoice_snapshot_builder_v2")
        self.assertEqual(snapshot["issuer"]["trade_name"], "MetalWolft")
        self.assertEqual(snapshot["customer"]["legal_name"], "Sergio Arias")
        self.assertEqual(snapshot["customer"]["email"], "cliente@example.com")
        self.assertEqual(snapshot["operation"]["order_id"], 123)
        self.assertEqual(snapshot["operation"]["order_locator"], "AB1234")
        self.assertEqual(snapshot["operation"]["order_date"], "2026-07-15")
        self.assertEqual(snapshot["operation"]["issue_date"], "2026-07-16")
        self.assertEqual(snapshot["operation"]["operation_date"], "2026-07-15")
        self.assertEqual(snapshot["operation"]["currency"], "EUR")
        self.assertEqual(snapshot["operation"]["discount_code"], None)
        self.assertEqual(snapshot["payment"]["provider"], "stripe")
        self.assertEqual(snapshot["payment"]["provider_reference"], "pi_test")
        self.assertEqual(snapshot["payment"]["status"], "paid")
        self.assertEqual(snapshot["references"]["checkout_session_id"], 10)
        self.assertEqual(snapshot["references"]["source"], "manual")

        self.assertEqual(len(snapshot["lines"]), 2)
        product_line = snapshot["lines"][0]
        self.assertEqual(product_line["line_type"], "product")
        self.assertEqual(product_line["product_id"], 7)
        self.assertEqual(product_line["model"], "Reja fija Pittsburgh")
        self.assertEqual(product_line["quantity"], "1")
        self.assertEqual(product_line["unit_price_net"], "78.512397")
        self.assertEqual(product_line["unit_amount_before_discount"], "95.00")
        self.assertEqual(product_line["line_amount_before_discount"], "95.00")
        self.assertEqual(product_line["discount_amount"], "0.00")
        self.assertEqual(product_line["line_tax_base_before_discount"], "78.51")
        self.assertEqual(product_line["discount_tax_base"], "0.00")
        self.assertEqual(product_line["line_total"], "95.00")
        self.assertEqual(product_line["tax_base"], "78.51")
        self.assertEqual(product_line["tax_amount"], "16.49")
        self.assertEqual(
            product_line["configuration"],
            {
                "height_cm": "30",
                "width_cm": "30",
                "anchoring": "Sin obra: con agujeros interiores",
                "color": "satinado_blanco",
            },
        )

        shipping_line = snapshot["lines"][1]
        self.assertEqual(shipping_line["line_type"], "shipping")
        self.assertEqual(shipping_line["unit_price_net"], "17.355372")
        self.assertEqual(shipping_line["description"], "Gastos de envío")
        self.assertEqual(shipping_line["unit_amount_before_discount"], "21.00")
        self.assertEqual(shipping_line["line_amount_before_discount"], "21.00")
        self.assertEqual(shipping_line["discount_amount"], "0.00")
        self.assertEqual(shipping_line["line_tax_base_before_discount"], "17.36")
        self.assertEqual(shipping_line["discount_tax_base"], "0.00")
        self.assertEqual(shipping_line["line_total"], "21.00")
        self.assertEqual(shipping_line["tax_base"], "17.36")
        self.assertEqual(shipping_line["tax_amount"], "3.64")

        self.assertEqual(
            snapshot["totals"],
            {
                "products_amount_before_discount": "95.00",
                "shipping_amount_before_discount": "21.00",
                "total_amount_before_discount": "116.00",
                "discount_amount": "0.00",
                "total_amount": "116.00",
                "tax_base": "95.87",
                "tax_amount": "20.13",
                "rounding_adjustment": "0.00",
            },
        )
        assert_fiscal_totals(self, snapshot)

    def test_new_snapshot_preserves_screw_configuration_and_authoritative_total(self):
        checkout_quote = quote(
            {
                "lines": [
                    {
                        **quote()["lines"][0],
                        "screw_option": "long_150",
                        "screw_length_mm": 150,
                        "screw_supplement": 8.95,
                        "unit_price": 103.95,
                        "line_total": 103.95,
                    }
                ],
                "subtotal": 103.95,
                "shipping_cost": 21.0,
                "total_amount": 124.95,
            }
        )
        session = checkout_session({"quote_snapshot": checkout_quote})

        snapshot = build(checkout_session=session)

        product_line = snapshot["lines"][0]
        self.assertEqual(product_line["configuration"]["screw_option"], "long_150")
        self.assertEqual(product_line["configuration"]["screw_length_mm"], 150)
        self.assertEqual(product_line["configuration"]["screw_supplement"], "8.95")
        self.assertEqual(product_line["unit_amount_before_discount"], "103.95")
        self.assertEqual(snapshot["totals"]["products_amount_before_discount"], "103.95")
        self.assertEqual(snapshot["totals"]["total_amount"], "124.95")
        assert_fiscal_totals(self, snapshot)

    def test_snapshot_preserves_claws_without_screw_configuration(self):
        checkout_quote = quote(
            {
                "lines": [
                    {
                        **quote()["lines"][0],
                        "anclaje": "Con obra: con garras metálicas",
                        "screw_option": "not_applicable",
                        "screw_length_mm": None,
                        "screw_supplement": 0.0,
                        "unit_price": 149.95,
                        "line_total": 149.95,
                    }
                ],
                "subtotal": 149.95,
                "shipping_cost": 21.0,
                "total_amount": 170.95,
            }
        )

        snapshot = build(checkout_session=checkout_session({"quote_snapshot": checkout_quote}))

        configuration = snapshot["lines"][0]["configuration"]
        self.assertEqual(configuration["anchoring"], "Con obra: con garras metálicas")
        self.assertEqual(configuration["screw_option"], "not_applicable")
        self.assertIsNone(configuration["screw_length_mm"])
        self.assertEqual(configuration["screw_supplement"], "0.00")
        self.assertEqual(snapshot["totals"]["products_amount_before_discount"], "149.95")

    def test_builds_customer_from_canonical_checkout_fields(self):
        canonical_customer = customer_snapshot(
            {
                "legal_name": "CONSTRUCCIONES EJEMPLO SL",
                "tax_id": "B12345678",
                "CIF": "B12345678",
                "email": "facturacion@example.com",
                "billing_province": "Ciudad Real",
                "billing_country_code": "ES",
            }
        )
        session = checkout_session({"customer_snapshot": canonical_customer})

        snapshot = build(checkout_session=session)

        self.assertEqual(snapshot["customer"]["legal_name"], "CONSTRUCCIONES EJEMPLO SL")
        self.assertEqual(snapshot["customer"]["tax_id"], "B12345678")
        self.assertEqual(snapshot["customer"]["email"], "facturacion@example.com")
        self.assertEqual(snapshot["customer"]["province"], "Ciudad Real")
        self.assertEqual(snapshot["customer"]["country_code"], "ES")

    def test_builds_valid_paypal_snapshot(self):
        paypal_session = checkout_session(
            {
                "payment_provider": "paypal",
                "payment_intent_id": None,
                "provider_order_id": "PAYPAL-ORDER",
                "provider_capture_id": "PAYPAL-CAPTURE",
            }
        )

        snapshot = build(checkout_session=paypal_session)

        self.assertEqual(snapshot["payment"]["provider"], "paypal")
        self.assertEqual(snapshot["payment"]["provider_reference"], "PAYPAL-CAPTURE")

    def test_includes_shipping_line_when_shipping_is_positive(self):
        snapshot = build()

        self.assertEqual([line["line_type"] for line in snapshot["lines"]], ["product", "shipping"])

    def test_omits_shipping_line_when_shipping_is_zero(self):
        free_shipping_quote = quote({"shipping_cost": 0.0, "total_amount": 95.0})
        session = checkout_session({"quote_snapshot": free_shipping_quote})

        snapshot = build(checkout_session=session)

        self.assertEqual(len(snapshot["lines"]), 1)
        self.assertEqual(snapshot["totals"]["shipping_amount_before_discount"], "0.00")

    def test_ten_percent_discount_is_allocated_between_product_and_shipping(self):
        discounted_quote = quote(
            {
                "discount_code": "REJAS10",
                "discount_code_valid": True,
                "discount_percent": 10.0,
                "discount_amount": 11.60,
                "total_amount": 104.40,
            }
        )
        session = checkout_session({"quote_snapshot": discounted_quote})

        snapshot = build(checkout_session=session)

        product_line, shipping_line = snapshot["lines"]
        self.assertEqual(product_line["line_tax_base_before_discount"], "78.51")
        self.assertEqual(product_line["discount_tax_base"], "7.85")
        self.assertEqual(product_line["discount_amount"], "9.50")
        self.assertEqual(product_line["line_total"], "85.50")
        self.assertEqual(product_line["tax_base"], "70.66")
        self.assertEqual(product_line["tax_amount"], "14.84")
        self.assertEqual(shipping_line["discount_amount"], "2.10")
        self.assertEqual(shipping_line["line_tax_base_before_discount"], "17.36")
        self.assertEqual(shipping_line["discount_tax_base"], "1.74")
        self.assertEqual(shipping_line["line_total"], "18.90")
        self.assertEqual(shipping_line["tax_base"], "15.62")
        self.assertEqual(shipping_line["tax_amount"], "3.28")
        self.assertEqual(snapshot["totals"]["discount_amount"], "11.60")
        self.assertEqual(snapshot["totals"]["tax_base"], "86.28")
        self.assertEqual(snapshot["totals"]["tax_amount"], "18.12")
        self.assertEqual(snapshot["totals"]["total_amount"], "104.40")
        assert_fiscal_totals(self, snapshot)

    def test_unit_price_net_keeps_six_decimal_precision_for_multiple_units(self):
        line = {**quote()["lines"][0], "quantity": 3, "line_total": "285.00"}
        multi_unit_quote = quote(
            {
                "lines": [line],
                "subtotal": "285.00",
                "shipping_cost": "0.00",
                "discount_amount": "28.50",
                "total_amount": "256.50",
            }
        )

        snapshot = build(checkout_session=checkout_session({"quote_snapshot": multi_unit_quote}))

        product_line = snapshot["lines"][0]
        self.assertEqual(product_line["quantity"], "3")
        self.assertEqual(product_line["unit_price_net"], "78.512397")
        self.assertEqual(product_line["line_tax_base_before_discount"], "235.54")
        self.assertEqual(product_line["discount_tax_base"], "23.56")
        self.assertEqual(product_line["tax_base"], "211.98")
        self.assertEqual(product_line["tax_amount"], "44.52")
        self.assertEqual(product_line["line_total"], "256.50")
        assert_fiscal_totals(self, snapshot)

    def test_sergio99_discount_is_allocated_without_negative_lines(self):
        discounted_quote = quote(
            {
                "shipping_cost": 21.0,
                "discount_code": "SERGIO99",
                "discount_code_valid": True,
                "discount_percent": 99.0,
                "discount_amount": 114.84,
                "total_amount": 1.16,
            }
        )
        session = checkout_session({"quote_snapshot": discounted_quote})

        snapshot = build(checkout_session=session)

        self.assertEqual(snapshot["operation"]["discount_code"], "SERGIO99")
        self.assertEqual(snapshot["totals"]["discount_amount"], "114.84")
        self.assertEqual(snapshot["totals"]["total_amount"], "1.16")
        self.assertEqual(snapshot["totals"]["tax_base"], "0.96")
        self.assertEqual(snapshot["totals"]["tax_amount"], "0.20")
        self.assertFalse(any(line["line_type"] == "discount" for line in snapshot["lines"]))
        self.assertEqual(snapshot["lines"][0]["discount_amount"], "94.05")
        self.assertEqual(snapshot["lines"][0]["line_total"], "0.95")
        self.assertEqual(snapshot["lines"][1]["discount_amount"], "20.79")
        self.assertEqual(snapshot["lines"][1]["line_total"], "0.21")
        assert_fiscal_totals(self, snapshot)

    def test_discount_is_allocated_across_multiple_different_amounts_and_shipping(self):
        multi_quote = quote(
            {
                "lines": [
                    quote_line(1, "50.00", "A"),
                    quote_line(2, "100.00", "B"),
                ],
                "subtotal": "150.00",
                "shipping_cost": "50.00",
                "discount_amount": "20.00",
                "total_amount": "180.00",
            }
        )
        session = checkout_session({"quote_snapshot": multi_quote})

        snapshot = build(checkout_session=session)

        self.assertEqual(
            [line["discount_amount"] for line in snapshot["lines"]],
            ["5.00", "10.00", "5.00"],
        )
        self.assertEqual(
            [line["line_total"] for line in snapshot["lines"]],
            ["45.00", "90.00", "45.00"],
        )
        self.assertEqual(snapshot["totals"]["tax_base"], "148.76")
        self.assertEqual(snapshot["totals"]["tax_amount"], "31.24")
        self.assertEqual(snapshot["totals"]["total_amount"], "180.00")
        assert_fiscal_totals(self, snapshot)

    def test_discount_residue_is_assigned_by_largest_remainder(self):
        residue_quote = quote(
            {
                "lines": [
                    quote_line(1, "33.33", "A"),
                    quote_line(2, "33.33", "B"),
                    quote_line(3, "33.34", "C"),
                ],
                "subtotal": "100.00",
                "shipping_cost": "0.00",
                "discount_amount": "10.00",
                "total_amount": "90.00",
            }
        )
        session = checkout_session({"quote_snapshot": residue_quote})

        snapshot = build(checkout_session=session)

        self.assertEqual(
            [line["discount_amount"] for line in snapshot["lines"]],
            ["3.33", "3.33", "3.34"],
        )
        self.assertEqual([line["line_total"] for line in snapshot["lines"]], ["30.00", "30.00", "30.00"])
        self.assertEqual(snapshot["totals"]["tax_base"], "74.37")
        self.assertEqual(snapshot["totals"]["tax_amount"], "15.63")
        assert_fiscal_totals(self, snapshot)

    def test_equal_remainder_residue_is_assigned_to_lowest_line_number(self):
        tie_quote = quote(
            {
                "lines": [
                    quote_line(1, "50.00", "A"),
                    quote_line(2, "50.00", "B"),
                ],
                "subtotal": "100.00",
                "shipping_cost": "0.00",
                "discount_amount": "0.01",
                "total_amount": "99.99",
            }
        )
        session = checkout_session({"quote_snapshot": tie_quote})

        snapshot = build(checkout_session=session)

        self.assertEqual([line["discount_amount"] for line in snapshot["lines"]], ["0.01", "0.00"])
        self.assertEqual([line["line_total"] for line in snapshot["lines"]], ["49.99", "50.00"])
        assert_fiscal_totals(self, snapshot)

    def test_discount_equal_to_total_leaves_zero_lines_without_negative_amounts(self):
        full_discount_quote = quote({"discount_amount": "116.00", "total_amount": "0.00"})
        session = checkout_session({"quote_snapshot": full_discount_quote})

        snapshot = build(checkout_session=session)

        self.assertEqual([line["discount_amount"] for line in snapshot["lines"]], ["95.00", "21.00"])
        self.assertEqual([line["line_total"] for line in snapshot["lines"]], ["0.00", "0.00"])
        self.assertEqual(snapshot["totals"]["tax_base"], "0.00")
        self.assertEqual(snapshot["totals"]["tax_amount"], "0.00")
        assert_fiscal_totals(self, snapshot)

    def test_discount_greater_than_total_is_rejected(self):
        excessive_discount_quote = quote({"discount_amount": "116.01", "total_amount": "0.00"})
        session = checkout_session({"quote_snapshot": excessive_discount_quote})

        self.assert_validation_error("totals.discount_amount", checkout_session=session)

    def test_zero_amount_line_keeps_zero_discount_and_does_not_receive_residue(self):
        zero_line_quote = quote(
            {
                "lines": [
                    quote_line(1, "0.00", "Zero"),
                    quote_line(2, "100.00", "A"),
                ],
                "subtotal": "100.00",
                "shipping_cost": "0.00",
                "discount_amount": "10.00",
                "total_amount": "90.00",
            }
        )
        session = checkout_session({"quote_snapshot": zero_line_quote})

        snapshot = build(checkout_session=session)

        self.assertEqual(snapshot["lines"][0]["discount_amount"], "0.00")
        self.assertEqual(snapshot["lines"][0]["line_total"], "0.00")
        self.assertEqual(snapshot["lines"][1]["discount_amount"], "10.00")
        self.assertEqual(snapshot["lines"][1]["line_total"], "90.00")
        assert_fiscal_totals(self, snapshot)

    def test_new_f1_snapshot_without_tax_id_is_rejected(self):
        session = checkout_session(
            {"customer_snapshot": customer_snapshot({"CIF": "", "tax_id": ""})}
        )

        self.assert_validation_error("customer.tax_id", checkout_session=session)

    def test_customer_tax_id_is_trimmed_and_uppercased(self):
        session = checkout_session(
            {"customer_snapshot": customer_snapshot({"CIF": "  b12345678  "})}
        )

        snapshot = build(checkout_session=session)

        self.assertEqual(snapshot["customer"]["tax_id"], "B12345678")

    def test_incomplete_issuer_is_rejected(self):
        self.assert_validation_error("issuer.tax_id", issuer=issuer({"tax_id": ""}))

    def test_customer_without_address_is_rejected(self):
        session = checkout_session(
            {"customer_snapshot": customer_snapshot({"billing_address": "", "shipping_address": ""})}
        )

        self.assert_validation_error("customer.address", checkout_session=session)

    def test_missing_quote_is_rejected(self):
        session = checkout_session({"quote_snapshot": None})

        self.assert_validation_error("quote_snapshot", checkout_session=session)

    def test_empty_lines_are_rejected(self):
        empty_quote = quote({"lines": [], "subtotal": 0.0, "shipping_cost": 0.0, "total_amount": 0.0})
        session = checkout_session({"quote_snapshot": empty_quote})

        self.assert_validation_error("lines", checkout_session=session)

    def test_invalid_amount_is_rejected(self):
        invalid_quote = quote({"subtotal": "not-a-number"})
        session = checkout_session({"quote_snapshot": invalid_quote})

        self.assert_validation_error("totals.products_total", checkout_session=session)

    def test_incoherent_total_is_rejected(self):
        incoherent_quote = quote({"total_amount": 999.0})
        session = checkout_session({"quote_snapshot": incoherent_quote})

        self.assert_validation_error("totals.total_amount", checkout_session=session)

    def test_money_is_serialized_with_two_decimal_places(self):
        decimal_quote = quote(
            {
                "lines": [
                    {
                        "product_id": 8,
                        "producto_id": 8,
                        "product_name": "Reja fija Albany",
                        "quantity": 2,
                        "alto": "120.5",
                        "ancho": "80.25",
                        "anclaje": "Sin obra: con pletinas",
                        "color": "forja_negro",
                        "unit_price": "119.955",
                        "line_total": "239.91",
                    }
                ],
                "subtotal": "239.91",
                "shipping_cost": "0",
                "discount_amount": "0",
                "total_amount": "239.91",
            }
        )
        session = checkout_session({"quote_snapshot": decimal_quote})

        snapshot = build(checkout_session=session)

        self.assertEqual(snapshot["lines"][0]["unit_amount_before_discount"], "119.96")
        self.assertEqual(snapshot["lines"][0]["line_amount_before_discount"], "239.91")
        self.assertEqual(snapshot["lines"][0]["discount_amount"], "0.00")
        self.assertEqual(snapshot["lines"][0]["line_total"], "239.91")
        self.assertEqual(snapshot["totals"]["total_amount"], "239.91")
        self.assertEqual(snapshot["lines"][0]["configuration"]["height_cm"], "120.5")

    def test_snapshot_contains_no_float_values(self):
        snapshot = build()

        assert_no_floats(self, snapshot)

    def test_builder_does_not_mutate_inputs(self):
        session = checkout_session()
        original_quote = copy.deepcopy(session.quote_snapshot)
        original_customer = copy.deepcopy(session.customer_snapshot)

        build(checkout_session=session)

        self.assertEqual(session.quote_snapshot, original_quote)
        self.assertEqual(session.customer_snapshot, original_customer)

    def test_repeated_builds_are_equal_except_generated_at(self):
        first = build()
        second = build()
        first["metadata"]["generated_at"] = "<generated>"
        second["metadata"]["generated_at"] = "<generated>"

        self.assertEqual(first, second)

    def test_non_final_checkout_session_is_rejected(self):
        session = checkout_session({"status": "processing"})

        self.assert_validation_error("checkout_session.status", checkout_session=session)

    def test_order_mismatch_is_rejected(self):
        session = checkout_session({"order_id": 999})

        self.assert_validation_error("checkout_session.order_id", checkout_session=session)

    def test_missing_customer_snapshot_is_rejected(self):
        session = checkout_session({"customer_snapshot": None})

        self.assert_validation_error("customer_snapshot", checkout_session=session)


class InvoiceRectificationSnapshotBuilderTest(unittest.TestCase):
    def assert_rectification_validation_error(self, field, **overrides):
        with self.assertRaises(InvoiceSnapshotValidationError) as error:
            build_rectification_snapshot_from_invoice(
                overrides.get("original_invoice", corrective_invoice()),
                issue_date=overrides.get("issue_date", datetime(2026, 7, 17, 9, 0)),
                rectification_type=overrides.get("rectification_type", "differences"),
                rectification_reason=overrides.get("rectification_reason", "invoice_error"),
                rectification_scope=overrides.get("rectification_scope", "total"),
                affected_line_numbers=overrides.get("affected_line_numbers"),
                source=overrides.get("source", "manual"),
                actor=overrides.get("actor"),
            )
        self.assertEqual(error.exception.field, field)

    def build_rectification(self, **overrides):
        return build_rectification_snapshot_from_invoice(
            overrides.get("original_invoice", corrective_invoice()),
            issue_date=overrides.get("issue_date", datetime(2026, 7, 17, 9, 0)),
            rectification_type=overrides.get("rectification_type", "differences"),
            rectification_reason=overrides.get("rectification_reason", "invoice_error"),
            rectification_scope=overrides.get("rectification_scope", "total"),
            affected_line_numbers=overrides.get("affected_line_numbers"),
            source=overrides.get("source", "manual"),
            actor=overrides.get("actor"),
        )

    def test_builds_deterministic_total_rectification_snapshot(self):
        original = corrective_invoice()
        original_snapshot = copy.deepcopy(original.invoice_snapshot)

        first = build_rectification_snapshot_from_invoice(
            original,
            issue_date=datetime(2026, 7, 17, 9, 0),
            rectification_type="differences",
            rectification_reason="invoice_error",
            rectification_scope="total",
            source="manual",
        )
        second = build_rectification_snapshot_from_invoice(
            original,
            issue_date=datetime(2026, 7, 17, 9, 0),
            rectification_type="differences",
            rectification_reason="invoice_error",
            rectification_scope="total",
            source="manual",
        )

        self.assertEqual(first, second)
        self.assertEqual(original.invoice_snapshot, original_snapshot)
        self.assertEqual(first["schema_version"], 3)
        self.assertEqual(first["metadata"]["generator"], "invoice_snapshot_builder_v3")
        self.assertEqual(first["operation"]["invoice_type"], "corrective")
        self.assertEqual(first["operation"]["rectification"]["rectification_type"], "differences")
        self.assertEqual(first["operation"]["rectification"]["rectification_scope"], "total")
        self.assertEqual(first["operation"]["rectification"]["rectification_reason"], "invoice_error")
        self.assertEqual(first["operation"]["rectification"]["rectification_reason_text"], "Factura emitida por error")
        self.assertEqual(first["operation"]["rectification"]["original_invoice_id"], 2001)
        self.assertEqual(first["operation"]["rectification"]["original_invoice_number"], "F2026000001")
        self.assertEqual(first["operation"]["rectification"]["original_invoice_issued_at"], "2026-07-16T10:00:00")
        self.assertEqual(first["operation"]["rectification"]["affected_line_numbers"], [1, 2])

    def test_total_rectification_inverts_base_iva_total_and_lines(self):
        original = corrective_invoice()
        snapshot = self.build_rectification(original_invoice=original)

        self.assertEqual(snapshot["schema_version"], 3)
        self.assertEqual(snapshot["totals"]["products_amount_before_discount"], "-95.00")
        self.assertEqual(snapshot["totals"]["shipping_amount_before_discount"], "-21.00")
        self.assertEqual(snapshot["totals"]["total_amount_before_discount"], "-116.00")
        self.assertEqual(snapshot["totals"]["discount_amount"], "0.00")
        self.assertEqual(snapshot["totals"]["tax_base"], "-95.87")
        self.assertEqual(snapshot["totals"]["tax_amount"], "-20.13")
        self.assertEqual(snapshot["totals"]["total_amount"], "-116.00")
        self.assertEqual(snapshot["references"]["original_invoice_id"], 2001)
        self.assertEqual(snapshot["references"]["original_invoice_number"], "F2026000001")
        self.assertEqual(snapshot["references"]["original_invoice_issued_at"], "2026-07-16T10:00:00")
        self.assertEqual(snapshot["lines"][0]["unit_price_net"], "-78.512397")
        self.assertEqual(snapshot["lines"][0]["unit_amount_before_discount"], "-95.00")
        self.assertEqual(snapshot["lines"][0]["line_amount_before_discount"], "-95.00")
        self.assertEqual(snapshot["lines"][0]["discount_amount"], "0.00")
        self.assertEqual(snapshot["lines"][0]["line_tax_base_before_discount"], "-78.51")
        self.assertEqual(snapshot["lines"][0]["discount_tax_base"], "0.00")
        self.assertEqual(snapshot["lines"][0]["tax_base"], "-78.51")
        self.assertEqual(snapshot["lines"][0]["tax_amount"], "-16.49")
        self.assertEqual(snapshot["lines"][1]["line_type"], "shipping")
        self.assertEqual(snapshot["lines"][1]["unit_price_net"], "-17.355372")
        self.assertEqual(snapshot["lines"][1]["unit_amount_before_discount"], "-21.00")
        self.assertEqual(snapshot["lines"][1]["line_amount_before_discount"], "-21.00")
        self.assertEqual(snapshot["lines"][1]["discount_amount"], "0.00")
        self.assertEqual(snapshot["lines"][1]["line_tax_base_before_discount"], "-17.36")
        self.assertEqual(snapshot["lines"][1]["discount_tax_base"], "0.00")
        self.assertEqual(snapshot["lines"][1]["tax_base"], "-17.36")
        self.assertEqual(snapshot["lines"][1]["tax_amount"], "-3.64")
        self.assertEqual(snapshot["payment"], original.invoice_snapshot["payment"])
        self.assertEqual(snapshot["operation"]["rectification"]["rectification_reason_text"], "Factura emitida por error")
        self.assertEqual(snapshot["operation"]["rectification"]["rectification_scope"], "total")
        self.assertEqual(snapshot["operation"]["rectification"]["affected_line_numbers"], [1, 2])
        assert_fiscal_totals(self, snapshot)

    def test_total_rectification_with_discount_and_shipping_neutralizes_amounts(self):
        discounted_snapshot = build(
            checkout_session=checkout_session(
                {
                    "quote_snapshot": quote(
                        {
                            "discount_code": "REJAS10",
                            "discount_code_valid": True,
                            "discount_percent": 10.0,
                            "discount_amount": 11.60,
                            "total_amount": 104.40,
                        }
                    )
                }
            )
        )
        discounted_original = corrective_invoice({"invoice_snapshot": discounted_snapshot})

        snapshot = self.build_rectification(original_invoice=discounted_original)

        self.assertEqual(snapshot["totals"]["discount_amount"], "-11.60")
        self.assertEqual(snapshot["totals"]["tax_base"], "-86.28")
        self.assertEqual(snapshot["totals"]["tax_amount"], "-18.12")
        self.assertEqual(snapshot["totals"]["total_amount"], "-104.40")
        self.assertEqual(snapshot["lines"][0]["discount_amount"], "-9.50")
        self.assertEqual(snapshot["lines"][0]["discount_tax_base"], "-7.85")
        self.assertEqual(snapshot["lines"][0]["line_total"], "-85.50")
        self.assertEqual(snapshot["lines"][1]["discount_amount"], "-2.10")
        self.assertEqual(snapshot["lines"][1]["discount_tax_base"], "-1.74")
        self.assertEqual(snapshot["lines"][1]["line_total"], "-18.90")
        assert_fiscal_totals(self, snapshot)

    def test_rejects_original_without_valid_snapshot(self):
        original = corrective_invoice({"invoice_snapshot": None})
        self.assert_rectification_validation_error(
            "original_invoice.invoice_snapshot",
            original_invoice=original,
        )

    def test_rejects_v1_original_to_avoid_emitting_a_non_renderable_v3_pdf(self):
        original = corrective_invoice()
        original.invoice_snapshot["schema_version"] = 1
        original.invoice_snapshot["metadata"]["generator"] = "invoice_snapshot_builder_v1"
        for line in original.invoice_snapshot["lines"]:
            line.pop("unit_price_net")
            line.pop("line_tax_base_before_discount")
            line.pop("discount_tax_base")

        self.assert_rectification_validation_error(
            "original_invoice.invoice_snapshot.schema_version",
            original_invoice=original,
        )

    def test_rejects_original_that_is_already_corrective(self):
        original = corrective_invoice({"invoice_type": "corrective"})
        self.assert_rectification_validation_error(
            "original_invoice.invoice_type",
            original_invoice=original,
        )

    def test_rejects_partial_rectification_explicitly(self):
        self.assert_rectification_validation_error(
            "operation.rectification.rectification_scope",
            rectification_scope="partial",
        )

    def test_rejects_missing_rectification_reason(self):
        self.assert_rectification_validation_error(
            "operation.rectification.rectification_reason",
            rectification_reason=None,
        )

    def test_rejects_missing_rectification_type(self):
        self.assert_rectification_validation_error(
            "operation.rectification.rectification_type",
            rectification_type=None,
        )

    def test_rejects_invalid_rectification_values(self):
        self.assert_rectification_validation_error(
            "operation.rectification.rectification_type",
            rectification_type="invalid",
        )
        self.assert_rectification_validation_error(
            "operation.rectification.rectification_reason",
            rectification_reason="invalid",
        )

    def test_rejects_invalid_affected_line_numbers(self):
        self.assert_rectification_validation_error(
            "operation.rectification.affected_line_numbers",
            affected_line_numbers=[1],
        )
        self.assert_rectification_validation_error(
            "operation.rectification.affected_line_numbers.2",
            affected_line_numbers=[1, 1],
        )

    def test_same_input_produces_same_snapshot(self):
        original = corrective_invoice()
        first = self.build_rectification(original_invoice=original)
        second = self.build_rectification(original_invoice=original)
        self.assertEqual(first, second)



if __name__ == "__main__":
    unittest.main()

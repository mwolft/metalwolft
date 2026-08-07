import json
import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from scripts.inspect_invoice_snapshot import (  # noqa: E402
    InvoiceSnapshotInspectionError,
    build_issuer_from_env,
    build_snapshot_for_order,
    build_summary,
    inspect_snapshot_from_database,
    select_checkout_session_for_order,
    serialize_snapshot,
    write_json_output,
)


def issuer():
    return {
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


def issuer_env(overrides=None):
    data = {
        "INVOICE_ISSUER_LEGAL_NAME": "MetalWolft Legal",
        "INVOICE_ISSUER_TRADE_NAME": "MetalWolft",
        "INVOICE_ISSUER_TAX_ID": "B00000000",
        "INVOICE_ISSUER_ADDRESS": "Calle Taller 1",
        "INVOICE_ISSUER_POSTAL_CODE": "13000",
        "INVOICE_ISSUER_CITY": "Ciudad Real",
        "INVOICE_ISSUER_COUNTRY_CODE": "ES",
    }
    data.update(overrides or {})
    return data


def quote():
    return {
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


def customer_snapshot():
    return {
        "firstname": "Sergio",
        "lastname": "Arias",
        "phone": "600000000",
        "billing_address": "Calle Factura 3",
        "billing_city": "Ciudad Real",
        "billing_postal_code": "13001",
        "CIF": "",
    }


def order(order_id=123):
    return SimpleNamespace(
        id=order_id,
        locator="AB1234",
        order_date=datetime(2026, 7, 15, 10, 30),
        user=SimpleNamespace(email="cliente@example.com"),
    )


def checkout_session(**overrides):
    data = {
        "id": 10,
        "order_id": 123,
        "payment_provider": "stripe",
        "payment_intent_id": "pi_test",
        "provider_order_id": None,
        "provider_capture_id": None,
        "provider_status": "succeeded",
        "public_checkout_token": "secret-public-token",
        "status": "order_created",
        "quote_snapshot": quote(),
        "customer_snapshot": customer_snapshot(),
        "user": SimpleNamespace(email="cliente@example.com"),
    }
    data.update(overrides)
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


def temp_output_path(filename):
    directory = ROOT_DIR / ".tmp_invoice_snapshot_inspector_tests"
    directory.mkdir(exist_ok=True)
    return directory / filename


def cleanup_temp_output(path):
    if path.exists():
        path.unlink()
    try:
        path.parent.rmdir()
    except OSError:
        pass


class FakeAppContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeApp:
    def app_context(self):
        return FakeAppContext()


class FakeQuery:
    def __init__(self, item=None, items=None):
        self.item = item
        self.items = items or []
        self.filter_kwargs = None

    def get(self, item_id):
        return self.item if self.item and self.item.id == item_id else None

    def filter_by(self, **kwargs):
        self.filter_kwargs = kwargs
        order_id = kwargs.get("order_id")
        return FakeQuery(items=[
            item for item in self.items if getattr(item, "order_id", None) == order_id
        ])

    def all(self):
        return list(self.items)


class FakeModel:
    def __init__(self, query):
        self.query = query


class InvoiceSnapshotInspectorTest(unittest.TestCase):
    def test_missing_order_fails(self):
        with self.assertRaisesRegex(InvoiceSnapshotInspectionError, "order not found"):
            select_checkout_session_for_order(None, [])

    def test_order_without_checkout_session_fails(self):
        with self.assertRaisesRegex(InvoiceSnapshotInspectionError, "no checkout session"):
            select_checkout_session_for_order(order(), [])

    def test_ambiguous_sessions_fail(self):
        sessions = [
            checkout_session(id=1),
            checkout_session(id=2, payment_intent_id="pi_second"),
        ]

        with self.assertRaisesRegex(InvoiceSnapshotInspectionError, "ambiguous"):
            select_checkout_session_for_order(order(), sessions)

    def test_valid_session_is_selected_deterministically(self):
        usable = checkout_session(id=1)
        ignored_processing = checkout_session(id=2, status="processing")
        ignored_other_order = checkout_session(id=3, order_id=999)

        selected = select_checkout_session_for_order(
            order(),
            [ignored_processing, ignored_other_order, usable],
        )

        self.assertEqual(selected.id, 1)

    def test_issuer_is_loaded_from_explicit_environment(self):
        loaded = build_issuer_from_env(issuer_env({
            "INVOICE_ISSUER_PROVINCE": "Ciudad Real",
            "INVOICE_ISSUER_EMAIL": "facturas@example.com",
        }))

        self.assertEqual(loaded["legal_name"], "MetalWolft Legal")
        self.assertEqual(loaded["trade_name"], "MetalWolft")
        self.assertEqual(loaded["province"], "Ciudad Real")
        self.assertEqual(loaded["email"], "facturas@example.com")

    def test_incomplete_issuer_fails_with_missing_variable_name(self):
        env = issuer_env({"INVOICE_ISSUER_TAX_ID": ""})

        with self.assertRaisesRegex(InvoiceSnapshotInspectionError, "INVOICE_ISSUER_TAX_ID"):
            build_issuer_from_env(env)

    def test_builder_returns_valid_snapshot(self):
        snapshot, selected = build_snapshot_for_order(
            order(),
            [checkout_session()],
            issuer(),
            issue_date=datetime(2026, 7, 16, 9, 0),
        )

        self.assertEqual(selected.id, 10)
        self.assertEqual(snapshot["schema_version"], 1)
        self.assertEqual(snapshot["references"]["source"], "inspection")
        self.assertEqual(snapshot["totals"]["total_amount"], "116.00")

    def test_serialized_json_contains_no_float_values(self):
        snapshot, _ = build_snapshot_for_order(
            order(),
            [checkout_session()],
            issuer(),
            issue_date=datetime(2026, 7, 16, 9, 0),
        )
        payload = json.loads(serialize_snapshot(snapshot, pretty=True))

        assert_no_floats(self, payload)

    def test_output_does_not_overwrite_without_force(self):
        output_path = temp_output_path("snapshot-no-overwrite.json")
        try:
            output_path.write_text("existing", encoding="utf-8")

            with self.assertRaisesRegex(InvoiceSnapshotInspectionError, "already exists"):
                write_json_output(output_path, "new", force=False)

            self.assertEqual(output_path.read_text(encoding="utf-8"), "existing")
        finally:
            cleanup_temp_output(output_path)

    def test_output_overwrites_with_force(self):
        output_path = temp_output_path("snapshot-force.json")
        try:
            output_path.write_text("existing", encoding="utf-8")

            write_json_output(output_path, "new", force=True)

            self.assertEqual(output_path.read_text(encoding="utf-8"), "new")
        finally:
            cleanup_temp_output(output_path)

    def test_database_inspection_uses_read_queries_without_commit(self):
        fake_order = order()
        fake_session = checkout_session()
        orders_model = FakeModel(FakeQuery(item=fake_order))
        sessions_model = FakeModel(FakeQuery(items=[fake_session]))

        snapshot, selected = inspect_snapshot_from_database(
            123,
            issuer(),
            issue_date=datetime(2026, 7, 16, 9, 0),
            components=(FakeApp(), orders_model, sessions_model),
        )

        self.assertEqual(selected.id, 10)
        self.assertEqual(snapshot["operation"]["order_id"], 123)

    def test_source_does_not_commit_or_create_invoice(self):
        source = (ROOT_DIR / "scripts" / "inspect_invoice_snapshot.py").read_text(encoding="utf-8")

        self.assertNotIn(".commit(", source)
        self.assertNotIn(".flush(", source)
        self.assertNotIn("Invoices", source)

    def test_errors_do_not_expose_public_checkout_token(self):
        secret_session = checkout_session(status="processing", public_checkout_token="secret-token")

        with self.assertRaises(InvoiceSnapshotInspectionError) as error:
            select_checkout_session_for_order(order(), [secret_session])

        self.assertNotIn("secret-token", str(error.exception))

    def test_summary_is_sanitized_and_contains_validation_data(self):
        snapshot, selected = build_snapshot_for_order(
            order(),
            [checkout_session()],
            issuer(),
            issue_date=datetime(2026, 7, 16, 9, 0),
        )

        summary = build_summary(snapshot, selected)

        self.assertIn("Order: 123", summary)
        self.assertIn("Validation: OK", summary)
        self.assertIn("Database writes: none", summary)
        self.assertNotIn("secret-public-token", summary)


if __name__ == "__main__":
    unittest.main()

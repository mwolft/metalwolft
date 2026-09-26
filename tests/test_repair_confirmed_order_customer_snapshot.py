import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from sqlalchemy import Column, Float, Integer, JSON, MetaData, Numeric, String, Table, create_engine, event, select, update


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from repair_confirmed_order_customer_snapshot import (  # noqa: E402
    RepairRejected,
    repair_customer_snapshot,
)


metadata = MetaData()
orders = Table(
    "orders", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer),
    Column("total_amount", Float),
    Column("invoice_number", String),
)
contexts = Table(
    "confirmed_order_contexts", metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer),
    Column("source", String),
    Column("source_checkout_session_id", Integer),
    Column("source_manual_draft_id", Integer),
    Column("quote_snapshot", JSON),
    Column("customer_snapshot", JSON),
    Column("payment_method", String),
    Column("payment_status", String),
    Column("payment_amount", Numeric(12, 2)),
    Column("currency", String),
    Column("payment_reference", String),
    Column("provider_identifiers", JSON),
    Column("payment_confirmed_at", String),
    Column("confirmed_by", String),
    Column("internal_note", String),
)
checkouts = Table(
    "checkout_sessions", metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer),
    Column("status", String),
    Column("quote_snapshot", JSON),
    Column("customer_snapshot", JSON),
    Column("payment_provider", String),
    Column("total_amount", Float),
    Column("payment_intent_id", String),
    Column("provider_order_id", String),
    Column("provider_capture_id", String),
)
invoices = Table(
    "invoices", metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer),
)


CUSTOMER = {
    "firstname": "Cliente", "lastname": "Prueba", "email": "cliente@example.com",
    "phone": "600000000", "billing_address": "Calle 1",
    "billing_postal_code": "13001", "billing_city": "Ciudad Real",
    "tax_id": "00000000T",
}
QUOTE = {"lines": [], "subtotal": 116.0, "shipping_cost": 0.0,
         "discount_amount": 0.0, "total_amount": 116.0}


class RepairConfirmedOrderCustomerSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        metadata.create_all(self.engine)
        with self.engine.begin() as conn:
            conn.execute(orders.insert().values(id=366, user_id=219, total_amount=116.0))
            conn.execute(contexts.insert().values(
                id=2, order_id=366, source="web_checkout", source_checkout_session_id=79,
                source_manual_draft_id=None, quote_snapshot=QUOTE, customer_snapshot={},
                payment_method="stripe", payment_status="confirmed", payment_amount=116.0,
                currency="EUR", payment_reference="pi_real", provider_identifiers={"payment_intent_id": "pi_real"},
            ))
            conn.execute(checkouts.insert().values(
                id=79, order_id=366, status="order_created", quote_snapshot=QUOTE,
                customer_snapshot=CUSTOMER, payment_provider="stripe", total_amount=116.0,
                payment_intent_id="pi_real",
            ))

    def tearDown(self):
        self.engine.dispose()

    def _run(self, *, apply=False):
        with self.engine.connect() as conn:
            with redirect_stdout(StringIO()):
                return repair_customer_snapshot(
                    conn, order_id=366, context_id=2, checkout_session_id=79,
                    apply=apply,
                )

    def _snapshot(self):
        with self.engine.connect() as conn:
            return conn.execute(select(contexts.c.customer_snapshot).where(contexts.c.id == 2)).scalar_one_or_none()

    def _alter(self, table, values, row_id):
        with self.engine.begin() as conn:
            conn.execute(update(table).where(table.c.id == row_id).values(**values))

    def _rejected(self, message):
        before = self._snapshot()
        with self.assertRaisesRegex(RepairRejected, message):
            self._run(apply=True)
        self.assertEqual(self._snapshot(), before)

    def test_equivalent_366_dry_run_performs_no_update(self):
        statements = []
        def record(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement.strip().upper())
        event.listen(self.engine, "before_cursor_execute", record)
        try:
            result = self._run()
        finally:
            event.remove(self.engine, "before_cursor_execute", record)
        self.assertEqual(result["mode"], "dry-run")
        self.assertEqual(result["status"], "eligible")
        self.assertIn("email", result["changed_fields"])
        self.assertTrue(result["old_sha256"])
        self.assertFalse(any(sql.startswith("UPDATE") for sql in statements))
        self.assertEqual(self._snapshot(), {})

    def test_apply_copies_exactly_one_customer_snapshot(self):
        before = self._other_records()
        statements = []
        def record(conn, cursor, statement, parameters, context, executemany):
            if statement.strip().upper().startswith("UPDATE"):
                statements.append(statement)
        event.listen(self.engine, "before_cursor_execute", record)
        try:
            result = self._run(apply=True)
        finally:
            event.remove(self.engine, "before_cursor_execute", record)
        self.assertEqual(result["status"], "applied")
        self.assertEqual(self._snapshot(), CUSTOMER)
        self.assertEqual(self._other_records(), before)
        self.assertEqual(len(statements), 1)
        self.assertIn("UPDATE confirmed_order_contexts SET customer_snapshot =", statements[0])

    def _other_records(self):
        with self.engine.connect() as conn:
            return (
                conn.execute(select(orders)).mappings().all(),
                conn.execute(select(checkouts)).mappings().all(),
                conn.execute(select(contexts.c.quote_snapshot, contexts.c.payment_amount,
                                    contexts.c.payment_reference)).mappings().all(),
                conn.execute(select(invoices)).mappings().all(),
            )

    def test_already_valid_does_not_modify(self):
        self._alter(contexts, {"customer_snapshot": CUSTOMER}, 2)
        result = self._run(apply=True)
        self.assertEqual(result["status"], "already_valid")
        self.assertEqual(self._snapshot(), CUSTOMER)

    def test_missing_order_aborts(self):
        with self.engine.begin() as conn:
            conn.execute(orders.delete().where(orders.c.id == 366))
        self._rejected("No existe Orders")

    def test_missing_context_aborts(self):
        with self.engine.begin() as conn:
            conn.execute(contexts.delete().where(contexts.c.id == 2))
        self._rejected("No existe ConfirmedOrderContext")

    def test_missing_checkout_aborts(self):
        with self.engine.begin() as conn:
            conn.execute(checkouts.delete().where(checkouts.c.id == 79))
        self._rejected("No existe CheckoutSession")

    def test_mismatched_context_order_aborts(self):
        self._alter(contexts, {"order_id": 999}, 2)
        self._rejected("COC.order_id")

    def test_mismatched_source_session_aborts(self):
        self._alter(contexts, {"source_checkout_session_id": 80}, 2)
        self._rejected("COC.source_checkout_session_id")

    def test_checkout_for_other_order_aborts(self):
        self._alter(checkouts, {"order_id": 999}, 79)
        self._rejected("CheckoutSession.order_id")

    def test_different_quotes_abort(self):
        self._alter(checkouts, {"quote_snapshot": {**QUOTE, "discount_amount": 1.0}}, 79)
        self._rejected("quote_snapshot")

    def test_order_total_mismatch_aborts(self):
        self._alter(orders, {"total_amount": 117.0}, 366)
        self._rejected("Orders.total_amount")

    def test_payment_amount_mismatch_aborts(self):
        self._alter(contexts, {"payment_amount": 115.0}, 2)
        self._rejected("pago del COC")

    def test_checkout_total_mismatch_aborts(self):
        self._alter(checkouts, {"total_amount": 115.0}, 79)
        self._rejected("total de checkout")

    def test_non_eur_aborts(self):
        self._alter(contexts, {"currency": "USD"}, 2)
        self._rejected("EUR")

    def test_unpaid_checkout_aborts(self):
        self._alter(checkouts, {"status": "pending_payment"}, 79)
        self._rejected("finalizada/pagada")

    def test_provider_reference_mismatch_aborts(self):
        self._alter(checkouts, {"payment_intent_id": "pi_other"}, 79)
        self._rejected("referencia o identificadores")

    def test_invalid_checkout_customer_aborts(self):
        self._alter(checkouts, {"customer_snapshot": {"firstname": "Cliente"}}, 79)
        self._rejected("fiscalmente valido")

    def test_existing_invoice_aborts(self):
        with self.engine.begin() as conn:
            conn.execute(invoices.insert().values(id=1, order_id=366))
        self._rejected("Ya existe Invoice")

    def test_existing_legacy_invoice_number_aborts(self):
        self._alter(orders, {"invoice_number": "F-1"}, 366)
        self._rejected("invoice_number")

    def test_conflicting_nonempty_customer_field_aborts(self):
        self._alter(contexts, {"customer_snapshot": {"firstname": "Distinto"}}, 2)
        self._rejected("contradictorio")

    def test_matching_partial_customer_can_be_repaired(self):
        self._alter(contexts, {"customer_snapshot": {"firstname": "Cliente"}}, 2)
        self._run(apply=True)
        self.assertEqual(self._snapshot(), CUSTOMER)

    def test_failure_after_update_rolls_back(self):
        def fail_after_sql(conn, cursor, statement, parameters, context, executemany):
            if statement.strip().upper().startswith("UPDATE CONFIRMED_ORDER_CONTEXTS"):
                raise RuntimeError("Injected failure")
        event.listen(self.engine, "after_cursor_execute", fail_after_sql)
        try:
            with self.assertRaisesRegex(RuntimeError, "Injected failure"):
                self._run(apply=True)
        finally:
            event.remove(self.engine, "after_cursor_execute", fail_after_sql)
        self.assertEqual(self._snapshot(), {})


if __name__ == "__main__":
    unittest.main()

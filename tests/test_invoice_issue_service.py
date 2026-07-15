import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.invoice_email_service import send_invoice_email
from api.invoice_issue_service import (
    DEFAULT_INVOICE_SERIES,
    ORDINARY_INVOICE_TYPE,
    InvoiceIssueError,
    issue_invoice_for_order,
)


class FakeDbSession:
    def __init__(self, *, fail_flush=False):
        self.added = []
        self.flush_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.fail_flush = fail_flush

    def add(self, item):
        self.added.append(item)

    def flush(self):
        self.flush_count += 1
        if self.fail_flush:
            raise RuntimeError("flush failed")

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1


class FakeInvoice:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeOrderDetail:
    def __init__(self, order):
        self.order = order

    def serialize(self):
        return {
            "product_id": 7,
            "quantity": 1,
            "invoice_number": self.order.invoice_number,
        }


def build_order():
    order = SimpleNamespace(
        id=123,
        total_amount=116.0,
        invoice_number=None,
        order_details=[],
    )
    order.order_details = [FakeOrderDetail(order)]
    return order


def checkout_session():
    return SimpleNamespace(
        id=456,
        order_id=123,
        status="paid",
        customer_snapshot={
            "firstname": "Sergio",
            "lastname": "Arias",
            "phone": "600000000",
            "billing_address": "Calle factura",
            "shipping_address": "Calle envio",
            "CIF": "00000000T",
        },
        quote_snapshot={"total": "116.00"},
    )


def issuer_snapshot():
    return {
        "legal_name": "MetalWolft",
        "tax_id": "B00000000",
        "address": "Calle Taller",
        "postal_code": "13000",
        "city": "Ciudad Real",
        "country_code": "ES",
    }


def invoice_snapshot():
    return {
        "schema_version": 1,
        "operation": {"order_id": 123, "invoice_type": ORDINARY_INVOICE_TYPE},
        "totals": {"grand_total": "116.00"},
    }


class InvoiceIssueServiceTest(unittest.TestCase):
    def test_service_issues_invoice_with_number_snapshot_hash_and_order_sync(self):
        order = build_order()
        session = FakeDbSession()
        issued_at = datetime(2026, 7, 15, 10, 30, 0)
        allocation = SimpleNamespace(invoice_number="F2026000001")

        with patch("api.invoice_issue_service._lock_order_for_update", return_value=order) as lock_order, patch(
            "api.invoice_issue_service._find_existing_ordinary_invoice", return_value=None
        ) as find_existing, patch(
            "api.invoice_issue_service._invoice_model", return_value=FakeInvoice
        ), patch(
            "api.invoice_issue_service.acquire_next_invoice_number", return_value=allocation
        ) as acquire_number, patch(
            "api.invoice_issue_service.build_invoice_snapshot", return_value=invoice_snapshot()
        ) as build_snapshot, patch(
            "api.invoice_issue_service.calculate_invoice_snapshot_hash", return_value="snapshot-hash"
        ) as calculate_hash:
            result = issue_invoice_for_order(
                db_session=session,
                order_id=123,
                checkout_session=checkout_session(),
                issuer=issuer_snapshot(),
                issue_date=issued_at,
                source="admin_manual",
                actor={"email": "admin@example.com"},
            )

        lock_order.assert_called_once_with(session, 123)
        find_existing.assert_called_once_with(session, 123)
        acquire_number.assert_called_once_with(
            session,
            series=DEFAULT_INVOICE_SERIES,
            fiscal_year=2026,
        )
        build_snapshot.assert_called_once()
        self.assertEqual(build_snapshot.call_args.args[0], order)
        self.assertEqual(build_snapshot.call_args.kwargs["issue_date"], issued_at)
        self.assertEqual(build_snapshot.call_args.kwargs["source"], "admin_manual")
        self.assertEqual(build_snapshot.call_args.kwargs["actor"], {"email": "admin@example.com"})
        calculate_hash.assert_called_once_with(invoice_snapshot())

        self.assertTrue(result.created)
        self.assertEqual(result.invoice_number, "F2026000001")
        self.assertEqual(result.invoice, session.added[0])
        self.assertEqual(result.invoice.invoice_number, "F2026000001")
        self.assertEqual(result.invoice.order_id, 123)
        self.assertEqual(result.invoice.invoice_type, ORDINARY_INVOICE_TYPE)
        self.assertIsNone(result.invoice.pdf_path)
        self.assertEqual(result.invoice.amount, 116.0)
        self.assertEqual(result.invoice.client_name, "Sergio Arias")
        self.assertEqual(result.invoice.client_address, "Calle factura")
        self.assertEqual(result.invoice.client_cif, "00000000T")
        self.assertEqual(result.invoice.client_phone, "600000000")
        self.assertEqual(result.invoice.invoice_snapshot, invoice_snapshot())
        self.assertEqual(result.invoice.invoice_snapshot_schema_version, 1)
        self.assertEqual(result.invoice.invoice_snapshot_hash, "snapshot-hash")
        self.assertEqual(result.invoice.issued_at, issued_at)
        self.assertEqual(result.invoice.issuance_source, "admin_manual")
        self.assertEqual(result.invoice.issued_by, "admin@example.com")
        self.assertEqual(order.invoice_number, "F2026000001")
        self.assertEqual(session.flush_count, 1)
        self.assertEqual(session.commit_count, 1)
        self.assertEqual(session.rollback_count, 0)

    def test_service_returns_existing_ordinary_invoice_without_consuming_number(self):
        order = build_order()
        existing_invoice = FakeInvoice(
            invoice_number="F2026000001",
            order_id=123,
            invoice_type=ORDINARY_INVOICE_TYPE,
        )
        session = FakeDbSession()

        with patch("api.invoice_issue_service._lock_order_for_update", return_value=order), patch(
            "api.invoice_issue_service._find_existing_ordinary_invoice", return_value=existing_invoice
        ), patch("api.invoice_issue_service.acquire_next_invoice_number") as acquire_number, patch(
            "api.invoice_issue_service.build_invoice_snapshot"
        ) as build_snapshot:
            result = issue_invoice_for_order(
                db_session=session,
                order_id=123,
                checkout_session=checkout_session(),
                issuer=issuer_snapshot(),
                issue_date=datetime(2026, 7, 15),
            )

        acquire_number.assert_not_called()
        build_snapshot.assert_not_called()
        self.assertFalse(result.created)
        self.assertEqual(result.invoice, existing_invoice)
        self.assertEqual(result.invoice_number, "F2026000001")
        self.assertEqual(session.added, [])
        self.assertEqual(session.flush_count, 0)
        self.assertEqual(session.commit_count, 1)
        self.assertEqual(session.rollback_count, 0)

    def test_second_call_returns_same_invoice_and_allocates_number_once(self):
        order = build_order()
        session = FakeDbSession()
        issued_invoice = None

        def find_existing(*_args):
            return issued_invoice

        def capture_added(invoice):
            nonlocal issued_invoice
            issued_invoice = invoice
            session.added.append(invoice)

        session.add = capture_added

        with patch("api.invoice_issue_service._lock_order_for_update", return_value=order), patch(
            "api.invoice_issue_service._find_existing_ordinary_invoice", side_effect=find_existing
        ), patch(
            "api.invoice_issue_service._invoice_model", return_value=FakeInvoice
        ), patch(
            "api.invoice_issue_service.acquire_next_invoice_number",
            return_value=SimpleNamespace(invoice_number="F2026000001"),
        ) as acquire_number, patch(
            "api.invoice_issue_service.build_invoice_snapshot", return_value=invoice_snapshot()
        ), patch(
            "api.invoice_issue_service.calculate_invoice_snapshot_hash", return_value="snapshot-hash"
        ):
            first = issue_invoice_for_order(
                db_session=session,
                order_id=123,
                checkout_session=checkout_session(),
                issuer=issuer_snapshot(),
                issue_date=datetime(2026, 7, 15),
            )
            second = issue_invoice_for_order(
                db_session=session,
                order_id=123,
                checkout_session=checkout_session(),
                issuer=issuer_snapshot(),
                issue_date=datetime(2026, 7, 15),
            )

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.invoice, second.invoice)
        acquire_number.assert_called_once()
        self.assertEqual(session.commit_count, 2)
        self.assertEqual(session.rollback_count, 0)

    def test_service_rolls_back_when_flush_fails_after_invoice_insert(self):
        order = build_order()
        session = FakeDbSession(fail_flush=True)

        with patch("api.invoice_issue_service._lock_order_for_update", return_value=order), patch(
            "api.invoice_issue_service._find_existing_ordinary_invoice", return_value=None
        ), patch(
            "api.invoice_issue_service._invoice_model", return_value=FakeInvoice
        ), patch(
            "api.invoice_issue_service.acquire_next_invoice_number",
            return_value=SimpleNamespace(invoice_number="F2026000001"),
        ), patch(
            "api.invoice_issue_service.build_invoice_snapshot", return_value=invoice_snapshot()
        ), patch(
            "api.invoice_issue_service.calculate_invoice_snapshot_hash", return_value="snapshot-hash"
        ):
            with self.assertRaisesRegex(RuntimeError, "flush failed"):
                issue_invoice_for_order(
                    db_session=session,
                    order_id=123,
                    checkout_session=checkout_session(),
                    issuer=issuer_snapshot(),
                    issue_date=datetime(2026, 7, 15),
                )

        self.assertEqual(session.commit_count, 0)
        self.assertEqual(session.rollback_count, 1)
        self.assertIsNone(order.invoice_number)

    def test_service_requires_order_identifier(self):
        with self.assertRaises(InvoiceIssueError):
            issue_invoice_for_order(
                db_session=FakeDbSession(),
                checkout_session=checkout_session(),
                issuer=issuer_snapshot(),
            )

    def test_service_source_has_no_document_or_legacy_number_side_effects(self):
        source = (SRC_DIR / "api/invoice_issue_service.py").read_text(encoding="utf-8")

        self.assertNotIn("render_original_order_invoice_pdf", source)
        self.assertNotIn("send_invoice_email", source)
        self.assertNotIn("generate_next_invoice_number", source)
        self.assertNotIn("VeriFactu", source)
        self.assertNotIn("open(", source)
        self.assertNotIn('pdf_path=""', source)

    def test_order_lock_uses_select_for_update(self):
        source = (SRC_DIR / "api/invoice_issue_service.py").read_text(encoding="utf-8")

        self.assertIn(".with_for_update()", source)


class InvoiceEmailServiceTest(unittest.TestCase):
    def test_email_service_uses_current_invoice_email_contract(self):
        sent = []
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: None)
        invoice_result = SimpleNamespace(invoice_number="NOV-2025-001", file_path="/tmp/invoice.pdf")
        user = SimpleNamespace(email="cliente@example.com")

        send_invoice_email(
            user=user,
            invoice_result=invoice_result,
            customer_firstname="Sergio",
            customer_lastname="Arias",
            mail_username="admin@example.com",
            logger=logger,
            send_email_func=lambda **kwargs: sent.append(kwargs) or True,
        )

        self.assertEqual(sent[0]["subject"], "Factura de tu pedido #NOV-2025-001")
        self.assertEqual(sent[0]["recipients"], ["cliente@example.com", "admin@example.com"])
        self.assertIn("Adjuntamos la factura NOV-2025-001", sent[0]["body"])
        self.assertEqual(sent[0]["attachment_path"], "/tmp/invoice.pdf")

    def test_email_error_does_not_escape_service(self):
        errors = []
        logger = SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: errors.append(args))
        invoice_result = SimpleNamespace(invoice_number="NOV-2025-001", file_path="/tmp/invoice.pdf")
        user = SimpleNamespace(email="cliente@example.com")

        send_invoice_email(
            user=user,
            invoice_result=invoice_result,
            customer_firstname="Sergio",
            customer_lastname="Arias",
            mail_username="admin@example.com",
            logger=logger,
            send_email_func=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("smtp down")),
        )

        self.assertTrue(errors)


class InvoiceFinalizerSourceRegressionTest(unittest.TestCase):
    def _finalizer_source(self):
        source = (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")
        start = source.index("def _finalize_order_from_checkout_quote")
        end = source.index("@api.route('/delivery-estimate'")
        return source[start:end]

    def test_order_confirmation_email_happens_after_main_commit(self):
        finalizer_source = self._finalizer_source()

        self.assertLess(
            finalizer_source.index("db.session.commit()"),
            finalizer_source.index("send_order_confirmation_email("),
        )

    def test_checkout_finalizer_no_longer_issues_invoice_automatically(self):
        finalizer_source = self._finalizer_source()

        self.assertNotIn("issue_invoice_for_order(", finalizer_source)
        self.assertNotIn("send_invoice_email(", finalizer_source)
        self.assertNotIn("Invoices(", finalizer_source)
        self.assertNotIn("invoice_number =", finalizer_source)
        self.assertNotIn(".invoice_number =", finalizer_source)

    def test_order_and_lines_are_still_created(self):
        finalizer_source = self._finalizer_source()

        self.assertIn("new_order = Orders(", finalizer_source)
        self.assertIn("new_detail = OrderDetails(", finalizer_source)
        self.assertIn("db.session.add(new_order)", finalizer_source)
        self.assertIn("db.session.add(new_detail)", finalizer_source)

    def test_checkout_session_and_selective_cart_cleanup_are_preserved(self):
        finalizer_source = self._finalizer_source()

        self.assertIn("checkout_session.order_id = new_order.id", finalizer_source)
        self.assertIn('checkout_session.status = "order_created"', finalizer_source)
        self.assertIn("cleanup_cart_lines_from_checkout_quote(", finalizer_source)

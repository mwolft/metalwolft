import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.post_order_invoice_hook import (
    FEATURE_DISABLED_REASON,
    WORKFLOW_NOT_CONNECTED_REASON,
    handle_post_order_invoice_workflow,
)


def routes_source():
    return (ROOT_DIR / "src/api/routes.py").read_text(encoding="utf-8")


def hook_source():
    return (ROOT_DIR / "src/api/post_order_invoice_hook.py").read_text(encoding="utf-8")


def finalizer_source():
    source = routes_source()
    start = source.index("def _finalize_order_from_checkout_quote")
    end = source.index("@api.route('/delivery-estimate'", start)
    return source[start:end]


class FakeSession:
    def __init__(self):
        self.commit_count = 0
        self.rollback_count = 0
        self.flush_count = 0

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def flush(self):
        self.flush_count += 1


class FakeLogger:
    def __init__(self):
        self.warnings = []

    def warning(self, *args):
        self.warnings.append(args)


def make_order():
    return SimpleNamespace(id=123, invoice_number=None, total_amount=121.0)


def make_checkout_session():
    return SimpleNamespace(id=456, order_id=123, status="order_created")


class PostOrderInvoiceHookTest(unittest.TestCase):
    def app_context(self, *, enabled=False):
        fake_app = SimpleNamespace(
            config={"ENABLE_INVOICE_WORKFLOW_AFTER_CHECKOUT": enabled},
            logger=FakeLogger(),
        )
        return patch("api.post_order_invoice_hook._get_current_app", return_value=fake_app)

    def test_flag_false_returns_feature_disabled(self):
        with self.app_context(enabled=False):
            result = handle_post_order_invoice_workflow(
                order=make_order(),
                checkout_session=make_checkout_session(),
                db_session=FakeSession(),
            )

        self.assertFalse(result.enabled)
        self.assertFalse(result.executed)
        self.assertEqual(result.skipped_reason, FEATURE_DISABLED_REASON)

    def test_flag_false_does_not_commit_or_rollback(self):
        session = FakeSession()

        with self.app_context(enabled=False):
            handle_post_order_invoice_workflow(
                order=make_order(),
                checkout_session=make_checkout_session(),
                db_session=session,
            )

        self.assertEqual(session.commit_count, 0)
        self.assertEqual(session.rollback_count, 0)
        self.assertEqual(session.flush_count, 0)

    def test_flag_false_does_not_modify_order_or_checkout_session(self):
        order = make_order()
        checkout_session = make_checkout_session()
        original_order_state = vars(order).copy()
        original_checkout_state = vars(checkout_session).copy()

        with self.app_context(enabled=False):
            handle_post_order_invoice_workflow(
                order=order,
                checkout_session=checkout_session,
                db_session=FakeSession(),
            )

        self.assertEqual(vars(order), original_order_state)
        self.assertEqual(vars(checkout_session), original_checkout_state)

    def test_hook_does_not_execute_document_workflow_yet(self):
        source = hook_source()

        self.assertNotIn("run_invoice_workflow_for_order", source)
        self.assertNotIn("issue_invoice_for_order", source)
        self.assertNotIn("generate_invoice_pdf", source)
        self.assertNotIn("create_accounting_entry", source)
        self.assertNotIn("create_pending_submission", source)
        self.assertNotIn("send_invoice_email", source)

    def test_flag_true_is_explicitly_not_connected_yet(self):
        with self.app_context(enabled=True):
            result = handle_post_order_invoice_workflow(
                order=make_order(),
                checkout_session=make_checkout_session(),
                db_session=FakeSession(),
            )

        self.assertTrue(result.enabled)
        self.assertFalse(result.executed)
        self.assertEqual(result.skipped_reason, WORKFLOW_NOT_CONNECTED_REASON)

    def test_finalizer_calls_hook_once_after_order_id_link_and_commit(self):
        source = finalizer_source()

        self.assertEqual(source.count("handle_post_order_invoice_workflow("), 1)
        self.assertLess(
            source.index("checkout_session.order_id = new_order.id"),
            source.index("db.session.commit()"),
        )
        self.assertLess(
            source.index("db.session.commit()"),
            source.index("handle_post_order_invoice_workflow("),
        )

    def test_unexpected_hook_error_is_logged_and_does_not_rollback_order(self):
        source = finalizer_source()
        hook_call = source[source.index("try:\n        handle_post_order_invoice_workflow("):source.index("try:\n        persisted_user")]

        self.assertIn("except Exception:", hook_call)
        self.assertIn("logger.exception(", hook_call)
        self.assertNotIn("db.session.rollback()", hook_call)
        self.assertNotIn("raise", hook_call)


if __name__ == "__main__":
    unittest.main()

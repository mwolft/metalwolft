import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.post_order_invoice_hook import (
    CHECKOUT_AUTO_ACTOR,
    CONFIGURATION_ERROR_STEP,
    FEATURE_DISABLED_REASON,
    UNEXPECTED_ERROR_STEP,
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
        self.exceptions = []

    def warning(self, *args, **kwargs):
        self.warnings.append((args, kwargs))

    def exception(self, *args, **kwargs):
        self.exceptions.append((args, kwargs))


def make_order():
    return SimpleNamespace(id=123, invoice_number=None, total_amount=121.0)


def make_checkout_session():
    return SimpleNamespace(id=456, order_id=123, status="order_created")


class PostOrderInvoiceHookTest(unittest.TestCase):
    def call_hook(self, **overrides):
        values = {
            "order": make_order(),
            "checkout_session": make_checkout_session(),
            "db_session": FakeSession(),
            "enabled": False,
            "issuer_factory": Mock(return_value={"legal_name": "MetalWolft"}),
            "invoice_output_dir": "/tmp/invoices",
            "mailer_factory": Mock(return_value=SimpleNamespace(name="mailer")),
            "logger": FakeLogger(),
            "workflow_runner": Mock(return_value=SimpleNamespace(
                completed=True,
                failed_step=None,
                invoice_id=789,
                invoice_number="F2026000001",
            )),
        }
        values.update(overrides)
        return handle_post_order_invoice_workflow(**values), values

    def test_flag_false_returns_feature_disabled(self):
        result, _ = self.call_hook(enabled=False)

        self.assertFalse(result.enabled)
        self.assertFalse(result.executed)
        self.assertFalse(result.completed)
        self.assertEqual(result.skipped_reason, FEATURE_DISABLED_REASON)

    def test_flag_false_does_not_commit_or_rollback(self):
        session = FakeSession()

        self.call_hook(enabled=False, db_session=session)

        self.assertEqual(session.commit_count, 0)
        self.assertEqual(session.rollback_count, 0)
        self.assertEqual(session.flush_count, 0)

    def test_flag_false_does_not_build_dependencies_or_execute_workflow(self):
        issuer_factory = Mock(side_effect=AssertionError("issuer must not be built"))
        mailer_factory = Mock(side_effect=AssertionError("mailer must not be built"))
        workflow_runner = Mock(side_effect=AssertionError("workflow must not run"))

        self.call_hook(
            enabled=False,
            issuer_factory=issuer_factory,
            mailer_factory=mailer_factory,
            workflow_runner=workflow_runner,
        )

        issuer_factory.assert_not_called()
        mailer_factory.assert_not_called()
        workflow_runner.assert_not_called()

    def test_flag_false_does_not_modify_order_or_checkout_session(self):
        order = make_order()
        checkout_session = make_checkout_session()
        original_order_state = vars(order).copy()
        original_checkout_state = vars(checkout_session).copy()

        self.call_hook(enabled=False, order=order, checkout_session=checkout_session)

        self.assertEqual(vars(order), original_order_state)
        self.assertEqual(vars(checkout_session), original_checkout_state)

    def test_flag_true_executes_workflow_once_with_expected_contract(self):
        order = make_order()
        checkout_session = make_checkout_session()
        session = FakeSession()
        issuer = {"legal_name": "MetalWolft"}
        mailer = SimpleNamespace(name="mailer")
        logger = FakeLogger()
        issuer_factory = Mock(return_value=issuer)
        mailer_factory = Mock(return_value=mailer)
        workflow_runner = Mock(return_value=SimpleNamespace(
            completed=True,
            failed_step=None,
            invoice_id=789,
            invoice_number="F2026000001",
        ))

        result, _ = self.call_hook(
            enabled=True,
            order=order,
            checkout_session=checkout_session,
            db_session=session,
            issuer_factory=issuer_factory,
            invoice_output_dir="/tmp/invoices",
            mailer_factory=mailer_factory,
            logger=logger,
            workflow_runner=workflow_runner,
        )

        issuer_factory.assert_called_once_with()
        mailer_factory.assert_called_once_with()
        workflow_runner.assert_called_once_with(
            123,
            issuer=issuer,
            checkout_session=checkout_session,
            actor=CHECKOUT_AUTO_ACTOR,
            invoice_output_dir="/tmp/invoices",
            mailer=mailer,
            db_session=session,
            logger=logger,
        )

        self.assertTrue(result.enabled)
        self.assertTrue(result.executed)
        self.assertTrue(result.completed)
        self.assertIsNone(result.failed_step)
        self.assertEqual(result.invoice_id, 789)
        self.assertEqual(result.invoice_number, "F2026000001")

    def test_configuration_error_is_controlled_and_does_not_execute_workflow(self):
        workflow_runner = Mock()
        logger = FakeLogger()

        result, _ = self.call_hook(
            enabled=True,
            invoice_output_dir="",
            logger=logger,
            workflow_runner=workflow_runner,
        )

        workflow_runner.assert_not_called()
        self.assertTrue(result.enabled)
        self.assertFalse(result.executed)
        self.assertFalse(result.completed)
        self.assertEqual(result.failed_step, CONFIGURATION_ERROR_STEP)
        self.assertEqual(len(logger.warnings), 1)

    def test_partial_workflow_failure_is_returned_without_propagating(self):
        logger = FakeLogger()
        workflow_runner = Mock(return_value=SimpleNamespace(
            completed=False,
            failed_step="email",
            invoice_id=789,
            invoice_number="F2026000001",
        ))

        result, _ = self.call_hook(
            enabled=True,
            logger=logger,
            workflow_runner=workflow_runner,
        )

        self.assertTrue(result.executed)
        self.assertFalse(result.completed)
        self.assertEqual(result.failed_step, "email")
        self.assertEqual(result.invoice_id, 789)
        self.assertEqual(result.invoice_number, "F2026000001")
        self.assertEqual(len(logger.warnings), 1)

    def test_unexpected_workflow_error_is_sanitized_and_not_propagated(self):
        logger = FakeLogger()
        workflow_runner = Mock(side_effect=RuntimeError("smtp detail"))

        result, _ = self.call_hook(
            enabled=True,
            logger=logger,
            workflow_runner=workflow_runner,
        )

        self.assertTrue(result.executed)
        self.assertFalse(result.completed)
        self.assertEqual(result.failed_step, UNEXPECTED_ERROR_STEP)
        self.assertEqual(len(logger.exceptions), 1)

    def test_unexpected_workflow_error_does_not_modify_confirmed_order_or_session(self):
        order = make_order()
        checkout_session = make_checkout_session()
        original_order_state = vars(order).copy()
        original_checkout_state = vars(checkout_session).copy()

        self.call_hook(
            enabled=True,
            order=order,
            checkout_session=checkout_session,
            workflow_runner=Mock(side_effect=RuntimeError("boom")),
        )

        self.assertEqual(vars(order), original_order_state)
        self.assertEqual(vars(checkout_session), original_checkout_state)

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
        self.assertIn('enabled=current_app.config.get("ENABLE_INVOICE_WORKFLOW_AFTER_CHECKOUT", False)', source)
        self.assertIn("issuer_factory=_build_invoice_issuer_from_config", source)
        self.assertIn('invoice_output_dir=current_app.config.get("INVOICE_FOLDER") or os.getenv("INVOICE_FOLDER")', source)
        self.assertIn("mailer_factory=lambda: FlaskMailInvoiceAdapter(mail)", source)
        self.assertIn("logger=logger", source)

    def test_unexpected_hook_error_is_logged_and_does_not_rollback_order(self):
        source = finalizer_source()
        hook_call = source[source.index("try:\n        handle_post_order_invoice_workflow("):source.index("try:\n        persisted_user")]

        self.assertIn("except Exception:", hook_call)
        self.assertIn("logger.exception(", hook_call)
        self.assertNotIn("db.session.rollback()", hook_call)
        self.assertNotIn("raise", hook_call)

    def test_checkout_paths_do_not_call_workflow_outside_hook(self):
        source = routes_source()
        finalizer = finalizer_source()

        self.assertEqual(finalizer.count("handle_post_order_invoice_workflow("), 1)
        self.assertIn("run_invoice_workflow_for_order(", source)
        self.assertNotIn("run_invoice_workflow_for_order(", finalizer)


if __name__ == "__main__":
    unittest.main()

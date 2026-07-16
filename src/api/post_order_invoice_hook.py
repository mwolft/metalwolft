from dataclasses import dataclass


FEATURE_DISABLED_REASON = "feature_disabled"
WORKFLOW_NOT_CONNECTED_REASON = "workflow_not_connected"


@dataclass(frozen=True)
class PostOrderInvoiceHookResult:
    enabled: bool
    executed: bool
    skipped_reason: str | None = None


def _get_current_app():
    from flask import current_app

    return current_app


def handle_post_order_invoice_workflow(*, order, checkout_session, db_session):
    app = _get_current_app()
    enabled = bool(app.config.get("ENABLE_INVOICE_WORKFLOW_AFTER_CHECKOUT", False))
    if not enabled:
        return PostOrderInvoiceHookResult(
            enabled=False,
            executed=False,
            skipped_reason=FEATURE_DISABLED_REASON,
        )

    app.logger.warning(
        "Automatic invoice workflow after checkout is enabled but not connected yet "
        "for order_id=%s checkout_session_id=%s.",
        getattr(order, "id", None),
        getattr(checkout_session, "id", None),
    )
    return PostOrderInvoiceHookResult(
        enabled=True,
        executed=False,
        skipped_reason=WORKFLOW_NOT_CONNECTED_REASON,
    )

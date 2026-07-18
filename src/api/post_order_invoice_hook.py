from dataclasses import dataclass


FEATURE_DISABLED_REASON = "feature_disabled"
CONFIGURATION_ERROR_STEP = "configuration"
UNEXPECTED_ERROR_STEP = "unexpected"
CHECKOUT_AUTO_ACTOR = "checkout:auto"


@dataclass(frozen=True)
class PostOrderInvoiceHookResult:
    enabled: bool
    executed: bool
    completed: bool = False
    failed_step: str | None = None
    invoice_id: int | None = None
    invoice_number: str | None = None
    skipped_reason: str | None = None


def handle_post_order_invoice_workflow(
    *,
    order,
    checkout_session,
    db_session,
    enabled,
    issuer_factory,
    invoice_output_dir,
    mailer_factory,
    logger,
    workflow_runner=None,
):
    enabled = bool(enabled)
    if not enabled:
        return PostOrderInvoiceHookResult(
            enabled=False,
            executed=False,
            skipped_reason=FEATURE_DISABLED_REASON,
        )

    order_id = getattr(order, "id", None)
    checkout_session_id = getattr(checkout_session, "id", None)

    try:
        _validate_hook_configuration(
            order_id=order_id,
            checkout_session=checkout_session,
            db_session=db_session,
            issuer_factory=issuer_factory,
            invoice_output_dir=invoice_output_dir,
            mailer_factory=mailer_factory,
        )
        issuer = issuer_factory()
        mailer = mailer_factory()
        if workflow_runner is None:
            workflow_runner = _default_workflow_runner()
    except Exception:
        logger.warning(
            "Automatic invoice workflow configuration failed for order_id=%s "
            "checkout_session_id=%s.",
            order_id,
            checkout_session_id,
            exc_info=True,
        )
        return PostOrderInvoiceHookResult(
            enabled=True,
            executed=False,
            completed=False,
            failed_step=CONFIGURATION_ERROR_STEP,
        )

    try:
        result = workflow_runner(
            order_id,
            issuer=issuer,
            checkout_session=checkout_session,
            actor=CHECKOUT_AUTO_ACTOR,
            invoice_output_dir=invoice_output_dir,
            mailer=mailer,
            db_session=db_session,
            logger=logger,
        )
    except Exception:
        logger.exception(
            "Unexpected error running automatic invoice workflow after checkout "
            "for order_id=%s checkout_session_id=%s.",
            order_id,
            checkout_session_id,
        )
        return PostOrderInvoiceHookResult(
            enabled=True,
            executed=True,
            completed=False,
            failed_step=UNEXPECTED_ERROR_STEP,
        )

    if not getattr(result, "completed", False):
        logger.warning(
            "Automatic invoice workflow finished partially for order_id=%s "
            "checkout_session_id=%s failed_step=%s.",
            order_id,
            checkout_session_id,
            getattr(result, "failed_step", None),
        )

    return PostOrderInvoiceHookResult(
        enabled=True,
        executed=True,
        completed=bool(getattr(result, "completed", False)),
        failed_step=getattr(result, "failed_step", None),
        invoice_id=getattr(result, "invoice_id", None),
        invoice_number=getattr(result, "invoice_number", None),
    )


def _validate_hook_configuration(
    *,
    order_id,
    checkout_session,
    db_session,
    issuer_factory,
    invoice_output_dir,
    mailer_factory,
):
    if not order_id:
        raise ValueError("Order is required.")
    if checkout_session is None:
        raise ValueError("Checkout session is required.")
    if db_session is None:
        raise ValueError("Database session is required.")
    if issuer_factory is None:
        raise ValueError("Issuer factory is required.")
    if not invoice_output_dir:
        raise ValueError("Invoice output directory is required.")
    if mailer_factory is None:
        raise ValueError("Mailer factory is required.")


def _default_workflow_runner():
    from api.invoice_workflow_service import run_invoice_workflow_for_order

    return run_invoice_workflow_for_order

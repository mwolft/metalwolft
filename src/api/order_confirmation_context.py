"""Read canonical confirmation snapshots with a bounded legacy fallback."""

from collections.abc import Mapping


def get_order_confirmation_context(order):
    """Return the persisted confirmation context when an order has one."""
    return getattr(order, "confirmed_order_context", None)


def get_order_quote_snapshot(order):
    """Prefer the canonical confirmation quote over legacy checkout data."""
    return _snapshot_from_confirmation_or_checkout(order, "quote_snapshot")


def get_order_customer_snapshot(order):
    """Prefer the canonical confirmation customer data over legacy checkout data."""
    return _snapshot_from_confirmation_or_checkout(order, "customer_snapshot")


def get_order_confirmation_recipient_email(order):
    """Resolve a confirmed order recipient without requiring an account."""
    customer_snapshot = get_order_customer_snapshot(order)
    snapshot_email = _normalized_text(customer_snapshot.get("email"))
    if snapshot_email:
        return snapshot_email

    return _normalized_text(getattr(getattr(order, "user", None), "email", None))


def get_order_confirmation_customer_firstname(order):
    """Resolve the greeting from frozen customer data before legacy account data."""
    customer_snapshot = get_order_customer_snapshot(order)
    snapshot_firstname = _normalized_text(customer_snapshot.get("firstname"))
    if snapshot_firstname:
        return snapshot_firstname

    return _normalized_text(getattr(getattr(order, "user", None), "firstname", None))


def _snapshot_from_confirmation_or_checkout(order, attribute):
    confirmation_context = get_order_confirmation_context(order)
    if confirmation_context is not None:
        confirmation_snapshot = getattr(confirmation_context, attribute, None)
        return confirmation_snapshot if isinstance(confirmation_snapshot, Mapping) else {}

    checkout_session = getattr(order, "checkout_session", None)
    checkout_snapshot = getattr(checkout_session, attribute, None)
    return checkout_snapshot if isinstance(checkout_snapshot, Mapping) else {}


def _normalized_text(value):
    return str(value or "").strip()

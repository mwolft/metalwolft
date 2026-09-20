"""Read canonical confirmation snapshots with a bounded legacy fallback."""

from collections.abc import Mapping


def get_order_confirmation_context(order):
    """Return the persisted confirmation context when an order has one."""
    return getattr(order, "confirmed_order_context", None)


def get_order_quote_snapshot(order):
    """Prefer the canonical confirmation quote over legacy checkout data."""
    return _snapshot_from_confirmation_or_checkout(order, "quote_snapshot")


def get_order_customer_snapshot(order):
    """Resolve frozen customer data with a field-wise legacy checkout fallback."""
    confirmation_context = get_order_confirmation_context(order)
    confirmation_snapshot = _mapping_snapshot(
        confirmation_context,
        "customer_snapshot",
    )
    checkout_snapshot = _checkout_snapshot(order, "customer_snapshot")
    return _merge_customer_snapshots(
        preferred_snapshot=confirmation_snapshot,
        fallback_snapshot=checkout_snapshot,
    )


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
        return _mapping_snapshot(confirmation_context, attribute)

    return _checkout_snapshot(order, attribute)


def _checkout_snapshot(order, attribute):
    checkout_session = getattr(order, "checkout_session", None)
    return _mapping_snapshot(checkout_session, attribute)


def _mapping_snapshot(source, attribute):
    snapshot = getattr(source, attribute, None)
    return dict(snapshot) if isinstance(snapshot, Mapping) else {}


def _merge_customer_snapshots(*, preferred_snapshot, fallback_snapshot):
    """Keep confirmed values while recovering absent historical checkout fields."""
    resolved = dict(fallback_snapshot)
    for field, value in preferred_snapshot.items():
        if _has_usable_value(value):
            resolved[field] = value
    return resolved


def _has_usable_value(value):
    if value is None:
        return False
    return not isinstance(value, str) or bool(value.strip())


def _normalized_text(value):
    return str(value or "").strip()

from datetime import date, timedelta


OPENING_TYPE_FIXED = "fixed"
OPENING_TYPE_HINGED = "hinged"


def calculate_delivery_adjustment_days(cart_items):
    """Return the calendar-day adjustment for persisted cart lines."""
    total_quantity = sum(max(int(item.quantity or 0), 0) for item in cart_items)
    has_hinged_product = any(
        getattr(getattr(item, "product", None), "opening_type", OPENING_TYPE_FIXED)
        == OPENING_TYPE_HINGED
        for item in cart_items
    )

    quantity_adjustment = 5 if total_quantity >= 6 else 2 if total_quantity >= 4 else 0
    return quantity_adjustment + (3 if has_hinged_product else 0)


def build_delivery_estimate(config, cart_items=None, today=None):
    """Build the public delivery range, optionally adjusted from real cart lines."""
    adjustment_days = calculate_delivery_adjustment_days(cart_items or [])
    current_day = today or date.today()
    start_date = current_day + timedelta(days=config.delivery_days + adjustment_days)
    end_date = start_date + timedelta(days=config.range_days)

    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "is_active": config.is_active,
    }

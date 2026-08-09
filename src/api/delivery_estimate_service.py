from datetime import date, timedelta


OPENING_TYPE_FIXED = "fixed"
OPENING_TYPE_HINGED = "hinged"


def calculate_delivery_adjustments(cart_items):
    """Return authoritative calendar-day adjustments for persisted cart lines."""
    total_quantity = sum(max(int(item.quantity or 0), 0) for item in cart_items)
    has_hinged_product = any(
        getattr(getattr(item, "product", None), "opening_type", OPENING_TYPE_FIXED)
        == OPENING_TYPE_HINGED
        for item in cart_items
    )

    adjustments = []
    if has_hinged_product:
        adjustments.append({
            "code": "hinged_product",
            "days": 3,
            "message": "+3 días por incluir una reja abatible",
        })
    if total_quantity >= 6:
        adjustments.append({
            "code": "quantity_six_or_more",
            "days": 5,
            "message": "+5 días por cantidad del pedido",
        })
    elif total_quantity >= 4:
        adjustments.append({
            "code": "quantity_four_to_five",
            "days": 2,
            "message": "+2 días por cantidad del pedido",
        })

    return adjustments


def calculate_delivery_adjustment_days(cart_items):
    """Return the total calendar-day adjustment for persisted cart lines."""
    return sum(adjustment["days"] for adjustment in calculate_delivery_adjustments(cart_items))


def build_delivery_estimate(config, cart_items=None, today=None, include_adjustments=False):
    """Build the public delivery range, optionally adjusted from real cart lines."""
    adjustments = calculate_delivery_adjustments(cart_items or [])
    adjustment_days = sum(adjustment["days"] for adjustment in adjustments)
    current_day = today or date.today()
    start_date = current_day + timedelta(days=config.delivery_days + adjustment_days)
    end_date = start_date + timedelta(days=config.range_days)

    estimate = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "is_active": config.is_active,
    }
    if include_adjustments:
        estimate["adjustments"] = adjustments

    return estimate

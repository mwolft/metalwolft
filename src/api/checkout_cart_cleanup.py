from api.utils import DEFAULT_CONFIGURATOR_SCREW_OPTION


def _to_int_quantity(value):
    try:
        quantity = int(value)
    except (TypeError, ValueError):
        return 0
    return max(quantity, 0)


def _to_float_or_none(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_text(value):
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _same_float(left, right):
    left_float = _to_float_or_none(left)
    right_float = _to_float_or_none(right)
    if left_float is None or right_float is None:
        return left_float is None and right_float is None
    return abs(left_float - right_float) < 0.000001


def _line_product_id(line):
    product_id = line.get("product_id")
    if product_id is None:
        product_id = line.get("producto_id")
    if product_id is None:
        return None
    try:
        return int(product_id)
    except (TypeError, ValueError):
        return None


def _cart_item_matches_line(cart_item, line):
    product_id = _line_product_id(line)
    if product_id is None or cart_item.producto_id != product_id:
        return False

    return all([
        _same_float(cart_item.alto, line.get("alto")),
        _same_float(cart_item.ancho, line.get("ancho")),
        _normalize_text(cart_item.anclaje) == _normalize_text(line.get("anclaje")),
        _normalize_text(cart_item.color) == _normalize_text(line.get("color")),
        (getattr(cart_item, "screw_option", None) or DEFAULT_CONFIGURATOR_SCREW_OPTION)
        == (line.get("screw_option") or DEFAULT_CONFIGURATOR_SCREW_OPTION),
    ])


def cleanup_cart_lines_from_checkout_quote(db_session, cart_model, user_id, checkout_quote, logger=None):
    """Remove only the cart quantities that were frozen in the checkout snapshot."""
    for line in (checkout_quote or {}).get("lines") or []:
        product_id = _line_product_id(line)
        purchased_quantity = _to_int_quantity(line.get("quantity"))
        if product_id is None or purchased_quantity < 1:
            continue

        cart_items = cart_model.query.filter_by(
            usuario_id=user_id,
            producto_id=product_id
        ).all()
        matching_items = sorted(
            (item for item in cart_items if _cart_item_matches_line(item, line)),
            key=lambda item: getattr(item, "id", 0) or 0
        )

        if not matching_items:
            if logger:
                logger.info(
                    "Checkout cart cleanup skipped missing line user_id=%s product_id=%s",
                    user_id,
                    product_id
            )
            continue

        total_matching_quantity = sum(_to_int_quantity(item.quantity) for item in matching_items)
        if total_matching_quantity < purchased_quantity:
            if logger:
                logger.info(
                    "Checkout cart cleanup preserved reduced line user_id=%s product_id=%s current=%s purchased=%s",
                    user_id,
                    product_id,
                    total_matching_quantity,
                    purchased_quantity
                )
            continue

        remaining_quantity = purchased_quantity
        for matching_item in matching_items:
            current_quantity = _to_int_quantity(matching_item.quantity)
            if current_quantity < 1:
                continue

            if current_quantity <= remaining_quantity:
                db_session.delete(matching_item)
                remaining_quantity -= current_quantity
            else:
                matching_item.quantity = current_quantity - remaining_quantity
                remaining_quantity = 0

            if remaining_quantity == 0:
                break

        if remaining_quantity and logger:
            logger.info(
                "Checkout cart cleanup stopped before consuming full quantity user_id=%s product_id=%s remaining=%s",
                user_id,
                product_id,
                remaining_quantity
            )

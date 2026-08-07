MODIFIABLE_STRIPE_CHECKOUT_STATUSES = {"pending_payment", "payment_failed"}


def is_modifiable_stripe_checkout_session(checkout_session, payment_intent_id):
    if not checkout_session or not payment_intent_id:
        return False
    if checkout_session.payment_provider != "stripe":
        return False
    if checkout_session.payment_intent_id != payment_intent_id:
        return False
    if checkout_session.order_id:
        return False
    return checkout_session.status in MODIFIABLE_STRIPE_CHECKOUT_STATUSES

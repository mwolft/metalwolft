import os

from flask import current_app

from api.invoice_snapshot_builder import FINAL_CHECKOUT_STATUSES, InvoiceSnapshotValidationError
from api.models import CheckoutSessions


REQUIRED_INVOICE_ISSUER_CONFIG = {
    "legal_name": "INVOICE_ISSUER_LEGAL_NAME",
    "trade_name": "INVOICE_ISSUER_TRADE_NAME",
    "tax_id": "INVOICE_ISSUER_TAX_ID",
    "address": "INVOICE_ISSUER_ADDRESS",
    "postal_code": "INVOICE_ISSUER_POSTAL_CODE",
    "city": "INVOICE_ISSUER_CITY",
    "country_code": "INVOICE_ISSUER_COUNTRY_CODE",
}

OPTIONAL_INVOICE_ISSUER_CONFIG = {
    "province": "INVOICE_ISSUER_PROVINCE",
    "email": "INVOICE_ISSUER_EMAIL",
    "phone": "INVOICE_ISSUER_PHONE",
}


def invoice_admin_actor_from_jwt(current_user):
    return current_user.get("email") or str(current_user.get("user_id") or "")


def invoice_admin_actor_from_basic_auth(auth):
    username = None
    if auth is not None:
        username = auth.get("username") if hasattr(auth, "get") else getattr(auth, "username", None)
    username = username or "unknown"
    return f"flask_admin:{username}"


def build_invoice_issuer_from_config():
    issuer = {}
    missing = []

    for field, env_name in REQUIRED_INVOICE_ISSUER_CONFIG.items():
        value = _invoice_issuer_config_value(env_name)
        if not value:
            missing.append(env_name)
        issuer[field] = value or None

    if missing:
        raise InvoiceSnapshotValidationError(
            "issuer",
            "Missing invoice issuer configuration: " + ", ".join(sorted(missing)),
        )

    for field, env_name in OPTIONAL_INVOICE_ISSUER_CONFIG.items():
        issuer[field] = _invoice_issuer_config_value(env_name) or None

    return issuer


def select_checkout_session_for_invoice(order):
    checkout_sessions = CheckoutSessions.query.filter_by(order_id=order.id).all()
    usable_sessions = [
        checkout_session
        for checkout_session in checkout_sessions
        if is_checkout_session_usable_for_invoice(checkout_session)
    ]

    if not usable_sessions:
        return None, "El pedido no esta listo para facturacion."

    if len(usable_sessions) > 1:
        return None, "El pedido tiene varias sesiones de checkout facturables."

    return usable_sessions[0], None


def is_checkout_session_usable_for_invoice(checkout_session):
    if checkout_session.status not in FINAL_CHECKOUT_STATUSES:
        return False

    if checkout_session.payment_provider == "stripe":
        return bool(checkout_session.payment_intent_id)

    if checkout_session.payment_provider == "paypal":
        return bool(checkout_session.provider_capture_id or checkout_session.provider_order_id)

    return bool(
        checkout_session.payment_intent_id
        or checkout_session.provider_capture_id
        or checkout_session.provider_order_id
    )


def _invoice_issuer_config_value(env_name):
    value = current_app.config.get(env_name)
    if value is None:
        value = os.getenv(env_name)
    return (str(value).strip() if value is not None else "")

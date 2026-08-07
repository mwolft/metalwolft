import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.invoice_snapshot_builder import (  # noqa: E402
    FINAL_CHECKOUT_STATUSES,
    InvoiceSnapshotValidationError,
    build_invoice_snapshot,
)


REQUIRED_ISSUER_ENV = {
    "legal_name": "INVOICE_ISSUER_LEGAL_NAME",
    "trade_name": "INVOICE_ISSUER_TRADE_NAME",
    "tax_id": "INVOICE_ISSUER_TAX_ID",
    "address": "INVOICE_ISSUER_ADDRESS",
    "postal_code": "INVOICE_ISSUER_POSTAL_CODE",
    "city": "INVOICE_ISSUER_CITY",
    "country_code": "INVOICE_ISSUER_COUNTRY_CODE",
}

OPTIONAL_ISSUER_ENV = {
    "province": "INVOICE_ISSUER_PROVINCE",
    "email": "INVOICE_ISSUER_EMAIL",
    "phone": "INVOICE_ISSUER_PHONE",
}


class InvoiceSnapshotInspectionError(RuntimeError):
    pass


def build_issuer_from_env(environ=None):
    environ = environ or os.environ
    issuer = {}
    missing = []

    for field, env_name in REQUIRED_ISSUER_ENV.items():
        value = (environ.get(env_name) or "").strip()
        if not value:
            missing.append(env_name)
        issuer[field] = value or None

    if missing:
        raise InvoiceSnapshotInspectionError(
            "missing issuer configuration: " + ", ".join(sorted(missing))
        )

    for field, env_name in OPTIONAL_ISSUER_ENV.items():
        value = (environ.get(env_name) or "").strip()
        issuer[field] = value or None

    return issuer


def select_checkout_session_for_order(order, checkout_sessions):
    if order is None:
        raise InvoiceSnapshotInspectionError("order not found")

    order_id = getattr(order, "id", None)
    linked_sessions = [
        session
        for session in checkout_sessions
        if getattr(session, "order_id", None) == order_id
    ]

    if not linked_sessions:
        raise InvoiceSnapshotInspectionError("no checkout session linked to order")

    usable_sessions = [
        session
        for session in linked_sessions
        if _is_usable_checkout_session(session)
    ]

    if not usable_sessions:
        raise InvoiceSnapshotInspectionError("no usable checkout session linked to order")

    if len(usable_sessions) > 1:
        raise InvoiceSnapshotInspectionError("ambiguous checkout sessions linked to order")

    return usable_sessions[0]


def _is_usable_checkout_session(checkout_session):
    status = getattr(checkout_session, "status", None)
    if status not in FINAL_CHECKOUT_STATUSES:
        return False

    provider = getattr(checkout_session, "payment_provider", None)
    if provider == "stripe":
        return bool(getattr(checkout_session, "payment_intent_id", None))
    if provider == "paypal":
        return bool(
            getattr(checkout_session, "provider_capture_id", None)
            or getattr(checkout_session, "provider_order_id", None)
        )

    return bool(
        getattr(checkout_session, "provider_capture_id", None)
        or getattr(checkout_session, "provider_order_id", None)
        or getattr(checkout_session, "payment_intent_id", None)
    )


def build_snapshot_for_order(order, checkout_sessions, issuer, *, issue_date=None):
    checkout_session = select_checkout_session_for_order(order, checkout_sessions)

    # Trigger lazy relationship reads inside the app context without mutating.
    getattr(order, "user", None)
    getattr(checkout_session, "user", None)

    snapshot = build_invoice_snapshot(
        order,
        checkout_session,
        issuer,
        issue_date=issue_date or date.today(),
        source="inspection",
        actor=None,
    )
    return snapshot, checkout_session


def inspect_snapshot_from_database(order_id, issuer, *, issue_date=None, components=None):
    app, orders_model, checkout_sessions_model = components or load_flask_components()

    with app.app_context():
        order = orders_model.query.get(order_id)
        if order is None:
            raise InvoiceSnapshotInspectionError("order not found")

        checkout_sessions = checkout_sessions_model.query.filter_by(order_id=order.id).all()
        return build_snapshot_for_order(
            order,
            checkout_sessions,
            issuer,
            issue_date=issue_date,
        )


def load_flask_components():
    from app import app
    from api.models import CheckoutSessions, Orders

    return app, Orders, CheckoutSessions


def serialize_snapshot(snapshot, *, pretty=False):
    return json.dumps(
        snapshot,
        ensure_ascii=False,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ) + "\n"


def write_json_output(output_path, content, *, force=False):
    path = Path(output_path)
    if path.exists() and not force:
        raise InvoiceSnapshotInspectionError(
            f"output file already exists: {path}. Use --force to overwrite."
        )
    path.write_text(content, encoding="utf-8")


def build_summary(snapshot, checkout_session):
    order = snapshot.get("operation", {})
    totals = snapshot.get("totals", {})
    return "\n".join([
        f"Order: {order.get('order_id')}",
        f"Locator: {order.get('order_locator') or '-'}",
        f"Provider: {getattr(checkout_session, 'payment_provider', '-')}",
        f"Lines: {len(snapshot.get('lines') or [])}",
        f"Before discount: {totals.get('total_amount_before_discount')} EUR",
        f"Discount: {totals.get('discount_amount')} EUR",
        f"Tax base: {totals.get('tax_base')} EUR",
        f"VAT: {totals.get('tax_amount')} EUR",
        f"Total: {totals.get('total_amount')} EUR",
        "Validation: OK",
        "Database writes: none",
    ])


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Inspect an InvoiceSnapshot v1 for an existing order without database writes."
    )
    parser.add_argument("--order-id", type=int, required=True)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--output", help="Write JSON snapshot to this path instead of stdout.")
    parser.add_argument("--force", action="store_true", help="Overwrite --output if it already exists.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        issuer = build_issuer_from_env()
        snapshot, checkout_session = inspect_snapshot_from_database(
            args.order_id,
            issuer,
        )
        content = serialize_snapshot(snapshot, pretty=args.pretty)
        if args.output:
            write_json_output(args.output, content, force=args.force)
        else:
            sys.stdout.write(content)

        print(build_summary(snapshot, checkout_session), file=sys.stderr)
        return 0
    except (InvoiceSnapshotInspectionError, InvoiceSnapshotValidationError) as error:
        print(
            "Invoice snapshot inspection failed:\n"
            f"order_id={args.order_id}\n"
            f"reason={error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

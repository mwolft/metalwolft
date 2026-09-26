"""Explicitly repair one historical web confirmation from its frozen checkout.

Requires DATABASE_URL in the environment. Dry-run is the default; --apply is
the only mode that can update data. Capture the JSON audit output securely.
"""

import argparse
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

from sqlalchemy import JSON, bindparam, create_engine, text


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from api.invoice_confirmation_context import (  # noqa: E402
    build_invoice_confirmation_context_from_checkout_session,
    build_invoice_confirmation_context_from_confirmed_order_context,
)
from api.invoice_snapshot_builder import validate_invoice_customer_snapshot  # noqa: E402


class RepairRejected(ValueError):
    """The persisted evidence does not justify an exact snapshot copy."""


_ORDER_SQL = "SELECT id, user_id, total_amount, invoice_number FROM orders WHERE id = :id"
_CONTEXT_SQL = """SELECT id, order_id, source, source_checkout_session_id,
    source_manual_draft_id, quote_snapshot, customer_snapshot, payment_method,
    payment_status, payment_amount, currency, payment_reference,
    provider_identifiers, payment_confirmed_at, confirmed_by, internal_note
    FROM confirmed_order_contexts WHERE id = :id"""
_CHECKOUT_SQL = """SELECT id, order_id, status, quote_snapshot,
    customer_snapshot, payment_provider, total_amount, payment_intent_id,
    provider_order_id, provider_capture_id
    FROM checkout_sessions WHERE id = :id"""
_UPDATE_SQL = text(
    "UPDATE confirmed_order_contexts SET customer_snapshot = :snapshot WHERE id = :id"
).bindparams(bindparam("snapshot", type_=JSON()))


def _require(condition, message):
    if not condition:
        raise RepairRejected(message)


def _money(value, label):
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise RepairRejected(f"Importe invalido: {label}.") from exc


def _mapping(value, label):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError as exc:
            raise RepairRejected(f"JSON invalido: {label}.") from exc
    _require(isinstance(value, dict), f"Snapshot invalido: {label}.")
    return value


def _fingerprint(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _empty(value):
    return value is None or (isinstance(value, str) and not value.strip()) or (
        isinstance(value, (dict, list)) and not value
    )


def _check_no_contradictions(old, frozen, path="customer_snapshot"):
    for key, value in old.items():
        if _empty(value):
            continue
        location = f"{path}.{key}"
        _require(key in frozen, f"Dato no presente en checkout: {location}.")
        if isinstance(value, dict) and isinstance(frozen[key], dict):
            _check_no_contradictions(value, frozen[key], location)
        else:
            _require(value == frozen[key], f"Dato contradictorio: {location}.")


def _fetch(conn, sql, row_id, label, *, lock):
    locking = " FOR UPDATE" if lock and conn.dialect.name == "postgresql" else ""
    row = conn.execute(text(sql + locking), {"id": row_id}).mappings().one_or_none()
    _require(row is not None, f"No existe {label} con id={row_id}.")
    return dict(row)


def _validate(conn, order_id, context_id, checkout_session_id, *, lock):
    # Invoice issuance locks the order first; use the same order to serialize both operations.
    order = _fetch(conn, _ORDER_SQL, order_id, "Orders", lock=lock)
    context = _fetch(conn, _CONTEXT_SQL, context_id, "ConfirmedOrderContext", lock=lock)
    checkout = _fetch(conn, _CHECKOUT_SQL, checkout_session_id, "CheckoutSession", lock=lock)

    _require(context["order_id"] == order_id, "COC.order_id no coincide.")
    _require(context["source_checkout_session_id"] == checkout_session_id, "COC.source_checkout_session_id no coincide.")
    _require(checkout["order_id"] == order_id, "CheckoutSession.order_id no coincide.")
    _require(context["source"] == "web_checkout" and context["source_manual_draft_id"] is None,
             "Solo se reparan contextos web de la sesion original.")
    _require(not order["invoice_number"], "Orders.invoice_number ya existe.")
    invoice = conn.execute(text("SELECT id FROM invoices WHERE order_id = :id LIMIT 1"), {"id": order_id}).first()
    _require(invoice is None, "Ya existe Invoice para este pedido.")

    context_quote = _mapping(context["quote_snapshot"], "COC.quote_snapshot")
    checkout_quote = _mapping(checkout["quote_snapshot"], "CheckoutSession.quote_snapshot")
    _require(context_quote == checkout_quote, "Los quote_snapshot no son equivalentes.")
    expected_total = _money(context_quote.get("total_amount"), "quote_snapshot.total_amount")
    _require(expected_total == _money(order["total_amount"], "Orders.total_amount"),
             "El quote no coincide con Orders.total_amount.")
    _require(expected_total == _money(context["payment_amount"], "COC.payment_amount"),
             "El pago del COC no coincide con el quote.")
    _require(expected_total == _money(checkout["total_amount"], "CheckoutSession.total_amount"),
             "El total de checkout no coincide con el quote.")
    _require(context["currency"] == "EUR", "La moneda del COC no es EUR.")
    _require(checkout["status"] in ("paid", "order_created"), "CheckoutSession no esta finalizada/pagada.")
    _require(context["payment_method"] == checkout["payment_provider"],
             "El proveedor de pago no coincide.")

    order_obj = SimpleNamespace(id=order_id, user=None)
    context_obj = SimpleNamespace(**context)
    context_obj.quote_snapshot = context_quote
    context_obj.customer_snapshot = _mapping(context["customer_snapshot"], "COC.customer_snapshot")
    if context_obj.provider_identifiers is not None:
        context_obj.provider_identifiers = _mapping(
            context_obj.provider_identifiers, "COC.provider_identifiers"
        )
    checkout_obj = SimpleNamespace(**checkout)
    checkout_obj.quote_snapshot = checkout_quote
    checkout_obj.customer_snapshot = _mapping(checkout["customer_snapshot"], "CheckoutSession.customer_snapshot")
    try:
        confirmed = build_invoice_confirmation_context_from_confirmed_order_context(
            order=order_obj, confirmed_order_context=context_obj
        )
        legacy = build_invoice_confirmation_context_from_checkout_session(
            order=order_obj, checkout_session=checkout_obj
        )
    except ValueError as exc:
        raise RepairRejected(f"Evidencia de pago/contexto invalida: {exc}") from exc
    _require(confirmed.payment_method == legacy.payment_method
             and confirmed.payment_reference == legacy.payment_reference
             and confirmed.provider_identifiers == legacy.provider_identifiers,
             "La referencia o identificadores del proveedor no coinciden con checkout.")

    old = context_obj.customer_snapshot
    frozen = checkout_obj.customer_snapshot
    _check_no_contradictions(old, frozen)
    try:
        validate_invoice_customer_snapshot(order_obj, frozen)
    except ValueError as exc:
        raise RepairRejected(f"El cliente de CheckoutSession no es fiscalmente valido: {exc}") from exc

    try:
        validate_invoice_customer_snapshot(order_obj, old)
    except ValueError:
        already_valid = False
    else:
        already_valid = True

    return context_obj, frozen, already_valid


def repair_customer_snapshot(conn, *, order_id, context_id, checkout_session_id, apply=False):
    """Validate and optionally copy the original snapshot in one transaction."""
    transaction = conn.begin()
    try:
        if not apply and conn.dialect.name == "postgresql":
            conn.exec_driver_sql("SET TRANSACTION READ ONLY")
        context, frozen, already_valid = _validate(
            conn, order_id, context_id, checkout_session_id, lock=apply
        )
        old = context.customer_snapshot
        audit = {
            "event": "explicit_historical_customer_snapshot_repair",
            "mode": "apply" if apply else "dry-run",
            "order_id": order_id,
            "confirmed_order_context_id": context_id,
            "checkout_session_id": checkout_session_id,
            "status": "already_valid" if already_valid else "eligible",
            "validated": [
                "record_links", "web_source", "matching_quotes", "matching_amounts",
                "eur", "confirmed_payment", "provider_evidence", "no_invoice",
                "no_invoice_number", "no_customer_contradictions", "fiscal_customer",
            ],
            "old_sha256": _fingerprint(old),
            "new_sha256": _fingerprint(frozen),
            "changed_fields": sorted(key for key in set(old) | set(frozen) if old.get(key) != frozen.get(key)),
        }
        if not apply or already_valid:
            if not apply:
                transaction.rollback()
            else:
                transaction.commit()
            return audit

        # Deliberately bypass the ORM immutability hook for this one audited field.
        audit["status"] = "applying"
        print(json.dumps(audit, ensure_ascii=False, sort_keys=True), flush=True)
        result = conn.execute(_UPDATE_SQL, {"id": context_id, "snapshot": deepcopy(frozen)})
        _require(result.rowcount == 1, "La actualizacion no afecto exactamente a un COC.")
        repaired, persisted, _ = _validate(
            conn, order_id, context_id, checkout_session_id, lock=False
        )
        _require(repaired.customer_snapshot == frozen and persisted == frozen,
                 "El snapshot reparado no coincide exactamente con CheckoutSession.")
        validate_invoice_customer_snapshot(SimpleNamespace(id=order_id, user=None), repaired.customer_snapshot)
        build_invoice_confirmation_context_from_confirmed_order_context(
            order=SimpleNamespace(id=order_id, user=None), confirmed_order_context=repaired
        )
        transaction.commit()
        audit["status"] = "applied"
        return audit
    except Exception:
        if transaction.is_active:
            transaction.rollback()
        if "audit" in locals() and audit.get("status") == "applying":
            audit["status"] = "rolled_back"
            print(json.dumps(audit, ensure_ascii=False, sort_keys=True), flush=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--order-id", type=int, required=True)
    parser.add_argument("--context-id", type=int, required=True)
    parser.add_argument("--checkout-session-id", type=int, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Validate only (default).")
    mode.add_argument("--apply", action="store_true", help="Perform the single validated update.")
    args = parser.parse_args()
    if min(args.order_id, args.context_id, args.checkout_session_id) <= 0:
        parser.error("All IDs must be positive.")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        parser.error("DATABASE_URL must be set in the environment.")
    engine = create_engine(database_url.replace("postgres://", "postgresql://"), future=True)
    try:
        with engine.connect() as conn:
            result = repair_customer_snapshot(
                conn, order_id=args.order_id, context_id=args.context_id,
                checkout_session_id=args.checkout_session_id, apply=args.apply,
            )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    except RepairRejected as exc:
        parser.exit(2, f"Repair rejected: {exc}\n")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

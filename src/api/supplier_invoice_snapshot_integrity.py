"""Canonical integrity helpers for registered supplier invoice snapshots."""

import hashlib
import json
from decimal import Decimal


class SupplierInvoiceSnapshotIntegrityError(ValueError):
    """Raised when a supplier invoice snapshot cannot be canonicalized."""


def canonicalize_supplier_invoice_snapshot(snapshot):
    """Return stable JSON without sharing sales-invoice-specific helpers."""
    return json.dumps(
        _normalize_value(snapshot, "snapshot"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def calculate_supplier_invoice_snapshot_hash(snapshot):
    canonical_snapshot = canonicalize_supplier_invoice_snapshot(snapshot)
    return hashlib.sha256(canonical_snapshot.encode("utf-8")).hexdigest()


def _normalize_value(value, path):
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise SupplierInvoiceSnapshotIntegrityError(f"No se admiten float en {path}.")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, list):
        return [_normalize_value(item, f"{path}[]") for item in value]
    if isinstance(value, dict):
        normalized = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise SupplierInvoiceSnapshotIntegrityError(f"Clave no valida en {path}.")
            normalized[key] = _normalize_value(item, f"{path}.{key}")
        return normalized
    raise SupplierInvoiceSnapshotIntegrityError(f"Valor no serializable en {path}.")

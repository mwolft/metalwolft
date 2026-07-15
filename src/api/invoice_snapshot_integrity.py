import hashlib
import json
from collections.abc import Mapping, Sequence


VOLATILE_METADATA_FIELDS = {"generated_at"}


class InvoiceSnapshotIntegrityError(ValueError):
    """Raised when a snapshot cannot be canonicalized safely."""


def canonicalize_invoice_snapshot(snapshot):
    """Return the stable canonical JSON representation used for hashing.

    `metadata.generated_at` is intentionally excluded because it is generated
    at build time and must not make an otherwise identical fiscal snapshot
    produce a different integrity hash.
    """
    if not isinstance(snapshot, Mapping):
        raise InvoiceSnapshotIntegrityError("Snapshot must be a JSON object.")
    normalized = _normalize_json_value(snapshot, ())
    try:
        return json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise InvoiceSnapshotIntegrityError("Snapshot contains a non-JSON value.") from exc


def calculate_invoice_snapshot_hash(snapshot):
    canonical_snapshot = canonicalize_invoice_snapshot(snapshot)
    return hashlib.sha256(canonical_snapshot.encode("utf-8")).hexdigest()


def _normalize_json_value(value, path):
    if isinstance(value, float):
        raise InvoiceSnapshotIntegrityError(
            f"Snapshot contains a float at {_format_path(path)}."
        )

    if isinstance(value, Mapping):
        normalized = {}
        for key, child in value.items():
            if not isinstance(key, str):
                raise InvoiceSnapshotIntegrityError(
                    f"Snapshot contains a non-string key at {_format_path(path)}."
                )
            if path == ("metadata",) and key in VOLATILE_METADATA_FIELDS:
                continue
            normalized[key] = _normalize_json_value(child, (*path, key))
        return normalized

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [
            _normalize_json_value(child, (*path, str(index)))
            for index, child in enumerate(value)
        ]

    return value


def _format_path(path):
    return "snapshot" if not path else "snapshot." + ".".join(path)

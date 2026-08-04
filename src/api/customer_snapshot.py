import re
from collections.abc import Mapping


CUSTOMER_SNAPSHOT_FIELD_LIMITS = {
    "firstname": 100,
    "lastname": 100,
    "email": 254,
    "phone": 50,
    "legal_name": 255,
    "tax_id": 20,
    "CIF": 20,
    "billing_address": 200,
    "billing_postal_code": 20,
    "billing_city": 100,
    "billing_province": 100,
    "billing_country_code": 2,
    "shipping_address": 200,
    "shipping_postal_code": 20,
    "shipping_city": 100,
    "shipping_province": 100,
    "shipping_country_code": 2,
    "province": 100,
    "country_code": 2,
}

REQUIRED_CHECKOUT_FIELDS = (
    "firstname",
    "lastname",
    "email",
    "phone",
    "legal_name",
    "tax_id",
    "billing_address",
    "billing_postal_code",
    "billing_city",
)

_BILLING_ADDRESS_FIELDS = (
    "billing_address",
    "billing_postal_code",
    "billing_city",
)
_SHIPPING_ADDRESS_FIELDS = (
    "shipping_address",
    "shipping_postal_code",
    "shipping_city",
)
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_COUNTRY_CODE_PATTERN = re.compile(r"^[A-Za-z]{2}$")


class CustomerSnapshotValidationError(ValueError):
    code = "INVALID_CUSTOMER_DATA"

    def __init__(self, field, message):
        self.field = field
        super().__init__(message)

    def to_dict(self):
        message = str(self)
        return {
            "error": message,
            "message": message,
            "code": self.code,
            "field": self.field,
        }


def extract_customer_snapshot(
    payload,
    *,
    require_checkout_fields=False,
    fallback_snapshot=None,
):
    if not isinstance(payload, Mapping):
        raise CustomerSnapshotValidationError(
            "customer_data",
            "Los datos de cliente deben ser un objeto.",
        )

    if fallback_snapshot is not None and not isinstance(fallback_snapshot, Mapping):
        raise CustomerSnapshotValidationError(
            "customer_snapshot",
            "Los datos de cliente alternativos deben ser un objeto.",
        )

    nested_source = payload.get("customer_data") if "customer_data" in payload else None
    if "customer_data" in payload:
        if nested_source is None:
            nested_source = {}
        elif not isinstance(nested_source, Mapping):
            raise CustomerSnapshotValidationError(
                "customer_data",
                "Los datos de cliente deben ser un objeto.",
            )

    if require_checkout_fields:
        _require_explicit_checkout_legal_name(payload, nested_source)

    source = {}
    _overlay_snapshot_fields(source, fallback_snapshot or {})
    _overlay_snapshot_fields(source, payload)
    if "customer_data" in payload:
        _overlay_snapshot_fields(source, nested_source)

    return normalize_customer_snapshot(
        source,
        require_checkout_fields=require_checkout_fields,
        validate_address_groups=require_checkout_fields,
    )


def _require_explicit_checkout_legal_name(payload, nested_source):
    value = payload.get("legal_name")
    if isinstance(nested_source, Mapping) and "legal_name" in nested_source:
        value = nested_source.get("legal_name")

    if value is None or (isinstance(value, str) and not value.strip()):
        raise CustomerSnapshotValidationError(
            "legal_name",
            "El campo 'legal_name' es obligatorio.",
        )


def _overlay_snapshot_fields(target, source):
    for field in CUSTOMER_SNAPSHOT_FIELD_LIMITS:
        if field not in source:
            continue
        value = source.get(field)
        if value is not None and value != "":
            target[field] = value


def normalize_customer_snapshot(
    snapshot,
    *,
    require_checkout_fields=False,
    validate_address_groups=True,
):
    if snapshot is None:
        snapshot = {}
    if not isinstance(snapshot, Mapping):
        raise CustomerSnapshotValidationError(
            "customer_snapshot",
            "El snapshot de cliente debe ser un objeto.",
        )

    normalized = {}
    for field, max_length in CUSTOMER_SNAPSHOT_FIELD_LIMITS.items():
        value = snapshot.get(field)
        if value is None or value == "":
            continue
        if not isinstance(value, str):
            raise CustomerSnapshotValidationError(
                field,
                f"El campo '{field}' debe ser texto.",
            )

        value = value.strip()
        if not value:
            continue
        if len(value) > max_length:
            raise CustomerSnapshotValidationError(
                field,
                f"El campo '{field}' supera la longitud maxima de {max_length} caracteres.",
            )
        normalized[field] = value

    _normalize_email(normalized)
    _normalize_tax_id(normalized)
    _normalize_country_codes(normalized)
    _normalize_legacy_location_fields(normalized)

    if require_checkout_fields and not normalized.get("legal_name"):
        raise CustomerSnapshotValidationError(
            "legal_name",
            "El campo 'legal_name' es obligatorio.",
        )

    _normalize_legal_name(normalized)
    _default_shipping_to_billing(normalized)

    if validate_address_groups:
        _validate_complete_group(normalized, _BILLING_ADDRESS_FIELDS)
        _validate_complete_group(normalized, _SHIPPING_ADDRESS_FIELDS)

    if require_checkout_fields:
        for field in REQUIRED_CHECKOUT_FIELDS:
            if not normalized.get(field):
                raise CustomerSnapshotValidationError(
                    field,
                    f"El campo '{field}' es obligatorio.",
                )

    return normalized


def merge_customer_snapshots(existing_snapshot, new_snapshot):
    if existing_snapshot is not None and not isinstance(existing_snapshot, Mapping):
        raise CustomerSnapshotValidationError(
            "customer_snapshot",
            "El snapshot de cliente existente debe ser un objeto.",
        )
    if new_snapshot is not None and not isinstance(new_snapshot, Mapping):
        raise CustomerSnapshotValidationError(
            "customer_snapshot",
            "El snapshot de cliente nuevo debe ser un objeto.",
        )

    merged = {
        **dict(existing_snapshot or {}),
        **dict(new_snapshot or {}),
    }
    return normalize_customer_snapshot(merged)


def _normalize_email(snapshot):
    email = snapshot.get("email")
    if not email:
        return
    if not _EMAIL_PATTERN.fullmatch(email):
        raise CustomerSnapshotValidationError(
            "email",
            "El campo 'email' no tiene un formato valido.",
        )
    snapshot["email"] = email.lower()


def _normalize_tax_id(snapshot):
    tax_id = snapshot.get("tax_id")
    legacy_tax_id = snapshot.get("CIF")
    if tax_id and legacy_tax_id and tax_id.upper() != legacy_tax_id.upper():
        raise CustomerSnapshotValidationError(
            "tax_id",
            "Los campos 'tax_id' y 'CIF' no coinciden.",
        )

    normalized_tax_id = (tax_id or legacy_tax_id or "").upper()
    if normalized_tax_id:
        snapshot["tax_id"] = normalized_tax_id
        snapshot["CIF"] = normalized_tax_id


def _normalize_country_codes(snapshot):
    for field in (
        "billing_country_code",
        "shipping_country_code",
        "country_code",
    ):
        country_code = snapshot.get(field)
        if not country_code:
            continue
        if not _COUNTRY_CODE_PATTERN.fullmatch(country_code):
            raise CustomerSnapshotValidationError(
                field,
                f"El campo '{field}' debe ser un codigo ISO de dos letras.",
            )
        snapshot[field] = country_code.upper()


def _normalize_legacy_location_fields(snapshot):
    if not snapshot.get("billing_province") and snapshot.get("province"):
        snapshot["billing_province"] = snapshot["province"]
    if not snapshot.get("billing_country_code") and snapshot.get("country_code"):
        snapshot["billing_country_code"] = snapshot["country_code"]
    snapshot.pop("province", None)
    snapshot.pop("country_code", None)


def _normalize_legal_name(snapshot):
    if snapshot.get("legal_name"):
        return
    legal_name = " ".join(
        part for part in (snapshot.get("firstname"), snapshot.get("lastname")) if part
    )
    if legal_name:
        snapshot["legal_name"] = legal_name


def _default_shipping_to_billing(snapshot):
    if any(snapshot.get(field) for field in _SHIPPING_ADDRESS_FIELDS):
        return

    for suffix in ("address", "postal_code", "city", "province", "country_code"):
        billing_field = f"billing_{suffix}"
        shipping_field = f"shipping_{suffix}"
        if snapshot.get(billing_field):
            snapshot[shipping_field] = snapshot[billing_field]


def _validate_complete_group(snapshot, fields):
    present = [field for field in fields if snapshot.get(field)]
    if not present or len(present) == len(fields):
        return

    missing = next(field for field in fields if not snapshot.get(field))
    raise CustomerSnapshotValidationError(
        missing,
        f"El campo '{missing}' es obligatorio para completar la direccion.",
    )

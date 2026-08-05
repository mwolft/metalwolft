from collections.abc import Mapping

from api.customer_snapshot import (
    CustomerSnapshotValidationError,
    normalize_customer_snapshot,
)


PROFILE_EDITABLE_FIELDS = (
    "firstname",
    "lastname",
    "phone",
    "shipping_address",
    "shipping_city",
    "shipping_postal_code",
    "billing_address",
    "billing_city",
    "billing_postal_code",
)

# Existing React clients may still send this persisted legacy field.
PROFILE_LEGACY_EDITABLE_FIELDS = ("CIF",)


def serialize_customer_profile(user):
    return {
        "id": user.id,
        "email": user.email,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "phone": user.phone,
        "shipping_address": user.shipping_address,
        "shipping_city": user.shipping_city,
        "shipping_postal_code": user.shipping_postal_code,
        "billing_address": user.billing_address,
        "billing_city": user.billing_city,
        "billing_postal_code": user.billing_postal_code,
        "CIF": user.CIF,
    }


def normalize_customer_profile_update(payload):
    if not isinstance(payload, Mapping):
        raise CustomerSnapshotValidationError(
            "profile",
            "Los datos del perfil deben ser un objeto.",
        )

    normalized_update = {}
    for field in (*PROFILE_EDITABLE_FIELDS, *PROFILE_LEGACY_EDITABLE_FIELDS):
        if field not in payload:
            continue

        value = payload.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            normalized_update[field] = None
            continue

        normalized_field = normalize_customer_snapshot(
            {field: value},
            validate_address_groups=False,
        )
        normalized_update[field] = normalized_field.get(field)

    return normalized_update

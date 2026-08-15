"""Read-only shipping-address presentation from checkout and order snapshots."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ShippingAddress:
    recipient: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    province: str | None = None
    country_code: str | None = None
    same_as_billing: bool = False

    @property
    def is_available(self):
        return any((self.address, self.postal_code, self.city))


def shipping_address_from_customer_snapshot(customer_snapshot):
    """Return delivery data frozen in the checkout session, never user-profile data."""
    if not isinstance(customer_snapshot, Mapping):
        return ShippingAddress()

    shipping = _snapshot_address(customer_snapshot, "shipping")
    billing = _snapshot_address(customer_snapshot, "billing")
    if not _has_address(shipping):
        shipping = billing

    return ShippingAddress(
        recipient=_recipient(customer_snapshot.get("firstname"), customer_snapshot.get("lastname")),
        **shipping,
        same_as_billing=_has_address(billing) and shipping == billing,
    )


def shipping_address_from_order_details(order_details):
    """Return the operational delivery address frozen on the first order line."""
    first_detail = next(iter(order_details or ()), None)
    if first_detail is None:
        return ShippingAddress()

    shipping = _detail_address(first_detail, "shipping")
    billing = _detail_address(first_detail, "billing")
    if not _has_address(shipping):
        shipping = billing

    return ShippingAddress(
        recipient=_recipient(
            getattr(first_detail, "firstname", None),
            getattr(first_detail, "lastname", None),
        ),
        **shipping,
        same_as_billing=_has_address(billing) and shipping == billing,
    )


def shipping_address_lines(shipping_address, *, include_recipient=True):
    if not shipping_address or not shipping_address.is_available:
        return ()

    lines = []
    if include_recipient and shipping_address.recipient:
        lines.append(shipping_address.recipient)
    if shipping_address.address:
        lines.append(shipping_address.address)

    locality = " ".join(
        part for part in (shipping_address.postal_code, shipping_address.city) if part
    )
    if locality:
        lines.append(locality)
    if shipping_address.province:
        lines.append(shipping_address.province)
    if shipping_address.country_code:
        lines.append(shipping_address.country_code)
    return tuple(lines)


def _snapshot_address(snapshot, prefix):
    return {
        "address": _text(snapshot.get(f"{prefix}_address")),
        "postal_code": _text(snapshot.get(f"{prefix}_postal_code")),
        "city": _text(snapshot.get(f"{prefix}_city")),
        "province": _text(snapshot.get(f"{prefix}_province")),
        "country_code": _text(snapshot.get(f"{prefix}_country_code")),
    }


def _detail_address(detail, prefix):
    return {
        "address": _text(getattr(detail, f"{prefix}_address", None)),
        "postal_code": _text(getattr(detail, f"{prefix}_postal_code", None)),
        "city": _text(getattr(detail, f"{prefix}_city", None)),
        "province": None,
        "country_code": None,
    }


def _has_address(address):
    return any((address["address"], address["postal_code"], address["city"]))


def _recipient(firstname, lastname):
    values = (_text(firstname), _text(lastname))
    return " ".join(value for value in values if value) or None


def _text(value):
    normalized = str(value or "").strip()
    return normalized or None

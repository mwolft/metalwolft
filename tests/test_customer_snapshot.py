import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.customer_snapshot import (  # noqa: E402
    CustomerSnapshotValidationError,
    extract_customer_snapshot,
    merge_customer_snapshots,
    normalize_customer_snapshot,
)


def current_customer_data(**overrides):
    data = {
        "firstname": " Sergio ",
        "lastname": " Arias ",
        "email": " CLIENTE@EXAMPLE.COM ",
        "phone": " 600000000 ",
        "legal_name": " Sergio Arias ",
        "CIF": " 00000000t ",
        "billing_address": " Calle Factura 3 ",
        "billing_postal_code": " 13001 ",
        "billing_city": " Ciudad Real ",
        "shipping_address": "",
        "shipping_postal_code": "",
        "shipping_city": "",
    }
    data.update(overrides)
    return data


class CustomerSnapshotContractTest(unittest.TestCase):
    def test_current_snapshot_is_normalized_to_canonical_shape(self):
        snapshot = extract_customer_snapshot(
            {"customer_data": current_customer_data()},
            require_checkout_fields=True,
        )

        self.assertEqual(snapshot["firstname"], "Sergio")
        self.assertEqual(snapshot["lastname"], "Arias")
        self.assertEqual(snapshot["email"], "cliente@example.com")
        self.assertEqual(snapshot["phone"], "600000000")
        self.assertEqual(snapshot["legal_name"], "Sergio Arias")
        self.assertEqual(snapshot["tax_id"], "00000000T")
        self.assertEqual(snapshot["CIF"], "00000000T")
        self.assertEqual(snapshot["shipping_address"], "Calle Factura 3")
        self.assertEqual(snapshot["shipping_postal_code"], "13001")
        self.assertEqual(snapshot["shipping_city"], "Ciudad Real")

    def test_nested_legacy_payload_uses_top_level_email(self):
        customer = current_customer_data()
        customer.pop("email")

        snapshot = extract_customer_snapshot(
            {
                "email": "legacy@example.com",
                "customer_data": customer,
            },
            require_checkout_fields=True,
        )

        self.assertEqual(snapshot["email"], "legacy@example.com")

    def test_authenticated_email_is_used_when_legacy_payload_omits_it(self):
        customer = current_customer_data()
        customer.pop("email")

        snapshot = extract_customer_snapshot(
            {"customer_data": customer},
            require_checkout_fields=True,
            fallback_snapshot={"email": "account@example.com"},
        )

        self.assertEqual(snapshot["email"], "account@example.com")

    def test_legacy_cif_is_preserved_as_alias_for_tax_id(self):
        snapshot = normalize_customer_snapshot({"CIF": "b12345678"})

        self.assertEqual(snapshot["tax_id"], "B12345678")
        self.assertEqual(snapshot["CIF"], "B12345678")

    def test_legal_name_falls_back_to_firstname_and_lastname(self):
        snapshot = normalize_customer_snapshot(
            {"firstname": "Juan", "lastname": "Garcia Lopez"}
        )

        self.assertEqual(snapshot["legal_name"], "Juan Garcia Lopez")

    def test_explicit_legal_name_is_not_replaced(self):
        snapshot = normalize_customer_snapshot(
            {
                "firstname": "Juan",
                "lastname": "Garcia Lopez",
                "legal_name": "CONSTRUCCIONES EJEMPLO SL",
            }
        )

        self.assertEqual(snapshot["legal_name"], "CONSTRUCCIONES EJEMPLO SL")

    def test_invalid_field_type_is_rejected(self):
        with self.assertRaises(CustomerSnapshotValidationError) as context:
            normalize_customer_snapshot({"phone": ["600000000"]})

        self.assertEqual(context.exception.field, "phone")

    def test_excessively_long_field_is_rejected(self):
        with self.assertRaises(CustomerSnapshotValidationError) as context:
            normalize_customer_snapshot({"firstname": "x" * 101})

        self.assertEqual(context.exception.field, "firstname")

    def test_invalid_email_is_rejected(self):
        with self.assertRaises(CustomerSnapshotValidationError) as context:
            extract_customer_snapshot(
                {"customer_data": current_customer_data(email="invalid")},
                require_checkout_fields=True,
            )

        self.assertEqual(context.exception.field, "email")

    def test_current_checkout_requires_phone(self):
        with self.assertRaises(CustomerSnapshotValidationError) as context:
            extract_customer_snapshot(
                {"customer_data": current_customer_data(phone="")},
                require_checkout_fields=True,
            )

        self.assertEqual(context.exception.field, "phone")

    def test_current_checkout_requires_explicit_legal_name(self):
        customer = current_customer_data()
        customer.pop("legal_name")

        with self.assertRaises(CustomerSnapshotValidationError) as context:
            extract_customer_snapshot(
                {"customer_data": customer},
                require_checkout_fields=True,
            )

        self.assertEqual(context.exception.field, "legal_name")

    def test_current_checkout_rejects_null_legal_name(self):
        with self.assertRaises(CustomerSnapshotValidationError) as context:
            extract_customer_snapshot(
                {"customer_data": current_customer_data(legal_name=None)},
                require_checkout_fields=True,
            )

        self.assertEqual(context.exception.field, "legal_name")

    def test_current_checkout_rejects_empty_legal_name(self):
        with self.assertRaises(CustomerSnapshotValidationError) as context:
            extract_customer_snapshot(
                {"customer_data": current_customer_data(legal_name="")},
                require_checkout_fields=True,
            )

        self.assertEqual(context.exception.field, "legal_name")

    def test_current_checkout_rejects_whitespace_legal_name(self):
        with self.assertRaises(CustomerSnapshotValidationError) as context:
            extract_customer_snapshot(
                {"customer_data": current_customer_data(legal_name="   ")},
                require_checkout_fields=True,
            )

        self.assertEqual(context.exception.field, "legal_name")

    def test_current_checkout_does_not_take_legal_name_from_fallback(self):
        customer = current_customer_data()
        customer.pop("legal_name")

        with self.assertRaises(CustomerSnapshotValidationError) as context:
            extract_customer_snapshot(
                {"customer_data": customer},
                require_checkout_fields=True,
                fallback_snapshot={"legal_name": "Fallback Customer"},
            )

        self.assertEqual(context.exception.field, "legal_name")

    def test_current_company_legal_name_is_not_replaced_by_contact(self):
        snapshot = extract_customer_snapshot(
            {
                "customer_data": current_customer_data(
                    firstname="Juan",
                    lastname="Garcia Lopez",
                    legal_name=" CONSTRUCCIONES EJEMPLO SL ",
                    CIF="B12345678",
                )
            },
            require_checkout_fields=True,
        )

        self.assertEqual(snapshot["firstname"], "Juan")
        self.assertEqual(snapshot["lastname"], "Garcia Lopez")
        self.assertEqual(snapshot["legal_name"], "CONSTRUCCIONES EJEMPLO SL")

    def test_current_checkout_requires_tax_id(self):
        with self.assertRaises(CustomerSnapshotValidationError) as context:
            extract_customer_snapshot(
                {"customer_data": current_customer_data(CIF="", tax_id="")},
                require_checkout_fields=True,
            )

        self.assertEqual(context.exception.field, "tax_id")

    def test_canonical_tax_id_is_trimmed_and_uppercased(self):
        snapshot = extract_customer_snapshot(
            {"customer_data": current_customer_data(CIF="", tax_id="  x1234567l  ")},
            require_checkout_fields=True,
        )

        self.assertEqual(snapshot["tax_id"], "X1234567L")
        self.assertEqual(snapshot["CIF"], "X1234567L")

    def test_current_checkout_rejects_tax_id_over_contract_limit(self):
        with self.assertRaises(CustomerSnapshotValidationError) as context:
            extract_customer_snapshot(
                {"customer_data": current_customer_data(CIF="", tax_id="X" * 21)},
                require_checkout_fields=True,
            )

        self.assertEqual(context.exception.field, "tax_id")

    def test_historical_snapshot_without_tax_id_remains_accepted(self):
        snapshot = normalize_customer_snapshot(
            {
                "firstname": "Cliente",
                "lastname": "Historico",
                "billing_address": "Calle Antigua 1",
                "billing_postal_code": "13001",
                "billing_city": "Ciudad Real",
            }
        )

        self.assertNotIn("tax_id", snapshot)
        self.assertNotIn("CIF", snapshot)

    def test_legacy_snapshot_without_province_or_country_is_accepted(self):
        snapshot = normalize_customer_snapshot(
            {
                "firstname": "Sergio",
                "lastname": "Arias",
                "billing_address": "Calle Factura 3",
                "billing_postal_code": "13001",
                "billing_city": "Ciudad Real",
            }
        )

        self.assertNotIn("billing_province", snapshot)
        self.assertNotIn("billing_country_code", snapshot)

    def test_partial_update_merges_with_existing_snapshot(self):
        existing = extract_customer_snapshot(
            {"customer_data": current_customer_data()},
            require_checkout_fields=True,
        )

        merged = merge_customer_snapshots(existing, {"phone": "611111111"})

        self.assertEqual(merged["phone"], "611111111")
        self.assertEqual(merged["email"], "cliente@example.com")
        self.assertEqual(merged["legal_name"], "Sergio Arias")


if __name__ == "__main__":
    unittest.main()

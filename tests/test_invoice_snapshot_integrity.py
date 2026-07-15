import copy
import importlib.util
import re
import sys
import unittest
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.invoice_snapshot_integrity import (  # noqa: E402
    InvoiceSnapshotIntegrityError,
    calculate_invoice_snapshot_hash,
    canonicalize_invoice_snapshot,
)


HAS_MODEL_DEPENDENCIES = (
    importlib.util.find_spec("flask_sqlalchemy") is not None
    and importlib.util.find_spec("slugify") is not None
)

if HAS_MODEL_DEPENDENCIES:
    from api.models import Invoices  # noqa: E402


def snapshot(overrides=None):
    data = {
        "schema_version": 1,
        "metadata": {
            "generator": "invoice_snapshot_builder_v1",
            "generated_at": "2026-07-15T10:00:00+00:00",
        },
        "issuer": {
            "legal_name": "MetalWolft",
            "tax_id": "B00000000",
        },
        "customer": {
            "legal_name": "Sergio Arias",
            "email": "cliente@example.com",
        },
        "lines": [
            {
                "line_type": "product",
                "description": "Reja fija Pittsburgh",
                "line_total": "95.00",
            },
            {
                "line_type": "shipping",
                "description": "Gastos de envío",
                "line_total": "21.00",
            },
        ],
        "totals": {
            "total_amount": "116.00",
            "tax_base": "95.87",
            "tax_amount": "20.13",
        },
    }
    data.update(overrides or {})
    return data


class InvoiceSnapshotIntegrityTest(unittest.TestCase):
    def test_canonicalization_is_stable_sorted_utf8_and_does_not_mutate_input(self):
        original = snapshot()
        original_copy = copy.deepcopy(original)
        reordered = {
            "totals": original["totals"],
            "lines": original["lines"],
            "customer": original["customer"],
            "issuer": original["issuer"],
            "metadata": {
                "generated_at": original["metadata"]["generated_at"],
                "generator": original["metadata"]["generator"],
            },
            "schema_version": original["schema_version"],
        }

        canonical = canonicalize_invoice_snapshot(original)

        self.assertEqual(canonical, canonicalize_invoice_snapshot(reordered))
        self.assertIn("envío", canonical)
        self.assertNotIn("\\u00ed", canonical)
        self.assertEqual(original, original_copy)

    def test_generated_at_is_excluded_from_canonical_snapshot_and_hash(self):
        first = snapshot()
        second = snapshot(
            {
                "metadata": {
                    "generator": "invoice_snapshot_builder_v1",
                    "generated_at": "2026-07-16T11:30:00+00:00",
                }
            }
        )

        self.assertNotIn("generated_at", canonicalize_invoice_snapshot(first))
        self.assertEqual(
            calculate_invoice_snapshot_hash(first),
            calculate_invoice_snapshot_hash(second),
        )

    def test_business_relevant_changes_change_hash(self):
        base_hash = calculate_invoice_snapshot_hash(snapshot())
        changed_total = snapshot({"totals": {"total_amount": "117.00", "tax_base": "96.69", "tax_amount": "20.31"}})

        self.assertNotEqual(base_hash, calculate_invoice_snapshot_hash(changed_total))

    def test_hash_is_sha256_hex(self):
        digest = calculate_invoice_snapshot_hash(snapshot())

        self.assertEqual(len(digest), 64)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_float_values_are_rejected(self):
        invalid = snapshot({"totals": {"total_amount": 116.0}})

        with self.assertRaisesRegex(InvoiceSnapshotIntegrityError, "float"):
            canonicalize_invoice_snapshot(invalid)

    def test_non_string_keys_are_rejected(self):
        invalid = snapshot()
        invalid["totals"] = {1: "116.00"}

        with self.assertRaisesRegex(InvoiceSnapshotIntegrityError, "non-string key"):
            canonicalize_invoice_snapshot(invalid)

    def test_non_json_values_are_rejected(self):
        invalid = snapshot({"issued_at": datetime(2026, 7, 15, 10, 0)})

        with self.assertRaisesRegex(InvoiceSnapshotIntegrityError, "non-JSON"):
            canonicalize_invoice_snapshot(invalid)

    def test_root_snapshot_must_be_json_object(self):
        with self.assertRaisesRegex(InvoiceSnapshotIntegrityError, "JSON object"):
            canonicalize_invoice_snapshot([])


@unittest.skipUnless(HAS_MODEL_DEPENDENCIES, "SQLAlchemy model dependencies are not installed.")
class InvoiceSnapshotPersistenceModelTest(unittest.TestCase):
    def build_legacy_invoice(self):
        return Invoices(
            invoice_number="JUL-2026-001",
            pdf_path="/api/download-invoice/invoice_JUL-2026-001.pdf",
            amount=116.0,
            client_name="Sergio Arias",
            client_address="Calle Factura 3",
            order_details=[],
        )

    def test_legacy_invoice_can_exist_without_snapshot_fields(self):
        invoice = self.build_legacy_invoice()

        self.assertIsNone(invoice.invoice_snapshot)
        self.assertIsNone(invoice.invoice_snapshot_schema_version)
        self.assertIsNone(invoice.invoice_snapshot_hash)
        self.assertIsNone(invoice.issued_at)
        self.assertIsNone(invoice.issuance_source)
        self.assertIsNone(invoice.issued_by)
        self.assertEqual(invoice.invoice_number, "JUL-2026-001")
        self.assertEqual(invoice.order_details, [])

    def test_invoice_can_store_versioned_snapshot_metadata_without_changing_legacy_fields(self):
        invoice = self.build_legacy_invoice()
        stored_snapshot = snapshot()
        stored_hash = calculate_invoice_snapshot_hash(stored_snapshot)

        invoice.invoice_snapshot = stored_snapshot
        invoice.invoice_snapshot_schema_version = 1
        invoice.invoice_snapshot_hash = stored_hash
        invoice.issued_at = datetime(2026, 7, 15, 10, 0)
        invoice.issuance_source = "manual"
        invoice.issued_by = "admin@example.com"

        self.assertEqual(invoice.invoice_snapshot["schema_version"], 1)
        self.assertEqual(invoice.invoice_snapshot_schema_version, 1)
        self.assertEqual(invoice.invoice_snapshot_hash, stored_hash)
        self.assertEqual(invoice.issuance_source, "manual")
        self.assertEqual(invoice.issued_by, "admin@example.com")
        self.assertEqual(invoice.invoice_number, "JUL-2026-001")
        self.assertEqual(invoice.pdf_path, "/api/download-invoice/invoice_JUL-2026-001.pdf")


class InvoiceSnapshotModelSourceTest(unittest.TestCase):
    def test_invoice_model_declares_nullable_snapshot_columns_without_serializer_contract_change(self):
        source = (ROOT_DIR / "src/api/models.py").read_text(encoding="utf-8")
        invoices_block = source[
            source.index("class Invoices(db.Model):"):source.index("class Favorites(db.Model):")
        ]

        self.assertIn("invoice_snapshot = db.Column(db.JSON, nullable=True)", invoices_block)
        self.assertIn(
            "invoice_snapshot_schema_version = db.Column(db.Integer, nullable=True)",
            invoices_block,
        )
        self.assertIn("invoice_snapshot_hash = db.Column(db.String(64), nullable=True)", invoices_block)
        self.assertIn("issued_at = db.Column(db.DateTime, nullable=True)", invoices_block)
        self.assertIn("issuance_source = db.Column(db.String(50), nullable=True)", invoices_block)
        self.assertIn("issued_by = db.Column(db.String(255), nullable=True)", invoices_block)
        self.assertIn('"order_details": self.order_details', invoices_block)
        self.assertNotIn('"invoice_snapshot": self.invoice_snapshot', invoices_block)


class InvoiceSnapshotMigrationTest(unittest.TestCase):
    def test_migration_adds_nullable_snapshot_columns_without_backfill(self):
        source = (
            ROOT_DIR
            / "src/migrations/versions/9a1f2d3c4b5e_add_invoice_snapshot_persistence.py"
        ).read_text(encoding="utf-8")

        for column in (
            "invoice_snapshot",
            "invoice_snapshot_schema_version",
            "invoice_snapshot_hash",
            "issued_at",
            "issuance_source",
            "issued_by",
        ):
            self.assertIn(f"op.add_column('invoices', sa.Column('{column}'", source)
            self.assertIn(f"op.drop_column('invoices', '{column}')", source)

        self.assertIn("down_revision = '8f2d9b7c1a4e'", source)
        self.assertNotRegex(source, re.compile(r"\b(update|execute|bulk_insert)\b"))


if __name__ == "__main__":
    unittest.main()

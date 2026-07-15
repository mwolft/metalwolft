import re
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/c8d0e1f2a3b4_add_invoice_type_partial_index.py"
)


def read(path):
    return (ROOT_DIR / path).read_text(encoding="utf-8")


def models_source():
    return read("src/api/models.py")


def invoices_block():
    source = models_source()
    return source[
        source.index("class Invoices(db.Model):"):source.index("class InvoiceSequence(db.Model):")
    ]


def migration_source():
    return MIGRATION_PATH.read_text(encoding="utf-8")


class InvoiceTypeModelTest(unittest.TestCase):
    def test_invoice_type_column_exists_nullable_string_20_without_default(self):
        source = invoices_block()
        column_line = "invoice_type = db.Column(db.String(20), nullable=True)"

        self.assertIn(column_line, source)
        self.assertNotIn("invoice_type = db.Column(db.String(20), nullable=False", source)
        self.assertNotRegex(column_line, re.compile(r"default|server_default"))

    def test_partial_unique_index_is_declared_on_order_id_for_ordinary_invoices(self):
        source = invoices_block()

        self.assertIn("db.Index(", source)
        self.assertIn('"uq_invoices_one_ordinary_per_order"', source)
        self.assertIn('"order_id"', source)
        self.assertIn("unique=True", source)
        self.assertIn(
            'postgresql_where=text("invoice_type = \'ordinary\' AND order_id IS NOT NULL")',
            source,
        )

    def test_order_id_is_not_made_globally_unique_and_backref_stays_legacy(self):
        source = invoices_block()

        self.assertIn("order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)", source)
        self.assertNotIn("order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, unique=True)", source)
        self.assertIn("order = db.relationship('Orders', backref='invoice', lazy=True)", source)

    def test_serializers_do_not_expose_or_require_invoice_type_yet(self):
        source = invoices_block()

        self.assertIn('"invoice_number": self.invoice_number', source)
        self.assertNotIn('"invoice_type": self.invoice_type', source)


class InvoiceTypeMigrationTest(unittest.TestCase):
    def test_migration_hangs_from_invoice_sequence_head(self):
        source = migration_source()

        self.assertIn("revision = 'c8d0e1f2a3b4'", source)
        self.assertIn("down_revision = 'b7c9d1e2f3a4'", source)

    def test_migration_adds_nullable_invoice_type_column(self):
        source = migration_source()

        self.assertIn(
            "op.add_column('invoices', sa.Column('invoice_type', sa.String(length=20), nullable=True))",
            source,
        )

    def test_migration_creates_partial_unique_index(self):
        source = migration_source()

        self.assertIn("op.create_index(", source)
        self.assertIn("'uq_invoices_one_ordinary_per_order'", source)
        self.assertIn("'invoices'", source)
        self.assertIn("['order_id']", source)
        self.assertIn("unique=True", source)
        self.assertIn(
            'postgresql_where=sa.text("invoice_type = \'ordinary\' AND order_id IS NOT NULL")',
            source,
        )

    def test_partial_index_allows_expected_non_indexed_cases_conceptually(self):
        source = migration_source()

        self.assertIn("invoice_type = 'ordinary'", source)
        self.assertIn("order_id IS NOT NULL", source)
        self.assertNotIn("invoice_type = 'corrective'", source)
        self.assertNotIn("UNIQUE(order_id, invoice_type)", source)

    def test_downgrade_drops_index_before_column(self):
        source = migration_source()

        drop_index_pos = source.index("op.drop_index('uq_invoices_one_ordinary_per_order'")
        drop_column_pos = source.index("op.drop_column('invoices', 'invoice_type')")
        self.assertLess(drop_index_pos, drop_column_pos)

    def test_migration_has_no_backfill_inserts_or_updates(self):
        source = migration_source()

        self.assertNotRegex(source, re.compile(r"\b(update|insert|execute|bulk_insert)\b", re.IGNORECASE))
        self.assertNotIn("op.alter_column('invoices', 'order_id'", source)
        self.assertNotIn("op.alter_column('orders'", source)


class InvoiceTypeCompatibilityTest(unittest.TestCase):
    def test_only_invoice_issue_service_sets_invoice_type_for_now(self):
        for relative_path in (
            "src/api/routes.py",
            "src/api/admin.py",
        ):
            source = read(relative_path)
            self.assertNotIn("invoice_type=", source)

        issue_service_source = read("src/api/invoice_issue_service.py")
        self.assertIn("invoice_type=", issue_service_source)

    def test_legacy_generators_are_not_modified(self):
        source = models_source()
        orders_block = source[
            source.index("class Orders(db.Model):"):source.index("class CheckoutSessions(db.Model):")
        ]
        invoices_generator_block = source[
            source.index("class Invoices(db.Model):"):source.index("class InvoiceSequence(db.Model):")
        ]

        self.assertIn("def generate_next_invoice_number", orders_block)
        self.assertIn("SELECT MAX(CAST(SUBSTRING(invoice_number", orders_block)
        self.assertIn("def generate_next_invoice_number", invoices_generator_block)
        self.assertIn("Invoices.invoice_number.like", invoices_generator_block)

    def test_domain_values_are_documented_not_implemented_as_sql_enum(self):
        source = invoices_block()

        self.assertIn("db.String(20)", source)
        self.assertNotIn("db.Enum", source)
        self.assertNotIn("Enum(", source)


if __name__ == "__main__":
    unittest.main()

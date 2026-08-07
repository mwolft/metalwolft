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
    / "src/migrations/versions/d9e0f1a2b3c4_make_invoice_pdf_path_nullable.py"
)


def read(relative_path):
    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


def invoices_block():
    source = read("src/api/models.py")
    return source[source.index("class Invoices(db.Model):"):source.index("class InvoiceSequence(db.Model):")]


def migration_source():
    return MIGRATION_PATH.read_text(encoding="utf-8")


class InvoicePdfPathNullableModelTest(unittest.TestCase):
    def test_invoice_pdf_path_is_nullable_without_default(self):
        source = invoices_block()

        self.assertIn("pdf_path = db.Column(db.String(255), nullable=True)", source)
        self.assertNotIn("pdf_path = db.Column(db.String(255), nullable=False)", source)
        self.assertNotIn("pdf_path = db.Column(db.String(255), default=", source)
        self.assertNotIn("server_default", source[source.index("pdf_path ="):source.index("amount =")])


class InvoicePdfPathNullableMigrationTest(unittest.TestCase):
    def test_migration_revision_and_down_revision(self):
        source = migration_source()

        self.assertIn("revision = 'd9e0f1a2b3c4'", source)
        self.assertIn("down_revision = 'c8d0e1f2a3b4'", source)

    def test_upgrade_only_makes_pdf_path_nullable(self):
        source = migration_source()

        self.assertIn("op.alter_column(", source)
        self.assertIn("'invoices'", source)
        self.assertIn("'pdf_path'", source)
        self.assertIn("existing_type=sa.String(length=255)", source)
        self.assertIn("nullable=True", source)
        self.assertNotIn("op.add_column", source)
        self.assertNotIn("op.drop_column", source)
        self.assertNotRegex(source, re.compile(r"\b(update|insert|execute|bulk_insert)\b", re.IGNORECASE))
        self.assertNotIn("invoice_snapshot", source)
        self.assertNotIn("invoice_type", source)

    def test_downgrade_restores_pdf_path_not_nullable(self):
        source = migration_source()

        downgrade_source = source[source.index("def downgrade():"):]
        self.assertIn("op.alter_column(", downgrade_source)
        self.assertIn("'pdf_path'", downgrade_source)
        self.assertIn("nullable=False", downgrade_source)


class InvoiceIssueServicePdfPathTest(unittest.TestCase):
    def test_invoice_issue_service_persists_null_pdf_path_not_empty_string(self):
        source = read("src/api/invoice_issue_service.py")

        self.assertIn("pdf_path=None", source)
        self.assertNotIn('pdf_path=""', source)
        self.assertNotIn("pdf_path=''", source)


if __name__ == "__main__":
    unittest.main()

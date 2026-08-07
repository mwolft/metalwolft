import importlib.util
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
    / "src/migrations/versions/b7c9d1e2f3a4_add_invoice_sequences_table.py"
)
FUTURE_FORMAT_EXAMPLE = "F2026000001"


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_DB_TEST_DEPENDENCIES = all(
    has_package(package)
    for package in ("flask", "flask_sqlalchemy", "sqlalchemy", "slugify")
)

if HAS_DB_TEST_DEPENDENCIES:
    from flask import Flask  # noqa: E402
    from sqlalchemy.exc import IntegrityError  # noqa: E402

    from api.models import InvoiceSequence, db  # noqa: E402


def model_source():
    return (ROOT_DIR / "src/api/models.py").read_text(encoding="utf-8")


def invoice_sequence_block():
    source = model_source()
    return source[
        source.index("class InvoiceSequence(db.Model):"):source.index("class Favorites(db.Model):")
    ]


def migration_source():
    return MIGRATION_PATH.read_text(encoding="utf-8")


class InvoiceSequenceModelSourceTest(unittest.TestCase):
    def test_model_declares_expected_table_and_columns(self):
        source = invoice_sequence_block()

        self.assertIn('__tablename__ = "invoice_sequences"', source)
        self.assertIn("id = db.Column(db.Integer, primary_key=True)", source)
        self.assertIn("series = db.Column(db.String(10), nullable=False)", source)
        self.assertIn("fiscal_year = db.Column(db.Integer, nullable=False)", source)
        self.assertIn("last_number = db.Column(", source)
        self.assertIn("nullable=False", source)
        self.assertIn("default=0", source)
        self.assertIn('server_default="0"', source)
        self.assertIn("created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())", source)
        self.assertIn("updated_at = db.Column(", source)

    def test_model_declares_unique_constraint_for_series_and_fiscal_year(self):
        source = invoice_sequence_block()

        self.assertIn("db.UniqueConstraint(", source)
        self.assertIn('"series"', source)
        self.assertIn('"fiscal_year"', source)
        self.assertIn('name="uq_invoice_sequences_series_fiscal_year"', source)

    def test_last_number_semantics_are_documented_without_formatting_logic(self):
        source = invoice_sequence_block()

        self.assertIn(
            "last_number = ultimo numero fiscal confirmado dentro de una transaccion.",
            source,
        )
        self.assertEqual(FUTURE_FORMAT_EXAMPLE, "F2026000001")
        self.assertNotIn("generate_next_invoice_number", source)

    def test_legacy_generators_are_not_modified_to_use_invoice_sequence(self):
        source = model_source()

        orders_generator = source[
            source.index("class Orders(db.Model):"):source.index("class CheckoutSessions(db.Model):")
        ]
        invoices_generator = source[
            source.index("class Invoices(db.Model):"):source.index("class InvoiceSequence(db.Model):")
        ]

        self.assertIn("def generate_next_invoice_number", orders_generator)
        self.assertIn("def generate_next_invoice_number", invoices_generator)
        self.assertNotIn("InvoiceSequence", orders_generator)
        self.assertNotIn("InvoiceSequence", invoices_generator)


class InvoiceSequenceMigrationTest(unittest.TestCase):
    def test_migration_hangs_from_invoice_snapshot_head_and_creates_only_invoice_sequences(self):
        source = migration_source()

        self.assertIn("down_revision = '9a1f2d3c4b5e'", source)
        self.assertIn("op.create_table(", source)
        self.assertIn("'invoice_sequences'", source)
        self.assertNotIn("'invoices'", source)
        self.assertNotIn("'orders'", source)

    def test_migration_columns_defaults_and_constraint(self):
        source = migration_source()

        self.assertIn("sa.Column('series', sa.String(length=10), nullable=False)", source)
        self.assertIn("sa.Column('fiscal_year', sa.Integer(), nullable=False)", source)
        self.assertIn(
            "sa.Column('last_number', sa.Integer(), server_default='0', nullable=False)",
            source,
        )
        self.assertIn("sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)", source)
        self.assertIn("sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)", source)
        self.assertIn("sa.UniqueConstraint(", source)
        self.assertIn("name='uq_invoice_sequences_series_fiscal_year'", source)

    def test_migration_downgrade_drops_only_invoice_sequences(self):
        source = migration_source()

        self.assertIn("def downgrade():", source)
        self.assertIn("op.drop_table('invoice_sequences')", source)
        self.assertNotIn("op.drop_column", source)

    def test_migration_has_no_inserts_backfill_or_updates(self):
        source = migration_source()

        self.assertNotRegex(source, re.compile(r"\b(insert|update|execute|bulk_insert)\b"))


@unittest.skipUnless(HAS_DB_TEST_DEPENDENCIES, "Flask/SQLAlchemy test dependencies are not installed.")
class InvoiceSequenceSQLiteConstraintTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        self.context = self.app.app_context()
        self.context.push()
        InvoiceSequence.__table__.create(bind=db.engine)

    def tearDown(self):
        db.session.remove()
        InvoiceSequence.__table__.drop(bind=db.engine)
        self.context.pop()

    def test_table_starts_empty_and_allows_different_years_and_series(self):
        self.assertEqual(db.session.query(InvoiceSequence).count(), 0)

        db.session.add(InvoiceSequence(series="F", fiscal_year=2026))
        db.session.add(InvoiceSequence(series="F", fiscal_year=2027))
        db.session.add(InvoiceSequence(series="R", fiscal_year=2026))
        db.session.commit()

        self.assertEqual(db.session.query(InvoiceSequence).count(), 3)

    def test_duplicate_series_and_fiscal_year_is_rejected(self):
        db.session.add(InvoiceSequence(series="F", fiscal_year=2026))
        db.session.commit()

        db.session.add(InvoiceSequence(series="F", fiscal_year=2026))
        with self.assertRaises(IntegrityError):
            db.session.commit()

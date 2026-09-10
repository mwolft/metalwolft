import importlib.util
import sys
import unittest
from decimal import Decimal
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/c9d0e1f2a3b4_add_manual_order_drafts.py"
)
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


HAS_DEPS = all(
    importlib.util.find_spec(package) is not None
    for package in ("flask", "flask_sqlalchemy", "sqlalchemy", "slugify")
)


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_MIGRATION_TEST_DEPENDENCIES = all(
    has_package(package)
    for package in ("alembic", "sqlalchemy")
)


if HAS_DEPS:
    from flask import Flask
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    from api.models import (
        Categories,
        ConfirmedOrderContext,
        ManualOrderDraft,
        ManualOrderDraftLine,
        Orders,
        Products,
        Users,
        db,
    )


if HAS_MIGRATION_TEST_DEPENDENCIES:
    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations


def load_migration_module():
    spec = importlib.util.spec_from_file_location(
        "manual_order_drafts_migration",
        MIGRATION_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(HAS_DEPS, "Flask/SQLAlchemy test dependencies are not installed.")
class ManualOrderDraftModelsTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            db.session.execute(text("PRAGMA foreign_keys=ON"))

            category = Categories(nombre="Rejas", descripcion="Tests", slug="rejas")
            user = Users(email="cliente@example.test", password="x")
            db.session.add_all([category, user])
            db.session.flush()
            product = Products(
                nombre="Reja fija Essex",
                descripcion="Modelo de pruebas",
                precio=100,
                categoria_id=category.id,
                slug="reja-fija-essex",
            )
            db.session.add(product)
            db.session.commit()
            self.user_id = user.id
            self.product_id = product.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _draft(self, **overrides):
        values = {
            "user_id": self.user_id,
            "customer_draft": {"email": "cliente@example.test"},
        }
        values.update(overrides)
        return ManualOrderDraft(**values)

    def _order(self, locator):
        order = Orders(
            user_id=self.user_id,
            locator=locator,
            total_amount=100.0,
            order_status="pendiente",
        )
        db.session.add(order)
        db.session.flush()
        return order

    def _context(self, *, order_id, draft_id):
        return ConfirmedOrderContext(
            order_id=order_id,
            source="admin_external",
            quote_snapshot={"currency": "EUR", "total_amount": 100.0, "lines": []},
            customer_snapshot={"email": "cliente@example.test"},
            payment_method="bank_transfer",
            payment_status="confirmed",
            payment_reference="TRF-REAL-001",
            payment_amount=Decimal("100.00"),
            currency="EUR",
            source_manual_draft_id=draft_id,
        )

    def test_creates_a_default_editable_draft_with_user_relationship(self):
        with self.app.app_context():
            draft = self._draft()
            db.session.add(draft)
            db.session.commit()

            self.assertEqual(draft.status, ManualOrderDraft.STATUS_DRAFT)
            self.assertTrue(draft.is_editable)
            self.assertFalse(draft.is_issued)
            self.assertFalse(draft.is_cancelled)
            self.assertEqual(draft.user.id, self.user_id)
            self.assertIn(draft, draft.user.manual_order_drafts)

    def test_user_is_required(self):
        with self.app.app_context():
            db.session.add(ManualOrderDraft())
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_payment_method_database_constraint(self):
        with self.app.app_context():
            db.session.add(self._draft(payment_method="wire"))
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_allowed_payment_methods_are_persisted(self):
        with self.app.app_context():
            drafts = [
                self._draft(payment_method=payment_method)
                for payment_method in ("bank_transfer", "cash", "external_other")
            ]
            db.session.add_all(drafts)
            db.session.commit()

            self.assertEqual(
                {draft.payment_method for draft in drafts},
                {"bank_transfer", "cash", "external_other"},
            )

    def test_lines_preserve_relationships_and_cascade_with_the_draft(self):
        with self.app.app_context():
            draft = self._draft()
            draft.lines.extend(
                (
                    ManualOrderDraftLine(
                        position=0,
                        product_id=self.product_id,
                        quantity=1,
                        alto=118,
                        ancho=122,
                        anclaje="Sin obra: con agujeros interiores",
                        color="satinado_blanco",
                        screw_option="standard",
                    ),
                    ManualOrderDraftLine(
                        position=1,
                        product_id=self.product_id,
                        quantity=2,
                        alto=100,
                        ancho=100,
                        anclaje="Sin obra: con agujeros interiores",
                        color="satinado_blanco",
                        screw_option="standard",
                    ),
                )
            )
            db.session.add(draft)
            db.session.commit()

            self.assertEqual([line.position for line in draft.lines], [0, 1])
            self.assertEqual(draft.lines[0].draft, draft)
            self.assertEqual(draft.lines[0].product.id, self.product_id)

            line_ids = [line.id for line in draft.lines]
            db.session.delete(draft)
            db.session.commit()
            self.assertEqual(
                db.session.query(ManualOrderDraftLine).filter(ManualOrderDraftLine.id.in_(line_ids)).count(),
                0,
            )

    def test_line_database_constraints_reject_invalid_quantity_and_position(self):
        with self.app.app_context():
            for position, quantity in ((0, 0), (-1, 1)):
                draft = self._draft()
                db.session.add(draft)
                db.session.flush()
                db.session.add(
                    ManualOrderDraftLine(
                        draft_id=draft.id,
                        position=position,
                        product_id=self.product_id,
                        quantity=quantity,
                    )
                )
                with self.assertRaises(IntegrityError):
                    db.session.commit()
                db.session.rollback()

    def test_duplicate_line_position_is_rejected(self):
        with self.app.app_context():
            draft = self._draft()
            db.session.add(draft)
            db.session.flush()
            for quantity in (1, 2):
                db.session.add(
                    ManualOrderDraftLine(
                        draft_id=draft.id,
                        position=0,
                        product_id=self.product_id,
                        quantity=quantity,
                    )
                )
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_issuance_key_and_issued_order_are_unique(self):
        with self.app.app_context():
            first = self._draft(issuance_key="same-issuance-key")
            second = self._draft(issuance_key="same-issuance-key")
            db.session.add_all([first, second])
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

            order = self._order("MO1001")
            db.session.add_all(
                (
                    self._draft(issued_order_id=order.id),
                    self._draft(issued_order_id=order.id),
                )
            )
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_confirmed_context_accepts_a_valid_manual_draft_foreign_key(self):
        with self.app.app_context():
            draft = self._draft()
            db.session.add(draft)
            db.session.flush()
            context = self._context(order_id=self._order("MO1002").id, draft_id=draft.id)
            db.session.add(context)
            db.session.commit()

            self.assertEqual(context.source_manual_draft.id, draft.id)
            self.assertEqual(draft.confirmed_order_context.id, context.id)

    def test_confirmed_context_rejects_an_unknown_manual_draft_foreign_key(self):
        with self.app.app_context():
            context = self._context(order_id=self._order("MO1003").id, draft_id=999999)
            db.session.add(context)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_status_helpers_distinguish_issued_and_cancelled_drafts(self):
        with self.app.app_context():
            issued = self._draft(status=ManualOrderDraft.STATUS_ISSUED)
            cancelled = self._draft(status=ManualOrderDraft.STATUS_CANCELLED)
            db.session.add_all([issued, cancelled])
            db.session.commit()

            self.assertTrue(issued.is_issued)
            self.assertFalse(issued.is_editable)
            self.assertTrue(cancelled.is_cancelled)
            self.assertFalse(cancelled.is_editable)


@unittest.skipUnless(
    HAS_MIGRATION_TEST_DEPENDENCIES,
    "Alembic/SQLAlchemy migration test dependencies are not installed.",
)
class ManualOrderDraftMigrationTest(unittest.TestCase):
    def test_upgrade_and_downgrade_preserve_the_existing_context_column(self):
        migration = load_migration_module()
        engine = sa.create_engine("sqlite:///:memory:")

        with engine.begin() as connection:
            connection.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
            connection.execute(sa.text("CREATE TABLE orders (id INTEGER PRIMARY KEY)"))
            connection.execute(sa.text("CREATE TABLE products (id INTEGER PRIMARY KEY)"))
            connection.execute(
                sa.text(
                    "CREATE TABLE confirmed_order_contexts ("
                    "id INTEGER PRIMARY KEY, "
                    "order_id INTEGER NOT NULL, "
                    "source_manual_draft_id INTEGER UNIQUE"
                    ")"
                )
            )
            context = MigrationContext.configure(connection)
            migration.op = Operations(context)

            migration.upgrade()

            inspector = sa.inspect(connection)
            self.assertIn("manual_order_drafts", inspector.get_table_names())
            self.assertIn("manual_order_draft_lines", inspector.get_table_names())

            draft_columns = {
                column["name"]: column
                for column in inspector.get_columns("manual_order_drafts")
            }
            self.assertFalse(draft_columns["user_id"]["nullable"])
            self.assertEqual(draft_columns["status"]["default"], "'draft'")

            context_columns = {
                column["name"]: column
                for column in inspector.get_columns("confirmed_order_contexts")
            }
            self.assertIn("source_manual_draft_id", context_columns)
            self.assertTrue(context_columns["source_manual_draft_id"]["nullable"])
            context_fks = inspector.get_foreign_keys("confirmed_order_contexts")
            self.assertTrue(
                any(
                    fk["referred_table"] == "manual_order_drafts"
                    and fk["constrained_columns"] == ["source_manual_draft_id"]
                    for fk in context_fks
                )
            )

            migration.downgrade()

            inspector = sa.inspect(connection)
            self.assertNotIn("manual_order_drafts", inspector.get_table_names())
            self.assertNotIn("manual_order_draft_lines", inspector.get_table_names())
            self.assertIn("source_manual_draft_id", {
                column["name"]
                for column in inspector.get_columns("confirmed_order_contexts")
            })
            self.assertFalse(inspector.get_foreign_keys("confirmed_order_contexts"))

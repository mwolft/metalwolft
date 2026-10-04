import importlib.util
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


MIGRATION_PATH = (
    ROOT_DIR
    / "src/migrations/versions/e7f8a9b0c1d2_add_product_lifecycle_fields.py"
)


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_DB_TEST_DEPENDENCIES = all(
    has_package(package)
    for package in ("alembic", "flask", "flask_sqlalchemy", "sqlalchemy", "slugify")
)

if HAS_DB_TEST_DEPENDENCIES:
    import sqlalchemy as sa  # noqa: E402
    from alembic.migration import MigrationContext  # noqa: E402
    from alembic.operations import Operations  # noqa: E402
    from flask import Flask  # noqa: E402
    from sqlalchemy.exc import IntegrityError  # noqa: E402

    from api.models import Categories, ProductImages, Products, db  # noqa: E402


def load_migration_module():
    spec = importlib.util.spec_from_file_location(
        "product_lifecycle_migration",
        MIGRATION_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def products_model_block():
    source = (ROOT_DIR / "src/api/models.py").read_text(encoding="utf-8")
    return source[
        source.index("class Products(db.Model):"):source.index("class ProductImages(db.Model):")
    ]


class ProductLifecycleModelSourceTest(unittest.TestCase):
    def test_model_declares_boolean_not_null_fields_with_safe_defaults(self):
        source = products_model_block()

        for field in ("published", "available_for_sale"):
            start = source.index(f"{field} = db.Column(")
            block = source[start:source.index(")\n", start) + 2]
            self.assertIn("db.Boolean", block)
            self.assertIn("nullable=False", block)
            self.assertIn("default=True", block)
            self.assertIn("server_default=db.true()", block)

    def test_model_declares_named_lifecycle_check_constraint(self):
        source = products_model_block()

        self.assertIn('"published OR NOT available_for_sale"', source)
        self.assertIn(
            'name="ck_products_published_available_for_sale"',
            source,
        )

    def test_public_serializer_exposes_only_sale_availability(self):
        source = products_model_block()
        serializer = source[source.index("def serialize(self):"):]

        self.assertNotIn('"published":', serializer)
        self.assertEqual(serializer.count('"available_for_sale":'), 1)
        self.assertIn(
            '"available_for_sale": self.available_for_sale',
            serializer,
        )


class ProductLifecycleMigrationSourceTest(unittest.TestCase):
    def test_migration_hangs_from_current_head_and_only_changes_products(self):
        source = MIGRATION_PATH.read_text(encoding="utf-8")

        self.assertIn("revision = 'e7f8a9b0c1d2'", source)
        self.assertIn("down_revision = 'd6e7f8a9b0c1'", source)
        self.assertNotIn("op.create_table", source)
        self.assertNotIn("'orders'", source)
        self.assertNotIn("'invoices'", source)

    def test_migration_adds_backfills_and_constrains_both_fields(self):
        source = MIGRATION_PATH.read_text(encoding="utf-8")

        self.assertIn("'published'", source)
        self.assertIn("'available_for_sale'", source)
        self.assertIn("server_default=sa.true()", source)
        self.assertIn(".values(published=True, available_for_sale=True)", source)
        self.assertIn("nullable=False", source)
        self.assertIn(
            "'ck_products_published_available_for_sale'",
            source,
        )
        self.assertIn("'published OR NOT available_for_sale'", source)

    def test_downgrade_removes_only_lifecycle_constraint_and_columns(self):
        source = MIGRATION_PATH.read_text(encoding="utf-8")
        downgrade = source[source.index("def downgrade():"):]

        self.assertIn("batch_op.drop_constraint(", downgrade)
        self.assertIn("batch_op.drop_column('available_for_sale')", downgrade)
        self.assertIn("batch_op.drop_column('published')", downgrade)
        self.assertNotIn("op.drop_table", downgrade)


@unittest.skipUnless(
    HAS_DB_TEST_DEPENDENCIES,
    "Database test dependencies are not installed.",
)
class ProductLifecycleSQLiteModelTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        self.context = self.app.app_context()
        self.context.push()
        Categories.__table__.create(bind=db.engine)
        Products.__table__.create(bind=db.engine)
        ProductImages.__table__.create(bind=db.engine)

        self.category = Categories(
            nombre="Lifecycle test",
            descripcion="Test category",
            slug="lifecycle-test",
        )
        db.session.add(self.category)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        ProductImages.__table__.drop(bind=db.engine)
        Products.__table__.drop(bind=db.engine)
        Categories.__table__.drop(bind=db.engine)
        self.context.pop()

    def make_product(self, **overrides):
        values = {
            "nombre": "Lifecycle product",
            "descripcion": "Test product",
            "precio": 100.0,
            "categoria_id": self.category.id,
        }
        values.update(overrides)
        return Products(**values)

    def test_existing_behavior_defaults_to_published_and_available(self):
        product = self.make_product()
        db.session.add(product)
        db.session.commit()

        self.assertIs(product.published, True)
        self.assertIs(product.available_for_sale, True)
        self.assertIs(product.serialize()["available_for_sale"], True)

    def test_serializer_preserves_contract_and_does_not_expose_published(self):
        product = self.make_product(available_for_sale=False)
        db.session.add(product)
        db.session.commit()

        serialized = product.serialize()

        self.assertEqual(
            set(serialized),
            {
                "id",
                "slug",
                "nombre",
                "descripcion",
                "descripcion_seo",
                "titulo_seo",
                "h1_seo",
                "precio",
                "precio_rebajado",
                "porcentaje_rebaja",
                "categoria_id",
                "category_slug",
                "subcategoria_id",
                "imagen",
                "opening_type",
                "has_abatible",
                "has_door_model",
                "es_mas_vendido",
                "es_nuevo_diseno",
                "available_for_sale",
            },
        )
        self.assertIs(serialized["available_for_sale"], False)
        self.assertEqual(serialized["opening_type"], "fixed")
        self.assertNotIn("published", serialized)

        serialized_with_images = product.serialize_with_images()
        self.assertIs(serialized_with_images["available_for_sale"], False)
        self.assertNotIn("published", serialized_with_images)

    def test_metadata_has_boolean_not_null_defaults_and_named_constraint(self):
        for column_name in ("published", "available_for_sale"):
            column = Products.__table__.c[column_name]
            self.assertIsInstance(column.type, sa.Boolean)
            self.assertFalse(column.nullable)
            self.assertIs(column.default.arg, True)
            self.assertEqual(str(column.server_default.arg).lower(), "true")

        constraint_names = {
            constraint.name for constraint in Products.__table__.constraints
        }
        self.assertIn(
            "ck_products_published_available_for_sale",
            constraint_names,
        )
        self.assertIn("ck_products_opening_type", constraint_names)

        opening_type = Products.__table__.c["opening_type"]
        self.assertFalse(opening_type.nullable)
        self.assertEqual(opening_type.default.arg, "fixed")
        self.assertEqual(str(opening_type.server_default.arg), "fixed")

    def test_published_but_unavailable_and_unpublished_unavailable_are_valid(self):
        db.session.add(self.make_product(available_for_sale=False))
        db.session.add(
            self.make_product(
                nombre="Archived lifecycle product",
                published=False,
                available_for_sale=False,
            )
        )
        db.session.commit()

        self.assertEqual(Products.query.count(), 2)

    def test_orm_validation_rejects_unpublished_available_product(self):
        db.session.add(
            self.make_product(published=False, available_for_sale=True)
        )

        with self.assertRaisesRegex(ValueError, "cannot be available for sale"):
            db.session.flush()
        db.session.rollback()

    def test_orm_validation_rejects_invalid_update(self):
        product = self.make_product()
        db.session.add(product)
        db.session.commit()

        product.published = False
        with self.assertRaisesRegex(ValueError, "cannot be available for sale"):
            db.session.flush()
        db.session.rollback()

    def test_loading_and_querying_product_does_not_trigger_validation(self):
        product = self.make_product()
        db.session.add(product)
        db.session.commit()
        product_id = product.id
        db.session.expire_all()

        loaded = db.session.get(Products, product_id)

        self.assertEqual(loaded.id, product_id)
        self.assertIs(loaded.published, True)
        self.assertIs(loaded.available_for_sale, True)

    def test_database_constraint_rejects_invalid_core_insert(self):
        with self.assertRaises(IntegrityError):
            db.session.execute(
                Products.__table__.insert().values(
                    slug="invalid-lifecycle-product",
                    nombre="Invalid lifecycle product",
                    descripcion="Invalid state",
                    precio=100.0,
                    categoria_id=self.category.id,
                    published=False,
                    available_for_sale=True,
                )
            )
            db.session.commit()
        db.session.rollback()


@unittest.skipUnless(
    HAS_DB_TEST_DEPENDENCIES,
    "Database test dependencies are not installed.",
)
class ProductLifecycleSQLiteMigrationTest(unittest.TestCase):
    def test_upgrade_backfills_and_downgrade_restores_original_schema(self):
        migration = load_migration_module()
        engine = sa.create_engine("sqlite:///:memory:")

        with engine.begin() as connection:
            connection.execute(
                sa.text(
                    "CREATE TABLE products ("
                    "id INTEGER PRIMARY KEY, "
                    "nombre VARCHAR(100) NOT NULL"
                    ")"
                )
            )
            connection.execute(
                sa.text("INSERT INTO products (id, nombre) VALUES (1, 'Existing')")
            )
            context = MigrationContext.configure(connection)
            migration.op = Operations(context)

            migration.upgrade()

            inspector = sa.inspect(connection)
            columns = {
                column["name"]: column
                for column in inspector.get_columns("products")
            }
            self.assertFalse(columns["published"]["nullable"])
            self.assertFalse(columns["available_for_sale"]["nullable"])
            self.assertIsNotNone(columns["published"]["default"])
            self.assertIsNotNone(columns["available_for_sale"]["default"])
            row = connection.execute(
                sa.text(
                    "SELECT published, available_for_sale FROM products WHERE id = 1"
                )
            ).one()
            self.assertEqual(tuple(row), (1, 1))
            checks = {
                constraint["name"]: constraint["sqltext"]
                for constraint in inspector.get_check_constraints("products")
            }
            self.assertIn("ck_products_published_available_for_sale", checks)

            connection.execute(
                sa.text("INSERT INTO products (id, nombre) VALUES (2, 'Defaulted')")
            )
            defaulted_row = connection.execute(
                sa.text(
                    "SELECT published, available_for_sale FROM products WHERE id = 2"
                )
            ).one()
            self.assertEqual(tuple(defaulted_row), (1, 1))

            savepoint = connection.begin_nested()
            try:
                with self.assertRaises(IntegrityError):
                    connection.execute(
                        sa.text(
                            "INSERT INTO products "
                            "(id, nombre, published, available_for_sale) "
                            "VALUES (3, 'Invalid', 0, 1)"
                        )
                    )
            finally:
                savepoint.rollback()

            migration.downgrade()

            remaining_columns = {
                column["name"]
                for column in sa.inspect(connection).get_columns("products")
            }
            self.assertEqual(remaining_columns, {"id", "nombre"})


if __name__ == "__main__":
    unittest.main()

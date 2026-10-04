import ast
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "src/migrations/versions/f5c6d7e8a9b0_add_product_card_copy.py"
MODEL = ROOT / "src/api/models.py"
ADMIN = ROOT / "src/api/admin.py"


class ProductCardCopyContractTest(unittest.TestCase):
    def test_migration_seeds_only_approved_copy(self):
        source = MIGRATION.read_text(encoding="utf-8")
        tree = ast.parse(source)
        assignment = next(
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "CARD_COPY" for target in node.targets)
        )
        copy = ast.literal_eval(assignment.value)

        self.assertEqual(len(copy), 24)
        self.assertNotIn("reja-fija-lancaster", copy)
        self.assertNotIn("reja-abatible-idaho", copy)
        self.assertEqual(copy["reja-fija-albany"], "Líneas horizontales · Estilo moderno")
        self.assertEqual(copy["reja-puerta-maryland"], "Para puertas · Perfil cuadrado")
        self.assertIn('down_revision = "e2f3a4b5c6d7"', source)
        self.assertIn('.where(products.c.slug == "reja-fija-albany")', source)
        self.assertIn('.values(best_seller_badge_variant="most_sold")', source)

    def test_model_and_admin_expose_editable_fields(self):
        model = MODEL.read_text(encoding="utf-8")
        admin = ADMIN.read_text(encoding="utf-8")
        product = model[model.index("class Products(db.Model):"):model.index("class ProductImages(db.Model):")]
        view = admin[admin.index("class ProductAdminView(SafeModelView):"):admin.index("def _find_order_ordinary_invoice")]

        self.assertIn('descripcion_card = db.Column(db.Text, nullable=True)', product)
        self.assertIn('"descripcion_card": self.descripcion_card', product)
        self.assertIn('"best_seller_badge_variant": self.best_seller_badge_variant', product)
        self.assertIn("'descripcion_card'", view)
        self.assertIn("'best_seller_badge_variant'", view)
        self.assertIn("('most_sold', 'Más vendida')", view)
        self.assertIn("form_choices = {", view)

    def test_migration_upgrade_and_downgrade_in_memory(self):
        import sqlalchemy as sa
        from alembic.migration import MigrationContext
        from alembic.operations import Operations

        spec = importlib.util.spec_from_file_location("product_card_copy_migration", MIGRATION)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        engine = sa.create_engine("sqlite:///:memory:")
        metadata = sa.MetaData()
        products = sa.Table(
            "products", metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("slug", sa.String(120), nullable=False),
            sa.Column("descripcion", sa.Text, nullable=False),
            sa.Column("descripcion_seo", sa.Text),
        )
        metadata.create_all(engine)

        with engine.begin() as connection:
            connection.execute(products.insert(), [
                {"id": 1, "slug": "reja-fija-albany", "descripcion": "técnica", "descripcion_seo": "SEO"},
                {"id": 2, "slug": "reja-fija-essex", "descripcion": "técnica", "descripcion_seo": "SEO"},
                {"id": 3, "slug": "reja-fija-lancaster", "descripcion": "técnica", "descripcion_seo": "SEO"},
                {"id": 4, "slug": "reja-abatible-idaho", "descripcion": "técnica", "descripcion_seo": "SEO"},
            ])
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                migration.upgrade()

            rows = connection.execute(sa.text(
                "SELECT slug, descripcion, descripcion_seo, descripcion_card, "
                "best_seller_badge_variant FROM products ORDER BY id"
            )).fetchall()
            self.assertEqual(rows[0][3:], ("Líneas horizontales · Estilo moderno", "most_sold"))
            self.assertEqual(rows[1][3:], ("Líneas verticales · Estilo clásico", "top_sales"))
            self.assertEqual(rows[2][3:], (None, "top_sales"))
            self.assertEqual(rows[3][3:], (None, "top_sales"))
            self.assertTrue(all(row[1:3] == ("técnica", "SEO") for row in rows))

            with Operations.context(context):
                migration.downgrade()
            columns = {column["name"] for column in sa.inspect(connection).get_columns("products")}
            self.assertNotIn("descripcion_card", columns)
            self.assertNotIn("best_seller_badge_variant", columns)


if __name__ == "__main__":
    unittest.main()

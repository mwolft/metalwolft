import importlib.util
import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

HAS_DEPS = all(importlib.util.find_spec(name) for name in ("flask", "flask_sqlalchemy", "sqlalchemy", "slugify"))

if HAS_DEPS:
    from flask import Flask
    from flask_jwt_extended import JWTManager, create_access_token
    from sqlalchemy import create_engine, text
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from api.models import Categories, ProductImages, Products, db
    from api.routes import api
    from api.product_image_order_service import (
        ProductImageOrderError, image_order_entries, replace_additional_images,
        save_product_image_order,
    )


@unittest.skipUnless(HAS_DEPS, "Product image test dependencies are unavailable")
class ProductImageOrderTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
        self.app.config["JWT_SECRET_KEY"] = "isolated-product-image-test-key"
        db.init_app(self.app)
        JWTManager(self.app)
        self.app.register_blueprint(api, url_prefix="/api")
        self.context = self.app.app_context()
        self.context.push()
        Categories.__table__.create(bind=db.engine)
        Products.__table__.create(bind=db.engine)
        ProductImages.__table__.create(bind=db.engine)
        category = Categories(nombre="Rejas", slug="rejas")
        db.session.add(category)
        db.session.flush()
        product = Products(nombre="Modelo", slug="modelo", descripcion="Prueba", precio=100,
                           categoria_id=category.id, imagen="https://example.test/main.jpg")
        db.session.add(product)
        db.session.flush()
        self.product_id = product.id
        db.session.add_all([
            ProductImages(product_id=product.id, image_url=f"https://example.test/{name}.jpg")
            for name in ("a", "b", "c", "d")
        ])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        ProductImages.__table__.drop(bind=db.engine)
        Products.__table__.drop(bind=db.engine)
        Categories.__table__.drop(bind=db.engine)
        self.context.pop()

    def product(self):
        return db.session.get(Products, self.product_id)

    def test_promote_additional_image_without_losing_old_primary(self):
        product = self.product()
        entries = image_order_entries(product)
        keys = [entries[2]["key"], entries[0]["key"], entries[1]["key"], entries[3]["key"], entries[4]["key"]]
        save_product_image_order(db.session, self.product_id, keys)
        product = self.product()
        self.assertEqual(product.imagen, "https://example.test/b.jpg")
        self.assertEqual([entry["url"] for entry in image_order_entries(product)],
                         ["https://example.test/b.jpg", "https://example.test/main.jpg",
                          "https://example.test/a.jpg", "https://example.test/c.jpg",
                          "https://example.test/d.jpg"])
        self.assertEqual(len(product.serialize_with_images()["images"]), 4)
        self.assertEqual(ProductImages.query.count(), 5)

    def test_rejects_missing_or_duplicate_keys_without_mutation(self):
        entries = image_order_entries(self.product())
        with self.assertRaises(ProductImageOrderError):
            save_product_image_order(db.session, self.product_id, [entries[0]["key"]] * len(entries))
        db.session.rollback()
        self.assertEqual(self.product().imagen, "https://example.test/main.jpg")

    def test_rejects_primary_url_longer_than_product_column(self):
        long_url = "https://example.test/" + "x" * 190
        row = ProductImages(product_id=self.product_id, image_url=long_url)
        db.session.add(row)
        db.session.commit()
        keys = [entry["key"] for entry in image_order_entries(self.product())]
        with self.assertRaises(ProductImageOrderError):
            save_product_image_order(db.session, self.product_id, [str(row.id)] + [key for key in keys if key != str(row.id)])
        db.session.rollback()
        self.assertEqual(self.product().imagen, "https://example.test/main.jpg")

    def test_explicit_edit_preserves_rows_and_positions(self):
        entries = image_order_entries(self.product())
        save_product_image_order(db.session, self.product_id, [entry["key"] for entry in entries])
        before = {row.image_url: (row.id, row.position) for row in ProductImages.query.all()}
        replace_additional_images(db.session, self.product(),
                                  ["https://example.test/a.jpg", "https://example.test/b.jpg",
                                   "https://example.test/c.jpg", "https://example.test/d.jpg"])
        db.session.commit()
        after = {row.image_url: (row.id, row.position) for row in ProductImages.query.all()}
        self.assertEqual(before, after)

    def test_duplicate_main_url_is_not_serialized_twice(self):
        db.session.add(ProductImages(product_id=self.product_id, image_url="https://example.test/main.jpg"))
        db.session.commit()
        self.assertEqual(len(self.product().serialize_with_images()["images"]), 4)

    def test_category_and_detail_return_the_saved_order(self):
        entries = image_order_entries(self.product())
        save_product_image_order(db.session, self.product_id,
                                 [entries[3]["key"], entries[0]["key"], entries[4]["key"],
                                  entries[2]["key"], entries[1]["key"]])
        category = self.client.get("/api/category/rejas/products")
        detail = self.client.get("/api/rejas/modelo")
        self.assertEqual((category.status_code, detail.status_code), (200, 200))
        for payload in (category.get_json()[0], detail.get_json()):
            self.assertEqual(payload["imagen"], "https://example.test/c.jpg")
            self.assertEqual([item["image_url"] for item in payload["images"]],
                             ["https://example.test/main.jpg", "https://example.test/d.jpg",
                              "https://example.test/b.jpg", "https://example.test/a.jpg"])

    def test_authenticated_product_edit_keeps_order_and_row_ids(self):
        entries = image_order_entries(self.product())
        save_product_image_order(db.session, self.product_id, [entry["key"] for entry in entries])
        before = {row.image_url: (row.id, row.position) for row in ProductImages.query.all()}
        token = create_access_token(identity="1", additional_claims={"is_admin": True})
        response = self.client.put(
            f"/api/products/{self.product_id}",
            json={"nombre": "Modelo editado", "images": [url for url in before if url != self.product().imagen]},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        after = {row.image_url: (row.id, row.position) for row in ProductImages.query.all()}
        self.assertEqual(before, after)

    def test_changing_primary_via_api_preserves_previous_photo(self):
        token = create_access_token(identity="1", additional_claims={"is_admin": True})
        response = self.client.put(
            f"/api/products/{self.product_id}",
            json={"imagen": "https://example.test/a.jpg", "images": ["https://example.test/b.jpg"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["imagen"], "https://example.test/a.jpg")
        self.assertIn("https://example.test/main.jpg",
                      [image["image_url"] for image in response.get_json()["images"]])

    def test_product_with_single_primary_image(self):
        ProductImages.query.filter_by(product_id=self.product_id).delete()
        db.session.commit()
        self.assertEqual(len(image_order_entries(self.product())), 1)
        detail = self.client.get("/api/rejas/modelo")
        self.assertEqual(detail.get_json()["imagen"], "https://example.test/main.jpg")
        self.assertEqual(detail.get_json()["images"], [])

    def test_additive_migration_preserves_historical_rows(self):
        from migrations.versions import d9f5a1b2c3d4_add_product_image_position as migration
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE product_images (id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL, image_url VARCHAR(255) NOT NULL)"))
            conn.execute(text("INSERT INTO product_images (id, product_id, image_url) VALUES (7, 3, 'https://example.test/old.jpg')"))
            context = MigrationContext.configure(conn)
            original_op = migration.op
            migration.op = Operations(context)
            try:
                migration.upgrade()
            finally:
                migration.op = original_op
            self.assertEqual(conn.execute(text("SELECT id, product_id, image_url, position FROM product_images")).one(),
                             (7, 3, "https://example.test/old.jpg", None))
        engine.dispose()


if __name__ == "__main__":
    unittest.main()

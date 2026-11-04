import base64
import datetime
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

HAS_DEPS = all(importlib.util.find_spec(name) for name in ("flask", "flask_admin", "flask_sqlalchemy"))

if HAS_DEPS:
    from flask import Flask
    from flask_admin import Admin
    from api.models import Categories, ProductImages, Products, Subcategories, db
    try:
        ZoneInfo("Europe/Madrid")
    except ZoneInfoNotFoundError:
        # Windows test environments may lack tzdata; this route does not use dates.
        with patch("zoneinfo.ZoneInfo", return_value=datetime.timezone.utc):
            import api.admin as admin_module
    else:
        import api.admin as admin_module


@unittest.skipUnless(HAS_DEPS, "Flask-Admin test dependencies are unavailable")
class ProductImageAdminTest(unittest.TestCase):
    def setUp(self):
        self.user_patch = patch.object(admin_module, "ADMIN_USER", "isolated-admin")
        self.password_patch = patch.object(admin_module, "ADMIN_PW", "isolated-password")
        self.user_patch.start()
        self.password_patch.start()
        self.app = Flask(
            __name__, template_folder=str(SRC_DIR / "templates"),
            static_folder=str(SRC_DIR / "static"),
        )
        self.app.config.update(
            SECRET_KEY="isolated-image-admin-test",
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        )
        db.init_app(self.app)
        admin = Admin(self.app, url="/admin", template_mode="bootstrap3")
        admin.add_view(admin_module.ProductAdminView(
            Products, db.session, name="Productos", endpoint="products",
        ))
        self.context = self.app.app_context()
        self.context.push()
        Categories.__table__.create(db.engine)
        Subcategories.__table__.create(db.engine)
        Products.__table__.create(db.engine)
        ProductImages.__table__.create(db.engine)
        category = Categories(nombre="Rejas", slug="rejas")
        db.session.add(category)
        db.session.flush()
        product = Products(
            nombre="Prueba", slug="prueba", descripcion="Prueba", precio=100,
            categoria_id=category.id, imagen="https://example.test/main.jpg",
        )
        db.session.add(product)
        db.session.flush()
        db.session.add(ProductImages(
            product_id=product.id, image_url="https://example.test/second.jpg",
        ))
        db.session.commit()
        self.product_id = product.id
        self.image_id = ProductImages.query.first().id
        self.client = self.app.test_client()
        credentials = base64.b64encode(b"isolated-admin:isolated-password").decode("ascii")
        self.auth = {"Authorization": f"Basic {credentials}"}
        self.path = f"/admin/products/order-images/{self.product_id}"

    def tearDown(self):
        db.session.remove()
        ProductImages.__table__.drop(db.engine)
        Products.__table__.drop(db.engine)
        Subcategories.__table__.drop(db.engine)
        Categories.__table__.drop(db.engine)
        self.context.pop()
        self.password_patch.stop()
        self.user_patch.stop()

    def test_requires_admin_credentials(self):
        self.assertEqual(self.client.get(self.path).status_code, 401)
        self.assertEqual(self.client.post(self.path, data={}).status_code, 401)

    def test_order_page_and_catalog_link(self):
        page = self.client.get(self.path, headers=self.auth)
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Guardar orden", page.data)
        self.assertIn(b"https://example.test/main.jpg", page.data)
        self.assertIn(b"https://example.test/second.jpg", page.data)
        catalog = self.client.get("/admin/products/", headers=self.auth)
        self.assertEqual(catalog.status_code, 200)
        self.assertIn(f"/admin/products/order-images/{self.product_id}".encode(), catalog.data)

    def test_csrf_rejection_and_persisted_reorder(self):
        self.client.get(self.path, headers=self.auth)
        invalid = self.client.post(self.path, headers=self.auth, data={
            "csrf_token": "invalid", "image_order": [str(self.image_id), "primary"],
        })
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(db.session.get(Products, self.product_id).imagen, "https://example.test/main.jpg")
        with self.client.session_transaction() as user_session:
            csrf = user_session["product_image_order_csrf"]
        saved = self.client.post(self.path, headers=self.auth, data={
            "csrf_token": csrf, "image_order": [str(self.image_id), "primary"],
        })
        self.assertEqual(saved.status_code, 302)
        self.assertEqual(db.session.get(Products, self.product_id).imagen, "https://example.test/second.jpg")
        urls = [image.image_url for image in ProductImages.query.all()]
        self.assertCountEqual(urls, ["https://example.test/main.jpg", "https://example.test/second.jpg"])


if __name__ == "__main__":
    unittest.main()

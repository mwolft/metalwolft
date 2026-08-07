import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ENDPOINT_DEPS = all(
    has_package(package)
    for package in (
        "flask",
        "flask_jwt_extended",
        "flask_sqlalchemy",
        "sqlalchemy",
        "slugify",
    )
)


if HAS_ENDPOINT_DEPS:
    from flask import Flask

    from api.models import Categories, Products, db
    from api.routes import api


@unittest.skipUnless(
    HAS_ENDPOINT_DEPS,
    "Flask/JWT/SQLAlchemy test dependencies are not installed.",
)
class ProductLifecycleSitemapTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.app.register_blueprint(api, url_prefix="/api")

        with self.app.app_context():
            Categories.__table__.create(bind=db.engine)
            Products.__table__.create(bind=db.engine)

            category = Categories(
                nombre="Rejas sitemap",
                descripcion="Sitemap lifecycle tests",
                slug="rejas-sitemap",
            )
            db.session.add(category)
            db.session.flush()
            db.session.add_all(
                [
                    Products(
                        nombre="Reja disponible sitemap",
                        slug="reja-disponible-sitemap",
                        descripcion="Disponible",
                        precio=100.0,
                        categoria_id=category.id,
                        published=True,
                        available_for_sale=True,
                    ),
                    Products(
                        nombre="Reja retirada sitemap",
                        slug="reja-retirada-sitemap",
                        descripcion="Retirada",
                        precio=110.0,
                        categoria_id=category.id,
                        published=True,
                        available_for_sale=False,
                    ),
                    Products(
                        nombre="Reja no publicada sitemap",
                        slug="reja-no-publicada-sitemap",
                        descripcion="No publicada",
                        precio=120.0,
                        categoria_id=category.id,
                        published=False,
                        available_for_sale=False,
                    ),
                ]
            )
            db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            Products.__table__.drop(bind=db.engine)
            Categories.__table__.drop(bind=db.engine)

    def test_sitemap_contract_contains_all_and_only_published_products(self):
        response = self.client.get("/api/sitemap/products")

        self.assertEqual(response.status_code, 200)
        products = response.get_json()
        self.assertEqual(
            [product["slug"] for product in products],
            ["reja-disponible-sitemap", "reja-retirada-sitemap"],
        )
        self.assertEqual(
            products,
            [
                {
                    "category_slug": "rejas-sitemap",
                    "slug": "reja-disponible-sitemap",
                },
                {
                    "category_slug": "rejas-sitemap",
                    "slug": "reja-retirada-sitemap",
                },
            ],
        )
        self.assertEqual(len(products), len({tuple(product.items()) for product in products}))

    def test_sitemap_contract_does_not_expose_lifecycle_or_commercial_fields(self):
        products = self.client.get("/api/sitemap/products").get_json()

        for product in products:
            self.assertEqual(set(product), {"category_slug", "slug"})
            self.assertNotIn("published", product)
            self.assertNotIn("available_for_sale", product)

    def test_sitemap_does_not_use_discovery_catalog_query(self):
        with patch(
            "api.routes.publicly_discoverable_products_query",
            side_effect=AssertionError("Discovery catalog must not build the sitemap"),
        ):
            response = self.client.get("/api/sitemap/products")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 2)


if __name__ == "__main__":
    unittest.main()

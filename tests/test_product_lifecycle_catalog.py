import importlib.util
import json
import sys
import unittest
from pathlib import Path


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

    from api.models import Categories, ProductImages, Products, Subcategories, db
    from api.routes import api
    from api.seo_routes import seo_bp
    from api.product_lifecycle import resolve_publicly_accessible_product_by_slugs


@unittest.skipUnless(
    HAS_ENDPOINT_DEPS,
    "Flask/JWT/SQLAlchemy test dependencies are not installed.",
)
class ProductLifecyclePublicCatalogTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.app.register_blueprint(api, url_prefix="/api")
        self.app.register_blueprint(seo_bp)

        with self.app.app_context():
            Categories.__table__.create(bind=db.engine)
            Subcategories.__table__.create(bind=db.engine)
            Products.__table__.create(bind=db.engine)
            ProductImages.__table__.create(bind=db.engine)

            category = Categories(
                nombre="Rejas publicas",
                descripcion="Catalog lifecycle tests",
                slug="rejas-publicas",
            )
            db.session.add(category)
            db.session.flush()

            available = Products(
                nombre="Reja disponible",
                slug="reja-disponible",
                descripcion="Disponible",
                precio=100.0,
                categoria_id=category.id,
                sort_order=2,
                published=True,
                available_for_sale=True,
            )
            unavailable = Products(
                nombre="Reja retirada",
                slug="reja-retirada",
                descripcion="Retirada",
                precio=110.0,
                categoria_id=category.id,
                sort_order=1,
                published=True,
                available_for_sale=False,
            )
            unpublished = Products(
                nombre="Reja borrador",
                slug="reja-borrador",
                descripcion="Borrador",
                precio=120.0,
                categoria_id=category.id,
                sort_order=0,
                published=False,
                available_for_sale=False,
            )
            db.session.add_all([available, unavailable, unpublished])
            db.session.flush()
            db.session.add(
                ProductImages(
                    product_id=available.id,
                    image_url="https://example.test/reja-disponible.jpg",
                )
            )
            db.session.commit()

            self.category_id = category.id
            self.available_id = available.id
            self.unavailable_id = unavailable.id
            self.unpublished_id = unpublished.id

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            ProductImages.__table__.drop(bind=db.engine)
            Products.__table__.drop(bind=db.engine)
            Subcategories.__table__.drop(bind=db.engine)
            Categories.__table__.drop(bind=db.engine)

    def assert_public_product_shape(self, product):
        self.assertNotIn("published", product)
        self.assertIn("available_for_sale", product)
        self.assertIn("precio", product)
        self.assertIn("categoria_id", product)
        self.assertIn("category_slug", product)

    def test_general_catalog_returns_only_discoverable_products(self):
        response = self.client.get("/api/products")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Total-Count"], "1")
        products = response.get_json()
        self.assertEqual([product["slug"] for product in products], ["reja-disponible"])
        self.assertEqual(products[0]["images"][0]["image_url"], "https://example.test/reja-disponible.jpg")
        self.assert_public_product_shape(products[0])

    def test_general_catalog_keeps_category_filter_and_response_shape(self):
        response = self.client.get(f"/api/products?category_id={self.category_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Total-Count"], "1")
        self.assertEqual(len(response.get_json()), 1)
        self.assertEqual(response.get_json()[0]["categoria_id"], self.category_id)

    def test_category_catalog_returns_only_discoverable_products_in_existing_order(self):
        response = self.client.get("/api/category/rejas-publicas/products")

        self.assertEqual(response.status_code, 200)
        products = response.get_json()
        self.assertEqual([product["slug"] for product in products], ["reja-disponible"])
        self.assert_public_product_shape(products[0])

    def test_category_counts_include_only_discoverable_products(self):
        response = self.client.get("/api/categories")

        self.assertEqual(response.status_code, 200)
        categories = response.get_json()
        category = next(item for item in categories if item["id"] == self.category_id)
        self.assertEqual(category["product_count"], 1)

    def test_slug_detail_returns_published_available_product(self):
        response = self.client.get("/api/rejas-publicas/reja-disponible")

        self.assertEqual(response.status_code, 200)
        product = response.get_json()
        self.assertIs(product["available_for_sale"], True)
        self.assert_public_product_shape(product)

    def test_slug_detail_keeps_published_unavailable_product_accessible(self):
        response = self.client.get("/api/rejas-publicas/reja-retirada")

        self.assertEqual(response.status_code, 200)
        product = response.get_json()
        self.assertIs(product["available_for_sale"], False)
        self.assert_public_product_shape(product)

    def test_slug_detail_hides_unpublished_product_like_missing_product(self):
        hidden = self.client.get("/api/rejas-publicas/reja-borrador")
        missing = self.client.get("/api/rejas-publicas/no-existe")

        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(hidden.get_json(), missing.get_json())

    def test_shared_public_product_resolver_uses_category_and_publication_rules(self):
        category, available = resolve_publicly_accessible_product_by_slugs(
            "rejas-publicas",
            "reja-disponible",
        )
        _, withdrawn = resolve_publicly_accessible_product_by_slugs(
            "rejas-publicas",
            "reja-retirada",
        )
        _, unpublished = resolve_publicly_accessible_product_by_slugs(
            "rejas-publicas",
            "reja-borrador",
        )
        _, missing = resolve_publicly_accessible_product_by_slugs(
            "rejas-publicas",
            "no-existe",
        )
        unknown_category, unknown_product = (
            resolve_publicly_accessible_product_by_slugs(
                "mi-cuenta",
                "pedidos",
            )
        )

        self.assertEqual(category.id, self.category_id)
        self.assertEqual(available.id, self.available_id)
        self.assertEqual(withdrawn.id, self.unavailable_id)
        self.assertIsNone(unpublished)
        self.assertIsNone(missing)
        self.assertIsNone(unknown_category)
        self.assertIsNone(unknown_product)

    def test_id_detail_keeps_published_unavailable_product_accessible(self):
        response = self.client.get(f"/api/products/{self.unavailable_id}")

        self.assertEqual(response.status_code, 200)
        product = response.get_json()
        self.assertIs(product["available_for_sale"], False)
        self.assert_public_product_shape(product)

    def test_id_detail_hides_unpublished_product_like_missing_product(self):
        hidden = self.client.get(f"/api/products/{self.unpublished_id}")
        missing = self.client.get("/api/products/999999")

        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(hidden.get_json(), missing.get_json())

    def test_seo_detail_keeps_withdrawn_product_and_hides_unpublished_product(self):
        withdrawn = self.client.get("/api/seo/rejas-publicas/reja-retirada")
        hidden = self.client.get("/api/seo/rejas-publicas/reja-borrador")
        missing = self.client.get("/api/seo/rejas-publicas/no-existe")

        self.assertEqual(withdrawn.status_code, 200)
        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(hidden.get_json(), missing.get_json())

    def test_seo_product_schema_excludes_unverified_ratings_and_reviews(self):
        response = self.client.get("/api/seo/rejas-publicas/reja-disponible")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        schema = json.loads(json.dumps(payload["json_ld"]))
        serialized_schema = json.dumps(schema)

        for unsupported_rating_field in (
            "AggregateRating",
            "Review",
            "Rating",
            "aggregateRating",
            "review",
            "reviewCount",
            "ratingValue",
            "reviewRating",
            "bestRating",
            "reviewBody",
            "datePublished",
            "Cliente verificado",
            "Muy satisfecho con la compra",
        ):
            self.assertNotIn(unsupported_rating_field, serialized_schema)

        self.assertEqual(schema["@type"], "Product")
        self.assertEqual(schema["sku"], "reja-disponible")
        self.assertEqual(
            payload["canonical"],
            "https://www.metalwolft.com/rejas-publicas/reja-disponible",
        )
        self.assertEqual(payload["robots"], "index, follow")

    def test_seo_product_offer_excludes_unverified_commercial_claims(self):
        response = self.client.get("/api/seo/rejas-publicas/reja-disponible")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        schema = json.loads(json.dumps(payload["json_ld"]))
        serialized_schema = json.dumps(schema)

        for unsupported_commercial_claim in (
            "availability",
            "InStock",
            "priceValidUntil",
            "shippingDetails",
            "OfferShippingDetails",
            "shippingRate",
            "MonetaryAmount",
            "shippingDestination",
            "DefinedRegion",
            "deliveryTime",
            "ShippingDeliveryTime",
            "handlingTime",
            "transitTime",
            "QuantitativeValue",
            "hasMerchantReturnPolicy",
            "MerchantReturnPolicy",
            "applicableCountry",
            "returnPolicyCategory",
            "merchantReturnDays",
            "returnMethod",
            "returnFees",
            "FreeReturn",
            "refundType",
        ):
            self.assertNotIn(unsupported_commercial_claim, serialized_schema)

        for removed_rating_claim in (
            "AggregateRating",
            "Review",
            "aggregateRating",
            "reviewCount",
            "ratingValue",
            "reviewRating",
            "reviewBody",
        ):
            self.assertNotIn(removed_rating_claim, serialized_schema)

        self.assertEqual(schema["@type"], "Product")
        self.assertEqual(schema["sku"], "reja-disponible")
        self.assertEqual(
            payload["canonical"],
            "https://www.metalwolft.com/rejas-publicas/reja-disponible",
        )
        self.assertEqual(payload["robots"], "index, follow")

    def test_seo_product_schema_excludes_non_reproducible_offer(self):
        response = self.client.get("/api/seo/rejas-publicas/reja-disponible")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        schema = json.loads(json.dumps(payload["json_ld"]))
        serialized_schema = json.dumps(schema)

        self.assertNotIn("offers", schema)
        for unsupported_offer_field in (
            "price",
            "priceCurrency",
            "lowPrice",
            "highPrice",
        ):
            self.assertNotIn(f'"{unsupported_offer_field}"', serialized_schema)
        for unsupported_offer_type in ("Offer", "AggregateOffer"):
            self.assertNotIn(
                f'"@type": "{unsupported_offer_type}"',
                serialized_schema,
            )

        self.assertEqual(schema["@context"], "https://schema.org/")
        self.assertEqual(schema["@type"], "Product")
        self.assertEqual(schema["name"], "Reja disponible")
        self.assertEqual(schema["description"], "Disponible")
        self.assertIsInstance(schema["image"], list)
        self.assertEqual(schema["sku"], "reja-disponible")
        self.assertEqual(schema["brand"]["@type"], "Brand")
        self.assertEqual(schema["brand"]["name"], "Metal Wolft")
        self.assertEqual(
            payload["canonical"],
            "https://www.metalwolft.com/rejas-publicas/reja-disponible",
        )
        self.assertEqual(payload["robots"], "index, follow")

    def test_seo_product_schema_excludes_internal_id_as_mpn(self):
        response = self.client.get("/api/seo/rejas-publicas/reja-disponible")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        schema = json.loads(json.dumps(payload["json_ld"]))
        serialized_schema = json.dumps(schema)

        self.assertNotIn("mpn", schema)
        self.assertNotIn('"mpn"', serialized_schema)
        self.assertEqual(
            set(schema),
            {
                "@context",
                "@type",
                "@id",
                "name",
                "description",
                "image",
                "sku",
                "brand",
            },
        )
        self.assertEqual(schema["@type"], "Product")
        self.assertEqual(schema["name"], "Reja disponible")
        self.assertEqual(schema["description"], "Disponible")
        self.assertIsInstance(schema["image"], list)
        self.assertEqual(schema["sku"], "reja-disponible")
        self.assertEqual(schema["brand"]["@type"], "Brand")
        self.assertEqual(schema["brand"]["name"], "Metal Wolft")
        self.assertEqual(
            payload["canonical"],
            "https://www.metalwolft.com/rejas-publicas/reja-disponible",
        )
        self.assertEqual(payload["robots"], "index, follow")


if __name__ == "__main__":
    unittest.main()

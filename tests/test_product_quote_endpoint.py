import importlib.util
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
    from flask_jwt_extended import JWTManager

    from api.models import Cart, Categories, OrderDetails, Orders, Products, db
    from api.routes import _build_order_details_from_checkout_quote, api
    from api.utils import (
        ANCHORAGE_FRONT_PLATES,
        ANCHORAGE_INTERIOR_HOLES,
        DEFAULT_CONFIGURATOR_SCREW_OPTION,
        SCREW_OPTION_LONG_150,
    )


@unittest.skipUnless(
    HAS_ENDPOINT_DEPS,
    "Flask/JWT/SQLAlchemy test dependencies are not installed.",
)
class ProductQuoteEndpointTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        JWTManager(self.app)
        db.init_app(self.app)
        self.app.register_blueprint(api, url_prefix="/api")

        with self.app.app_context():
            db.create_all()
            category = Categories(
                nombre="Rejas quote",
                descripcion="Quote endpoint tests",
                slug="rejas-quote",
            )
            db.session.add(category)
            db.session.flush()
            products = [
                Products(
                    nombre="Reja disponible",
                    descripcion="Producto disponible",
                    precio=100.0,
                    categoria_id=category.id,
                    slug="reja-disponible",
                ),
                Products(
                    nombre="Reja retirada",
                    descripcion="Producto retirado",
                    precio=100.0,
                    categoria_id=category.id,
                    slug="reja-retirada",
                    published=True,
                    available_for_sale=False,
                ),
                Products(
                    nombre="Reja no publicada",
                    descripcion="Producto no publicado",
                    precio=100.0,
                    categoria_id=category.id,
                    slug="reja-no-publicada",
                    published=False,
                    available_for_sale=False,
                ),
            ]
            db.session.add_all(products)
            db.session.commit()
            self.available_product_id = products[0].id
            self.unavailable_product_id = products[1].id
            self.unpublished_product_id = products[2].id

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def quote_payload(self, **overrides):
        payload = {
            "alto": 30,
            "ancho": 30,
            "anclaje": ANCHORAGE_FRONT_PLATES,
            "color": "satinado_blanco",
            "quantity": 2,
        }
        payload.update(overrides)
        return payload

    def post_quote(self, product_id, payload=None):
        return self.client.post(
            f"/api/products/{product_id}/quote",
            json=self.quote_payload() if payload is None else payload,
        )

    def get_configuration(self, product_id):
        return self.client.get(f"/api/products/{product_id}/configuration")

    def test_configuration_returns_authoritative_rules(self):
        response = self.get_configuration(self.available_product_id)

        self.assertEqual(response.status_code, 200)
        configuration = response.get_json()
        self.assertEqual(
            set(configuration),
            {
                "schema_version",
                "product_id",
                "dimensions",
                "anchorages",
                "colors",
                "screw_options",
                "defaults",
            },
        )
        self.assertEqual(configuration["schema_version"], 2)
        self.assertEqual(configuration["product_id"], self.available_product_id)
        self.assertEqual(
            configuration["dimensions"],
            {
                "alto": {"min_cm": 30.0, "max_cm": 250.0},
                "ancho": {"min_cm": 30.0, "max_cm": 250.0},
                "max_sum_cm": 400.0,
            },
        )
        self.assertEqual(
            configuration["defaults"],
            {
                "anchorage": ANCHORAGE_INTERIOR_HOLES,
                "color": "satinado_blanco",
                "screw_option": DEFAULT_CONFIGURATOR_SCREW_OPTION,
            },
        )
        self.assertEqual(
            [option["supplement"] for option in configuration["anchorages"]],
            [0.0, 24.95, 39.95],
        )
        self.assertEqual(
            [option["enabled"] for option in configuration["anchorages"]],
            [True, True, False],
        )
        self.assertEqual(
            configuration["anchorages"][1]["name"],
            "Pletinas",
        )
        self.assertEqual(
            configuration["anchorages"][1]["description"],
            "Instalación sin obra mediante pletinas.",
        )
        self.assertEqual(len(configuration["colors"]), 10)
        self.assertEqual(
            [
                option["length_mm"]
                for option in configuration["screw_options"][ANCHORAGE_FRONT_PLATES]
            ],
            [70, 150],
        )
        self.assertTrue(all(option["enabled"] for option in configuration["colors"]))
        self.assertEqual(
            configuration["colors"][0],
            {
                "value": "satinado_blanco",
                "name": "Blanco",
                "label": "Blanco liso",
                "finish": "liso",
                "finish_label": "Satinado liso",
                "enabled": True,
            },
        )
        self.assertNotIn("price", configuration)

    def test_configuration_is_idempotent_and_does_not_create_state(self):
        first = self.get_configuration(self.available_product_id)
        second = self.get_configuration(self.available_product_id)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.get_json(), second.get_json())
        with self.app.app_context():
            self.assertEqual(Cart.query.count(), 0)
            self.assertEqual(Orders.query.count(), 0)

    def test_configuration_rejects_unavailable_unpublished_and_missing_products(self):
        unavailable = self.get_configuration(self.unavailable_product_id)
        unpublished = self.get_configuration(self.unpublished_product_id)
        missing = self.get_configuration(999_999)

        self.assertEqual(unavailable.status_code, 400)
        self.assertEqual(unpublished.status_code, 404)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(unpublished.get_json(), missing.get_json())

    def test_returns_only_authoritative_commercial_quote(self):
        response = self.post_quote(self.available_product_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "product_id": self.available_product_id,
                "quantity": 2,
                "alto": 30.0,
                "ancho": 30.0,
                "anclaje": ANCHORAGE_FRONT_PLATES,
                "color": "satinado_blanco",
                "screw_option": DEFAULT_CONFIGURATOR_SCREW_OPTION,
                "screw_length_mm": 70,
                "currency": "EUR",
                "base_unit_price": 95.0,
                "anchorage_supplement": 24.95,
                "screw_supplement": 0.0,
                "unit_price": 119.95,
                "subtotal": 239.9,
            },
        )

    def test_repeated_quote_is_idempotent_and_does_not_create_state(self):
        first = self.post_quote(self.available_product_id)
        second = self.post_quote(self.available_product_id)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.get_json(), second.get_json())
        with self.app.app_context():
            self.assertEqual(Cart.query.count(), 0)
            self.assertEqual(Orders.query.count(), 0)

    def test_rejects_client_supplied_price(self):
        response = self.post_quote(
            self.available_product_id,
            self.quote_payload(precio_total=0.01),
        )

        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_configuration_like_checkout(self):
        invalid_dimensions = self.post_quote(
            self.available_product_id,
            self.quote_payload(alto=10),
        )
        invalid_anchorage = self.post_quote(
            self.available_product_id,
            self.quote_payload(anclaje="Anclaje inventado"),
        )
        invalid_screw_option = self.post_quote(
            self.available_product_id,
            self.quote_payload(screw_option="invented"),
        )

        self.assertEqual(invalid_dimensions.status_code, 400)
        self.assertEqual(invalid_anchorage.status_code, 400)
        self.assertEqual(invalid_screw_option.status_code, 400)

    def test_long_screws_are_priced_by_backend(self):
        response = self.post_quote(
            self.available_product_id,
            self.quote_payload(screw_option=SCREW_OPTION_LONG_150, quantity=1),
        )

        self.assertEqual(response.status_code, 200)
        quote = response.get_json()
        self.assertEqual(quote["screw_option"], SCREW_OPTION_LONG_150)
        self.assertEqual(quote["screw_length_mm"], 150)
        self.assertEqual(quote["screw_supplement"], 8.95)
        self.assertEqual(quote["unit_price"], 128.9)

    def test_order_line_freezes_resolved_screw_configuration(self):
        response = self.post_quote(
            self.available_product_id,
            self.quote_payload(screw_option=SCREW_OPTION_LONG_150, quantity=1),
        )
        quote_line = {
            **response.get_json(),
            "product_name": "Reja disponible",
            "line_total": 128.9,
            "shipping_type": "normal",
            "shipping_cost": 0.0,
        }

        detail_data = _build_order_details_from_checkout_quote({"lines": [quote_line]})[0]
        detail = OrderDetails(
            order_id=1,
            product_id=detail_data["producto_id"],
            quantity=detail_data["quantity"],
            alto=detail_data["alto"],
            ancho=detail_data["ancho"],
            anclaje=detail_data["anclaje"],
            color=detail_data["color"],
            screw_option=detail_data["screw_option"],
            screw_length_mm=detail_data["screw_length_mm"],
            screw_supplement=detail_data["screw_supplement"],
            precio_total=detail_data["precio_total"],
        )

        serialized = detail.serialize()
        self.assertEqual(serialized["screw_option"], SCREW_OPTION_LONG_150)
        self.assertEqual(serialized["screw_length_mm"], 150)
        self.assertEqual(serialized["screw_supplement"], 8.95)

    def test_rejects_unavailable_product(self):
        response = self.post_quote(self.unavailable_product_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("no esta disponible", response.get_json()["message"])

    def test_unpublished_and_missing_products_share_404(self):
        unpublished = self.post_quote(self.unpublished_product_id)
        missing = self.post_quote(999_999)

        self.assertEqual(unpublished.status_code, 404)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(unpublished.get_json(), missing.get_json())

    def test_quantity_defaults_to_one(self):
        payload = self.quote_payload()
        del payload["quantity"]

        response = self.post_quote(self.available_product_id, payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["quantity"], 1)
        self.assertEqual(response.get_json()["subtotal"], 119.95)


if __name__ == "__main__":
    unittest.main()

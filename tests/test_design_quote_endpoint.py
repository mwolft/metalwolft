import importlib.util
import sys
import unittest
from decimal import Decimal
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
    for package in ("flask", "flask_jwt_extended", "flask_sqlalchemy", "sqlalchemy", "slugify")
)


if HAS_ENDPOINT_DEPS:
    from flask import Flask
    from flask_jwt_extended import JWTManager

    from api.models import (
        Categories,
        CheckoutSessions,
        DesignRequest,
        DesignServiceConfig,
        DesignServicePriceTier,
        Orders,
        Products,
        db,
    )
    from api.routes import (
        DESIGN_QUOTE_RATE_LIMIT_REQUESTS,
        _design_quote_rate_limiter,
        api,
    )


@unittest.skipUnless(HAS_ENDPOINT_DEPS, "Flask/JWT/SQLAlchemy test dependencies are not installed.")
class DesignQuoteEndpointTest(unittest.TestCase):
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
            category = Categories(nombre="Diseño previo", descripcion="Tests", slug="diseno-previo")
            db.session.add(category)
            db.session.flush()
            products = [
                Products(nombre="Maryland", descripcion="Modelo", precio=100.0, categoria_id=category.id, slug="maryland"),
                Products(nombre="Vermont", descripcion="Modelo", precio=100.0, categoria_id=category.id, slug="vermont"),
            ]
            db.session.add_all(products)
            db.session.add(DesignServiceConfig(
                id=1,
                is_active=True,
                base_price_gross=Decimal("24.95"),
                currency="EUR",
                lead_time_hours=24,
            ))
            db.session.add_all([
                DesignServicePriceTier(config_id=1, min_design_count=2, unit_price_gross=Decimal("22.45")),
                DesignServicePriceTier(config_id=1, min_design_count=3, unit_price_gross=Decimal("19.95")),
                DesignServicePriceTier(config_id=1, min_design_count=4, unit_price_gross=Decimal("17.95")),
            ])
            db.session.commit()
            self.maryland_id = products[0].id
            self.vermont_id = products[1].id

        self.client = self.app.test_client()
        _design_quote_rate_limiter.reset()

    def tearDown(self):
        _design_quote_rate_limiter.reset()
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def items(self, count=1):
        return [
            {
                "product_id": self.maryland_id if index % 2 == 0 else self.vermont_id,
                "width_cm": 100 + index,
                "height_cm": 120,
            }
            for index in range(count)
        ]

    def quote(self, payload):
        return self.client.post("/api/design-requests/quote", json=payload)

    def test_anonymous_quote_is_read_only_and_uses_authoritative_price(self):
        with self.app.app_context():
            before = (
                DesignRequest.query.count(),
                Orders.query.count(),
                CheckoutSessions.query.count(),
            )

        response = self.quote({
            "items": self.items(1),
            "price": "0.01",
            "subtotal": "0.01",
            "discount_amount": "999.00",
            "total_amount": "0.01",
        })

        self.assertEqual(response.status_code, 200)
        quote = response.get_json()
        self.assertEqual(quote["total_amount"], "24.95")
        self.assertEqual(quote["tax_base"], "20.62")
        self.assertEqual(quote["tax_amount"], "4.33")
        self.assertEqual(quote["shipping_cost"], "0.00")
        self.assertFalse(quote["requires_shipping"])
        with self.app.app_context():
            self.assertEqual(
                (DesignRequest.query.count(), Orders.query.count(), CheckoutSessions.query.count()),
                before,
            )

    def test_authoritative_tiers_apply_for_one_to_five_designs(self):
        expected = {1: "24.95", 2: "44.90", 3: "59.85", 4: "71.80", 5: "89.75"}
        for count, total in expected.items():
            response = self.quote({"items": self.items(count)})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["total_amount"], total)

    def test_exact_duplicates_are_one_billable_design(self):
        item = {"product_id": self.maryland_id, "width_cm": 200, "height_cm": 120}
        response = self.quote({"items": [item, item, item]})
        self.assertEqual(response.status_code, 200)
        quote = response.get_json()
        self.assertEqual(len(quote["items"]), 1)
        self.assertEqual(quote["total_amount"], "24.95")

    def test_invalid_model_or_dimensions_and_inactive_service_are_rejected(self):
        self.assertEqual(
            self.quote({"items": [{"product_id": 999999, "width_cm": 100, "height_cm": 120}]}).status_code,
            400,
        )
        self.assertEqual(
            self.quote({"items": [{"product_id": self.maryland_id, "width_cm": 0, "height_cm": 120}]}).status_code,
            400,
        )
        with self.app.app_context():
            db.session.get(DesignServiceConfig, 1).is_active = False
            db.session.commit()
        self.assertEqual(self.quote({"items": self.items(1)}).status_code, 400)

    def test_private_design_request_endpoints_still_require_jwt(self):
        self.assertEqual(self.client.post("/api/design-requests", json={"items": self.items(1)}).status_code, 401)
        self.assertEqual(
            self.client.post("/api/design-requests/1/checkout-quote", json={}).status_code,
            401,
        )

    def test_public_quote_rate_limit_returns_retry_after(self):
        for _ in range(DESIGN_QUOTE_RATE_LIMIT_REQUESTS):
            self.assertEqual(self.quote({"items": self.items(1)}).status_code, 200)
        response = self.quote({"items": self.items(1)})
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response.headers["Retry-After"]), 0)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
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
    for package in ("flask", "flask_jwt_extended", "flask_sqlalchemy", "sqlalchemy")
)


if HAS_ENDPOINT_DEPS:
    from flask import Flask  # noqa: E402
    from flask_jwt_extended import JWTManager, create_access_token  # noqa: E402

    from api.models import Cart, Categories, DeliveryEstimateConfig, Products, Users, db  # noqa: E402
    from api.routes import api  # noqa: E402


@unittest.skipUnless(
    HAS_ENDPOINT_DEPS,
    "Flask/JWT/SQLAlchemy test dependencies are not installed.",
)
class CartDeliveryEstimateEndpointTest(unittest.TestCase):
    def setUp(self):
        self.invoice_dir = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            JWT_SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            INVOICE_FOLDER=self.invoice_dir.name,
        )
        JWTManager(self.app)
        db.init_app(self.app)
        self.app.register_blueprint(api, url_prefix="/api")

        with self.app.app_context():
            db.create_all()
            user = Users(email="delivery@example.test", password="test-password")
            category = Categories(
                nombre="Rejas delivery",
                descripcion="Delivery tests",
                slug="rejas-delivery",
            )
            db.session.add_all([user, category])
            db.session.flush()
            self.fixed_product = Products(
                nombre="Reja fija",
                descripcion="Producto fijo",
                precio=100.0,
                categoria_id=category.id,
                opening_type="fixed",
            )
            self.hinged_product = Products(
                nombre="Reja abatible",
                descripcion="Producto abatible",
                precio=100.0,
                categoria_id=category.id,
                opening_type="hinged",
            )
            db.session.add_all([
                self.fixed_product,
                self.hinged_product,
                DeliveryEstimateConfig(delivery_days=15, range_days=7, is_active=True),
            ])
            db.session.commit()
            self.user_id = user.id
            self.fixed_product_id = self.fixed_product.id
            self.hinged_product_id = self.hinged_product.id
            self.token = create_access_token(
                identity=str(user.id),
                additional_claims={"email": user.email, "is_admin": False},
            )

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.invoice_dir.cleanup()

    def auth(self):
        return {"Authorization": f"Bearer {self.token}"}

    def add_cart_line(self, product_id, quantity):
        with self.app.app_context():
            db.session.add(
                Cart(
                    usuario_id=self.user_id,
                    producto_id=product_id,
                    alto=100,
                    ancho=100,
                    anclaje="interior_holes",
                    color="satinado_blanco",
                    precio_total=100,
                    quantity=quantity,
                    added_at=datetime.now(timezone.utc),
                )
            )
            db.session.commit()

    def test_requires_authentication(self):
        response = self.client.get("/api/cart/delivery-estimate")

        self.assertIn(response.status_code, (401, 422))

    def test_uses_persisted_cart_and_disables_caching(self):
        self.add_cart_line(self.fixed_product_id, 5)
        self.add_cart_line(self.hinged_product_id, 1)

        response = self.client.get("/api/cart/delivery-estimate", headers=self.auth())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")
        self.assertEqual(response.headers["Vary"], "Authorization")
        payload = response.get_json()
        today = date.today()
        self.assertEqual(payload["start_date"], (today + timedelta(days=23)).isoformat())
        self.assertEqual(payload["end_date"], (today + timedelta(days=30)).isoformat())
        self.assertEqual(
            payload["adjustments"],
            [
                {
                    "code": "hinged_product",
                    "days": 3,
                    "message": "+3 días por incluir una reja abatible",
                },
                {
                    "code": "quantity_six_or_more",
                    "days": 5,
                    "message": "+5 días por cantidad del pedido",
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()

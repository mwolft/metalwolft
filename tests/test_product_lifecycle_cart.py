import importlib.util
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.product_lifecycle import (  # noqa: E402
    ProductNotAvailableForSaleError,
    ensure_product_available_for_sale,
)


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
    )
)


class ProductAvailabilityGuardTest(unittest.TestCase):
    def test_returns_available_product(self):
        product = SimpleNamespace(available_for_sale=True)

        self.assertIs(ensure_product_available_for_sale(product), product)

    def test_rejects_unavailable_product(self):
        product = SimpleNamespace(available_for_sale=False)

        with self.assertRaises(ProductNotAvailableForSaleError):
            ensure_product_available_for_sale(product)

if HAS_ENDPOINT_DEPS:
    from flask import Flask  # noqa: E402
    from flask_jwt_extended import JWTManager, create_access_token  # noqa: E402

    from api.models import Cart, Categories, Products, Users, db  # noqa: E402
    from api.routes import api  # noqa: E402
    from api.utils import (  # noqa: E402
        ANCHORAGE_INTERIOR_HOLES,
    )


@unittest.skipUnless(
    HAS_ENDPOINT_DEPS,
    "Flask/JWT/SQLAlchemy test dependencies are not installed.",
)
class ProductLifecycleCartEndpointTest(unittest.TestCase):
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
            user = Users(
                email="cart-lifecycle@example.test",
                password="test-password",
                firstname="Cart",
                lastname="Lifecycle",
                is_active=True,
                is_admin=False,
            )
            category = Categories(
                nombre="Rejas lifecycle",
                descripcion="Lifecycle tests",
                slug="rejas-lifecycle",
            )
            db.session.add_all([user, category])
            db.session.flush()
            available_product = Products(
                nombre="Reja disponible",
                descripcion="Producto disponible",
                precio=100.0,
                categoria_id=category.id,
            )
            unavailable_product = Products(
                nombre="Reja retirada",
                descripcion="Producto retirado",
                precio=100.0,
                categoria_id=category.id,
                published=True,
                available_for_sale=False,
            )
            db.session.add_all([available_product, unavailable_product])
            db.session.commit()

            self.user_id = user.id
            self.available_product_id = available_product.id
            self.unavailable_product_id = unavailable_product.id
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

    def cart_payload(self, *, quantity=1):
        return {
            "alto": 30,
            "ancho": 30,
            "anclaje": ANCHORAGE_INTERIOR_HOLES,
            "color": "satinado_blanco",
            "quantity": quantity,
        }

    def create_cart_item(self, product_id):
        with self.app.app_context():
            item = Cart(
                usuario_id=self.user_id,
                producto_id=product_id,
                alto=30,
                ancho=30,
                anclaje=ANCHORAGE_INTERIOR_HOLES,
                color="satinado_blanco",
                precio_total=95.0,
                quantity=1,
                added_at=datetime.now(timezone.utc),
            )
            db.session.add(item)
            db.session.commit()
            return item.id

    def test_adds_available_product_and_preserves_previous_behavior(self):
        payload = {
            "product_id": self.available_product_id,
            **self.cart_payload(quantity=2),
        }

        response = self.client.post(
            "/api/cart",
            json=payload,
            headers=self.auth(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.get_json()), 1)
        self.assertIs(response.get_json()[0]["available_for_sale"], True)
        with self.app.app_context():
            item = Cart.query.one()
            self.assertEqual(item.quantity, 2)
            self.assertEqual(item.precio_total, 95.0)

    def test_rejects_adding_unavailable_product(self):
        payload = {
            "product_id": self.unavailable_product_id,
            **self.cart_payload(),
        }

        response = self.client.post(
            "/api/cart",
            json=payload,
            headers=self.auth(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("no esta disponible", response.get_json()["message"])
        with self.app.app_context():
            self.assertEqual(Cart.query.count(), 0)

    def test_reads_existing_line_after_product_is_withdrawn(self):
        self.create_cart_item(self.available_product_id)
        with self.app.app_context():
            product = db.session.get(Products, self.available_product_id)
            product.available_for_sale = False
            db.session.commit()

        response = self.client.get("/api/cart", headers=self.auth())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)
        self.assertIs(response.get_json()[0]["available_for_sale"], False)

    def test_deletes_existing_line_after_product_is_withdrawn(self):
        self.create_cart_item(self.available_product_id)
        with self.app.app_context():
            product = db.session.get(Products, self.available_product_id)
            product.available_for_sale = False
            db.session.commit()

        response = self.client.delete(
            f"/api/cart/{self.available_product_id}",
            json=self.cart_payload(),
            headers=self.auth(),
        )

        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertEqual(Cart.query.count(), 0)

    def test_rejects_updating_existing_line_after_product_is_withdrawn(self):
        self.create_cart_item(self.available_product_id)
        with self.app.app_context():
            product = db.session.get(Products, self.available_product_id)
            product.available_for_sale = False
            db.session.commit()

        response = self.client.put(
            f"/api/cart/{self.available_product_id}",
            json=self.cart_payload(quantity=2),
            headers=self.auth(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("no esta disponible", response.get_json()["message"])
        with self.app.app_context():
            item = Cart.query.one()
            self.assertEqual(item.quantity, 1)
            self.assertEqual(item.precio_total, 95.0)


if __name__ == "__main__":
    unittest.main()

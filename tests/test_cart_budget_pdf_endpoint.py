import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO
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
        "reportlab",
        "pypdf",
    )
)


if HAS_ENDPOINT_DEPS:
    from flask import Flask
    from flask_jwt_extended import JWTManager, create_access_token
    from pypdf import PdfReader

    from api.models import (AccountingEntry, Cart, Categories, CheckoutSessions, Invoices, Orders, Products, Users, db)
    from api.cart_budget_pdf_service import render_cart_budget_pdf
    from api.routes import api
    from api.utils import ANCHORAGE_INTERIOR_HOLES, ANCHORAGE_METAL_CLAWS


@unittest.skipUnless(HAS_ENDPOINT_DEPS, "Flask/PDF test dependencies are not installed.")
class CartBudgetPdfEndpointTest(unittest.TestCase):
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
            user = Users(email="budget@example.test", password="test-password")
            category = Categories(nombre="Rejas", descripcion="Tests", slug="rejas-tests")
            product = Products(
                nombre="Reja presupuestada",
                descripcion="Reja para presupuesto",
                precio=100.0,
                categoria_id=1,
                slug="reja-presupuestada",
            )
            db.session.add_all([user, category])
            db.session.flush()
            product.categoria_id = category.id
            db.session.add(product)
            db.session.commit()
            self.user_id = user.id
            self.product_id = product.id
            self.token = create_access_token(
                identity=str(user.id),
                additional_claims={"email": user.email, "is_admin": False},
            )
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def auth(self):
        return {"Authorization": f"Bearer {self.token}"}

    def add_cart_line(self, *, anchorage=ANCHORAGE_INTERIOR_HOLES, screw_option="standard"):
        with self.app.app_context():
            db.session.add(Cart(
                usuario_id=self.user_id,
                producto_id=self.product_id,
                alto=100,
                ancho=100,
                anclaje=anchorage,
                color="satinado_blanco",
                screw_option=screw_option,
                screw_length_mm=None,
                screw_supplement=0.0,
                precio_total=0.01,
                quantity=1,
                added_at=datetime.now(timezone.utc),
            ))
            db.session.commit()

    def budget_pdf_text(self, response):
        return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(response.data)).pages)

    def test_requires_jwt(self):
        response = self.client.post("/api/cart/budget/pdf", json={})
        self.assertIn(response.status_code, (401, 422))

    def test_rejects_an_empty_cart(self):
        response = self.client.post("/api/cart/budget/pdf", json={}, headers=self.auth())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["message"], "El carrito está vacío.")

    def test_generates_an_authoritative_non_fiscal_pdf_without_persistence(self):
        self.add_cart_line()
        with self.app.app_context():
            before = {
                "cart": Cart.query.count(),
                "orders": Orders.query.count(),
                "checkout": CheckoutSessions.query.count(),
                "invoices": Invoices.query.count(),
                "accounting": AccountingEntry.query.count(),
            }

        response = self.client.post(
            "/api/cart/budget/pdf",
            json={
                "lines": [{"unit_price": 999999}],
                "subtotal": 999999,
                "shipping_cost": 999999,
                "total_amount": 999999,
            },
            headers=self.auth(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("attachment;", response.headers["Content-Disposition"])
        self.assertIn("presupuesto-metalwolft-", response.headers["Content-Disposition"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        text = self.budget_pdf_text(response)
        self.assertIn("PRESUPUESTO", text)
        self.assertIn("Reja presupuestada", text)
        self.assertIn("Alto: 100 cm", text)
        self.assertIn("Anclaje: Sin obra: con agujeros interiores", text)
        self.assertIn("Tornillos: 80 mm incluidos", text)
        self.assertIn("Color: Blanco liso · Acabado: esmalte sintético", text)
        self.assertIn("121,00 €", text)
        self.assertIn("Base imponible", text)
        self.assertIn("100,00 €", text)
        self.assertIn("IVA 21 %", text)
        self.assertIn("21,00 €", text)
        self.assertIn("Documento informativo.", text)
        self.assertNotIn("999.999", text)
        self.assertNotIn("FACTURA", text)

        with self.app.app_context():
            self.assertEqual(Cart.query.count(), before["cart"])
            self.assertEqual(Orders.query.count(), before["orders"])
            self.assertEqual(CheckoutSessions.query.count(), before["checkout"])
            self.assertEqual(Invoices.query.count(), before["invoices"])
            self.assertEqual(AccountingEntry.query.count(), before["accounting"])

    def test_uses_a_valid_coupon_from_the_authoritative_quote(self):
        self.add_cart_line()
        response = self.client.post(
            "/api/cart/budget/pdf",
            json={"discount_code": "REJAS10"},
            headers=self.auth(),
        )

        self.assertEqual(response.status_code, 200)
        text = self.budget_pdf_text(response)
        self.assertIn("Descuento (REJAS10)", text)
        self.assertIn("108,90 €", text)

    def test_metal_claws_do_not_render_a_screw_line(self):
        self.add_cart_line(anchorage=ANCHORAGE_METAL_CLAWS, screw_option="not_applicable")
        response = self.client.post("/api/cart/budget/pdf", json={}, headers=self.auth())

        self.assertEqual(response.status_code, 200)
        text = self.budget_pdf_text(response)
        self.assertIn("Anclaje: Con obra: con garras metálicas", text)
        self.assertNotIn("Tornillos:", text)

    def test_renders_tax_breakdowns_from_authoritative_gross_totals(self):
        scenarios = (
            ("envio de pago", "100.00", "12.00", "0.00", "112.00", "92,56 €", "19,44 €"),
            ("envio gratis", "100.00", "0.00", "0.00", "100.00", "82,64 €", "17,36 €"),
            ("cupon", "100.00", "10.00", "11.00", "99.00", "81,82 €", "17,18 €"),
            ("redondeo", "0.01", "0.00", "0.00", "0.01", "0,01 €", "0,00 €"),
        )
        for name, subtotal, shipping, discount, total, expected_base, expected_tax in scenarios:
            with self.subTest(name=name):
                pdf = render_cart_budget_pdf(
                    quote={
                        "lines": [{
                            "product_name": "Reja presupuestada",
                            "quantity": 1,
                            "unit_price": subtotal,
                            "line_total": subtotal,
                            "alto": 100,
                            "ancho": 100,
                            "anclaje": ANCHORAGE_INTERIOR_HOLES,
                            "color": "satinado_blanco",
                            "screw_length_mm": 80,
                            "screw_supplement": "0.00",
                        }],
                        "subtotal": subtotal,
                        "shipping_cost": shipping,
                        "discount_amount": discount,
                        "discount_percent": "10.00" if discount != "0.00" else "0.00",
                        "discount_code": "REJAS10" if discount != "0.00" else None,
                        "total_amount": total,
                    },
                    issued_at=datetime(2026, 8, 24, tzinfo=timezone.utc),
                )
                text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
                self.assertIn(expected_base, text)
                self.assertIn(expected_tax, text)
                self.assertIn(f"TOTAL\n {Decimal(total):.2f}".replace(".", ","), text)
                self.assertEqual(
                    Decimal(expected_base.replace(",", ".").replace(" €", ""))
                    + Decimal(expected_tax.replace(",", ".").replace(" €", "")),
                    Decimal(total),
                )


if __name__ == "__main__":
    unittest.main()

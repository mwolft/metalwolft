import base64
import importlib.util
import json
import re
import sys
import unittest
from datetime import date, datetime
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


HAS_DEPS = all(
    has_package(package)
    for package in (
        "flask", "flask_admin", "flask_sqlalchemy", "sqlalchemy", "slugify", "PIL", "reportlab",
    )
)


if HAS_DEPS:
    from flask import Flask
    from flask_admin import Admin
    from PIL import Image
    from requests import Timeout
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import configure_mappers

    import api.admin as admin_module
    from api.models import (
        Categories,
        CheckoutSessions,
        OrderDetails,
        Orders,
        Products,
        Users,
        WorkOrder,
        db,
    )
    from api.utils import ANCHORAGE_INTERIOR_HOLES, ANCHORAGE_METAL_CLAWS
    from api.work_order_builder import (
        WORK_ORDER_SCHEMA_VERSION,
        WorkOrderBuilder,
        WorkOrderValidationError,
        assert_snapshot_has_no_economic_data,
        get_or_create_work_order,
    )
    from api.work_order_pdf_service import generate_work_order_pdf


@unittest.skipUnless(HAS_DEPS, "Flask Admin test dependencies are not installed.")
class WorkOrderBuilderTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"
        configure_mappers()
        self.app = Flask(
            __name__,
            template_folder=str(SRC_DIR / "templates"),
            static_folder=str(SRC_DIR / "static"),
        )
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="work-order-test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.admin = Admin(self.app, url="/admin")
        self.view = admin_module.OrderAdminView(Orders, db.session, name="Pedidos")
        self.admin.add_view(self.view)

        with self.app.app_context():
            db.create_all()
            self.order = self._create_physical_order()
            db.session.commit()
            self.order_id = self.order.id
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_physical_order(self, *, include_second_line=False, image=True):
        category = Categories(
            nombre="Rejas",
            descripcion="Categoría de pruebas",
            slug=f"rejas-{Users.query.count() + Products.query.count() + 1}",
        )
        db.session.add(category)
        db.session.flush()
        product = Products(
            nombre="Reja Essex",
            descripcion="Descripción de catálogo que no debe llegar al parte.",
            precio=154.47,
            categoria_id=category.id,
            slug=f"reja-essex-{category.id}",
            imagen="https://res.cloudinary.com/dewanllxn/image/upload/essex.webp" if image else None,
            opening_type="fixed",
        )
        db.session.add(product)
        db.session.flush()
        user = Users(email=f"cliente-{category.id}@example.test", password="hash")
        db.session.add(user)
        db.session.flush()
        order = Orders(
            user_id=user.id,
            total_amount=308.94,
            locator=f"WO{category.id:04d}",
            order_date=datetime(2026, 9, 9, 10, 30),
            order_status="pendiente",
        )
        db.session.add(order)
        db.session.flush()
        detail = OrderDetails(
            order_id=order.id,
            product_id=product.id,
            quantity=2,
            line_type="physical",
            alto=109.0,
            ancho=198.0,
            anclaje=ANCHORAGE_INTERIOR_HOLES,
            color="satinado_blanco",
            screw_length_mm=150,
            screw_supplement=8.95,
            precio_total=154.47,
            firstname="María",
            lastname="Taller",
            shipping_address="Calle de prueba 1",
            shipping_city="Ciudad Real",
            shipping_postal_code="13001",
        )
        db.session.add(detail)
        if include_second_line:
            second = Products(
                nombre="Reja Vermont",
                descripcion="Otra descripción",
                precio=90.0,
                categoria_id=category.id,
                slug=f"reja-vermont-{category.id}",
                opening_type="hinged",
            )
            db.session.add(second)
            db.session.flush()
            db.session.add(
                OrderDetails(
                    order_id=order.id,
                    product_id=second.id,
                    quantity=1,
                    line_type="physical",
                    alto=80.5,
                    ancho=100.0,
                    anclaje=ANCHORAGE_METAL_CLAWS,
                    color="forja_negro",
                    screw_length_mm=None,
                    precio_total=90.0,
                )
            )
        db.session.flush()
        db.session.add(
            CheckoutSessions(
                user_id=user.id,
                order_id=order.id,
                public_checkout_token=f"checkout-{category.id}",
                quote_snapshot={"lines": [{"product_name": "Reja Essex"}]},
                customer_snapshot={
                    "firstname": "María",
                    "lastname": "Taller",
                    "phone": "600 123 123",
                    "shipping_address": "Calle de prueba 1",
                    "shipping_postal_code": "13001",
                    "shipping_city": "Ciudad Real",
                    "shipping_province": "Ciudad Real",
                    "shipping_country_code": "ES",
                },
            )
        )
        db.session.flush()
        return order

    def _auth_header(self):
        token = base64.b64encode(b"admin:secret").decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _work_order_url(self, order_id=None):
        order_id = order_id or self.order_id
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".work_order_view"):
                return rule.rule.replace("<int:order_id>", str(order_id))
        raise AssertionError("Work-order route was not registered")

    def _observations_url(self, order_id=None):
        order_id = order_id or self.order_id
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".update_work_order_observations"):
                return rule.rule.replace("<int:order_id>", str(order_id))
        raise AssertionError("Work-order observation route was not registered")

    def _pdf_url(self, order_id=None):
        order_id = order_id or self.order_id
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".work_order_pdf_view"):
                return rule.rule.replace("<int:order_id>", str(order_id))
        raise AssertionError("Work-order PDF route was not registered")

    def _manufactured_url(self, *, manufactured, order_id=None):
        order_id = order_id or self.order_id
        endpoint_suffix = ".mark_work_order_manufactured" if manufactured else ".unmark_work_order_manufactured"
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(endpoint_suffix):
                return rule.rule.replace("<int:order_id>", str(order_id))
        raise AssertionError("Work-order manufactured route was not registered")

    def _detail_url(self, order_id=None):
        order_id = order_id or self.order_id
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.endswith(".details_view"):
                return f"{rule.rule}?id={order_id}"
        raise AssertionError("Order details route was not registered")

    def test_snapshot_v1_freezes_physical_configuration_without_economic_data(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            work_order, created = get_or_create_work_order(
                db_session=db.session,
                order=order,
                created_by="admin",
            )
            db.session.commit()

            self.assertTrue(created)
            self.assertEqual(work_order.schema_version, WORK_ORDER_SCHEMA_VERSION)
            self.assertEqual(work_order.snapshot["lines"][0]["quantity"], 2)
            self.assertEqual(work_order.snapshot["lines"][0]["dimensions"], {
                "unit": "cm", "height": "109", "width": "198",
            })
            self.assertEqual(work_order.snapshot["lines"][0]["anchorage"]["label"], "Agujeros interiores")
            self.assertEqual(work_order.snapshot["lines"][0]["color"]["label"], "Blanco liso")
            self.assertEqual(work_order.snapshot["lines"][0]["color"]["finish_label"], "Satinado liso")
            self.assertEqual(work_order.snapshot["lines"][0]["screws"]["display"], "150 mm")
            self.assertEqual(work_order.snapshot["lines"][0]["opening_type"]["label"], "Fija")
            self.assertEqual(
                work_order.snapshot["lines"][0]["image_url"],
                "https://res.cloudinary.com/dewanllxn/image/upload/essex.webp",
            )
            self.assertEqual(work_order.snapshot["customer"]["phone"], "600 123 123")
            self.assertIn("Ciudad Real", work_order.snapshot["customer"]["delivery_address"])
            assert_snapshot_has_no_economic_data(work_order.snapshot)
            snapshot_json = json.dumps(work_order.snapshot, ensure_ascii=False).lower()
            for forbidden in ("precio", "subtotal", "descuento", "iva", "stripe", "paypal", "factura"):
                self.assertNotIn(forbidden, snapshot_json)

    def test_existing_work_order_is_unique_and_catalog_changes_do_not_change_it(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            work_order, created = get_or_create_work_order(
                db_session=db.session, order=order, created_by="admin"
            )
            db.session.commit()
            same, created_again = get_or_create_work_order(
                db_session=db.session, order=order, created_by="admin-2"
            )
            self.assertTrue(created)
            self.assertFalse(created_again)
            self.assertEqual(same.id, work_order.id)
            unique_constraint_names = {
                constraint.name
                for constraint in WorkOrder.__table__.constraints
                if constraint.__class__.__name__ == "UniqueConstraint"
            }
            self.assertIn("uq_work_orders_order_id", unique_constraint_names)

            product = order.order_details[0].product
            product.nombre = "Nombre cambiado"
            product.imagen = "https://res.cloudinary.com/dewanllxn/image/upload/cambiada.webp"
            product.opening_type = "hinged"
            db.session.commit()

            data = WorkOrderBuilder.from_work_order(db.session.get(WorkOrder, work_order.id))
            self.assertEqual(data.lines[0]["model_name"], "Reja Essex")
            self.assertEqual(data.lines[0]["opening_type"]["label"], "Fija")
            self.assertEqual(
                data.lines[0]["image_url"],
                "https://res.cloudinary.com/dewanllxn/image/upload/essex.webp",
            )

    def test_multiple_lines_and_historical_gaps_are_explicit(self):
        with self.app.app_context():
            order = self._create_physical_order(include_second_line=True, image=False)
            db.session.commit()
            work_order, _created = get_or_create_work_order(
                db_session=db.session, order=order, created_by="admin"
            )
            db.session.commit()
            lines = work_order.snapshot["lines"]
            self.assertEqual([line["line_number"] for line in lines], [1, 2])
            self.assertIsNone(lines[0]["image_url"])
            self.assertEqual(lines[1]["quantity"], 1)
            self.assertEqual(lines[1]["dimensions"]["height"], "80.5")
            self.assertEqual(lines[1]["screws"]["display"], "No aplica")
            self.assertEqual(lines[1]["opening_type"]["label"], "Abatible")

    def test_snapshot_rejects_untrusted_image_urls_without_using_live_catalog_afterwards(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            order.order_details[0].product.imagen = "https://example.test/untrusted-image.png"
            db.session.commit()
            work_order, _created = get_or_create_work_order(
                db_session=db.session, order=order, created_by="admin"
            )
            db.session.commit()
            self.assertIsNone(work_order.snapshot["lines"][0]["image_url"])

            order.order_details[0].product.imagen = "https://res.cloudinary.com/dewanllxn/image/upload/new.png"
            db.session.commit()
            data = WorkOrderBuilder.from_work_order(work_order)
            self.assertIsNone(data.lines[0]["image_url"])

    def test_html_work_order_image_host_is_permitted_by_flask_csp(self):
        app_source = (SRC_DIR / "app.py").read_text(encoding="utf-8")
        self.assertIn('"img-src": ["\'self\'", "https://res.cloudinary.com"]', app_source)

    def test_design_service_orders_are_rejected_without_persisting_a_work_order(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            order.order_details[0].line_type = "design_service"
            with self.assertRaises(WorkOrderValidationError):
                get_or_create_work_order(db_session=db.session, order=order, created_by="admin")
            self.assertEqual(db.session.query(WorkOrder).filter_by(order_id=order.id).count(), 0)

    def test_internal_notes_are_mutable_without_changing_snapshot(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            work_order, _created = get_or_create_work_order(
                db_session=db.session, order=order, created_by="admin"
            )
            db.session.commit()
            original_snapshot = deepcopy_json(work_order.snapshot)
            work_order.internal_notes = "Comprobar remates antes de embalar."
            db.session.commit()
            self.assertEqual(work_order.snapshot, original_snapshot)
            work_order.snapshot = {"schema_version": 1, "order": {}, "customer": {}, "lines": []}
            with self.assertRaises(ValueError):
                db.session.commit()
            db.session.rollback()

    def test_admin_work_order_view_is_protected_and_contains_no_economic_data(self):
        unauthenticated = self.client.get(self._work_order_url())
        self.assertEqual(unauthenticated.status_code, 401)

        response = self.client.get(self._work_order_url(), headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PARTE DE FABRICACI", response.data.upper())
        self.assertIn(b"Reja Essex", response.data)
        self.assertIn(b"109 cm", response.data)
        self.assertIn(b"198 cm", response.data)
        self.assertIn(b"Agujeros interiores", response.data)
        self.assertIn(b"Blanco liso", response.data)
        self.assertIn(b"150 mm", response.data)
        self.assertNotIn(b"308.94", response.data)
        self.assertNotIn(b"precio_total", response.data)
        self.assertNotIn(b"PayPal", response.data)

        with self.app.app_context():
            self.assertEqual(db.session.query(WorkOrder).filter_by(order_id=self.order_id).count(), 1)

    def test_admin_notes_require_csrf_and_preserve_snapshot(self):
        response = self.client.get(self._work_order_url(), headers=self._auth_header())
        csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', response.data).group(1).decode()

        missing_csrf = self.client.post(
            self._observations_url(),
            data={"internal_notes": "No debe guardarse"},
            headers=self._auth_header(),
        )
        self.assertEqual(missing_csrf.status_code, 302)

        with self.app.app_context():
            work_order = db.session.query(WorkOrder).filter_by(order_id=self.order_id).one()
            original_snapshot = deepcopy_json(work_order.snapshot)

        saved = self.client.post(
            self._observations_url(),
            data={"csrf_token": csrf_token, "internal_notes": "Preparar embalaje reforzado."},
            headers=self._auth_header(),
        )
        self.assertEqual(saved.status_code, 302)
        with self.app.app_context():
            work_order = db.session.query(WorkOrder).filter_by(order_id=self.order_id).one()
            self.assertEqual(work_order.internal_notes, "Preparar embalaje reforzado.")
            self.assertEqual(work_order.snapshot, original_snapshot)

    def test_pdf_uses_frozen_work_order_data_and_safe_cloudinary_png_rendering(self):
        class FakeImageResponse:
            status_code = 200
            headers = {"Content-Type": "image/png", "Content-Length": "70"}

            def __init__(self, content):
                self._content = content

            def iter_content(self, chunk_size):
                yield self._content

        png = Path(__file__).read_bytes()[:0]
        image_buffer = __import__("io").BytesIO()
        Image.new("RGB", (4, 4), "white").save(image_buffer, format="PNG")
        png = image_buffer.getvalue()

        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            work_order, _created = get_or_create_work_order(
                db_session=db.session, order=order, created_by="admin"
            )
            db.session.commit()
            data = WorkOrderBuilder.from_work_order(work_order)
            original_snapshot = deepcopy_json(work_order.snapshot)
            order.order_details[0].product.nombre = "Nombre vivo que no debe usarse"
            db.session.commit()

            with patch(
                "api.work_order_pdf_service.requests.get",
                return_value=FakeImageResponse(png),
            ) as request_get:
                pdf = generate_work_order_pdf(data)

            self.assertTrue(pdf.startswith(b"%PDF"))
            self.assertIn(b"Reja Essex", pdf)
            self.assertNotIn(b"308.94", pdf)
            self.assertNotIn(b"PayPal", pdf)
            self.assertEqual(work_order.snapshot, original_snapshot)
            self.assertIn("/image/upload/f_png/", request_get.call_args.args[0])

    def test_pdf_endpoint_is_protected_and_handles_missing_images(self):
        with self.app.app_context():
            order = self._create_physical_order(image=False)
            db.session.commit()
            order_id = order.id
            get_or_create_work_order(db_session=db.session, order=order, created_by="admin")
            db.session.commit()

        unauthenticated = self.client.get(self._pdf_url(order_id))
        self.assertEqual(unauthenticated.status_code, 401)
        response = self.client.get(self._pdf_url(order_id), headers=self._auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn(b"Imagen no disponible", response.data)
        self.assertNotIn(b"precio_total", response.data)

    def test_pdf_handles_image_download_failure_and_multiple_frozen_lines(self):
        with self.app.app_context():
            order = self._create_physical_order(include_second_line=True)
            db.session.commit()
            work_order, _created = get_or_create_work_order(
                db_session=db.session, order=order, created_by="admin"
            )
            db.session.commit()
            data = WorkOrderBuilder.from_work_order(work_order)
            with patch("api.work_order_pdf_service.requests.get", side_effect=Timeout):
                pdf = generate_work_order_pdf(data)

            self.assertTrue(pdf.startswith(b"%PDF"))
            self.assertIn(b"Reja Essex", pdf)
            self.assertIn(b"Reja Vermont", pdf)
            self.assertIn(b"Imagen no disponible", pdf)
            self.assertNotIn(b"precio_total", pdf)
            self.assertNotIn(b"308.94", pdf)

    def test_manufactured_state_requires_csrf_preserves_order_and_can_be_reversed(self):
        view = self.client.get(self._work_order_url(), headers=self._auth_header())
        csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', view.data).group(1).decode()
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            initial_status = order.order_status
            initial_snapshot = deepcopy_json(order.work_order.snapshot)

        unauthenticated = self.client.post(
            self._manufactured_url(manufactured=True),
            data={"csrf_token": csrf_token, "confirm_manufactured": "yes"},
        )
        self.assertEqual(unauthenticated.status_code, 401)
        rejected = self.client.post(
            self._manufactured_url(manufactured=True),
            data={"confirm_manufactured": "yes"},
            headers=self._auth_header(),
        )
        self.assertEqual(rejected.status_code, 302)
        marked = self.client.post(
            self._manufactured_url(manufactured=True),
            data={"csrf_token": csrf_token, "confirm_manufactured": "yes"},
            headers=self._auth_header(),
        )
        self.assertEqual(marked.status_code, 302)
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            self.assertEqual(order.order_status, initial_status)
            self.assertEqual(order.work_order.snapshot, initial_snapshot)
            self.assertIsNotNone(order.work_order.manufactured_at)
            self.assertEqual(order.work_order.manufactured_by, "admin")

        unmarked = self.client.post(
            self._manufactured_url(manufactured=False),
            data={"csrf_token": csrf_token, "confirm_manufactured": "yes"},
            headers=self._auth_header(),
        )
        self.assertEqual(unmarked.status_code, 302)
        with self.app.app_context():
            work_order = db.session.query(WorkOrder).filter_by(order_id=self.order_id).one()
            self.assertIsNone(work_order.manufactured_at)
            self.assertIsNone(work_order.manufactured_by)

    def test_production_queue_filters_paid_physical_orders_without_creating_work_orders(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            order.checkout_session.status = "order_created"
            design_order = self._create_physical_order()
            design_order.order_details[0].line_type = "design_service"
            design_order.checkout_session.status = "order_created"
            cancelled_order = self._create_physical_order()
            cancelled_order.checkout_session.status = "order_created"
            cancelled_order.order_status = "cancelado"
            unpaid_order = self._create_physical_order()
            unpaid_order.checkout_session.status = "pending_payment"
            multiple_order = self._create_physical_order(include_second_line=True)
            multiple_order.checkout_session.status = "order_created"
            db.session.commit()

            with self.app.test_request_context("/admin/"):
                queue = admin_module._pending_manufacturing_queue(db.session)
            self.assertEqual(
                [item["locator"] for item in queue],
                [order.locator, multiple_order.locator],
            )
            self.assertIn("2 ud.", queue[0]["summary"])
            self.assertEqual(queue[1]["summary"], "2 configuraciones · 3 unidades")
            self.assertNotIn(design_order.locator, [item["locator"] for item in queue])
            self.assertNotIn(cancelled_order.locator, [item["locator"] for item in queue])
            self.assertNotIn(unpaid_order.locator, [item["locator"] for item in queue])
            self.assertEqual(db.session.query(WorkOrder).filter_by(order_id=order.id).count(), 0)

            order.checkout_session.status = "pending_payment"
            db.session.commit()
            with self.app.test_request_context("/admin/"):
                remaining_after_unpaid = admin_module._pending_manufacturing_queue(db.session)
            self.assertEqual(
                [item["locator"] for item in remaining_after_unpaid],
                [multiple_order.locator],
            )

            order.checkout_session.status = "order_created"
            get_or_create_work_order(db_session=db.session, order=order, created_by="admin")
            db.session.commit()
            order.work_order.manufactured_at = datetime.now()
            order.work_order.manufactured_by = "admin"
            db.session.commit()
            with self.app.test_request_context("/admin/"):
                remaining = admin_module._pending_manufacturing_queue(db.session)
            self.assertEqual([item["locator"] for item in remaining], [multiple_order.locator])

    def test_production_queue_exposes_frozen_configurations_and_delivery_countdown(self):
        with self.app.app_context():
            order = db.session.get(Orders, self.order_id)
            detail = order.order_details[0]
            detail.product.nombre = "Nombre vivo del catálogo"
            order.checkout_session.quote_snapshot = {
                "lines": [{
                    "product_id": detail.product_id,
                    "product_name": "Reja fija Essex congelada",
                }]
            }
            order.estimated_delivery_at = date(2026, 9, 16)

            with self.app.test_request_context("/admin/"):
                item = admin_module._pending_manufacturing_item(order, today=date(2026, 9, 9))
                self.assertEqual(item["entry_date"], "09/09/2026")
                self.assertEqual(item["delivery_countdown"], "Faltan 7 días")
                self.assertEqual(item["configurations"], ({
                    "model_name": "Reja fija Essex congelada",
                    "quantity": 2,
                    "quantity_label": "2 uds.",
                    "height": "109",
                    "width": "198",
                },))

                order.estimated_delivery_at = date(2026, 9, 10)
                self.assertEqual(
                    admin_module._pending_manufacturing_item(order, today=date(2026, 9, 9))["delivery_countdown"],
                    "Falta 1 día",
                )
                order.estimated_delivery_at = date(2026, 9, 9)
                self.assertEqual(
                    admin_module._pending_manufacturing_item(order, today=date(2026, 9, 9))["delivery_countdown"],
                    "Entrega hoy",
                )
                order.estimated_delivery_at = date(2026, 9, 7)
                self.assertEqual(
                    admin_module._pending_manufacturing_item(order, today=date(2026, 9, 9))["delivery_countdown"],
                    "Retraso: 2 días",
                )
                order.estimated_delivery_at = None
                self.assertIsNone(
                    admin_module._pending_manufacturing_item(order, today=date(2026, 9, 9))["delivery_countdown"]
                )

                order.checkout_session.quote_snapshot = {"lines": []}
                self.assertEqual(
                    admin_module._pending_manufacturing_item(order, today=date(2026, 9, 9))["configurations"][0]["model_name"],
                    "Nombre vivo del catálogo",
                )

            multiple_order = self._create_physical_order(include_second_line=True)
            multiple_order.checkout_session.quote_snapshot = {
                "lines": [
                    {
                        "product_id": multiple_order.order_details[0].product_id,
                        "product_name": "Reja fija Essex",
                    },
                    {
                        "product_id": multiple_order.order_details[1].product_id,
                        "product_name": "Reja Vermont",
                    },
                ]
            }
            with self.app.test_request_context("/admin/"):
                multiple_item = admin_module._pending_manufacturing_item(
                    multiple_order,
                    today=date(2026, 9, 9),
                )
            self.assertEqual(
                [(line["model_name"], line["quantity_label"]) for line in multiple_item["configurations"]],
                [("Reja fija Essex", "2 uds."), ("Reja Vermont", "1 ud.")],
            )
            self.assertEqual(
                [(line["height"], line["width"]) for line in multiple_item["configurations"]],
                [("109", "198"), ("80.5", "100")],
            )

    def test_order_detail_action_is_only_available_for_physical_orders(self):
        physical_response = self.client.get(self._detail_url(), headers=self._auth_header())
        self.assertEqual(physical_response.status_code, 200)
        self.assertIn(b"PARTE DE TRABAJO", physical_response.data)

        with self.app.app_context():
            physical = db.session.get(Orders, self.order_id)
            physical.order_details[0].line_type = "design_service"
            db.session.commit()

        design_response = self.client.get(self._detail_url(), headers=self._auth_header())
        self.assertEqual(design_response.status_code, 200)
        self.assertIn(b"No disponible para dise", design_response.data)


def deepcopy_json(value):
    return json.loads(json.dumps(value))


if __name__ == "__main__":
    unittest.main()

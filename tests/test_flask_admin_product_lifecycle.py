import ast
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ADMIN_PATH = SRC_DIR / "api" / "admin.py"
MODELS_PATH = SRC_DIR / "api" / "models.py"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def class_node(class_name):
    tree = ast.parse(ADMIN_PATH.read_text(encoding="utf-8"))
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )


def class_assignment(class_name, attribute):
    node = class_node(class_name)
    assignment = next(
        item
        for item in node.body
        if isinstance(item, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == attribute for target in item.targets)
    )
    return ast.literal_eval(assignment.value)


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ADMIN_DEPS = all(
    has_package(package)
    for package in (
        "flask",
        "flask_admin",
        "flask_sqlalchemy",
        "sqlalchemy",
        "slugify",
        "wtforms",
    )
)


class ProductLifecycleAdminConfigurationTest(unittest.TestCase):
    def test_form_exposes_both_lifecycle_fields_with_distinct_labels(self):
        form_columns = class_assignment("ProductAdminView", "form_columns")
        labels = class_assignment("ProductAdminView", "column_labels")
        form_args = class_assignment("ProductAdminView", "form_args")

        self.assertIn("published", form_columns)
        self.assertIn("available_for_sale", form_columns)
        self.assertEqual(labels["published"], "Publicado")
        self.assertEqual(labels["available_for_sale"], "Disponible para venta")
        self.assertNotEqual(
            form_args["published"]["description"],
            form_args["available_for_sale"]["description"],
        )
        self.assertIn("ficha pública", form_args["published"]["description"])
        self.assertIn("nuevos pedidos", form_args["available_for_sale"]["description"])
        self.assertIs(form_args["published"]["default"], True)
        self.assertIs(form_args["available_for_sale"]["default"], True)

    def test_filters_include_both_lifecycle_fields(self):
        filters = class_assignment("ProductAdminView", "column_filters")

        self.assertIn("published", filters)
        self.assertIn("available_for_sale", filters)

    def test_public_serializer_still_does_not_expose_published(self):
        source = MODELS_PATH.read_text(encoding="utf-8")
        model = next(
            node
            for node in ast.parse(source).body
            if isinstance(node, ast.ClassDef) and node.name == "Products"
        )
        serializer = next(
            node
            for node in model.body
            if isinstance(node, ast.FunctionDef) and node.name == "serialize"
        )
        serializer_source = ast.get_source_segment(source, serializer)

        self.assertNotIn('"published":', serializer_source)
        self.assertIn('"available_for_sale":', serializer_source)


if HAS_ADMIN_DEPS:
    from flask import Flask, get_flashed_messages
    from sqlalchemy.exc import IntegrityError

    from api import admin as admin_module
    from api.models import Categories, Products, db


@unittest.skipUnless(
    HAS_ADMIN_DEPS,
    "Flask-Admin/SQLAlchemy/WTForms test dependencies are not installed.",
)
class ProductLifecycleAdminFunctionalTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="product-lifecycle-admin-test",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)

        with self.app.app_context():
            Categories.__table__.create(bind=db.engine)
            Products.__table__.create(bind=db.engine)
            category = Categories(
                nombre="Rejas admin",
                descripcion="Admin lifecycle tests",
                slug="rejas-admin",
            )
            db.session.add(category)
            db.session.commit()
            self.category_id = category.id

        self.view = admin_module.ProductAdminView(Products, db.session)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            Products.__table__.drop(bind=db.engine)
            Categories.__table__.drop(bind=db.engine)

    def make_product(self, suffix, *, published=None, available_for_sale=None):
        values = {
            "nombre": f"Reja admin {suffix}",
            "slug": f"reja-admin-{suffix}",
            "descripcion": "Producto de prueba",
            "precio": 100.0,
            "categoria_id": self.category_id,
        }
        if published is not None:
            values["published"] = published
        if available_for_sale is not None:
            values["available_for_sale"] = available_for_sale
        return Products(**values)

    def persist_through_admin_hook(self, product, *, is_created=True):
        with self.app.test_request_context("/admin/products/new"):
            self.view.on_model_change(None, product, is_created)
            db.session.add(product)
            db.session.commit()
            messages = get_flashed_messages(with_categories=True)
        return messages

    def test_list_and_form_expose_lifecycle_fields(self):
        with self.app.test_request_context("/admin/products/new"):
            list_columns = [name for name, _label in self.view.get_list_columns()]
            form = self.view.create_form()

        self.assertIn("published", list_columns)
        self.assertIn("available_for_sale", list_columns)
        self.assertEqual(form.published.label.text, "Publicado")
        self.assertEqual(form.available_for_sale.label.text, "Disponible para venta")
        self.assertIn("sitemap", form.published.description)
        self.assertIn("nuevos pedidos", form.available_for_sale.description)
        self.assertIs(form.published.data, True)
        self.assertIs(form.available_for_sale.data, True)

    def test_all_valid_states_can_be_persisted(self):
        states = ((True, True), (True, False), (False, False))

        for index, (published, available_for_sale) in enumerate(states):
            product = self.make_product(
                str(index),
                published=published,
                available_for_sale=available_for_sale,
            )
            self.persist_through_admin_hook(product)
            self.assertIs(product.published, published)
            self.assertIs(product.available_for_sale, available_for_sale)

    def test_new_product_preserves_available_defaults(self):
        product = self.make_product("defaults")

        self.persist_through_admin_hook(product)

        self.assertIs(product.published, True)
        self.assertIs(product.available_for_sale, True)

    def test_unpublishing_normalizes_sale_availability_and_flashes_warning(self):
        product = self.make_product(
            "normalize",
            published=False,
            available_for_sale=True,
        )

        messages = self.persist_through_admin_hook(product)

        self.assertIs(product.published, False)
        self.assertIs(product.available_for_sale, False)
        self.assertIn(
            (
                "warning",
                "Al despublicar el producto también se ha desactivado su disponibilidad para venta.",
            ),
            messages,
        )

    def test_lifecycle_constraint_error_is_translated(self):
        lifecycle_error = IntegrityError(
            "UPDATE products",
            {},
            Exception("ck_products_published_available_for_sale"),
        )

        with self.app.test_request_context("/admin/products/edit"):
            handled = self.view.handle_view_exception(lifecycle_error)
            messages = get_flashed_messages(with_categories=True)

        self.assertIs(handled, True)
        self.assertIn(
            (
                "error",
                "Un producto no publicado no puede estar disponible para la venta.",
            ),
            messages,
        )


if __name__ == "__main__":
    unittest.main()

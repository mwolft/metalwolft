import ast
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ADMIN_PATH = SRC_DIR / "api" / "admin.py"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def source():
    return ADMIN_PATH.read_text(encoding="utf-8")


def setup_admin_node():
    for node in ast.parse(source()).body:
        if isinstance(node, ast.FunctionDef) and node.name == "setup_admin":
            return node
    raise AssertionError("setup_admin not found")


def literal_keyword(call, name):
    keyword = next((item for item in call.keywords if item.arg == name), None)
    return ast.literal_eval(keyword.value) if keyword else None


def registered_views():
    views = []
    for statement in setup_admin_node().body:
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Attribute)
            and statement.value.func.attr == "add_view"
        ):
            continue

        view = statement.value.args[0]
        if not isinstance(view, ast.Call) or not isinstance(view.func, ast.Name):
            raise AssertionError("admin.add_view must receive a view constructor")
        model = view.args[0]
        if not isinstance(model, ast.Name):
            raise AssertionError("model view must receive a model class")
        views.append(
            {
                "view": view.func.id,
                "model": model.id,
                "name": literal_keyword(view, "name"),
                "category": literal_keyword(view, "category"),
                "endpoint": literal_keyword(view, "endpoint"),
                "url": literal_keyword(view, "url"),
            }
        )
    return views


class FlaskAdminNavigationTest(unittest.TestCase):
    def test_index_is_named_resumen_without_changing_its_route(self):
        self.assertIn("index_view=SecureAdminIndexView(name='Resumen')", source())
        self.assertIn("url='/admin'", source())

    def test_views_follow_the_expected_native_category_order(self):
        self.assertEqual(
            [(item["category"], item["name"]) for item in registered_views()],
            [
                ("Catálogo", "Categorías"),
                ("Catálogo", "Subcategorías"),
                ("Catálogo", "Productos"),
                ("Catálogo", "Imágenes de producto"),
                ("Ventas", "Pedidos"),
                ("Ventas", "Líneas de pedido"),
                ("Ventas", "Carritos"),
                ("Diseño previo", "Solicitudes"),
                ("Diseño previo", "Configuración"),
                ("Diseño previo", "Tarifas"),
                ("Clientes", "Usuarios"),
                ("Clientes", "Favoritos"),
                ("Clientes", "Comentarios"),
                ("Facturación", "Facturas"),
                ("Facturación", "Facturas manuales"),
                ("Facturación", "Facturas recibidas"),
                ("Facturación", "VeriFactu"),
                ("Contenido", "Publicaciones"),
                ("Configuración", "Entrega estimada"),
            ],
        )

    def test_view_classes_models_and_default_endpoints_are_unchanged(self):
        expected = [
            ("SafeModelView", "Categories", "categories"),
            ("SafeModelView", "Subcategories", "subcategories"),
            ("ProductAdminView", "Products", "products"),
            ("SafeModelView", "ProductImages", "productimages"),
            ("OrderAdminView", "Orders", "orders"),
            ("OrderDetailsAdminView", "OrderDetails", "orderdetails"),
            ("CartAdminView", "Cart", "cart"),
            ("DesignRequestAdminView", "DesignRequest", "designrequest"),
            ("DesignServiceConfigAdminView", "DesignServiceConfig", "designserviceconfig"),
            ("DesignServicePriceTierAdminView", "DesignServicePriceTier", "designservicepricetier"),
            ("UsersAdminView", "Users", "users"),
            ("FavoritesAdminView", "Favorites", "favorites"),
            ("SafeModelView", "Comments", "comments"),
            ("InvoiceAdminView", "Invoices", "invoices"),
            ("ManualInvoiceDraftAdminView", "ManualInvoiceDraft", "manualinvoicedraft"),
            ("SupplierInvoiceAdminView", "SupplierInvoice", "supplierinvoice"),
            ("VeriFactuRecordAdminView", "VeriFactuRecord", "verifacturecord"),
            ("SafeModelView", "Posts", "posts"),
            ("SafeModelView", "DeliveryEstimateConfig", "deliveryestimateconfig"),
        ]
        actual = registered_views()
        self.assertEqual(
            [(item["view"], item["model"], item["model"].lower()) for item in actual],
            expected,
        )
        self.assertTrue(all(item["endpoint"] is None and item["url"] is None for item in actual))
        self.assertEqual(
            [f"/admin/{endpoint}/" for _, _, endpoint in expected],
            [f"/admin/{item['model'].lower()}/" for item in actual],
        )

    def test_existing_admin_access_control_remains_in_place(self):
        text = source()
        self.assertIn("class SecureAdminIndexView(AdminIndexView):", text)
        self.assertIn("class SecureModelView(ModelView):", text)
        self.assertIn("request.authorization", text)
        self.assertIn("WWW-Authenticate", text)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ADMIN_PATH = SRC_DIR / "api" / "admin.py"
MASTER_TEMPLATE = SRC_DIR / "templates" / "admin" / "master.html"
ADMIN_CSS = SRC_DIR / "static" / "admin" / "metalwolft-admin.css"
ADMIN_FAVICON = SRC_DIR / "static" / "admin" / "favicon.png"
ADMIN_ISOTYPE = SRC_DIR / "static" / "admin" / "metalwolft-isotipo.webp"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_ADMIN_DEPS = all(
    has_package(package)
    for package in ("flask", "flask_admin", "flask_sqlalchemy", "sqlalchemy", "slugify")
)

if HAS_ADMIN_DEPS:
    from flask import Flask  # noqa: E402

    import api.admin as admin_module  # noqa: E402
    from api.models import db  # noqa: E402


class FlaskAdminIdentitySourceTest(unittest.TestCase):
    def test_admin_master_preserves_flask_admin_navigation_blocks(self):
        template = MASTER_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("{% extends admin_base_template %}", template)
        self.assertIn("{{ layout.menu() }}", template)
        self.assertIn("{{ layout.menu_links() }}", template)
        self.assertIn("{% block access_control %}", template)
        self.assertIn("{% if admin_view.extra_css %}", template)
        self.assertIn("{% if admin_view.extra_js %}", template)

    def test_master_uses_the_admin_identity_and_assets(self):
        template = MASTER_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("METALWOLFT", template)
        self.assertIn("Administración", template)
        self.assertNotIn(">MetalWolft.com<", template)
        self.assertIn("admin/metalwolft-isotipo.webp", template)
        self.assertIn("admin/favicon.png", template)
        self.assertIn("admin/metalwolft-admin.css", template)

    def test_identity_assets_and_css_are_admin_scoped(self):
        self.assertGreater(ADMIN_FAVICON.stat().st_size, 0)
        self.assertGreater(ADMIN_ISOTYPE.stat().st_size, 0)
        stylesheet = ADMIN_CSS.read_text(encoding="utf-8")

        self.assertIn(".navbar .mw-admin-brand", stylesheet)
        self.assertIn(".mw-admin-brand__icon", stylesheet)
        self.assertIn(".mw-admin-brand__subtitle", stylesheet)
        self.assertNotIn("table", stylesheet)
        self.assertNotIn("form", stylesheet)

    def test_admin_title_no_longer_uses_the_public_domain_brand(self):
        source = ADMIN_PATH.read_text(encoding="utf-8")

        self.assertIn("name='MetalWolft Administración'", source)
        self.assertNotIn("name='MetalWolft.com'", source)


@unittest.skipUnless(HAS_ADMIN_DEPS, "Flask-Admin test dependencies are not installed.")
class FlaskAdminIdentityRenderTest(unittest.TestCase):
    def setUp(self):
        admin_module.ADMIN_USER = "admin"
        admin_module.ADMIN_PW = "secret"
        self.app = Flask(
            __name__,
            template_folder=str(SRC_DIR / "templates"),
            static_folder=str(SRC_DIR / "static"),
        )
        self.app.config.update(
            SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        admin_module.setup_admin(self.app)
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _auth_header(self):
        import base64

        return {"Authorization": f"Basic {base64.b64encode(b'admin:secret').decode('ascii')}"}

    def test_protected_admin_renders_identity_assets_and_native_navigation(self):
        response = self.client.get("/admin/", headers=self._auth_header())

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"METALWOLFT", response.data)
        self.assertIn("Administración".encode("utf-8"), response.data)
        self.assertIn(b"/static/admin/favicon.png", response.data)
        self.assertIn(b"/static/admin/metalwolft-admin.css", response.data)
        for label in ("Resumen", "Catálogo", "Ventas", "Diseño previo", "Clientes", "Facturación"):
            self.assertIn(label.encode("utf-8"), response.data)

    def test_existing_protected_view_route_still_resolves(self):
        response = self.client.get("/admin/orders/", headers=self._auth_header())
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()

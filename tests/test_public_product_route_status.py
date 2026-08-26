import importlib
import importlib.util
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def has_package(package):
    try:
        return importlib.util.find_spec(package) is not None
    except (ImportError, ValueError):
        return False


HAS_APP_DEPENDENCIES = all(
    has_package(package)
    for package in (
        "flask",
        "flask_admin",
        "flask_cors",
        "flask_jwt_extended",
        "flask_mail",
        "flask_migrate",
        "flask_sqlalchemy",
        "flask_talisman",
        "sqlalchemy",
    )
)
APP_IMPORT_ERROR = None
APP_MODULE = None

if HAS_APP_DEPENDENCIES:
    try:
        APP_MODULE = importlib.import_module("app")
    except Exception as error:  # pragma: no cover - reported through the skip reason
        APP_IMPORT_ERROR = error


@unittest.skipUnless(
    HAS_APP_DEPENDENCIES and APP_MODULE is not None,
    f"Flask app dependencies are unavailable: {APP_IMPORT_ERROR or 'missing package'}",
)
class PublicProductRouteStatusTest(unittest.TestCase):
    def setUp(self):
        APP_MODULE.app.config.update(TESTING=True)
        self.client = APP_MODULE.app.test_client()
        self.category = SimpleNamespace(id=10, slug="rejas-publicas")
        self.product = SimpleNamespace(id=20, slug="reja-disponible")

    def _shell_response(self, *args, **kwargs):
        return APP_MODULE.app.response_class("legacy shell", status=200)

    def test_valid_product_continues_to_shell_for_browser(self):
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            return_value=(self.category, self.product),
        ), patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ) as send_shell:
            response = self.client.get("/rejas-publicas/reja-disponible")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "legacy shell")
        send_shell.assert_called_once()

    def test_valid_product_reaches_prerender_for_googlebot(self):
        prerender_response = SimpleNamespace(
            content=b"prerendered product",
            status_code=200,
            headers={},
        )
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            return_value=(self.category, self.product),
        ), patch.object(
            APP_MODULE.session,
            "get",
            return_value=prerender_response,
        ) as prerender_get:
            response = self.client.get(
                "/rejas-publicas/reja-disponible",
                headers={"User-Agent": "Googlebot"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(), b"prerendered product")
        prerender_get.assert_called_once()

    def test_missing_and_unpublished_products_return_same_404_before_prerender(self):
        for product_slug in ("no-existe", "reja-no-publicada"):
            with self.subTest(product_slug=product_slug), patch.object(
                APP_MODULE,
                "resolve_publicly_accessible_product_by_slugs",
                return_value=(self.category, None),
            ), patch.object(APP_MODULE.session, "get") as prerender_get, patch.object(
                APP_MODULE,
                "send_from_directory",
            ) as send_shell:
                browser_response = self.client.get(
                    f"/rejas-publicas/{product_slug}"
                )
                bot_response = self.client.get(
                    f"/rejas-publicas/{product_slug}",
                    headers={"User-Agent": "Googlebot"},
                )

            for response in (browser_response, bot_response):
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    response.headers["X-Robots-Tag"],
                    "noindex, nofollow",
                )
                self.assertEqual(response.get_json(), {"message": "Product not found"})
            prerender_get.assert_not_called()
            send_shell.assert_not_called()

    def test_resolution_failure_returns_safe_503_before_prerender(self):
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            side_effect=RuntimeError("private database detail"),
        ), patch.object(APP_MODULE.session, "get") as prerender_get, patch.object(
            APP_MODULE,
            "send_from_directory",
        ) as send_shell:
            browser_response = self.client.get(
                "/rejas-publicas/reja-disponible"
            )
            bot_response = self.client.get(
                "/rejas-publicas/reja-disponible",
                headers={"User-Agent": "Googlebot"},
            )

        for response in (browser_response, bot_response):
            self.assertEqual(response.status_code, 503)
            self.assertEqual(
                response.get_json(),
                {"message": "Service temporarily unavailable"},
            )
            self.assertNotIn(
                "private database detail",
                response.get_data(as_text=True),
            )
        prerender_get.assert_not_called()
        send_shell.assert_not_called()

    def test_next_only_account_orders_route_is_not_owned_by_legacy(self):
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
        ) as resolve_product, patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ) as send_shell:
            response = self.client.get("/mi-cuenta/pedidos")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")
        resolve_product.assert_not_called()
        send_shell.assert_not_called()

    def test_non_product_route_ignores_catalog_resolution_failure(self):
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            side_effect=RuntimeError("catalog unavailable"),
        ) as resolve_product, patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ):
            response = self.client.get("/mi-cuenta/pedidos")

        self.assertEqual(response.status_code, 404)
        resolve_product.assert_not_called()

    def test_reserved_namespaces_assets_and_options_do_not_query_catalog(self):
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
        ) as resolve_product, patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ), patch.object(
            APP_MODULE,
            "_legacy_spa_asset_exists",
            side_effect=lambda path: path == "/assets/application.js",
        ):
            api_response = self.client.get("/api/not-a-real-endpoint")
            admin_response = self.client.get("/admin/not-a-real-endpoint")
            static_response = self.client.get("/static/not-a-real-file")
            asset_response = self.client.get("/assets/application.js")
            options_response = self.client.options(
                "/rejas-publicas/reja-disponible"
            )

        for response in (api_response, admin_response, static_response):
            self.assertNotEqual(response.status_code, 503)
        self.assertEqual(asset_response.status_code, 200)
        self.assertEqual(options_response.status_code, 200)
        resolve_product.assert_not_called()

    def test_design_request_preflight_allows_idempotency_key(self):
        origin = "https://example-3002.app.github.dev"
        response = self.client.options(
            "/api/design-requests",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization, content-type, idempotency-key",
            },
        )

        self.assertIn(response.status_code, {200, 204})
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin)
        allowed_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
        self.assertIn("authorization", allowed_headers)
        self.assertIn("content-type", allowed_headers)
        self.assertIn("idempotency-key", allowed_headers)

    def test_static_public_private_transactional_and_category_routes_reach_shell(self):
        paths = (
            "/",
            "/contact",
            "/mi-cuenta",
            "/checkout-form",
            "/rejas-para-ventanas",
        )
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            side_effect=RuntimeError("catalog unavailable"),
        ) as resolve_product, patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ) as send_shell:
            responses = [self.client.get(path) for path in paths]

        self.assertTrue(all(response.status_code == 200 for response in responses))
        resolve_product.assert_not_called()
        self.assertEqual(send_shell.call_count, len(paths))

    def test_legacy_static_allowlist_matches_exact_react_router_paths(self):
        layout_source = (SRC_DIR / "front" / "js" / "Layout.jsx").read_text(
            encoding="utf-8"
        )
        declared_static_paths = set(
            re.findall(r'<Route path="(/[^":*]*)"', layout_source)
        )

        self.assertEqual(
            declared_static_paths,
            set(APP_MODULE.LEGACY_SPA_STATIC_PATHS),
        )

    def test_static_route_reaches_prerender_for_googlebot(self):
        prerender_response = SimpleNamespace(
            content=b"prerendered static route",
            status_code=200,
            headers={},
        )
        with patch.object(
            APP_MODULE.session,
            "get",
            return_value=prerender_response,
        ) as prerender_get, patch.object(
            APP_MODULE,
            "send_from_directory",
        ) as send_shell:
            response = self.client.get(
                "/contact",
                headers={"User-Agent": "Googlebot"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(), b"prerendered static route")
        prerender_get.assert_called_once()
        send_shell.assert_not_called()

    def test_static_route_with_query_and_trailing_slash_remains_valid(self):
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
        ) as resolve_product, patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ):
            response = self.client.get("/contact/?utm_source=test")

        self.assertEqual(response.status_code, 200)
        resolve_product.assert_not_called()

    def test_unknown_routes_return_404_before_prerender_and_shell(self):
        paths = (
            "/inventada",
            "/categoria-inventada/producto-inventado",
            "/uno/dos/tres",
            "/mi-cuenta/seccion-inventada",
            "/catalogo",
        )
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            return_value=(None, None),
        ), patch.object(APP_MODULE.session, "get") as prerender_get, patch.object(
            APP_MODULE,
            "send_from_directory",
        ) as send_shell:
            for path in paths:
                with self.subTest(path=path):
                    browser_response = self.client.get(path)
                    bot_response = self.client.get(
                        path,
                        headers={"User-Agent": "Googlebot"},
                    )
                    self.assertEqual(browser_response.status_code, 404)
                    self.assertEqual(bot_response.status_code, 404)
                    self.assertEqual(
                        browser_response.headers["X-Robots-Tag"],
                        "noindex, nofollow",
                    )

        prerender_get.assert_not_called()
        send_shell.assert_not_called()

    def test_head_unknown_route_returns_404_without_body(self):
        with patch.object(APP_MODULE.session, "get") as prerender_get, patch.object(
            APP_MODULE,
            "send_from_directory",
        ) as send_shell:
            response = self.client.head("/inventada")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_data(), b"")
        prerender_get.assert_not_called()
        send_shell.assert_not_called()

    def test_next_only_routes_are_not_added_to_legacy_allowlist(self):
        paths = (
            "/checkout",
            "/registro",
            "/forgot-password",
            "/mi-cuenta/pedidos",
        )
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
        ) as resolve_product, patch.object(
            APP_MODULE,
            "send_from_directory",
        ) as send_shell:
            responses = [self.client.get(path) for path in paths]

        self.assertTrue(all(response.status_code == 404 for response in responses))
        resolve_product.assert_not_called()
        send_shell.assert_not_called()

    def test_head_missing_product_returns_404_without_body_or_fallback(self):
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            return_value=(self.category, None),
        ), patch.object(APP_MODULE.session, "get") as prerender_get, patch.object(
            APP_MODULE,
            "send_from_directory",
        ) as send_shell:
            response = self.client.head("/rejas-publicas/no-existe")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_data(), b"")
        self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")
        prerender_get.assert_not_called()
        send_shell.assert_not_called()

    def test_query_string_does_not_change_product_resolution(self):
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            return_value=(self.category, None),
        ) as resolve_product:
            response = self.client.get(
                "/rejas-publicas/no-existe?utm_source=test"
            )

        self.assertEqual(response.status_code, 404)
        resolve_product.assert_called_once_with("rejas-publicas", "no-existe")

    def test_redirects_and_gone_routes_keep_precedence(self):
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
        ) as resolve_product, patch.object(
            APP_MODULE.session,
            "get",
        ) as prerender_get:
            redirect_response = self.client.get(
                "/rejas/rejas-para-ventanas-pittsburgh"
            )
            gone_response = self.client.get("/preguntas-frecuentes")

        self.assertEqual(redirect_response.status_code, 301)
        self.assertEqual(gone_response.status_code, 410)
        resolve_product.assert_not_called()
        prerender_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()

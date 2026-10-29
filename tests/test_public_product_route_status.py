import importlib
import importlib.util
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

    def test_retired_poole_redirects_directly_to_essex(self):
        for method in ("get", "head"):
            with self.subTest(method=method):
                response = getattr(self.client, method)("/rejas-para-ventanas/reja-fija-poole")
                self.assertEqual(response.status_code, 301)
                self.assertEqual(
                    response.headers["Location"],
                    "https://www.metalwolft.com/rejas-para-ventanas/reja-fija-essex",
                )

    def test_product_outside_verified_category_does_not_redirect_or_serve_spa(self):
        product = SimpleNamespace(id=20, slug="reja-fija-albany")
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            return_value=(self.category, product),
        ), patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ) as send_shell:
            response = self.client.get("/rejas-publicas/reja-fija-albany")

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Location", response.headers)
        send_shell.assert_not_called()

    def test_verified_sellable_product_redirects_get_and_head(self):
        category = SimpleNamespace(id=10, slug="rejas-para-ventanas")
        product = SimpleNamespace(id=20, slug="reja-fija-albany", available_for_sale=True)
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            return_value=(category, product),
        ) as resolve_product, patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ) as send_shell:
            response = self.client.get(
                "/rejas-para-ventanas/reja-fija-albany"
                "?utm_source=email&utm_campaign=autumn&token=secret&alto=120"
            )
            head_response = self.client.head("/rejas-para-ventanas/reja-fija-albany")

        destination = "https://www.metalwolft.com/rejas-para-ventanas/reja-fija-albany"
        self.assertEqual(response.status_code, 302)
        self.assertEqual(head_response.status_code, 302)
        self.assertEqual(response.headers["Location"], destination + "?utm_source=email&utm_campaign=autumn")
        self.assertEqual(head_response.headers["Location"], destination)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertEqual(resolve_product.call_count, 2)
        send_shell.assert_not_called()

    def test_verified_unavailable_product_redirects_without_reenabling_sale(self):
        category = SimpleNamespace(id=10, slug="rejas-para-ventanas")
        for slug in ("reja-puerta-essex",):
            product = SimpleNamespace(id=20, slug=slug, available_for_sale=False)
            with self.subTest(slug=slug), patch.object(
                APP_MODULE,
                "resolve_publicly_accessible_product_by_slugs",
                return_value=(category, product),
            ), patch.object(APP_MODULE, "send_from_directory") as send_shell:
                response = self.client.get(f"/rejas-para-ventanas/{slug}")
                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.headers["Location"],
                    f"https://www.metalwolft.com/rejas-para-ventanas/{slug}",
                )
                self.assertFalse(product.available_for_sale)
                send_shell.assert_not_called()

    def test_only_the_28_verified_product_slugs_can_redirect(self):
        self.assertEqual(len(APP_MODULE.NEXT_PRODUCT_REDIRECT_SLUGS), 28)
        category = SimpleNamespace(id=10, slug="rejas-para-ventanas")
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            side_effect=lambda category_slug, product_slug: (
                category,
                SimpleNamespace(slug=product_slug),
            ),
        ):
            for slug in APP_MODULE.NEXT_PRODUCT_REDIRECT_SLUGS:
                with self.subTest(slug=slug):
                    response = self.client.get(f"/rejas-para-ventanas/{slug}")
                    self.assertEqual(response.status_code, 301 if slug == "reja-fija-poole" else 302)
            response = self.client.get("/rejas-para-ventanas/reja-fija-futura")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Location", response.headers)

    def test_missing_public_catalog_product_does_not_redirect(self):
        category = SimpleNamespace(id=10, slug="rejas-para-ventanas")
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            return_value=(category, None),
        ):
            response = self.client.get("/rejas-para-ventanas/no-existe")

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Location", response.headers)

    def test_unpublished_verified_product_does_not_redirect(self):
        category = SimpleNamespace(id=10, slug="rejas-para-ventanas")
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            return_value=(category, None),
        ), patch.object(APP_MODULE, "send_from_directory") as send_shell:
            response = self.client.get("/rejas-para-ventanas/reja-fija-albany")

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Location", response.headers)
        send_shell.assert_not_called()

    def test_verified_product_redirects_before_prerender_for_googlebot(self):
        category = SimpleNamespace(id=10, slug="rejas-para-ventanas")
        product = SimpleNamespace(id=20, slug="reja-fija-albany")
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            return_value=(category, product),
        ), patch.object(
            APP_MODULE.session,
            "get",
        ) as prerender_get:
            response = self.client.get(
                "/rejas-para-ventanas/reja-fija-albany",
                headers={"User-Agent": "Googlebot"},
            )

        self.assertEqual(response.status_code, 302)
        prerender_get.assert_not_called()

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

    def test_confirmed_static_routes_redirect_and_transactional_routes_keep_shell(self):
        redirects = {
            "/": "/",
            "/contact": "/contact",
            "/rejas-para-ventanas": "/rejas-para-ventanas",
            "/cookies-esenciales": "/politica-cookies",
            "/informacion-recogida": "/politica-privacidad",
        }
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
            side_effect=RuntimeError("catalog unavailable"),
        ) as resolve_product, patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ) as send_shell:
            responses = {path: self.client.get(path) for path in redirects}
            retained = [self.client.get(path) for path in APP_MODULE.LEGACY_SPA_RETAINED_PATHS]

        for path, destination in redirects.items():
            self.assertEqual(responses[path].status_code, 301)
            self.assertEqual(
                responses[path].headers["Location"],
                f"https://www.metalwolft.com{destination}",
            )
        self.assertTrue(all(response.status_code == 200 for response in retained))
        resolve_product.assert_not_called()
        self.assertEqual(send_shell.call_count, len(retained))

    def test_legacy_shell_is_retained_for_account_cart_and_transactional_paths(self):
        self.assertEqual(
            APP_MODULE.LEGACY_SPA_RETAINED_PATHS,
            {
                "/cart", "/checkout-form", "/login", "/mi-cuenta",
                "/profile", "/thank-you",
            },
        )

    def test_static_redirect_destinations_exist_in_next(self):
        next_app = ROOT_DIR / "apps" / "web-next" / "app"
        for destination in APP_MODULE.NEXT_STOREFRONT_REDIRECTS.values():
            with self.subTest(destination=destination):
                self.assertTrue((next_app / destination.strip("/") / "page.tsx").is_file())

    def test_redirected_static_route_does_not_reach_prerender_for_googlebot(self):
        with patch.object(
            APP_MODULE.session,
            "get",
        ) as prerender_get, patch.object(
            APP_MODULE,
            "send_from_directory",
        ) as send_shell:
            response = self.client.get(
                "/contact",
                headers={"User-Agent": "Googlebot"},
            )

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers["Location"], "https://www.metalwolft.com/contact")
        prerender_get.assert_not_called()
        send_shell.assert_not_called()

    def test_static_route_with_query_and_trailing_slash_redirects(self):
        with patch.object(
            APP_MODULE,
            "resolve_publicly_accessible_product_by_slugs",
        ) as resolve_product, patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ):
            response = self.client.get("/contact/?utm_source=test")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response.headers["Location"],
            "https://www.metalwolft.com/contact?utm_source=test",
        )
        resolve_product.assert_not_called()

    def test_account_cart_and_recovery_queries_stay_on_legacy_origin(self):
        paths = (
            "/login?next=%2Fcheckout",
            "/cart?step=payment",
            "/mi-cuenta",
            "/profile",
            "/checkout-form",
            "/thank-you?checkout_token=opaque",
        )
        with patch.object(
            APP_MODULE,
            "send_from_directory",
            side_effect=self._shell_response,
        ) as send_shell:
            for path in paths:
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertNotIn("Location", response.headers)
        self.assertEqual(send_shell.call_count, len(paths))

    def test_reset_password_redirect_preserves_all_parameters_without_caching(self):
        path = "/reset-password?token=opaque%2Bvalue&source=email&next=%2Flogin"
        with patch.object(APP_MODULE, "send_from_directory") as send_shell:
            for method in ("get", "head"):
                with self.subTest(method=method):
                    response = getattr(self.client, method)(path)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(
                        response.headers["Location"],
                        "https://www.metalwolft.com/reset-password"
                        "?token=opaque%2Bvalue&source=email&next=%2Flogin",
                    )
                    self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertNotEqual(self.client.post(path).status_code, 302)
        send_shell.assert_not_called()

    def test_carrito_has_no_legacy_route_or_forced_redirect(self):
        response = self.client.get("/carrito")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Location", response.headers)

    def test_retired_auxiliary_routes_return_404_and_non_get_is_not_redirected(self):
        with patch.object(APP_MODULE, "send_from_directory") as send_shell:
            for path in ("/favoritos", "/carrusel", "/product", "/pay-pal-button"):
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 404)
            for path in ("/cart", "/contact", "/rejas-para-ventanas/reja-fija-albany"):
                with self.subTest(path=path):
                    response = self.client.post(path)
                    self.assertNotIn(response.status_code, {301, 302})
                    self.assertNotIn("Location", response.headers)
            self.assertNotEqual(self.client.get("/admin/not-a-real-endpoint").status_code, 301)
        send_shell.assert_not_called()

    def test_api_webhooks_and_admin_assets_remain_outside_spa_routing(self):
        rules = {rule.rule: rule for rule in APP_MODULE.app.url_map.iter_rules()}
        self.assertIn("POST", rules["/api/webhook"].methods)
        self.assertIn("POST", rules["/api/paypal/webhook"].methods)
        self.assertNotEqual(rules["/api/webhook"].endpoint, "serve_spa")
        self.assertNotEqual(rules["/api/paypal/webhook"].endpoint, "serve_spa")

        response = self.client.get("/static/admin/order_sent_email_options.js")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Location", response.headers)
        response.close()

    def test_legacy_information_metadata_points_to_current_privacy_page(self):
        response = self.client.get("/api/seo/informacion-recogida")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["canonical"],
            "https://www.metalwolft.com/politica-privacidad",
        )

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

    def test_retired_category_routes_do_not_serve_legacy_shell(self):
        paths = (
            "/vallados-metalicos-exteriores",
            "/puertas-peatonales-metalicas",
            "/puertas-correderas-interiores",
            "/puertas-correderas-exteriores",
            "/cerramientos-de-cocina-con-cristal",
            "/vallados-metalicos",
            "/puertas-peatonales",
        )
        with patch.object(APP_MODULE, "send_from_directory") as send_shell:
            for path in paths:
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 404)
                    self.assertEqual(response.headers["X-Robots-Tag"], "noindex, nofollow")
        send_shell.assert_not_called()

    def test_historical_reja_redirects_are_direct_and_delhi_is_retired(self):
        redirects = {
            "pittsburgh": "reja-fija-pittsburgh",
            "livingston": "reja-fija-livingston",
            "lancaster": "reja-fija-lancaster",
            "essex": "reja-fija-essex",
        }
        with patch.object(
            APP_MODULE, "resolve_publicly_accessible_product_by_slugs", return_value=(None, None)
        ):
            for old_slug, new_slug in redirects.items():
                with self.subTest(slug=old_slug):
                    response = self.client.get(f"/rejas/rejas-para-ventanas-{old_slug}")
                    self.assertEqual(response.status_code, 301)
                    self.assertEqual(
                        response.headers["Location"],
                        f"https://www.metalwolft.com/rejas-para-ventanas/{new_slug}",
                    )

            old_home = self.client.head("/index.php")
            self.assertEqual(old_home.status_code, 301)
            self.assertEqual(old_home.headers["Location"], "https://www.metalwolft.com/")

            delhi = self.client.get("/rejas/rejas-para-ventanas-delhi")
            self.assertEqual(delhi.status_code, 404)
            self.assertNotIn("Location", delhi.headers)

            retired_alias = self.client.get(
                "/puertas-correderas/puerta-corredera-canberra"
            )
            self.assertEqual(retired_alias.status_code, 404)
            self.assertNotIn("Location", retired_alias.headers)


if __name__ == "__main__":
    unittest.main()

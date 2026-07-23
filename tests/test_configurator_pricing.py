import importlib
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def ensure_optional_flask_modules_for_local_tests():
    if importlib.util.find_spec("flask") is None:
        fake_flask = types.ModuleType("flask")
        fake_flask.current_app = SimpleNamespace(
            config={},
            logger=SimpleNamespace(info=lambda *args, **kwargs: None, error=lambda *args, **kwargs: None),
        )
        fake_flask.jsonify = lambda *args, **kwargs: {"args": args, "kwargs": kwargs}
        fake_flask.url_for = lambda *args, **kwargs: ""
        sys.modules["flask"] = fake_flask

    if importlib.util.find_spec("flask_mail") is None:
        fake_flask_mail = types.ModuleType("flask_mail")

        class FakeMail:
            def send(self, message):
                return None

        class FakeMessage:
            def __init__(self, *args, **kwargs):
                pass

            def attach(self, *args, **kwargs):
                return None

        fake_flask_mail.Mail = FakeMail
        fake_flask_mail.Message = FakeMessage
        sys.modules["flask_mail"] = fake_flask_mail


ensure_optional_flask_modules_for_local_tests()

from api.utils import (
    ANCHORAGE_FRONT_PLATES,
    ANCHORAGE_INTERIOR_HOLES,
    ANCHORAGE_LEGACY_FRONT_HOLES,
    ANCHORAGE_METAL_CLAWS,
    LEGACY_ANCHORAGE_RECONFIGURE_MESSAGE,
    build_configured_reja_quote,
    serialize_configurator_configuration,
)

DEFAULT_COLOR = "satinado_blanco"
PRICE_M2 = 100.0


def quote(alto, ancho, anclaje=ANCHORAGE_INTERIOR_HOLES, color=DEFAULT_COLOR):
    return build_configured_reja_quote(
        alto_cm=alto,
        ancho_cm=ancho,
        precio_m2=PRICE_M2,
        anclaje=anclaje,
        color=color,
    )


class FakeProductQuery:
    def __init__(self, *, exists=True, available_for_sale=True):
        self.exists = exists
        self.available_for_sale = available_for_sale

    def get(self, product_id):
        if not self.exists:
            return None
        return SimpleNamespace(
            id=product_id,
            nombre="Reja test",
            precio=PRICE_M2,
            precio_rebajado=None,
            available_for_sale=self.available_for_sale,
        )


def load_checkout_service_with_fake_models():
    fake_models = types.ModuleType("api.models")

    class FakeProducts:
        query = FakeProductQuery()

    fake_models.Products = FakeProducts
    original_models = sys.modules.get("api.models")
    sys.modules["api.models"] = fake_models

    try:
        checkout_module_path = SRC_DIR / "api" / "checkout_service.py"
        module_name = "checkout_service_under_test"
        spec = importlib.util.spec_from_file_location(module_name, checkout_module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if original_models is not None:
            sys.modules["api.models"] = original_models
        else:
            sys.modules.pop("api.models", None)


class ConfiguratorPricingTest(unittest.TestCase):
    def test_serialized_configuration_uses_the_authoritative_rules(self):
        configuration = serialize_configurator_configuration(7)

        self.assertEqual(configuration["schema_version"], 1)
        self.assertEqual(configuration["product_id"], 7)
        self.assertEqual(
            configuration["dimensions"],
            {
                "alto": {"min_cm": 30.0, "max_cm": 250.0},
                "ancho": {"min_cm": 30.0, "max_cm": 250.0},
                "max_sum_cm": 400.0,
            },
        )
        self.assertEqual(
            [option["supplement"] for option in configuration["anchorages"]],
            [0.0, 24.95, 39.95],
        )
        self.assertEqual(
            [option["enabled"] for option in configuration["anchorages"]],
            [True, True, False],
        )
        self.assertEqual(len(configuration["colors"]), 10)
        self.assertEqual(
            {option["finish"] for option in configuration["colors"]},
            {"liso", "forja"},
        )
        self.assertEqual(
            configuration["colors"][0]["label"],
            "Blanco liso",
        )
        self.assertTrue(
            all(option["description"] for option in configuration["anchorages"])
        )
        self.assertEqual(quote(30, 250)["base_unit_price"], 95.0)
        with self.assertRaisesRegex(ValueError, "Dimensiones"):
            quote(151, 250)

    def test_authoritative_product_quote_returns_commercial_breakdown(self):
        checkout_service = load_checkout_service_with_fake_models()
        product = SimpleNamespace(
            id=7,
            precio=PRICE_M2,
            precio_rebajado=None,
            available_for_sale=True,
        )

        result = checkout_service.build_product_configuration_quote(
            product=product,
            alto=30,
            ancho=30,
            anclaje=ANCHORAGE_FRONT_PLATES,
            color=DEFAULT_COLOR,
            quantity=2,
        )

        self.assertEqual(
            result,
            {
                "product_id": 7,
                "quantity": 2,
                "alto": 30.0,
                "ancho": 30.0,
                "anclaje": ANCHORAGE_FRONT_PLATES,
                "color": DEFAULT_COLOR,
                "currency": "EUR",
                "base_unit_price": 95.0,
                "anchorage_supplement": 24.95,
                "unit_price": 119.95,
                "subtotal": 239.9,
            },
        )

    def test_authoritative_product_quote_is_idempotent(self):
        checkout_service = load_checkout_service_with_fake_models()
        product = SimpleNamespace(
            id=7,
            precio=PRICE_M2,
            precio_rebajado=None,
            available_for_sale=True,
        )
        configuration = {
            "product": product,
            "alto": 100,
            "ancho": 100,
            "anclaje": ANCHORAGE_INTERIOR_HOLES,
            "color": DEFAULT_COLOR,
        }

        first = checkout_service.build_product_configuration_quote(**configuration)
        second = checkout_service.build_product_configuration_quote(**configuration)

        self.assertEqual(first, second)

    def test_30x30_interior_uses_minimum_price(self):
        self.assertEqual(quote(30, 30)["unit_price"], 95.0)

    def test_30x30_plates_adds_supplement_after_minimum(self):
        result = quote(30, 30, ANCHORAGE_FRONT_PLATES)

        self.assertEqual(result["base_unit_price"], 95.0)
        self.assertEqual(result["anchorage_supplement"], 24.95)
        self.assertEqual(result["unit_price"], 119.95)

    def test_100x100_interior_uses_area_price(self):
        self.assertEqual(quote(100, 100)["unit_price"], 100.0)

    def test_100x100_plates_adds_supplement_once(self):
        self.assertEqual(quote(100, 100, ANCHORAGE_FRONT_PLATES)["unit_price"], 124.95)

    def test_disabled_metal_claws_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "disponible"):
            quote(100, 100, ANCHORAGE_METAL_CLAWS)

    def test_unknown_anchorage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "instalaci"):
            quote(100, 100, "Anclaje inventado")

    def test_legacy_front_holes_are_rejected_with_reconfigure_message(self):
        with self.assertRaisesRegex(ValueError, "Vuelve a configurar"):
            quote(100, 100, ANCHORAGE_LEGACY_FRONT_HOLES)

    def test_unknown_color_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "color"):
            quote(100, 100, color="ral_inventado")

    def test_sum_400_is_valid(self):
        self.assertEqual(quote(150, 250)["unit_price"], 375.0)

    def test_sum_401_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Dimensiones"):
            quote(151, 250)

    def test_checkout_ignores_manipulated_frontend_unit_price(self):
        checkout_service = load_checkout_service_with_fake_models()
        with patch.object(checkout_service.Products, "query", FakeProductQuery(), create=True):
            checkout_quote = checkout_service.build_checkout_quote(
                raw_products=[
                    {
                        "product_id": 1,
                        "quantity": 2,
                        "alto": 30,
                        "ancho": 30,
                        "anclaje": ANCHORAGE_FRONT_PLATES,
                        "color": DEFAULT_COLOR,
                        "precio_total": 0.01,
                    }
                ]
            )

        line = checkout_quote["lines"][0]
        self.assertEqual(line["unit_price"], 119.95)
        self.assertEqual(line["line_total"], 239.9)
        self.assertEqual(line["frontend_unit_price"], 0.01)
        self.assertEqual(line["price_difference"], -119.94)
        self.assertEqual(checkout_quote["subtotal"], 239.9)

    def test_30x30_interior_cart_quote_matches_checkout_unit_price(self):
        checkout_service = load_checkout_service_with_fake_models()
        cart_quote = quote(30, 30, ANCHORAGE_INTERIOR_HOLES)

        with patch.object(checkout_service.Products, "query", FakeProductQuery(), create=True):
            checkout_quote = checkout_service.build_checkout_quote(
                raw_products=[
                    {
                        "product_id": 1,
                        "quantity": 1,
                        "alto": 30,
                        "ancho": 30,
                        "anclaje": ANCHORAGE_INTERIOR_HOLES,
                        "color": DEFAULT_COLOR,
                        "precio_total": 0.01,
                    }
                ]
            )

        self.assertEqual(cart_quote["unit_price"], 95.0)
        self.assertEqual(checkout_quote["lines"][0]["unit_price"], 95.0)
        self.assertEqual(checkout_quote["lines"][0]["line_total"], 95.0)

    def test_30x30_plates_cart_quote_matches_checkout_unit_price(self):
        checkout_service = load_checkout_service_with_fake_models()
        cart_quote = quote(30, 30, ANCHORAGE_FRONT_PLATES)

        with patch.object(checkout_service.Products, "query", FakeProductQuery(), create=True):
            checkout_quote = checkout_service.build_checkout_quote(
                raw_products=[
                    {
                        "product_id": 1,
                        "quantity": 1,
                        "alto": 30,
                        "ancho": 30,
                        "anclaje": ANCHORAGE_FRONT_PLATES,
                        "color": DEFAULT_COLOR,
                        "precio_total": 0.01,
                    }
                ]
            )

        self.assertEqual(cart_quote["unit_price"], 119.95)
        self.assertEqual(checkout_quote["lines"][0]["unit_price"], 119.95)
        self.assertEqual(checkout_quote["lines"][0]["line_total"], 119.95)

    def test_quantity_two_plates_keeps_unit_price_and_multiplies_line_total(self):
        checkout_service = load_checkout_service_with_fake_models()

        with patch.object(checkout_service.Products, "query", FakeProductQuery(), create=True):
            checkout_quote = checkout_service.build_checkout_quote(
                raw_products=[
                    {
                        "product_id": 1,
                        "quantity": 2,
                        "alto": 30,
                        "ancho": 30,
                        "anclaje": ANCHORAGE_FRONT_PLATES,
                        "color": DEFAULT_COLOR,
                        "precio_total": 0.01,
                    }
                ]
            )

        self.assertEqual(checkout_quote["lines"][0]["unit_price"], 119.95)
        self.assertEqual(checkout_quote["lines"][0]["line_total"], 239.9)

    def test_checkout_uses_same_configured_price_as_cart_quote(self):
        checkout_service = load_checkout_service_with_fake_models()
        with patch.object(checkout_service.Products, "query", FakeProductQuery(), create=True):
            checkout_quote = checkout_service.build_checkout_quote(
                raw_products=[
                    {
                        "product_id": 1,
                        "quantity": 1,
                        "alto": 100,
                        "ancho": 100,
                        "anclaje": ANCHORAGE_FRONT_PLATES,
                        "color": DEFAULT_COLOR,
                        "precio_total": 100.0,
                    }
                ]
            )

        expected = quote(100, 100, ANCHORAGE_FRONT_PLATES)["unit_price"]
        self.assertEqual(checkout_quote["lines"][0]["unit_price"], expected)

    def test_checkout_rejects_legacy_front_holes_with_clear_message(self):
        checkout_service = load_checkout_service_with_fake_models()
        with patch.object(checkout_service.Products, "query", FakeProductQuery(), create=True):
            with self.assertRaisesRegex(ValueError, "Vuelve a configurar"):
                checkout_service.build_checkout_quote(
                    raw_products=[
                        {
                            "product_id": 1,
                            "quantity": 1,
                            "alto": 100,
                            "ancho": 100,
                            "anclaje": ANCHORAGE_LEGACY_FRONT_HOLES,
                            "color": DEFAULT_COLOR,
                            "precio_total": 100.0,
                        }
                    ]
                )

        self.assertIn("Vuelve a configurar", LEGACY_ANCHORAGE_RECONFIGURE_MESSAGE)

    def test_checkout_quote_accepts_available_product(self):
        checkout_service = load_checkout_service_with_fake_models()

        result = checkout_service.build_checkout_quote(
            raw_products=[
                {
                    "product_id": 1,
                    "quantity": 1,
                    "alto": 30,
                    "ancho": 30,
                    "anclaje": ANCHORAGE_INTERIOR_HOLES,
                    "color": DEFAULT_COLOR,
                }
            ]
        )

        self.assertEqual(result["lines"][0]["product_id"], 1)

    def test_checkout_quote_rejects_unavailable_product(self):
        checkout_service = load_checkout_service_with_fake_models()
        unavailable_query = FakeProductQuery(available_for_sale=False)

        with patch.object(
            checkout_service.Products,
            "query",
            unavailable_query,
            create=True,
        ):
            with patch.object(
                checkout_service,
                "build_configured_reja_quote",
            ) as pricing:
                with self.assertRaisesRegex(ValueError, "no esta disponible"):
                    checkout_service.build_checkout_quote(
                        raw_products=[
                            {
                                "product_id": 1,
                                "quantity": 1,
                                "alto": 30,
                                "ancho": 30,
                                "anclaje": ANCHORAGE_INTERIOR_HOLES,
                                "color": DEFAULT_COLOR,
                                "available_for_sale": True,
                            }
                        ]
                    )
                pricing.assert_not_called()

    def test_checkout_quote_rejects_missing_product(self):
        checkout_service = load_checkout_service_with_fake_models()
        missing_query = FakeProductQuery(exists=False)

        with patch.object(
            checkout_service.Products,
            "query",
            missing_query,
            create=True,
        ):
            with self.assertRaisesRegex(ValueError, "no encontrado"):
                checkout_service.build_checkout_quote(
                    raw_products=[
                        {
                            "product_id": 999,
                            "quantity": 1,
                            "alto": 30,
                            "ancho": 30,
                            "anclaje": ANCHORAGE_INTERIOR_HOLES,
                            "color": DEFAULT_COLOR,
                        }
                    ]
                )


if __name__ == "__main__":
    unittest.main()

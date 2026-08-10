import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.transactional_email_renderer import (  # noqa: E402
    OrderEmailLine,
    TransactionalEmailRenderError,
    render_invoice_delivery_email,
    render_order_confirmation_email,
)


def order_line(**overrides):
    data = {
        "product_name": "Reja fija Albany",
        "quantity": 2,
        "measurements": "100 × 100 cm",
        "anchorage": "Pletinas",
        "color": "Negro forja",
        "screw_configuration": "150 mm (+8,95 €)",
        "line_total": "1234.50",
    }
    data.update(overrides)
    return OrderEmailLine(**data)


def render_order(**overrides):
    data = {
        "order_reference": "QE2885",
        "customer_firstname": "Sergio",
        "lines": (order_line(),),
        "subtotal": "1234.50",
        "shipping_cost": "0.00",
        "discount_amount": "171.17",
        "total_amount": "1063.33",
    }
    data.update(overrides)
    return render_order_confirmation_email(**data)


class TransactionalOrderEmailRendererTest(unittest.TestCase):
    def test_renders_complete_plain_text_and_html_contract(self):
        rendered = render_order()

        for expected in (
            "METALWOLFT",
            "Rejas para ventanas a medida",
            "Pedido: QE2885",
            "Estado del pago: confirmado",
            "Reja fija Albany",
            "100 × 100 cm",
            "Pletinas",
            "Negro forja",
            "150 mm (+8,95 €)",
            "Cantidad: 2",
            "Importe: 1.234,50 €",
            "Subtotal: 1.234,50 €",
            "Envío: GRATIS",
            "Descuento: −171,17 €",
            "TOTAL: 1.063,33 €",
        ):
            self.assertIn(expected, rendered.text)

        self.assertIn("<!doctype html>", rendered.html)
        self.assertIn("METAL", rendered.html)
        self.assertIn("WOLFT", rendered.html)
        self.assertIn("Pago confirmado", rendered.html)
        self.assertIn("Negro forja", rendered.html)
        self.assertIn("1.234,50 €", rendered.html)
        self.assertIn("GRATIS", rendered.html)
        self.assertNotIn("<script", rendered.html.lower())

    def test_renders_standard_and_long_screw_configurations(self):
        rendered = render_order(
            lines=(
                order_line(screw_configuration="100 mm incluidos", line_total="100"),
                order_line(screw_configuration="150 mm (+8,95 €)", line_total="108.95"),
            ),
            subtotal="208.95",
            total_amount="208.95",
            discount_amount=0,
        )

        self.assertIn("Tornillos: 100 mm incluidos", rendered.text)
        self.assertIn("Tornillos: 150 mm (+8,95 €)", rendered.text)
        self.assertIn("Tornillos 100 mm incluidos", rendered.html)
        self.assertIn("Tornillos 150 mm (+8,95 €)", rendered.html)
        self.assertNotIn("Descuento:", rendered.text)

    def test_omits_screws_when_the_anchorage_does_not_use_them(self):
        rendered = render_order(
            lines=(order_line(anchorage="Garras metálicas", screw_configuration=None),)
        )

        self.assertIn("Instalación: Garras metálicas", rendered.text)
        self.assertNotIn("Tornillos", rendered.text)
        self.assertNotIn("Tornillos", rendered.html)

    def test_escapes_every_dynamic_value_in_html(self):
        malicious = '<script>alert("owned")</script> & "cliente"'
        rendered = render_order(
            order_reference=malicious,
            customer_firstname=malicious,
            lines=(
                order_line(
                    product_name=malicious,
                    measurements=malicious,
                    anchorage=malicious,
                    color=malicious,
                    screw_configuration=malicious,
                ),
            ),
        )

        self.assertNotIn("<script>", rendered.html)
        self.assertNotIn('alert("owned")', rendered.html)
        self.assertIn("&lt;script&gt;alert(&quot;owned&quot;)&lt;/script&gt;", rendered.html)
        self.assertIn("&amp; &quot;cliente&quot;", rendered.html)
        self.assertIn(malicious, rendered.text)

    def test_missing_authoritative_line_total_is_rejected_without_fallback(self):
        with self.assertRaises(TransactionalEmailRenderError) as context:
            render_order(lines=(order_line(line_total=None),))

        self.assertIn("line_total", str(context.exception))
        self.assertNotIn("unit_price", OrderEmailLine.__dataclass_fields__)

    def test_required_summary_amounts_are_not_invented(self):
        for field in ("subtotal", "shipping_cost", "total_amount"):
            with self.subTest(field=field):
                with self.assertRaises(TransactionalEmailRenderError):
                    render_order(**{field: None})


class TransactionalInvoiceEmailRendererTest(unittest.TestCase):
    def test_renders_simple_invoice_plain_text_and_html(self):
        rendered = render_invoice_delivery_email(
            invoice_number="F2026000004",
            order_reference="QE2885",
            trade_name="MetalWolft",
            customer_name="Sergio Arias",
        )

        for expected in (
            "Tu factura F2026000004",
            "Pedido: QE2885",
            "Documento: PDF adjunto",
            "Hola Sergio Arias,",
        ):
            self.assertIn(expected, rendered.text)

        for expected in (
            "Tu factura F2026000004",
            "QE2885",
            "PDF adjunto",
            "Hola Sergio Arias,",
        ):
            self.assertIn(expected, rendered.html)

        self.assertNotIn("00000000T", rendered.text)
        self.assertNotIn("IVA", rendered.html)
        self.assertNotIn("Dirección", rendered.html)

    def test_invoice_dynamic_values_are_escaped(self):
        rendered = render_invoice_delivery_email(
            invoice_number="F<script>1</script>",
            order_reference='QE"<b>2</b>',
            trade_name="MetalWolft & Hijos",
            customer_name="<img src=x onerror=alert(1)>",
        )

        self.assertNotIn("<script>", rendered.html)
        self.assertNotIn("<img", rendered.html)
        self.assertIn("&lt;script&gt;1&lt;/script&gt;", rendered.html)
        self.assertIn("MetalWolft &amp; Hijos", rendered.html)


if __name__ == "__main__":
    unittest.main()

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
    render_account_welcome_email,
    render_order_delivery_estimate_update_email,
    render_order_confirmation_email,
    render_order_status_update_email,
)
from api.order_shipping import ShippingAddress  # noqa: E402


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

    def test_renders_full_frozen_shipping_address_in_plain_text_and_html(self):
        rendered = render_order(
            shipping_address=ShippingAddress(
                recipient="Ana Cliente",
                address="Calle Mayor 12",
                postal_code="28013",
                city="Madrid",
                province="Madrid",
                country_code="ES",
            )
        )

        for expected in (
            "DIRECCI\u00d3N DE ENV\u00cdO",
            "Ana Cliente",
            "Calle Mayor 12",
            "28013 Madrid",
            "Madrid",
            "ES",
        ):
            self.assertIn(expected, rendered.text)
            self.assertIn(expected, rendered.html)

    def test_renders_same_as_billing_message_when_shipping_is_not_different(self):
        rendered = render_order(
            shipping_address=ShippingAddress(
                address="Calle Mayor 12",
                postal_code="28013",
                city="Madrid",
                same_as_billing=True,
            )
        )

        expected = "Misma que la direcci\u00f3n de facturaci\u00f3n."
        self.assertIn(expected, rendered.text)
        self.assertIn(expected, rendered.html)

    def test_omits_screws_when_the_anchorage_does_not_use_them(self):
        rendered = render_order(
            lines=(order_line(anchorage="Garras metálicas", screw_configuration=None),)
        )

        self.assertIn("Instalación: Garras metálicas", rendered.text)
        self.assertNotIn("Tornillos", rendered.text)
        self.assertNotIn("Tornillos", rendered.html)


class TransactionalOrderStatusEmailRendererTest(unittest.TestCase):
    def test_renders_status_progress_details_and_plain_text(self):
        rendered = render_order_status_update_email(
            order_reference="QE2885",
            current_status="pintura",
            statuses=(
                ("pendiente", "Recibido"),
                ("fabricacion", "Fabricaci\u00f3n"),
                ("pintura", "Pintura"),
                ("embalaje", "Embalaje"),
            ),
            estimated_delivery_date="15/09/2026",
            estimated_delivery_note="Preparaci\u00f3n de la expedici\u00f3n",
        )

        for expected in (
            "ESTADO DE TU PEDIDO",
            "Pintura",
            "QE2885",
            "15/09/2026",
            "Preparaci\u00f3n de la expedici\u00f3n",
            "Completado: Recibido",
            "Actual: Pintura",
        ):
            self.assertIn(expected, rendered.text)

        for expected in (
            "Estado de tu pedido",
            "Pintura",
            "QE2885",
            "15/09/2026",
            "Preparaci\u00f3n de la expedici\u00f3n",
            "PROGRESO DEL PEDIDO",
        ):
            self.assertIn(expected, rendered.html)

        self.assertIn("Estado actual", rendered.html)
        self.assertIn("#cf1c35", rendered.html)
        self.assertNotIn("\U0001f4e6", rendered.html)
        self.assertNotIn("\U0001f4cd", rendered.html)

    def test_sent_status_includes_only_the_installation_guide(self):
        rendered = render_order_status_update_email(
            order_reference="QE2885",
            current_status="enviado",
            statuses=(("pendiente", "Recibido"), ("enviado", "Enviado"), ("entregado", "Entregado")),
        )

        for body in (rendered.text, rendered.html):
            self.assertIn("Prepárate para la instalación", body)
            self.assertIn("Ver guía de instalación", body)
            self.assertIn("https://www.metalwolft.com/instalation-rejas-para-ventanas", body)
            self.assertNotIn("Mantenimiento y retoque", body)

        self.assertLess(rendered.html.index("PROGRESO DEL PEDIDO"), rendered.html.index("Prepárate para la instalación"))
        self.assertLess(
            rendered.html.index("Prepárate para la instalación"),
            rendered.html.index("Si tienes cualquier duda"),
        )

    def test_sent_status_can_include_the_selected_receipt_installation_and_incident_links(self):
        rendered = render_order_status_update_email(
            order_reference="QE2885",
            current_status="enviado",
            statuses=(("pendiente", "Recibido"), ("enviado", "Enviado")),
            include_receipt_guide=True,
            include_installation_guide=True,
            include_incident_form=True,
        )

        for body in (rendered.text, rendered.html):
            self.assertIn("Guía de recepción del pedido", body)
            self.assertIn("https://www.metalwolft.com/recepcion-pedidos-revisar-antes-firmar", body)
            self.assertIn("Ver guía de instalación", body)
            self.assertIn("https://www.metalwolft.com/instalation-rejas-para-ventanas", body)
            self.assertIn("Formulario de incidencias", body)
            self.assertIn("https://www.metalwolft.com/formulario-incidencias", body)

    def test_sent_status_omits_guidance_when_no_additional_link_is_selected(self):
        rendered = render_order_status_update_email(
            order_reference="QE2885",
            current_status="enviado",
            statuses=(("pendiente", "Recibido"), ("enviado", "Enviado")),
            include_receipt_guide=False,
            include_installation_guide=False,
            include_incident_form=False,
        )

        for body in (rendered.text, rendered.html):
            self.assertNotIn("Prepárate para la instalación", body)
            self.assertNotIn("Guía de recepción del pedido", body)
            self.assertNotIn("Formulario de incidencias", body)

    def test_delivered_status_includes_installation_and_maintenance_guides(self):
        rendered = render_order_status_update_email(
            order_reference="QE2885",
            current_status="entregado",
            statuses=(("pendiente", "Recibido"), ("enviado", "Enviado"), ("entregado", "Entregado")),
        )

        for body in (rendered.text, rendered.html):
            self.assertIn("Ya tienes tu reja", body)
            self.assertIn("Guía de instalación", body)
            self.assertIn("Mantenimiento y acabado", body)
            self.assertIn("https://www.metalwolft.com/instalation-rejas-para-ventanas", body)
            self.assertIn("https://www.metalwolft.com/mantenimiento-acabado-rejas-metalicas", body)
            self.assertIn("y conservación del acabado.", body)

    def test_non_post_sale_statuses_do_not_include_guides(self):
        statuses = (
            ("pendiente", "Recibido"),
            ("fabricacion", "Fabricación"),
            ("pintura", "Pintura"),
            ("embalaje", "Embalaje"),
        )
        for current_status, _ in statuses:
            rendered = render_order_status_update_email(
                order_reference="QE2885",
                current_status=current_status,
                statuses=statuses,
            )

            for body in (rendered.text, rendered.html):
                self.assertNotIn("Prepárate para la instalación", body)
                self.assertNotIn("Ya tienes tu reja", body)
                self.assertNotIn("mantenimiento-acabado-rejas-metalicas", body)


class TransactionalWelcomeEmailRendererTest(unittest.TestCase):
    def test_renders_welcome_email_with_name_cta_and_plain_text_equivalent(self):
        rendered = render_account_welcome_email(
            customer_firstname="Sergio",
            login_url="https://www.metalwolft.com/login",
        )

        for expected in (
            "\u00a1Bienvenido a MetalWolft!",
            "Hola, Sergio,",
            "Tu cuenta ha sido creada correctamente.",
            "Iniciar sesi\u00f3n",
            "https://www.metalwolft.com/login",
            "Gracias por registrarte en MetalWolft.",
        ):
            self.assertIn(expected, rendered.text)
            self.assertIn(expected, rendered.html)

        self.assertIn('href="https://www.metalwolft.com/login"', rendered.html)
        self.assertIn("border-radius:999px", rendered.html)
        self.assertIn("<!doctype html>", rendered.html)
        self.assertNotIn("Metal Wolft \u00a9 2025", rendered.html)

    def test_renders_generic_greeting_without_customer_name(self):
        rendered = render_account_welcome_email(
            login_url="https://www.metalwolft.com/login",
        )

        self.assertIn("Hola,\n", rendered.text)
        self.assertNotIn("Hola, None", rendered.text)
        self.assertIn("<!doctype html>", rendered.html)

    def test_renders_delivery_estimate_update_with_details_and_plain_text(self):
        rendered = render_order_delivery_estimate_update_email(
            order_reference="QE2885",
            estimated_delivery_date="15/09/2026",
            estimated_delivery_note="Preparaci\u00f3n de la expedici\u00f3n",
        )

        for expected in (
            "ACTUALIZACI\u00d3N DE ENTREGA",
            "Fecha estimada de entrega: 15/09/2026",
            "Nota: Preparaci\u00f3n de la expedici\u00f3n",
            "Localizador: QE2885",
        ):
            self.assertIn(expected, rendered.text)

        for expected in (
            "Actualizaci\u00f3n de entrega",
            "Fecha estimada de entrega",
            "15/09/2026",
            "Preparaci\u00f3n de la expedici\u00f3n",
            "QE2885",
            "<!doctype html>",
        ):
            self.assertIn(expected, rendered.html)
        self.assertNotIn("\U0001f4cd", rendered.html)

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

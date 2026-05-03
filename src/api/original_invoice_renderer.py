"""
Renderer aislado para la factura original de pedido.

IMPORTANTE:
- Replica la lógica visual/fiscal del bloque inline real que hoy vive en `src/api/routes.py`
  dentro de `_finalize_order_from_checkout_quote(...)` y `POST /api/orders`.
- Todavía NO está conectado a producción.
- No consulta BD.
- No escribe en disco.
- No envía emails.
- Solo devuelve los bytes del PDF para una futura refactorización controlada.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, date
from io import BytesIO
from typing import Any, Mapping, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle


DEFAULT_PROVIDER_NAME = "Sergio Arias Fernández"
DEFAULT_PROVIDER_CIF = "05703874N"
DEFAULT_PROVIDER_ADDRESS = "Francisco Fernández Ordoñez 32"
DEFAULT_PROVIDER_CITY = "13170 Miguelturra"
DEFAULT_PROVIDER_PHONE = "634112604"
DEFAULT_LOGO_URL = "https://res.cloudinary.com/dewanllxn/image/upload/v1740167674/logo_uxlqof.png"

COLOR_LABELS = {
    "satinado_blanco": "Blanco liso",
    "satinado_negro": "Negro liso",
    "satinado_gris": "Gris medio liso",
    "satinado_verde": "Verde carruajes liso",
    "forja_negro": "Negro forja",
    "forja_gris": "Gris acero forja",
    "forja_marron": "Marrón castaño forja",
    "forja_azul": "Azul forja",
    "forja_verde": "Verde bronce forja",
    "forja_dorado": "Dorado forja",
    # Compatibilidad con pedidos antiguos
    "blanco": "Blanco",
    "negro": "Negro",
    "gris": "Gris",
    "marrón": "Marrón",
    "marron": "Marrón",
    "verde": "Verde",
}


def _format_issue_date(issue_date: date | datetime | str | None) -> str:
    if isinstance(issue_date, datetime):
        return issue_date.strftime("%d/%m/%Y")
    if isinstance(issue_date, date):
        return issue_date.strftime("%d/%m/%Y")
    if isinstance(issue_date, str) and issue_date.strip():
        return issue_date.strip()
    return datetime.now().strftime("%d/%m/%Y")


def _display_product_name(detail: Mapping[str, Any]) -> str:
    return (
        detail.get("product_name")
        or detail.get("producto_nombre")
        or detail.get("product")
        or detail.get("name")
        or detail.get("nombre")
        or "Desconocido"
    )


def _group_invoice_lines(order_details: Sequence[Mapping[str, Any]]) -> list[list[str]]:
    grouped_details: dict[tuple[Any, ...], dict[str, Any]] = defaultdict(
        lambda: {"quantity": 0, "precio_unitario": 0.0, "product_name": "Desconocido"}
    )

    for detail in order_details:
        product_name = _display_product_name(detail)
        color = detail.get("color")
        key = (
            product_name,
            detail.get("alto"),
            detail.get("ancho"),
            detail.get("anclaje"),
            color,
        )
        grouped_details[key]["quantity"] += detail.get("quantity", 1)
        grouped_details[key]["precio_unitario"] = float(detail.get("precio_total", 0.0) or 0.0)
        grouped_details[key]["product_name"] = product_name

    rows: list[list[str]] = []
    for (product_name, alto, ancho, anclaje, color), values in grouped_details.items():
        cantidad = values["quantity"]
        precio_unitario = values["precio_unitario"]
        importe_total = precio_unitario * cantidad

        rows.append([
            str(product_name)[:24],
            f"{alto} cm",
            f"{ancho} cm",
            (anclaje[:20] if anclaje else ""),
            (COLOR_LABELS.get(color, color)[:18] if color else ""),
            str(cantidad),
            f"{importe_total:.2f}",
        ])

    return rows


def _shipping_label(shipping_cost: float) -> str:
    if shipping_cost == 59:
        return "Tarifa A (59 €)"
    if shipping_cost == 99:
        return "Tarifa B (99 €)"
    if shipping_cost == 21:
        return "Estándar (21 €)"
    return "Gratuito"


def render_original_order_invoice_pdf(
    *,
    invoice_number: str,
    customer_firstname: str = "",
    customer_lastname: str = "",
    customer_phone: str | None = None,
    customer_billing_address: str | None = None,
    customer_billing_city: str | None = None,
    customer_billing_postal_code: str | None = None,
    customer_cif: str | None = None,
    customer_shipping_address: str | None = None,
    customer_shipping_city: str | None = None,
    customer_shipping_postal_code: str | None = None,
    order_details: Sequence[Mapping[str, Any]] = (),
    total_amount: float = 0.0,
    shipping_cost: float = 0.0,
    discount_value: float = 0.0,
    discount_code: str | None = None,
    discount_percent: float = 0.0,
    issue_date: date | datetime | str | None = None,
    provider_name: str = DEFAULT_PROVIDER_NAME,
    provider_cif: str = DEFAULT_PROVIDER_CIF,
    provider_address: str = DEFAULT_PROVIDER_ADDRESS,
    provider_city: str = DEFAULT_PROVIDER_CITY,
    provider_phone: str = DEFAULT_PROVIDER_PHONE,
    logo_url: str = DEFAULT_LOGO_URL,
) -> bytes:
    """
    Replica el PDF original inline de routes.py para pedidos reales.

    Nota:
    - `order_details` debe llegar ya enriquecido con `product_name`/`producto_nombre`
      o equivalente, porque este renderer no consulta BD.
    - Devuelve bytes del PDF; el caller futuro decidirá si lo guarda, lo envía por email
      o lo sirve por descarga.
    """
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)

    pdf.drawImage(logo_url, 300, 750, width=250, height=64)

    pdf.setTitle(f"Factura_{invoice_number}")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 800, f"Factura No: {invoice_number}")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 780, f"Fecha: {_format_issue_date(issue_date)}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(400, 700, "PROVEEDOR")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(400, 680, provider_name)
    pdf.drawString(400, 665, provider_cif)
    pdf.drawString(400, 650, provider_address)
    pdf.drawString(400, 635, provider_city)
    pdf.drawString(400, 620, provider_phone)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 700, "CLIENTE")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 680, f"{customer_firstname or ''} {customer_lastname or ''}".strip())
    pdf.drawString(
        50,
        665,
        f"{customer_billing_address or ''}, {customer_billing_city or ''} ({customer_billing_postal_code or ''})",
    )
    pdf.drawString(50, 650, f"{customer_cif or ''}")
    pdf.drawString(50, 635, f"{customer_phone or 'No proporcionado'}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 580, "Dirección de Envío")
    pdf.setFont("Helvetica", 10)

    if not customer_shipping_address or customer_shipping_address == customer_billing_address:
        pdf.drawString(50, 560, "La misma que la de facturación")
    else:
        pdf.drawString(
            50,
            560,
            f"{customer_shipping_address or ''}, {customer_shipping_city or ''} ({customer_shipping_postal_code or ''})",
        )

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 510, "Detalles del Pedido")
    pdf.setFont("Helvetica", 10)

    data_table = [["Prod.", "Alto", "Ancho", "Anc.", "Col.", "Ud.", "Importe (€)"]]
    data_table.extend(_group_invoice_lines(order_details))

    table = Table(data_table, colWidths=[4 * cm, 1.5 * cm, 1.5 * cm, 4.2 * cm, 3.2 * cm, 1 * cm, 2.3 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(1, 0.196, 0.302)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    y_position = 480
    table.wrapOn(pdf, 50, y_position)
    table_height = table._height
    table.drawOn(pdf, 50, y_position - table_height)

    totals_y_position = y_position - table_height - 30
    if totals_y_position < 50:
        pdf.showPage()
        totals_y_position = 750

    total = float(total_amount or 0.0)
    shipping_cost = float(shipping_cost or 0.0)
    discount_value = float(discount_value or 0.0)
    discount_percent = float(discount_percent or 0.0)

    base_total = total / 1.21 if total else 0.0
    iva_calculado = total - base_total
    base_envio = shipping_cost / 1.21 if shipping_cost else 0.0
    base_productos = base_total - base_envio

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, totals_y_position, "DETALLE FISCAL")
    pdf.setFont("Helvetica", 10)

    pdf.drawString(50, totals_y_position - 15, f"Base imponible productos: {base_productos:.2f} €")
    pdf.drawString(50, totals_y_position - 30, f"Base imponible envío: {base_envio:.2f} €")

    pdf.setStrokeColor(colors.black)
    pdf.line(50, totals_y_position - 35, 200, totals_y_position - 35)

    pdf.drawString(50, totals_y_position - 50, f"Base imponible total: {base_total:.2f} €")
    pdf.drawString(50, totals_y_position - 65, f"IVA (21%): {iva_calculado:.2f} €")

    pdf.line(50, totals_y_position - 70, 200, totals_y_position - 70)

    subtotal_con_iva = base_total + iva_calculado
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, totals_y_position - 85, f"Subtotal (IVA incl.): {subtotal_con_iva:.2f} €")

    if discount_value > 0:
        pdf.setFont("Helvetica-Bold", 11)
        pdf.setFillColor(colors.green)
        pdf.drawString(
            50,
            totals_y_position - 100,
            f"Descuento comercial ({discount_code or ''} {discount_percent:.0f}%): -{discount_value:.2f} €"
        )
        pdf.setFillColor(colors.black)

    pdf.line(50, totals_y_position - 105, 200, totals_y_position - 105)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, totals_y_position - 120, f"TOTAL A PAGAR: {total:.2f} €")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, totals_y_position - 140, f"Tipo de envío: {_shipping_label(shipping_cost)}")
    if discount_code:
        pdf.drawString(50, totals_y_position - 155, f"Código descuento: {discount_code}")

    pdf.save()
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

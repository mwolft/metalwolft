from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

from api.utils import format_screw_configuration
from api.order_shipping import shipping_address_from_order_details, shipping_address_lines
from api.design_service import order_contains_design_service


COLOR_PRIMARY = colors.Color(1, 0.196, 0.302)
COLOR_BORDER = colors.HexColor("#d9dee5")
COLOR_TEXT = colors.HexColor("#0f172a")
COLOR_MUTED = colors.HexColor("#5b6472")
COLOR_SURFACE = colors.HexColor("#f8fafc")

FONT_BASE = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

M_LEFT = 1.8 * cm
M_RIGHT = 1.8 * cm
M_TOP = 1.8 * cm
M_BOTTOM = 1.8 * cm

TECHNICAL_DESCRIPTION_LIMIT = 180


def _format_date(value):
    if not value:
        return "-"

    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")

    return str(value)


def _format_status(value):
    if not value:
        return "-"

    if str(value).strip().lower() == "pendiente":
        return "Recibido"

    normalized = str(value).strip().replace("_", " ")
    return normalized[:1].upper() + normalized[1:]


def _format_color(value):
    if not value:
        return "-"

    return str(value).replace("_", " ")


def _truncate_text(value, limit=TECHNICAL_DESCRIPTION_LIMIT):
    if not value:
        return "-"

    normalized = " ".join(str(value).split())
    if len(normalized) <= limit:
        return normalized

    return f"{normalized[: limit - 3].rstrip()}..."


def _build_header_rows(order):
    rows = [
        ("Localizador", order.locator or "-"),
        ("Factura", order.invoice_number or "-"),
        ("Fecha pedido", _format_date(order.order_date)),
        ("Entrega estimada", _format_date(order.estimated_delivery_at)),
        ("Estado", _format_status(order.order_status)),
    ]

    if order.estimated_delivery_note:
        rows.append(("Nota entrega", order.estimated_delivery_note))

    shipping_address = shipping_address_from_order_details(order.order_details)
    shipping_lines = shipping_address_lines(shipping_address)
    if shipping_lines:
        rows.append(("Direcci\u00f3n de env\u00edo", " | ".join(shipping_lines)))

    return rows


def _build_line_rows(order, paragraph_style):
    rows = [[
        Paragraph("<b>Producto / modelo</b>", paragraph_style),
        Paragraph("<b>Ud.</b>", paragraph_style),
        Paragraph("<b>Alto</b>", paragraph_style),
        Paragraph("<b>Ancho</b>", paragraph_style),
        Paragraph("<b>Anclaje</b>", paragraph_style),
        Paragraph("<b>Color / acabado</b>", paragraph_style),
        Paragraph("<b>Descripcion tecnica</b>", paragraph_style),
    ]]

    for detail in order.order_details:
        product = detail.product
        product_name = product.nombre if product and product.nombre else f"Producto #{detail.product_id}"
        screw_configuration = format_screw_configuration(
            getattr(detail, "screw_length_mm", None),
            getattr(detail, "screw_supplement", 0.0),
        )
        technical_parts = []
        if screw_configuration:
            technical_parts.append(f"Tornillos: {screw_configuration}.")
        if product and product.descripcion:
            technical_parts.append(product.descripcion)
        technical_description = _truncate_text(" ".join(technical_parts))

        rows.append([
            Paragraph(product_name, paragraph_style),
            Paragraph(str(detail.quantity or 0), paragraph_style),
            Paragraph(f"{detail.alto or '-'} cm", paragraph_style),
            Paragraph(f"{detail.ancho or '-'} cm", paragraph_style),
            Paragraph(detail.anclaje or "-", paragraph_style),
            Paragraph(_format_color(detail.color), paragraph_style),
            Paragraph(technical_description, paragraph_style),
        ])

    return rows


def generate_work_order_pdf(order):
    if order_contains_design_service(order):
        raise ValueError("Los servicios de diseño previo no generan orden de trabajo de fabricación.")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "work-order-body",
        parent=styles["BodyText"],
        fontName=FONT_BASE,
        fontSize=8.2,
        leading=10,
        textColor=COLOR_TEXT,
    )

    y = height - M_TOP

    pdf.setFont(FONT_BOLD, 18)
    pdf.setFillColor(COLOR_PRIMARY)
    pdf.drawString(M_LEFT, y, "Parte de Trabajo")

    pdf.setFont(FONT_BASE, 9.5)
    pdf.setFillColor(COLOR_MUTED)
    pdf.drawString(M_LEFT, y - 16, "Documento interno de fabricacion")

    header_rows = _build_header_rows(order)
    header_data = []
    for label, value in header_rows:
        header_data.append([
            Paragraph(f"<b>{label}</b>", body_style),
            Paragraph(str(value or "-"), body_style),
        ])

    header_table = Table(
        header_data,
        colWidths=[4.2 * cm, width - M_LEFT - M_RIGHT - 4.2 * cm],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_SURFACE),
        ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    header_table.wrapOn(pdf, M_LEFT, y - 40)
    header_height = header_table._height
    header_table.drawOn(pdf, M_LEFT, y - 38 - header_height)

    table_title_y = y - 58 - header_height
    pdf.setFont(FONT_BOLD, 12)
    pdf.setFillColor(COLOR_TEXT)
    pdf.drawString(M_LEFT, table_title_y, "Lineas de fabricacion")

    line_rows = _build_line_rows(order, body_style)
    line_table = Table(
        line_rows,
        colWidths=[4.0 * cm, 1.0 * cm, 1.6 * cm, 1.6 * cm, 2.9 * cm, 2.9 * cm, 4.2 * cm],
        repeatRows=1,
    )
    line_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("BOX", (0, 0), (-1, -1), 0.8, COLOR_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    table_top_y = table_title_y - 14
    line_table.wrapOn(pdf, M_LEFT, table_top_y)
    line_table_height = line_table._height

    if table_top_y - line_table_height < M_BOTTOM:
        pdf.showPage()
        y = height - M_TOP
        pdf.setFont(FONT_BOLD, 18)
        pdf.setFillColor(COLOR_PRIMARY)
        pdf.drawString(M_LEFT, y, "Parte de Trabajo")
        pdf.setFont(FONT_BASE, 9.5)
        pdf.setFillColor(COLOR_MUTED)
        pdf.drawString(M_LEFT, y - 16, f"Localizador {order.locator or '-'}")
        table_top_y = y - 42
        line_table.wrapOn(pdf, M_LEFT, table_top_y)
        line_table_height = line_table._height

    line_table.drawOn(pdf, M_LEFT, table_top_y - line_table_height)

    footer_y = max(M_BOTTOM - 4, table_top_y - line_table_height - 18)
    pdf.setFont(FONT_BASE, 8)
    pdf.setFillColor(COLOR_MUTED)
    pdf.drawString(
        M_LEFT,
        footer_y,
        "Uso interno de taller. Documento sin datos economicos ni fiscales.",
    )

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()

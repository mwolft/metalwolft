"""Render a printable, non-economic delivery receipt on demand."""

from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from api.delivery_receipt_builder import DeliveryReceiptData


_TEXT = colors.HexColor("#1f2937")
_MUTED = colors.HexColor("#64748b")
_BORDER = colors.HexColor("#d9dee5")
_ACCENT = colors.HexColor("#cf1c35")


def generate_delivery_receipt_pdf(data: DeliveryReceiptData) -> bytes:
    if not isinstance(data, DeliveryReceiptData) or not data.lines:
        raise ValueError("El parte de entrega requiere un pedido físico con artículos.")

    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.45 * cm,
        title="Parte de entrega MetalWolft",
        author="MetalWolft",
        pageCompression=0,
    )
    styles = _styles()
    story = [
        Paragraph("METALWOLFT", styles["brand"]),
        Paragraph("PARTE DE ENTREGA", styles["title"]),
        Spacer(1, 0.2 * cm),
        _metadata(data, styles, document.width),
        Spacer(1, 0.3 * cm),
        Paragraph("DATOS DE ENTREGA", styles["section"]),
        _customer(data, styles, document.width),
        Spacer(1, 0.3 * cm),
        Paragraph("ARTICULOS ENTREGADOS", styles["section"]),
        _items(data, styles, document.width),
        Spacer(1, 0.35 * cm),
        KeepTogether(_reception(styles, document.width)),
    ]
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output.getvalue()


def _styles():
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "delivery-brand", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=10, leading=12, textColor=_ACCENT, spaceAfter=3,
        ),
        "title": ParagraphStyle(
            "delivery-title", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=19, leading=22, textColor=_TEXT,
        ),
        "section": ParagraphStyle(
            "delivery-section", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=10, leading=13, textColor=_TEXT, spaceAfter=7,
        ),
        "label": ParagraphStyle(
            "delivery-label", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=8, leading=11, textColor=_MUTED,
        ),
        "body": ParagraphStyle(
            "delivery-body", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9.5, leading=13, textColor=_TEXT,
        ),
        "strong": ParagraphStyle(
            "delivery-strong", parent=base["BodyText"], fontName="Helvetica-Bold",
            fontSize=9.5, leading=13, textColor=_TEXT,
        ),
        "small": ParagraphStyle(
            "delivery-small", parent=base["BodyText"], fontName="Helvetica",
            fontSize=8.5, leading=12, textColor=_TEXT,
        ),
    }


def _p(value, style):
    return Paragraph(escape(str(value or "No consta")), style)


def _box(rows, widths):
    table = Table(rows, colWidths=widths, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def _field(label, value, styles):
    return [Paragraph(label, styles["label"]), _p(value, styles["body"])]


def _metadata(data, styles, width):
    return _box([[
        _field("PEDIDO", data.locator, styles),
        _field("FECHA DEL PEDIDO", data.ordered_at, styles),
    ]], [width / 2, width / 2])


def _customer(data, styles, width):
    address = "<br/>".join(escape(part) for part in data.delivery_address) or "No consta"
    rows = [[
        _field("CLIENTE", data.customer_name, styles),
        _field("TELEFONO", data.phone, styles),
    ], [
        _field("EMAIL", data.email, styles),
        [Paragraph("DIRECCION DE ENTREGA", styles["label"]), Paragraph(address, styles["body"])],
    ]]
    table = _box(rows, [width * 0.42, width * 0.58])
    table.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.4, _BORDER)]))
    return table


def _items(data, styles, width):
    rows = [[
        Paragraph("UD.", styles["label"]),
        Paragraph("MODELO / PRODUCTO", styles["label"]),
        Paragraph("MEDIDAS", styles["label"]),
        Paragraph("CARACTERISTICAS", styles["label"]),
    ]]
    for line in data.lines:
        dimensions = line["dimensions"]
        unit = dimensions.get("unit") or "cm"
        height = dimensions.get("height") or "No consta"
        width_value = dimensions.get("width") or "No consta"
        characteristics = [
            line.get("opening_type"),
            line.get("anchorage"),
            " · ".join(part for part in (line.get("color"), line.get("finish")) if part),
            f"Tornillería: {line['screws']}" if line.get("screws") and line["screws"] != "No consta" else None,
        ]
        rows.append([
            _p(line.get("quantity"), styles["strong"]),
            _p(line.get("model_name"), styles["strong"]),
            Paragraph(
                f"Alto {escape(str(height))} {escape(str(unit))}<br/>"
                f"Ancho {escape(str(width_value))} {escape(str(unit))}",
                styles["body"],
            ),
            Paragraph("<br/>".join(escape(str(item)) for item in characteristics if item), styles["small"]),
        ])
    table = LongTable(rows, colWidths=[width * 0.08, width * 0.27, width * 0.22, width * 0.43], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.7, _BORDER),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def _reception(styles, width):
    lines = [
        Paragraph("RECEPCION", styles["section"]),
        Table([[
            Paragraph("FECHA DE ENTREGA: ______________________", styles["body"]),
            Paragraph("HORA: ______________________", styles["body"]),
        ]], colWidths=[width * 0.6, width * 0.4]),
        Spacer(1, 0.16 * cm),
        Paragraph("ENTREGADO A (nombre y apellidos): ____________________________________________", styles["body"]),
        Spacer(1, 0.15 * cm),
        Paragraph("DNI/NIF (opcional): ____________________________________________________", styles["body"]),
        Spacer(1, 0.18 * cm),
        Paragraph("OBSERVACIONES:", styles["label"]),
    ]
    for _ in range(3):
        lines.append(Paragraph("________________________________________________________________________________", styles["body"]))
    lines.extend([
        Spacer(1, 0.2 * cm),
        Paragraph(
            "Mediante la firma del presente documento se deja constancia de la recepción de los artículos indicados.",
            styles["small"],
        ),
        Spacer(1, 0.26 * cm),
        Paragraph("FIRMA DE QUIEN RECIBE", styles["section"]),
        Spacer(1, 1.65 * cm),
        Paragraph("____________________________________", styles["body"]),
        Paragraph("Nombre / firma", styles["small"]),
    ])
    return lines


def _footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(_BORDER)
    canvas.line(document.leftMargin, 1.1 * cm, A4[0] - document.rightMargin, 1.1 * cm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_MUTED)
    canvas.drawString(document.leftMargin, 0.8 * cm, "MetalWolft · Parte de entrega")
    canvas.drawRightString(A4[0] - document.rightMargin, 0.8 * cm, str(document.page))
    canvas.restoreState()

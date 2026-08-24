"""In-memory renderer for non-fiscal cart budget PDFs."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from api.invoice_snapshot_builder import SUPPORTED_TAX_RATE, _tax_from_gross
from api.utils import CONFIGURATOR_ANCHORAGES, CONFIGURATOR_COLORS, format_screw_configuration


BRAND_RED = "#cf1c35"
BRAND_TEXT = "#1f2937"
BRAND_MUTED = "#6b7280"
BRAND_BORDER = "#e5e7eb"
BRAND_SURFACE = "#f8f7f7"
BRAND_ICON_PATH = Path(__file__).resolve().parents[2] / "apps" / "web-next" / "app" / "icon.png"
MONEY = Decimal("0.01")


class CartBudgetPdfError(ValueError):
    """Raised when a server-side checkout quote cannot be rendered safely."""


def render_cart_budget_pdf(*, quote, issued_at=None):
    """Render a non-fiscal budget exclusively from an authoritative checkout quote."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Image,
        KeepTogether,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    normalized_quote = _validated_quote(quote)
    generated_at = issued_at or datetime.now(timezone.utc)
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.65 * cm,
        rightMargin=1.65 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.75 * cm,
        title="Presupuesto MetalWolft",
        author="MetalWolft",
    )
    styles = _styles(colors, getSampleStyleSheet(), TA_RIGHT)
    available_width = A4[0] - document.leftMargin - document.rightMargin
    story = [
        _header(available_width, generated_at, styles, Image, Paragraph, Table, TableStyle, cm),
        HRFlowable(width="100%", thickness=1.1, color=colors.HexColor(BRAND_RED), spaceBefore=8, spaceAfter=14),
        Paragraph("Configuración presupuestada", styles["section"]),
        _line_table(normalized_quote["lines"], styles, Table, TableStyle, Paragraph, colors, available_width),
        Spacer(1, 14),
        KeepTogether(_totals(normalized_quote, styles, Table, TableStyle, Paragraph, colors, available_width)),
        Spacer(1, 14),
        Paragraph(
            "Documento informativo. Los precios corresponden a la configuración y condiciones vigentes en la fecha de emisión.",
            styles["disclaimer"],
        ),
    ]

    def draw_footer(pdf, doc):
        pdf.saveState()
        pdf.setStrokeColor(colors.HexColor(BRAND_BORDER))
        pdf.line(doc.leftMargin, 1.28 * cm, A4[0] - doc.rightMargin, 1.28 * cm)
        pdf.setFillColor(colors.HexColor(BRAND_MUTED))
        pdf.setFont("Helvetica", 7.2)
        pdf.drawString(doc.leftMargin, 0.82 * cm, "MetalWolft · Fabricación de rejas a medida")
        pdf.drawRightString(A4[0] - doc.rightMargin, 0.82 * cm, "Presupuesto informativo")
        pdf.restoreState()

    document.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return buffer.getvalue()


def _validated_quote(quote):
    if not isinstance(quote, dict):
        raise CartBudgetPdfError("No se ha podido preparar el presupuesto.")
    lines = quote.get("lines")
    if not isinstance(lines, list) or not lines:
        raise CartBudgetPdfError("El carrito está vacío.")

    result = dict(quote)
    result["lines"] = []
    for index, line in enumerate(lines, start=1):
        if not isinstance(line, dict):
            raise CartBudgetPdfError("La configuración del carrito no es válida.")
        name = _text(line.get("product_name"))
        if not name:
            raise CartBudgetPdfError("La configuración del carrito no es válida.")
        quantity = _positive_integer(line.get("quantity"))
        result["lines"].append({
            **line,
            "product_name": name,
            "quantity": quantity,
            "unit_price": _money(line.get("unit_price")),
            "line_total": _money(line.get("line_total")),
            "alto": _number(line.get("alto")),
            "ancho": _number(line.get("ancho")),
        })

    for field in ("subtotal", "shipping_cost", "discount_amount", "total_amount"):
        result[field] = _money(quote.get(field))
    result["discount_percent"] = _number(
        quote.get("discount_percent", 0),
        allow_zero=True,
    )
    result["discount_code"] = _text(quote.get("discount_code"))
    return result


def _header(available_width, generated_at, styles, Image, Paragraph, Table, TableStyle, cm):
    brand_copy = Paragraph(
        f"<font size='15'><b>METAL</b></font><font size='15' color='{BRAND_RED}'><b>WOLFT</b></font>"
        "<br/><font size='8' color='#6b7280'>Rejas para ventanas a medida</font>",
        styles["body"],
    )
    if BRAND_ICON_PATH.is_file():
        logo = Image(str(BRAND_ICON_PATH), width=1.02 * cm, height=0.99 * cm, mask="auto")
        brand = Table(
            [[logo, brand_copy]],
            colWidths=[1.18 * cm, 6.15 * cm],
            style=TableStyle(_no_padding_style()),
        )
    else:
        brand = brand_copy

    details = Paragraph(
        "<font size='12'><b>PRESUPUESTO</b></font><br/>"
        f"<font size='7' color='{BRAND_MUTED}'>FECHA DE EMISIÓN</font><br/>"
        f"{generated_at.astimezone(timezone.utc).strftime('%d/%m/%Y')}",
        styles["body"],
    )
    table = Table([[brand, details]], colWidths=[available_width * 0.62, available_width * 0.38])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        *_no_padding_style(),
    ]))
    return table


def _line_table(lines, styles, Table, TableStyle, Paragraph, colors, available_width):
    rows = [[
        Paragraph("Producto y configuración", styles["header"]),
        Paragraph("Cant.", styles["header_center"]),
        Paragraph("Precio unidad", styles["header_right"]),
        Paragraph("Total", styles["header_right"]),
    ]]
    for line in lines:
        rows.append([
            Paragraph(_line_description(line), styles["body"]),
            Paragraph(str(line["quantity"]), styles["body_center"]),
            Paragraph(_currency(line["unit_price"]), styles["money"]),
            Paragraph(_currency(line["line_total"]), styles["money_strong"]),
        ])
    table = Table(rows, colWidths=[available_width * 0.55, available_width * 0.1, available_width * 0.17, available_width * 0.18])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_SURFACE)),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor(BRAND_BORDER)),
        ("LINEBELOW", (0, 1), (-1, -1), 0.45, colors.HexColor(BRAND_BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def _totals(quote, styles, Table, TableStyle, Paragraph, colors, available_width):
    tax_base, tax_amount = _tax_from_gross(quote["total_amount"], SUPPORTED_TAX_RATE)
    entries = [
        ("Subtotal", _currency(quote["subtotal"]), "total_value"),
        ("Envío", "GRATIS" if quote["shipping_cost"] == 0 else _currency(quote["shipping_cost"]), "total_value"),
    ]
    if quote["discount_amount"] > 0:
        coupon = f"Descuento ({escape(quote['discount_code'])})" if quote["discount_code"] else "Descuento"
        entries.append((coupon, f"-{_currency(quote['discount_amount'])}", "total_value"))
    entries.extend([
        ("Base imponible", _currency(tax_base), "total_value_secondary"),
        (f"IVA {_display_number(SUPPORTED_TAX_RATE)} %", _currency(tax_amount), "total_value_secondary"),
        ("TOTAL", _currency(quote["total_amount"]), "total_strong"),
    ])
    rows = [[Paragraph(label, styles["total_label"]), Paragraph(value, styles[style])] for label, value, style in entries]
    totals_width = min(available_width, 255)
    table = Table(rows, colWidths=[totals_width * 0.62, totals_width * 0.38], hAlign="RIGHT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ("LINEABOVE", (0, len(entries) - 1), (-1, len(entries) - 1), 1, colors.HexColor(BRAND_RED)),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [table]


def _line_description(line):
    anchorage = _anchorage_label(line.get("anclaje"))
    color = _color_label(line.get("color"))
    dimensions = f"Alto: {_display_number(line['alto'])} cm · Ancho: {_display_number(line['ancho'])} cm"
    details = [dimensions, f"Anclaje: {anchorage}"]
    screws = format_screw_configuration(line.get("screw_length_mm"), line.get("screw_supplement"))
    if screws:
        details.append(f"Tornillos: {screws}")
    details.append(f"Color: {color} · Acabado: esmalte sintético")
    return f"<b>{escape(line['product_name'])}</b><br/><font size='7' color='{BRAND_MUTED}'>{escape('<br/>'.join(details)).replace('&lt;br/&gt;', '<br/>')}</font>"


def _styles(colors, sample, right_alignment):
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle

    body = ParagraphStyle("budget-body", parent=sample["BodyText"], fontName="Helvetica", fontSize=8.4, leading=10.8, textColor=colors.HexColor(BRAND_TEXT))
    small = ParagraphStyle("budget-small", parent=body, fontSize=7.2, leading=9, textColor=colors.HexColor(BRAND_MUTED))
    return {
        "body": body,
        "body_center": ParagraphStyle("budget-body-center", parent=body, alignment=TA_CENTER),
        "header": ParagraphStyle("budget-header", parent=small, fontName="Helvetica-Bold"),
        "header_center": ParagraphStyle("budget-header-center", parent=small, fontName="Helvetica-Bold", alignment=TA_CENTER),
        "header_right": ParagraphStyle("budget-header-right", parent=small, fontName="Helvetica-Bold", alignment=right_alignment),
        "money": ParagraphStyle("budget-money", parent=body, alignment=right_alignment),
        "money_strong": ParagraphStyle("budget-money-strong", parent=body, fontName="Helvetica-Bold", alignment=right_alignment),
        "section": ParagraphStyle("budget-section", parent=body, fontName="Helvetica-Bold", fontSize=9.5, leading=11, spaceAfter=6),
        "total_label": ParagraphStyle("budget-total-label", parent=body, fontSize=8.4),
        "total_value": ParagraphStyle("budget-total-value", parent=body, fontSize=8.4, alignment=right_alignment),
        "total_value_secondary": ParagraphStyle("budget-total-value-secondary", parent=small, alignment=right_alignment),
        "total_strong": ParagraphStyle("budget-total-strong", parent=body, fontName="Helvetica-Bold", fontSize=10, alignment=right_alignment, textColor=colors.HexColor(BRAND_RED)),
        "disclaimer": ParagraphStyle("budget-disclaimer", parent=small, leading=10),
        "disclaimer_right": ParagraphStyle("budget-disclaimer-right", parent=small, alignment=right_alignment),
    }


def _no_padding_style():
    return [
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]


def _anchorage_label(value):
    rule = CONFIGURATOR_ANCHORAGES.get(value)
    return rule["label"] if rule else _text(value) or "-"


def _color_label(value):
    rule = CONFIGURATOR_COLORS.get(value)
    return rule["label"] if rule else _text(value) or "-"


def _money(value):
    try:
        result = Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CartBudgetPdfError("La quote no contiene importes válidos.") from exc
    if not result.is_finite() or result < 0:
        raise CartBudgetPdfError("La quote no contiene importes válidos.")
    return result


def _number(value, *, allow_zero=False):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CartBudgetPdfError("La configuración del carrito no es válida.") from exc
    if not result.is_finite() or result < 0 or (not allow_zero and result == 0):
        raise CartBudgetPdfError("La configuración del carrito no es válida.")
    return result


def _positive_integer(value):
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise CartBudgetPdfError("La configuración del carrito no es válida.") from exc
    if result < 1:
        raise CartBudgetPdfError("La configuración del carrito no es válida.")
    return result


def _text(value):
    return str(value).strip() if value is not None else None


def _display_number(value):
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _currency(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

"""Render manufacturing work orders from their frozen WorkOrderData contract."""

from __future__ import annotations

from io import BytesIO
import logging
from typing import Any, Mapping
from urllib.parse import urlparse, urlunparse
from xml.sax.saxutils import escape as xml_escape

import requests
from PIL import Image, UnidentifiedImageError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as PdfImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from api.work_order_builder import WORK_ORDER_IMAGE_HOSTS, WorkOrderData


logger = logging.getLogger(__name__)

_MAX_IMAGE_BYTES = 5 * 1024 * 1024
_MAX_IMAGE_PIXELS = 16_000_000
_IMAGE_TIMEOUT = (3.05, 8)

_COLOR_PRIMARY = colors.HexColor("#cf1c35")
_COLOR_TEXT = colors.HexColor("#1f2937")
_COLOR_MUTED = colors.HexColor("#64748b")
_COLOR_BORDER = colors.HexColor("#d9dee5")
_COLOR_SURFACE = colors.HexColor("#f8fafc")

_CARD_CELL_PADDING = 8
_CARD_IMAGE_WIDTH = 3.8 * cm


class WorkOrderPdfError(ValueError):
    """Raised when a work-order PDF cannot be rendered from its frozen data."""


def generate_work_order_pdf(data: WorkOrderData) -> bytes:
    """Generate a non-economic A4 PDF using only the WorkOrderData instance."""
    if not isinstance(data, WorkOrderData):
        raise WorkOrderPdfError("El PDF requiere datos de parte de fabricación válidos.")

    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=1.55 * cm,
        rightMargin=1.55 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.45 * cm,
        title="Parte de fabricación MetalWolft",
        author="MetalWolft",
        pageCompression=0,
    )
    styles = _styles()
    story = [
        Paragraph("METALWOLFT", styles["brand"]),
        Paragraph("PARTE DE FABRICACION", styles["title"]),
        Spacer(1, 0.24 * cm),
        _metadata_table(data, styles),
        Spacer(1, 0.32 * cm),
        Paragraph("CLIENTE / ENTREGA", styles["section"]),
        _customer_table(data.customer, styles),
        Spacer(1, 0.36 * cm),
        Paragraph("CONFIGURACIONES A FABRICAR", styles["section"]),
        Spacer(1, 0.1 * cm),
    ]

    for line in data.lines:
        story.append(KeepTogether(_line_card(line, styles, document.width)))
        story.append(Spacer(1, 0.26 * cm))

    if data.internal_notes:
        story.extend(
            [
                Paragraph("OBSERVACIONES INTERNAS DE FABRICACION", styles["section"]),
                _notes_box(data.internal_notes, styles),
            ]
        )

    document.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    return output.getvalue()


def _styles():
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "work-order-brand",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=_COLOR_PRIMARY,
            spaceAfter=3,
        ),
        "title": ParagraphStyle(
            "work-order-title",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=23,
            textColor=_COLOR_TEXT,
        ),
        "section": ParagraphStyle(
            "work-order-section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=_COLOR_TEXT,
            spaceAfter=7,
        ),
        "label": ParagraphStyle(
            "work-order-label",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=_COLOR_MUTED,
        ),
        "value": ParagraphStyle(
            "work-order-value",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12,
            textColor=_COLOR_TEXT,
        ),
        "model": ParagraphStyle(
            "work-order-model",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=_COLOR_TEXT,
        ),
        "quantity": ParagraphStyle(
            "work-order-quantity",
            parent=base["BodyText"],
            alignment=2,
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=14,
            textColor=_COLOR_TEXT,
        ),
        "dimension": ParagraphStyle(
            "work-order-dimension",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=20,
            textColor=_COLOR_TEXT,
        ),
    }


def _metadata_table(data: WorkOrderData, styles):
    values = (
        ("PEDIDO", data.order.get("locator") or "No consta"),
        ("FECHA PEDIDO", data.order.get("ordered_at") or "No consta"),
        ("PARTE GENERADO", data.generated_at or "No consta"),
    )
    table = Table(
        [[_label_value(label, value, styles) for label, value in values]],
        colWidths=[5.85 * cm, 5.85 * cm, 5.85 * cm],
    )
    table.setStyle(_boxed_table_style())
    return table


def _customer_table(customer: Mapping[str, Any], styles):
    address = "<br/>".join(_escape(item) for item in customer.get("delivery_address", ()) or ())
    values = [
        _label_value("NOMBRE", customer.get("name") or "No consta", styles),
        _label_value("TELEFONO", customer.get("phone") or "No consta", styles),
        _label_value("DIRECCION DE ENTREGA", address or "No consta", styles, escaped=True),
    ]
    table = Table([values], colWidths=[5.85 * cm, 4.45 * cm, 7.25 * cm])
    table.setStyle(_boxed_table_style())
    return table


def _line_card(line: Mapping[str, Any], styles, available_width: float):
    image_column_width = _CARD_IMAGE_WIDTH + (2 * _CARD_CELL_PADDING)
    technical_column_width = available_width - image_column_width
    technical_content_width = technical_column_width - (2 * _CARD_CELL_PADDING)
    technical_column_widths = [technical_content_width / 2, technical_content_width / 2]

    image = _image_or_placeholder(line.get("image_url"), styles)
    dimensions = line.get("dimensions") or {}
    unit = dimensions.get("unit") or "cm"
    technical = Table(
        [
            [Paragraph(_escape(line.get("model_name") or "Producto no identificado"), styles["model"]), _quantity(line, styles)],
            [
                _label_value("ALTO", _dimension(dimensions.get("height"), unit), styles),
                _label_value("ANCHO", _dimension(dimensions.get("width"), unit), styles),
            ],
            [
                _label_value("ANCLAJE", _nested_text(line, "anchorage", "label"), styles),
                _label_value("COLOR / ACABADO", _color_text(line), styles),
            ],
            [
                _label_value("TORNILLERIA", _nested_text(line, "screws", "display"), styles),
                _label_value("TIPO", _nested_text(line, "opening_type", "label"), styles),
            ],
        ],
        colWidths=technical_column_widths,
    )
    technical.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _COLOR_SURFACE),
                ("SPAN", (0, 0), (0, 0)),
                ("BOX", (0, 0), (-1, -1), 0.7, _COLOR_BORDER),
                ("INNERGRID", (0, 1), (-1, -1), 0.4, _COLOR_BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    card = Table(
        [[image, technical]],
        colWidths=[image_column_width, technical_column_width],
    )
    card.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.9, _COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), _CARD_CELL_PADDING),
                ("RIGHTPADDING", (0, 0), (-1, -1), _CARD_CELL_PADDING),
                ("TOPPADDING", (0, 0), (-1, -1), _CARD_CELL_PADDING),
                ("BOTTOMPADDING", (0, 0), (-1, -1), _CARD_CELL_PADDING),
            ]
        )
    )
    return [card]


def _quantity(line: Mapping[str, Any], styles):
    value = line.get("quantity")
    display = f"Unidades: {value if value is not None else 'No consta'}"
    return Paragraph(display, styles["quantity"])


def _image_or_placeholder(image_url, styles):
    image_reader = _load_pdf_image(image_url)
    if image_reader is None:
        placeholder = Table([[Paragraph("Imagen no disponible", styles["label"])]], colWidths=[3.8 * cm], rowHeights=[4.0 * cm])
        placeholder.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), _COLOR_SURFACE),
                    ("BOX", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return placeholder
    image = PdfImage(image_reader, width=3.8 * cm, height=4.0 * cm, kind="proportional")
    image.hAlign = "CENTER"
    return image


def _load_pdf_image(image_url):
    transformed_url = _cloudinary_png_url(image_url)
    if transformed_url is None:
        return None
    try:
        response = requests.get(
            transformed_url,
            timeout=_IMAGE_TIMEOUT,
            stream=True,
            allow_redirects=False,
        )
        if response.status_code != 200:
            return None
        content_type = (response.headers.get("Content-Type") or "").lower()
        if not content_type.startswith("image/"):
            return None
        declared_length = response.headers.get("Content-Length")
        if declared_length and int(declared_length) > _MAX_IMAGE_BYTES:
            return None
        content = _read_limited_content(response)
        if not content:
            return None
        return _normalized_image_stream(content)
    except (OSError, ValueError, requests.RequestException, UnidentifiedImageError):
        logger.info("No se pudo cargar una imagen del parte de fabricación.")
        return None


def _cloudinary_png_url(image_url):
    if not isinstance(image_url, str):
        return None
    parsed = urlparse(image_url.strip())
    if parsed.scheme != "https" or parsed.hostname not in WORK_ORDER_IMAGE_HOSTS:
        return None
    marker = "/image/upload/"
    if marker not in parsed.path:
        return None
    png_path = parsed.path.replace(marker, "/image/upload/f_png/", 1)
    return urlunparse(parsed._replace(path=png_path))


def _read_limited_content(response):
    chunks = []
    size = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        size += len(chunk)
        if size > _MAX_IMAGE_BYTES:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


def _normalized_image_stream(content):
    with Image.open(BytesIO(content)) as source:
        if source.width * source.height > _MAX_IMAGE_PIXELS:
            return None
        source.load()
        if source.mode in ("RGBA", "LA"):
            background = Image.new("RGB", source.size, "white")
            alpha = source.getchannel("A")
            background.paste(source.convert("RGB"), mask=alpha)
            image = background
        else:
            image = source.convert("RGB")
        normalized = BytesIO()
        image.save(normalized, format="PNG")
        normalized.seek(0)
        return normalized


def _notes_box(notes, styles):
    table = Table([[Paragraph(_escape(notes), styles["value"])]], colWidths=[17.6 * cm])
    table.setStyle(_boxed_table_style())
    return table


def _boxed_table_style():
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, -1), _COLOR_SURFACE),
            ("BOX", (0, 0), (-1, -1), 0.7, _COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, _COLOR_BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )


def _label_value(label, value, styles, *, escaped=False):
    rendered_value = value if escaped else _escape(value)
    return [
        Paragraph(label, styles["label"]),
        Paragraph(rendered_value or "No consta", styles["value"]),
    ]


def _dimension(value, unit):
    return f"{value} {unit}" if value else "No consta"


def _nested_text(line, section, key):
    value = line.get(section) or {}
    return value.get(key) or "No consta" if isinstance(value, Mapping) else "No consta"


def _color_text(line):
    color = line.get("color") or {}
    if not isinstance(color, Mapping):
        return "No consta"
    label = color.get("label") or "No consta"
    finish = color.get("finish_label")
    return f"{label} - {finish}" if finish else label


def _escape(value):
    return xml_escape(str(value or ""))


def _draw_footer(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(_COLOR_MUTED)
    canvas.drawString(document.leftMargin, 0.8 * cm, "Uso interno de taller. Documento sin datos económicos ni fiscales.")
    canvas.restoreState()

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html import escape
from pathlib import Path

from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash
from api.utils import CONFIGURATOR_ANCHORAGES, CONFIGURATOR_COLORS


SUPPORTED_SCHEMA_VERSIONS = {1, 2}
PDF_ROUTE_PREFIX = "/api/download-invoice"
FILENAME_PREFIX = "invoice_"
FILENAME_SUFFIX = ".pdf"
BRAND_RED = "#cf1c35"
BRAND_TEXT = "#1f2937"
BRAND_MUTED = "#6b7280"
BRAND_BORDER = "#e5e7eb"
BRAND_SURFACE = "#f8f7f7"
BRAND_SURFACE_ACCENT = "#fff6f7"
BRAND_ICON_PATH = Path(__file__).resolve().parents[2] / "apps" / "web-next" / "app" / "icon.png"


class InvoicePdfError(Exception):
    """Base error for invoice PDF generation."""


class InvoicePdfSnapshotMissing(InvoicePdfError):
    """Raised when the invoice does not contain a persisted fiscal snapshot."""


class InvoicePdfIntegrityError(InvoicePdfError):
    """Raised when the persisted snapshot hash does not match the snapshot."""


class InvoicePdfUnsupportedSchema(InvoicePdfError):
    """Raised when the snapshot schema version cannot be rendered."""


class InvoicePdfWriteError(InvoicePdfError):
    """Raised when the PDF cannot be written safely."""


@dataclass(frozen=True)
class InvoicePdfResult:
    pdf_path: str
    filename: str
    generated_at: datetime
    file_size: int


def generate_invoice_pdf(invoice, *, output_dir=None, regenerate=False):
    """Generate a PDF document from an immutable supported InvoiceSnapshot.

    The function deliberately does not commit. It only assigns `invoice.pdf_path`
    after a successful write (or when returning a previously generated file).
    """
    generated_at = datetime.now(timezone.utc)
    invoice_number = _required_invoice_number(invoice)
    snapshot = _validated_snapshot(invoice)
    _validate_snapshot_hash(invoice, snapshot)
    _validate_snapshot_contract(snapshot)

    filename = _invoice_pdf_filename(invoice_number)
    pdf_path = f"{PDF_ROUTE_PREFIX}/{filename}"
    output_path = _safe_output_path(output_dir, filename)

    if output_path.exists():
        if not regenerate and getattr(invoice, "pdf_path", None) == pdf_path:
            return InvoicePdfResult(
                pdf_path=pdf_path,
                filename=filename,
                generated_at=generated_at,
                file_size=output_path.stat().st_size,
            )
        if not regenerate:
            raise InvoicePdfWriteError("No se puede sobrescribir un PDF existente.")

    pdf_bytes = _render_invoice_snapshot_pdf(
        invoice_number=invoice_number,
        issued_at=getattr(invoice, "issued_at", None),
        snapshot=snapshot,
        snapshot_hash=getattr(invoice, "invoice_snapshot_hash", None),
    )
    _write_pdf(output_path, pdf_bytes)

    invoice.pdf_path = pdf_path
    return InvoicePdfResult(
        pdf_path=pdf_path,
        filename=filename,
        generated_at=generated_at,
        file_size=output_path.stat().st_size,
    )


def _required_invoice_number(invoice):
    if invoice is None:
        raise InvoicePdfSnapshotMissing("La factura es obligatoria.")

    invoice_number = getattr(invoice, "invoice_number", None)
    if not invoice_number:
        raise InvoicePdfSnapshotMissing("La factura no tiene numero fiscal.")
    return str(invoice_number)


def _validated_snapshot(invoice):
    snapshot = getattr(invoice, "invoice_snapshot", None)
    if not isinstance(snapshot, dict):
        raise InvoicePdfSnapshotMissing("La factura no tiene snapshot fiscal.")

    schema_version = snapshot.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise InvoicePdfUnsupportedSchema("Version de snapshot no soportada.")
    return snapshot


def _validate_snapshot_hash(invoice, snapshot):
    stored_hash = getattr(invoice, "invoice_snapshot_hash", None)
    if not stored_hash:
        raise InvoicePdfIntegrityError("La factura no tiene hash fiscal.")

    calculated_hash = calculate_invoice_snapshot_hash(snapshot)
    if calculated_hash != stored_hash:
        raise InvoicePdfIntegrityError("El hash fiscal de la factura no coincide.")


def _validate_snapshot_contract(snapshot):
    for key in ("issuer", "customer", "operation", "lines", "totals"):
        if key not in snapshot:
            raise InvoicePdfSnapshotMissing(f"El snapshot no contiene {key}.")

    for key in ("issuer", "customer", "operation", "totals"):
        if not isinstance(snapshot.get(key), dict):
            raise InvoicePdfSnapshotMissing(f"El bloque {key} del snapshot no es valido.")

    lines = snapshot.get("lines")
    if not isinstance(lines, list) or not lines:
        raise InvoicePdfSnapshotMissing("El snapshot no contiene lineas facturables.")

    if snapshot.get("schema_version") == 2:
        required_line_fields = (
            "unit_price_net",
            "line_tax_base_before_discount",
            "discount_tax_base",
            "tax_base",
            "tax_amount",
            "line_total",
        )
        for index, line in enumerate(lines, start=1):
            if not isinstance(line, dict):
                raise InvoicePdfSnapshotMissing(f"La linea {index} del snapshot no es valida.")
            for field in required_line_fields:
                if line.get(field) in (None, ""):
                    raise InvoicePdfSnapshotMissing(
                        f"La linea {index} del snapshot v2 no contiene {field}."
                    )


def _invoice_pdf_filename(invoice_number):
    safe_number = re.sub(r"[^A-Za-z0-9._-]+", "_", str(invoice_number)).strip("._-")
    if not safe_number:
        raise InvoicePdfWriteError("Numero de factura no valido para nombre de archivo.")
    return f"{FILENAME_PREFIX}{safe_number}{FILENAME_SUFFIX}"


def _safe_output_path(output_dir, filename):
    base_dir = Path(output_dir or _default_output_dir()).resolve()
    output_path = (base_dir / filename).resolve()
    if output_path.parent != base_dir:
        raise InvoicePdfWriteError("Ruta de salida no valida.")
    return output_path


def _default_output_dir():
    try:
        from flask import current_app

        configured_folder = current_app.config.get("INVOICE_FOLDER")
    except RuntimeError:
        configured_folder = None

    return configured_folder or os.path.join(os.getcwd(), "invoices")


def _write_pdf(output_path, pdf_bytes):
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as pdf_file:
            pdf_file.write(pdf_bytes)
    except OSError as exc:
        raise InvoicePdfWriteError("No se pudo escribir el PDF de factura.") from exc


def _render_invoice_snapshot_pdf(*, invoice_number, issued_at, snapshot, snapshot_hash):
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        KeepTogether,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()
    margin_left = 1.8 * cm
    margin_right = 1.8 * cm
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margin_left,
        rightMargin=margin_right,
        topMargin=1.55 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "invoice-body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.5,
        textColor=colors.HexColor(BRAND_TEXT),
    )
    small_style = ParagraphStyle(
        "invoice-small",
        parent=body_style,
        fontSize=7.2,
        leading=9,
        textColor=colors.HexColor(BRAND_MUTED),
    )
    centered_small_style = ParagraphStyle(
        "invoice-small-centered",
        parent=small_style,
        alignment=TA_CENTER,
    )
    table_header_style = ParagraphStyle(
        "invoice-table-header",
        parent=small_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor(BRAND_TEXT),
        alignment=TA_CENTER,
    )
    money_style = ParagraphStyle(
        "invoice-money",
        parent=small_style,
        textColor=colors.HexColor(BRAND_TEXT),
        alignment=TA_RIGHT,
    )
    strong_money_style = ParagraphStyle(
        "invoice-money-strong",
        parent=money_style,
        fontName="Helvetica-Bold",
    )
    section_style = ParagraphStyle(
        "invoice-section",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=11,
        spaceAfter=6,
        textColor=colors.HexColor(BRAND_TEXT),
    )
    total_label_style = ParagraphStyle(
        "invoice-total-label",
        parent=body_style,
        fontSize=8.4,
    )
    total_value_style = ParagraphStyle(
        "invoice-total-value",
        parent=total_label_style,
        alignment=TA_RIGHT,
    )
    total_strong_style = ParagraphStyle(
        "invoice-total-strong",
        parent=total_value_style,
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor(BRAND_RED),
    )
    style_map = {
        "body": body_style,
        "small": small_style,
        "small_center": centered_small_style,
        "table_header": table_header_style,
        "money": money_style,
        "money_strong": strong_money_style,
        "section": section_style,
        "total_label": total_label_style,
        "total_value": total_value_style,
        "total_strong": total_strong_style,
    }

    operation = snapshot["operation"]
    issuer = snapshot["issuer"]
    customer = snapshot["customer"]
    available_width = A4[0] - margin_left - margin_right
    box_gap = 0.8 * cm
    box_width = (available_width - box_gap) / 2

    story = [
        _build_invoice_header(
            invoice_number=invoice_number,
            issued_at=issued_at,
            operation=operation,
            available_width=available_width,
            styles=style_map,
        ),
        HRFlowable(
            width="100%",
            thickness=1.1,
            color=colors.HexColor(BRAND_RED),
            spaceBefore=8,
            spaceAfter=14,
        ),
        Table(
            [[
                _build_party_card("Emisor", issuer, box_width, style_map),
                "",
                _build_party_card("Cliente", customer, box_width, style_map),
            ]],
            colWidths=[box_width, box_gap, box_width],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]),
        ),
        Spacer(1, 13),
        _build_order_panel(operation, available_width, style_map),
        Spacer(1, 16),
        Paragraph("Líneas de factura", section_style),
        _build_line_table(snapshot["lines"], style_map, snapshot["schema_version"]),
        Spacer(1, 15),
        KeepTogether(_build_totals_block(snapshot["totals"], snapshot["lines"], style_map)),
    ]

    def draw_page(pdf, doc):
        _draw_page_footer(
            pdf,
            doc,
            invoice_number=invoice_number,
            issuer_email=issuer.get("email"),
        )

    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    buffer.seek(0)
    return buffer.getvalue()


def _build_invoice_header(*, invoice_number, issued_at, operation, available_width, styles):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, Paragraph, Table, TableStyle

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
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]),
        )
    else:
        brand = brand_copy

    issue_value = issued_at or operation.get("issue_date")
    metadata = [
        "<font size='12'><b>FACTURA</b></font>",
        f"<font size='7' color='{BRAND_MUTED}'>NÚMERO</font><br/><b>{_pdf_text(invoice_number)}</b>",
        f"<font size='7' color='{BRAND_MUTED}'>FECHA DE EXPEDICIÓN</font><br/>{_pdf_text(_display_date(issue_value))}",
    ]
    operation_date = operation.get("operation_date")
    if operation_date and _date_key(operation_date) != _date_key(issue_value):
        metadata.append(
            f"<font size='7' color='{BRAND_MUTED}'>FECHA DE OPERACIÓN</font> "
            f"{_pdf_text(_display_date(operation_date))}"
        )
    invoice_info = Paragraph("<br/>".join(metadata), styles["body"])

    table = Table(
        [[brand, invoice_info]],
        colWidths=[available_width * 0.62, available_width * 0.38],
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(BRAND_TEXT)),
    ]))
    return table


def _build_party_card(title, party, width, styles):
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    name = party.get("legal_name") or party.get("trade_name") or "-"
    details = []
    if party.get("tax_id"):
        details.append(f"<font color='{BRAND_MUTED}'>NIF/CIF</font> {_pdf_text(party.get('tax_id'))}")
    if party.get("address"):
        details.append(_pdf_text(party.get("address")))
    city_line = " ".join(
        filter(None, [_text(party.get("postal_code")), _text(party.get("city"))])
    ).strip()
    if city_line:
        details.append(_pdf_text(city_line))
    region_line = " · ".join(
        filter(None, [_text(party.get("province")), _text(party.get("country_code") or "ES")])
    ).strip()
    if region_line:
        details.append(_pdf_text(region_line))

    table = Table(
        [
            [Paragraph(_pdf_text(title.upper()), styles["section"])],
            [Paragraph(
                f"<b>{_pdf_text(name)}</b>" + (f"<br/>{'<br/>'.join(details)}" if details else ""),
                styles["body"],
            )],
        ],
        colWidths=[width],
    )
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(BRAND_BORDER)),
        ("LINEABOVE", (0, 0), (-1, 0), 1.6, colors.HexColor(BRAND_RED)),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.HexColor(BRAND_BORDER)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_SURFACE)),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
        ("TOPPADDING", (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _build_order_panel(operation, width, styles):
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    reference = operation.get("order_locator") or operation.get("order_id") or "-"
    metadata = [
        f"Fecha del pedido: {_pdf_text(_display_date(operation.get('order_date') or operation.get('operation_date')))}",
        f"Moneda: {_pdf_text(operation.get('currency') or 'EUR')}",
    ]
    if operation.get("discount_code"):
        metadata.append(f"Código de descuento: {_pdf_text(operation.get('discount_code'))}")
    content = Paragraph(
        f"<font color='{BRAND_RED}'><b>PEDIDO {_pdf_text(reference)}</b></font>"
        f"<br/><font size='7.4' color='{BRAND_MUTED}'>{' · '.join(metadata)}</font>",
        styles["body"],
    )
    table = Table([[content]], colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(BRAND_SURFACE)),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(BRAND_BORDER)),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, colors.HexColor(BRAND_RED)),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def _build_line_table(lines, styles, schema_version):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle

    table = Table(
        _line_table_rows(lines, styles, schema_version),
        colWidths=[0.70 * cm, 5.25 * cm, 0.95 * cm, 3.00 * cm, 2.25 * cm, 2.55 * cm, 2.70 * cm]
        if schema_version == 2
        else [0.75 * cm, 6.55 * cm, 1.05 * cm, 2.35 * cm, 2.05 * cm, 2.35 * cm, 2.30 * cm],
        repeatRows=1,
        splitByRow=1,
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_SURFACE)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fcfcfc")]),
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, colors.HexColor(BRAND_RED)),
        ("LINEBELOW", (0, 0), (-1, 0), 0.55, colors.HexColor(BRAND_BORDER)),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, colors.HexColor(BRAND_BORDER)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
    ]))
    return table


def _line_table_rows(lines, styles, schema_version):
    from reportlab.platypus import Paragraph

    if schema_version == 2:
        return _line_table_rows_v2(lines, styles)

    rows = [[
        Paragraph("N.º", styles["table_header"]),
        Paragraph("Producto / configuración", styles["table_header"]),
        Paragraph("Cant.", styles["table_header"]),
        Paragraph("Importe original", styles["table_header"]),
        Paragraph("Descuento", styles["table_header"]),
        Paragraph("Base imponible", styles["table_header"]),
        Paragraph("Total", styles["table_header"]),
    ]]

    for line in lines:
        rows.append([
            Paragraph(_pdf_text(line.get("line_number")), styles["small_center"]),
            Paragraph(_line_description(line), styles["body"]),
            Paragraph(_pdf_text(line.get("quantity")), styles["small_center"]),
            Paragraph(_pdf_text(_money(line.get("line_amount_before_discount"))), styles["money"]),
            Paragraph(_pdf_text(_money(line.get("discount_amount"), as_discount=True)), styles["money"]),
            Paragraph(_pdf_text(_money(line.get("tax_base"))), styles["money"]),
            Paragraph(_pdf_text(_money(line.get("line_total"))), styles["money_strong"]),
        ])
    return rows


def _line_table_rows_v2(lines, styles):
    from reportlab.platypus import Paragraph

    rows = [[
        Paragraph("N.º", styles["table_header"]),
        Paragraph("Producto / configuración", styles["table_header"]),
        Paragraph("Cant.", styles["table_header"]),
        Paragraph("Precio unitario sin IVA", styles["table_header"]),
        Paragraph("Descuento s/base", styles["table_header"]),
        Paragraph("Base imponible", styles["table_header"]),
        Paragraph("Total", styles["table_header"]),
    ]]

    for line in lines:
        rows.append([
            Paragraph(_pdf_text(line.get("line_number")), styles["small_center"]),
            Paragraph(_line_description(line), styles["body"]),
            Paragraph(_pdf_text(line.get("quantity")), styles["small_center"]),
            Paragraph(_pdf_text(_money_precise(line.get("unit_price_net"))), styles["money"]),
            Paragraph(_pdf_text(_money(line.get("discount_tax_base"), as_discount=True)), styles["money"]),
            Paragraph(_pdf_text(_money(line.get("tax_base"))), styles["money"]),
            Paragraph(_pdf_text(_money(line.get("line_total"))), styles["money_strong"]),
        ])
    return rows


def _line_description(line):
    description = _pdf_text(line.get("description") or line.get("model") or "Línea")
    configuration = line.get("configuration")
    if not isinstance(configuration, dict):
        return f"<b>{description}</b>"

    primary_details = []
    height = _format_measurement(configuration.get("height_cm"))
    width = _format_measurement(configuration.get("width_cm"))
    if height and width:
        primary_details.append(f"{_pdf_text(height)} × {_pdf_text(width)} cm")
    elif height:
        primary_details.append(f"Alto {_pdf_text(height)} cm")
    elif width:
        primary_details.append(f"Ancho {_pdf_text(width)} cm")

    anchoring = _humanize_anchoring(configuration.get("anchoring"))
    if anchoring:
        primary_details.append(_pdf_text(anchoring))

    secondary_details = []
    color = _humanize_color(configuration.get("color"))
    if color:
        secondary_details.append(_pdf_text(color))
    screw_length = _format_measurement(configuration.get("screw_length_mm"))
    if screw_length:
        secondary_details.append(f"Tornillos {_pdf_text(screw_length)} mm")

    detail_lines = []
    if primary_details:
        detail_lines.append(" · ".join(primary_details))
    if secondary_details:
        detail_lines.append(" · ".join(secondary_details))
    if not detail_lines:
        return f"<b>{description}</b>"
    return (
        f"<b>{description}</b><br/>"
        f"<font size='7.2' color='{BRAND_MUTED}'>{'<br/>'.join(detail_lines)}</font>"
    )


def _build_totals_block(totals, lines, styles):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, Table, TableStyle

    rows = [
        [
            Paragraph("Importe antes del descuento", styles["total_label"]),
            Paragraph(_pdf_text(_money(totals.get("total_amount_before_discount"))), styles["total_value"]),
        ],
        [
            Paragraph("Descuento", styles["total_label"]),
            Paragraph(_pdf_text(_money(totals.get("discount_amount"), as_discount=True)), styles["total_value"]),
        ],
        [
            Paragraph("Base imponible", styles["total_label"]),
            Paragraph(_pdf_text(_money(totals.get("tax_base"))), styles["total_value"]),
        ],
        [
            Paragraph(_pdf_text(_tax_label(lines)), styles["total_label"]),
            Paragraph(_pdf_text(_money(totals.get("tax_amount"))), styles["total_value"]),
        ],
        [
            Paragraph("TOTAL", styles["section"]),
            Paragraph(_pdf_text(_money(totals.get("total_amount"))), styles["total_strong"]),
        ],
    ]
    table = Table(rows, colWidths=[4.45 * cm, 2.55 * cm], hAlign="RIGHT")
    table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.55, colors.HexColor(BRAND_BORDER)),
        ("LINEABOVE", (0, 2), (-1, 2), 0.35, colors.HexColor(BRAND_BORDER)),
        ("LINEABOVE", (0, 4), (-1, 4), 1.2, colors.HexColor(BRAND_RED)),
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor(BRAND_SURFACE_ACCENT)),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return [Paragraph("Resumen", styles["section"]), table]


def _draw_page_footer(pdf, doc, *, invoice_number, issuer_email):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm

    pdf.saveState()
    pdf.setTitle(f"Factura {invoice_number}")
    pdf.setAuthor("MetalWolft")
    pdf.setSubject("Factura emitida por MetalWolft")
    pdf.setKeywords("factura, MetalWolft")
    pdf.setStrokeColor(colors.HexColor(BRAND_BORDER))
    pdf.setLineWidth(0.45)
    pdf.line(1.8 * cm, 1.35 * cm, A4[0] - 1.8 * cm, 1.35 * cm)
    pdf.setFillColor(colors.HexColor(BRAND_MUTED))
    pdf.setFont("Helvetica", 7)
    footer_text = "MetalWolft"
    if issuer_email:
        footer_text += f" · {_text(issuer_email)}"
    pdf.drawString(1.8 * cm, 0.92 * cm, footer_text)
    pdf.drawRightString(A4[0] - 1.8 * cm, 0.92 * cm, f"Página {doc.page}")
    pdf.restoreState()


def _display_date(value):
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).strftime("%d/%m/%Y")
        except ValueError:
            return value
    return "-"


def _date_key(value):
    if hasattr(value, "date"):
        return value.date().isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            return value.strip()
    return ""


def _format_measurement(value):
    if value is None or value == "":
        return ""
    try:
        measurement = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return _text(value).strip()
    if not measurement.is_finite():
        return _text(value).strip()
    return format(measurement.normalize(), "f")


def _humanize_anchoring(value):
    normalized = _text(value).strip()
    if not normalized:
        return ""
    rule = CONFIGURATOR_ANCHORAGES.get(normalized)
    if not rule:
        return normalized
    return _text(rule.get("name") or rule.get("label") or normalized).strip()


def _humanize_color(value):
    normalized = _text(value).strip()
    if not normalized:
        return ""
    rule = CONFIGURATOR_COLORS.get(normalized)
    if not rule:
        return normalized
    return _text(rule.get("label") or rule.get("name") or normalized).strip()


def _tax_label(lines):
    rates = []
    for line in lines:
        rate = _format_measurement(line.get("tax_rate"))
        if rate and rate not in rates:
            rates.append(rate)
    if len(rates) == 1:
        return f"IVA {rates[0]} %"
    return "Cuota de IVA"


def _money(value, *, as_discount=False):
    try:
        amount = Decimal(str(value or "0.00"))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0.00")
    amount = amount.quantize(Decimal("0.01"))
    prefix = ""
    if amount < 0:
        prefix = "-"
        amount = abs(amount)
    elif as_discount and amount > 0:
        prefix = "-"
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{prefix}{formatted} €"


def _money_precise(value):
    """Format an already-frozen precise amount without deriving fiscal data."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise InvoicePdfSnapshotMissing("El precio unitario sin IVA no es valido.")
    if not amount.is_finite():
        raise InvoicePdfSnapshotMissing("El precio unitario sin IVA no es valido.")

    sign = "-" if amount < 0 else ""
    integer, _, decimals = format(abs(amount), "f").partition(".")
    decimals = decimals.rstrip("0").ljust(2, "0")
    grouped_integer = f"{int(integer):,}".replace(",", ".")
    return f"{sign}{grouped_integer},{decimals} €"


def _text(value):
    if value is None:
        return ""
    return str(value)


def _pdf_text(value):
    return escape(_text(value))

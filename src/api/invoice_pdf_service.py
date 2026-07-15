import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html import escape
from pathlib import Path

from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash


SUPPORTED_SCHEMA_VERSION = 1
PDF_ROUTE_PREFIX = "/api/download-invoice"
FILENAME_PREFIX = "invoice_"
FILENAME_SUFFIX = ".pdf"


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
    """Generate a PDF document from the immutable InvoiceSnapshot v1 only.

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
    if schema_version != SUPPORTED_SCHEMA_VERSION:
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
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Paragraph, Table, TableStyle

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Factura {invoice_number}")
    pdf.setAuthor("MetalWolft")
    pdf.setSubject(f"InvoiceSnapshot v1 {snapshot_hash}")
    pdf.setKeywords(f"invoice_snapshot_hash:{snapshot_hash}")

    width, height = A4
    margin_left = 1.8 * cm
    margin_right = 1.8 * cm
    y = height - 1.8 * cm

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "invoice-v2-body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=9.5,
    )
    header_style = ParagraphStyle(
        "invoice-v2-header",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=colors.whitesmoke,
    )

    operation = snapshot["operation"]
    issuer = snapshot["issuer"]
    customer = snapshot["customer"]

    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(colors.Color(1, 0.196, 0.302))
    pdf.drawString(margin_left, y, "MetalWolft")
    pdf.setFont("Helvetica-Bold", 13)
    pdf.setFillColor(colors.black)
    pdf.drawRightString(width - margin_right, y, "Factura")

    y -= 20
    pdf.setFont("Helvetica", 9)
    pdf.drawString(margin_left, y, "Rejas para ventanas a medida")
    pdf.drawRightString(width - margin_right, y, f"Numero: {invoice_number}")

    y -= 14
    pdf.drawRightString(
        width - margin_right,
        y,
        f"Fecha emision: {_display_date(issued_at or operation.get('issue_date'))}",
    )

    y -= 28
    box_gap = 0.8 * cm
    box_width = (width - margin_left - margin_right - box_gap) / 2
    issuer_rows = _party_rows("Emisor", issuer)
    customer_rows = _party_rows("Cliente", customer)
    issuer_height = _draw_info_table(pdf, margin_left, y, box_width, issuer_rows, body_style, header_style)
    customer_height = _draw_info_table(
        pdf,
        margin_left + box_width + box_gap,
        y,
        box_width,
        customer_rows,
        body_style,
        header_style,
    )

    y -= max(issuer_height, customer_height) + 24
    operation_rows = [
        ["Referencia pedido", _text(operation.get("order_locator") or operation.get("order_id"))],
        ["Fecha pedido", _display_date(operation.get("order_date") or operation.get("operation_date"))],
        ["Moneda", _text(operation.get("currency") or "EUR")],
    ]
    if operation.get("discount_code"):
        operation_rows.append(["Codigo descuento", _text(operation.get("discount_code"))])
    operation_height = _draw_info_table(
        pdf,
        margin_left,
        y,
        width - margin_left - margin_right,
        [["Pedido", ""]] + operation_rows,
        body_style,
        header_style,
    )

    y -= operation_height + 24
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margin_left, y, "Lineas de factura")
    y -= 8

    line_rows = _line_table_rows(snapshot["lines"], body_style, header_style)
    line_table = Table(
        line_rows,
        colWidths=[1.0 * cm, 5.0 * cm, 1.2 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm],
        repeatRows=1,
    )
    line_table.setStyle(_table_style())
    line_table.wrapOn(pdf, margin_left, y)
    line_height = line_table._height
    if y - line_height < 4.0 * cm:
        pdf.showPage()
        y = height - 1.8 * cm
    line_table.drawOn(pdf, margin_left, y - line_height)

    y -= line_height + 22
    if y < 5.0 * cm:
        pdf.showPage()
        y = height - 1.8 * cm

    totals_height = _draw_totals_table(
        pdf,
        width - margin_right - 7.0 * cm,
        y,
        7.0 * cm,
        snapshot["totals"],
        body_style,
        header_style,
    )

    y -= totals_height + 22
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(colors.HexColor("#5b6472"))
    pdf.drawString(margin_left, max(y, 1.5 * cm), f"Integridad fiscal: {snapshot_hash}")

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def _party_rows(title, party):
    rows = [[title, ""]]
    rows.append(["Nombre", _text(party.get("legal_name") or party.get("trade_name"))])
    rows.append(["NIF/CIF", _text(party.get("tax_id"))])
    rows.append(["Direccion", _text(party.get("address"))])
    rows.append(["CP / Ciudad", " ".join(filter(None, [_text(party.get("postal_code")), _text(party.get("city"))])).strip()])
    if party.get("province"):
        rows.append(["Provincia", _text(party.get("province"))])
    rows.append(["Pais", _text(party.get("country_code") or "ES")])
    if party.get("email"):
        rows.append(["Email", _text(party.get("email"))])
    if party.get("phone"):
        rows.append(["Telefono", _text(party.get("phone"))])
    return rows


def _draw_info_table(pdf, x, y, width, rows, body_style, header_style):
    from reportlab.platypus import Paragraph, Table

    table_data = []
    for index, row in enumerate(rows):
        style = header_style if index == 0 else body_style
        table_data.append([Paragraph(_pdf_text(row[0]), style), Paragraph(_pdf_text(row[1]), style)])

    table = Table(table_data, colWidths=[width * 0.34, width * 0.66])
    table.setStyle(_table_style(span_header=True))
    table.wrapOn(pdf, x, y)
    table_height = table._height
    table.drawOn(pdf, x, y - table_height)
    return table_height


def _line_table_rows(lines, body_style, header_style):
    from reportlab.platypus import Paragraph

    rows = [[
        Paragraph("Linea", header_style),
        Paragraph("Descripcion / configuracion", header_style),
        Paragraph("Ud.", header_style),
        Paragraph("Antes dto.", header_style),
        Paragraph("Descuento", header_style),
        Paragraph("Base imp.", header_style),
        Paragraph("Total", header_style),
    ]]

    for line in lines:
        rows.append([
            Paragraph(_pdf_text(line.get("line_number")), body_style),
            Paragraph(_line_description(line), body_style),
            Paragraph(_pdf_text(line.get("quantity")), body_style),
            Paragraph(_pdf_text(_money(line.get("line_amount_before_discount"))), body_style),
            Paragraph(_pdf_text(_money(line.get("discount_amount"))), body_style),
            Paragraph(_pdf_text(_money(line.get("tax_base"))), body_style),
            Paragraph(_pdf_text(_money(line.get("line_total"))), body_style),
        ])
    return rows


def _line_description(line):
    description = _pdf_text(line.get("description") or line.get("model") or "Linea")
    configuration = line.get("configuration") or {}
    details = []
    if configuration.get("height_cm"):
        details.append(f"Alto {_pdf_text(configuration.get('height_cm'))} cm")
    if configuration.get("width_cm"):
        details.append(f"Ancho {_pdf_text(configuration.get('width_cm'))} cm")
    if configuration.get("anchoring"):
        details.append(f"Anclaje: {_pdf_text(configuration.get('anchoring'))}")
    if configuration.get("color"):
        details.append(f"Color: {_pdf_text(_format_color(configuration.get('color')))}")
    if details:
        return f"{description}<br/><font size='7'>{' | '.join(details)}</font>"
    return description


def _draw_totals_table(pdf, x, y, width, totals, body_style, header_style):
    from reportlab.platypus import Paragraph, Table

    rows = [
        [Paragraph("Totales", header_style), ""],
        [Paragraph("Importe antes descuento", body_style), Paragraph(_pdf_text(_money(totals.get("total_amount_before_discount"))), body_style)],
        [Paragraph("Descuento", body_style), Paragraph(_pdf_text(_money(totals.get("discount_amount"))), body_style)],
        [Paragraph("Base imponible", body_style), Paragraph(_pdf_text(_money(totals.get("tax_base"))), body_style)],
        [Paragraph("IVA 21 %", body_style), Paragraph(_pdf_text(_money(totals.get("tax_amount"))), body_style)],
        [Paragraph("Total EUR", body_style), Paragraph(_pdf_text(_money(totals.get("total_amount"))), body_style)],
    ]
    table = Table(rows, colWidths=[width * 0.58, width * 0.42])
    table.setStyle(_table_style(span_header=True))
    table.wrapOn(pdf, x, y)
    table_height = table._height
    table.drawOn(pdf, x, y - table_height)
    return table_height


def _table_style(*, span_header=False):
    from reportlab.lib import colors
    from reportlab.platypus import TableStyle

    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(1, 0.196, 0.302)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#d9dee5")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d9dee5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if span_header:
        commands.append(("SPAN", (0, 0), (1, 0)))
    return TableStyle(commands)


def _display_date(value):
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).strftime("%d/%m/%Y")
        except ValueError:
            return value
    return "-"


def _format_color(value):
    return _text(value).replace("_", " ")


def _money(value):
    try:
        amount = Decimal(str(value or "0.00"))
    except (InvalidOperation, ValueError):
        amount = Decimal("0.00")
    return f"{amount.quantize(Decimal('0.01')):.2f} EUR"


def _text(value):
    if value is None:
        return ""
    return str(value)


def _pdf_text(value):
    return escape(_text(value))

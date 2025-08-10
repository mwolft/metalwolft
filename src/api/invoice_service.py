# api/invoice_service.py
from io import BytesIO
from datetime import datetime
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

# (Opcional) permitir logo por URL
try:
    import requests
except Exception:
    requests = None


# ================= Estilos y constantes =================
COLOR_PRIMARY = colors.Color(1, 0.196, 0.302)    # rojo marca
COLOR_BOX_BG  = colors.HexColor("#f9fafb")
COLOR_BOX_BD  = colors.HexColor("#dddddd")
COLOR_TEXT    = colors.black

FONT_BASE     = "Helvetica"
FONT_BOLD     = "Helvetica-Bold"

# Márgenes
M_LEFT, M_RIGHT, M_TOP, M_BOTTOM = 2*cm, 2*cm, 2*cm, 2*cm

# ------------------------------------------------------------------TODO: ajustar interlineado de filas en cajas Proveedor/Cliente (leading)
# Valores típicos: 10–12 (menos = más compacto)

# Paragraph styles
STYLE_LABEL = ParagraphStyle('label', fontName=FONT_BOLD, fontSize=9, leading=10)
STYLE_VALUE = ParagraphStyle('value', fontName=FONT_BASE, fontSize=9, leading=10)
STYLE_TITLE = ParagraphStyle('title', fontName=FONT_BOLD, fontSize=9, leading=10, textColor=colors.whitesmoke)


# ================= Helpers =================
def _draw_title_value(pdf, x, y, title, value, title_font=FONT_BOLD, value_font=FONT_BASE, title_size=9, value_size=10):
    pdf.setFont(title_font, title_size)
    pdf.setFillColor(COLOR_TEXT)
    pdf.drawString(x, y, title)
    pdf.setFont(value_font, value_size)
    pdf.drawString(x, y-12, value)


def _load_logo_reader(logo_path_or_url):
    """
    Devuelve un ImageReader válido a partir de ruta local o URL.
    Si falla, devuelve None.
    """
    if not logo_path_or_url:
        return None
    try:
        # Si es URL y requests está disponible
        if (str(logo_path_or_url).startswith("http://") or str(logo_path_or_url).startswith("https://")) and requests:
            resp = requests.get(logo_path_or_url, timeout=5)
            resp.raise_for_status()
            return ImageReader(BytesIO(resp.content))
        # Ruta local
        return ImageReader(logo_path_or_url)
    except Exception:
        return None


def _draw_info_box(pdf, x, y, w, title, rows):
    """
    Dibuja una caja (Table) con:
      - fila de título (span 2 cols)
      - filas label–valor
    Retorna: altura total usada por la tabla (para gestionar el y siguiente)
    """
    data = [[Paragraph(title, STYLE_TITLE), ""]]
    for label, value in rows:
        data.append([Paragraph(label, STYLE_LABEL), Paragraph(value or "—", STYLE_VALUE)])

    table = Table(
        data,
        colWidths=[w * 0.35, w * 0.65],
        hAlign='LEFT'
    )
    table.setStyle(TableStyle([
        # Caja exterior y fondos
        ('BOX', (0,0), (-1,-1), 0.8, COLOR_BOX_BD),
        ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),       # banda del título
        ('BACKGROUND', (0,1), (-1,-1), COLOR_BOX_BG),       # cuerpo
        # Span del título en dos columnas
        ('SPAN', (0,0), (1,0)),
        # Tipografías y colores
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONT', (0,0), (-1,0), FONT_BOLD, 9),
        ('FONT', (0,1), (-1,-1), FONT_BASE, 9),
        # ---------------------------------------------------------------- TODO: padding interno de las cajas (más bajo = caja más compacta)
        # TOP/BOTTOM típicos: 3–6; LEFT/RIGHT: 6–10
        # Padding
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
        # Separador vertical entre label y valor
        ('LINEBEFORE', (1,1), (1,-1), 0.3, COLOR_BOX_BD),
    ]))

    table.wrapOn(pdf, x, y)
    h = table._height
    table.drawOn(pdf, x, y - h)
    return h


# ================= Render principal =================
def render_invoice_pdf(inv: dict) -> bytes:
    """
    inv: dict con claves:
      series (opcional), invoice_number (str|None), date (dd/mm/YYYY opcional), locator (opcional)
      logo_path (opcional, ruta local o URL)
      supplier: {name,cif,address,city,phone,email(optional)}
      client:   {firstname,lastname,billing_address,billing_city,billing_postal_code,phone,cif}
      shipping: {same_as_billing(bool), address, city, postal_code}
      payment:  {method, iban(optional), due_date(optional)}
      lines:    [{name, alto, ancho, anclaje, color, qty, unit_price}]
      totals:   {shipping_cost, iva_rate(0.21), total (opcional)}
      footer_notes (str opcional)
    Devuelve: bytes del PDF
    """
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # ====== Cabecera ======
    y = height - M_TOP

    # Logo (izquierda)
    logo_w, logo_h = 4.8*cm, 1.4*cm
    logo_x, logo_y = M_LEFT, y - logo_h
    logo_reader = _load_logo_reader(inv.get("logo_path"))
    if logo_reader:
        try:
            pdf.drawImage(logo_reader, logo_x, logo_y, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass  # no romper si falla

    # Caja “Factura” (derecha)
    box_w = 8*cm
    # ------------------------------------------ TODO: altura de la caja "Factura" (más alto = más aire dentro)
    box_h = 3.2*cm
    box_x = width - M_RIGHT - box_w
    box_y = y

    # Marco de la caja
    pdf.setFillColor(COLOR_BOX_BG)
    pdf.setStrokeColor(COLOR_BOX_BD)
    pdf.setLineWidth(1)
    pdf.roundRect(box_x, box_y - box_h, box_w, box_h, 6, stroke=1, fill=1)

    # Banda de título
    title_band_h = 16
    pdf.setFillColor(COLOR_PRIMARY)
    pdf.roundRect(box_x, box_y - title_band_h, box_w, title_band_h, 6, stroke=0, fill=1)
    pdf.setFillColor(colors.whitesmoke)
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(box_x + 8, box_y - title_band_h + 4, "Factura")

    # Contenido de la caja (número, fecha, locator)
    # ------------------------------------ TODO: punto de inicio del contenido en "Factura" (más grande = baja el texto)
    cur_y = box_y - 24
    pdf.setFillColor(COLOR_TEXT)
    series = inv.get('series')
    num = inv.get('invoice_number') or "PREVIEW"
    num_txt = f"{series}-{num}" if series and num else num

    pdf.setFont(FONT_BOLD, 10); pdf.drawString(box_x + 8, cur_y, "Número:")
    pdf.setFont(FONT_BASE, 10);  pdf.drawRightString(box_x + box_w - 8, cur_y, num_txt)
# --------------------------------------------------------------------------------------TODO: separación entre líneas dentro de "Factura"
    cur_y -= 14
    fecha = inv.get('date') or datetime.now().strftime("%d/%m/%Y")
    pdf.setFont(FONT_BOLD, 10); pdf.drawString(box_x + 8, cur_y, "Fecha:")
    pdf.setFont(FONT_BASE, 10);  pdf.drawRightString(box_x + box_w - 8, cur_y, fecha)

    loc = inv.get('locator')
    if loc:
# --------------------------------------------------------------------------------------TODO: separación entre líneas dentro de "Factura"
        cur_y -= 14
        pdf.setFont(FONT_BOLD, 10); pdf.drawString(box_x + 8, cur_y, "Localizador:")
        pdf.setFont(FONT_BASE, 10);  pdf.drawRightString(box_x + box_w - 8, cur_y, str(loc))

    # Título principal a la izquierda
    pdf.setFont(FONT_BOLD, 14)
    pdf.setFillColor(COLOR_PRIMARY)
    pdf.drawString(M_LEFT, y - 4, "Factura")

    # ====== Cajas Proveedor y Cliente/Envío ======
    top_after_header = y - (logo_h + 16)

    # Anchos y posiciones
    box_gap = 0.8*cm
    col_w = (width - M_LEFT - M_RIGHT - box_gap) / 2.0
    left_x = M_LEFT
    right_x = M_LEFT + col_w + box_gap
    row_top_y = top_after_header

    # PROVEEDOR
    s = inv.get('supplier', {}) or {}
    supplier_rows = [
        ("Nombre",   s.get('name','') or ''),
        ("NIF/CIF",  s.get('cif','') or ''),
        ("Dirección",s.get('address','') or ''),
        ("Ciudad",   s.get('city','') or ''),
    ]
    contact = " · ".join(filter(None, [
        f"Tel: {s['phone']}" if s.get('phone') else '',
        s.get('email','')
    ])).strip(" ·")
    if contact:
        supplier_rows.append(("Contacto", contact))

    supplier_h = _draw_info_box(pdf, left_x, row_top_y, col_w, "Proveedor", supplier_rows)

    # CLIENTE
    c = inv.get('client', {}) or {}
    fullname = f"{c.get('firstname','')} {c.get('lastname','')}".strip() or "—"
    city_line = " ".join(list(filter(None, [
        c.get('billing_city',''),
        f"({c.get('billing_postal_code','')})" if c.get('billing_postal_code') else ""
    ]))).strip()

    client_rows = [
        ("Nombre",   fullname),
        ("NIF/CIF",  c.get('cif','') or '—'),
        ("Dirección",c.get('billing_address','') or '—'),
        ("Ciudad",   city_line or '—'),
    ]
    if c.get('phone'):
        client_rows.append(("Teléfono", c.get('phone')))

    client_h = _draw_info_box(pdf, right_x, row_top_y, col_w, "Cliente", client_rows)

    # ENVÍO
    sh = inv.get('shipping', {}) or {}
    if sh.get('same_as_billing', False) or not sh.get('address'):
        envio_rows = [("Dirección de envío", "La misma que la de facturación")]
    else:
        envio_city = " ".join(list(filter(None, [
            sh.get('city',''),
            f"({sh.get('postal_code','')})" if sh.get('postal_code') else ""
        ]))).strip()
        envio_rows = [
            ("Dirección de envío", sh.get('address','') or '—'),
            ("Ciudad", envio_city or '—')
        ]

    envio_top_y = row_top_y - client_h - 0.4*cm
    envio_h = _draw_info_box(pdf, right_x, envio_top_y, col_w, "Envío", envio_rows)

    # Punto de inicio para la tabla de líneas
    y_below_boxes = min(row_top_y - supplier_h, envio_top_y - envio_h) - 1.2*cm

    # ====== Tabla de líneas ======
    table_top = y_below_boxes
    pdf.setFont(FONT_BOLD, 12); pdf.setFillColor(COLOR_TEXT)
    pdf.drawString(M_LEFT, table_top + 8, "Detalles del Pedido")

    data = [["Producto", "Alto", "Ancho", "Anc.", "Color", "Ud.", "P. unit.", "Importe"]]
    total_lineas = 0.0

    for ln in inv.get('lines', []):
        qty = int(ln.get('qty', 1))
        unit = float(ln.get('unit_price', 0))
        importe = unit * qty
        total_lineas += importe
        data.append([
            (ln.get('name','') or '')[:40],
            str(ln.get('alto','') or ''),
            str(ln.get('ancho','') or ''),
            ln.get('anclaje','') or '',
            (ln.get('color','') or '')[:12],
            str(qty),
            f"{unit:.2f}",
            f"{importe:.2f}",
        ])

    table = Table(
        data,
        colWidths=[6.0*cm, 1.3*cm, 1.3*cm, 2.2*cm, 2.0*cm, 1.2*cm, 2.2*cm, 2.2*cm]
    )

    # Estilos + zebra striping
    styles = [
        ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME',   (0,0), (-1,0), FONT_BOLD),
        ('FONTSIZE',   (0,0), (-1,0), 9),
        ('ALIGN',      (1,1), (-1,-1), 'CENTER'),
        ('FONTNAME',   (0,1), (-1,-1), FONT_BASE),
        ('FONTSIZE',   (0,1), (-1,-1), 9),
        ('GRID',       (0,0), (-1,-1), 0.5, colors.black),
        ('TOPPADDING',    (0,1), (-1,-1), 4),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 1:
            styles.append(('BACKGROUND', (0,i), (-1,i), colors.whitesmoke))
    table.setStyle(TableStyle(styles))

    y_table = table_top - 10
    table.wrapOn(pdf, M_LEFT, y_table)
    table_h = table._height
    table.drawOn(pdf, M_LEFT, y_table - table_h)

    # ====== Totales (en caja) ======
    totals_top = y_table - table_h - 12
    totals_w = 8*cm
    totals_h = 3.8*cm
    totals_x = width - M_RIGHT - totals_w
    totals_y = totals_top

    # Caja resumen
    pdf.setFillColor(COLOR_BOX_BG)
    pdf.setStrokeColor(COLOR_BOX_BD)
    pdf.setLineWidth(1)
    pdf.roundRect(totals_x, totals_y - totals_h, totals_w, totals_h, 6, stroke=1, fill=1)
    # Título
    pdf.setFillColor(COLOR_PRIMARY)
    pdf.roundRect(totals_x, totals_y - 16, totals_w, 16, 6, stroke=0, fill=1)
    pdf.setFillColor(colors.whitesmoke)
    pdf.setFont(FONT_BOLD, 9)
    pdf.drawString(totals_x + 8, totals_y - 12, "Resumen")

    # Cálculos
    t = inv.get('totals', {}) or {}
    iva_rate = float(t.get('iva_rate', 0.21))
    shipping_cost = float(t.get('shipping_cost', 0.0))
    total = float(t.get('total', total_lineas + shipping_cost))
    base_total = total / (1 + iva_rate)
    base_envio = shipping_cost / (1 + iva_rate)
    base_prod = max(base_total - base_envio, 0)
    iva_calc = total - base_total

    cur = totals_y - 26
    pdf.setFont(FONT_BASE, 10); pdf.setFillColor(COLOR_TEXT)
    pdf.drawString(totals_x + 8, cur, "Base productos:")
    pdf.drawRightString(totals_x + totals_w - 8, cur, f"{base_prod:.2f} €")
    cur -= 14
    pdf.drawString(totals_x + 8, cur, "Envío (base):")
    pdf.drawRightString(totals_x + totals_w - 8, cur, f"{base_envio:.2f} €")
    cur -= 14
    pdf.drawString(totals_x + 8, cur, f"IVA ({int(iva_rate*100)}%):")
    pdf.drawRightString(totals_x + totals_w - 8, cur, f"{iva_calc:.2f} €")
    cur -= 20
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(totals_x + 8, cur, "TOTAL:")
    pdf.drawRightString(totals_x + totals_w - 8, cur, f"{total:.2f} €")

    # ====== Pago (opcional) ======
    pay = inv.get('payment') or {}
    if pay.get('method') or pay.get('iban') or pay.get('due_date'):
        pay_w = (width - M_LEFT - M_RIGHT) - totals_w - 0.6*cm
        pay_x = M_LEFT
        pay_y = totals_top
        pay_h = totals_h
        # Caja
        pdf.setFillColor(COLOR_BOX_BG)
        pdf.setStrokeColor(COLOR_BOX_BD)
        pdf.setLineWidth(1)
        pdf.roundRect(pay_x, pay_y - pay_h, pay_w, pay_h, 6, stroke=1, fill=1)
        # Título
        pdf.setFillColor(COLOR_PRIMARY)
        pdf.roundRect(pay_x, pay_y - 16, pay_w, 16, 6, stroke=0, fill=1)
        pdf.setFillColor(colors.whitesmoke)
        pdf.setFont(FONT_BOLD, 9)
        pdf.drawString(pay_x + 8, pay_y - 12, "Pago")

        py = pay_y - 26
        pdf.setFont(FONT_BASE, 10); pdf.setFillColor(COLOR_TEXT)
        if pay.get('method'):
            _draw_title_value(pdf, pay_x + 8, py, "Método", str(pay['method']))
            py -= 20
        if pay.get('iban'):
            _draw_title_value(pdf, pay_x + 8, py, "IBAN", str(pay['iban']))
            py -= 20
        if pay.get('due_date'):
            _draw_title_value(pdf, pay_x + 8, py, "Vencimiento", str(pay['due_date']))

    # ====== Pie y marca PREVIEW ======
    footer_y = M_BOTTOM
    notes = inv.get('footer_notes') or "Precios con IVA incluido. Gracias por su compra. Para soporte y devoluciones: www.metalwolft.com"
    pdf.setFont(FONT_BASE, 8); pdf.setFillColor(COLOR_TEXT)
    pdf.drawString(M_LEFT, footer_y, notes)

    if not inv.get('invoice_number'):
        pdf.setFont(FONT_BOLD, 48)
        pdf.setFillGray(0.90)
        pdf.drawString(130, height/2, "PREVIEW / NO VÁLIDA")

    # Página
    pdf.setFont(FONT_BASE, 8); pdf.setFillColor(COLOR_TEXT)
    pdf.drawRightString(width - M_RIGHT, footer_y, "Página 1 de 1")

    pdf.save()
    buf.seek(0)
    return buf.getvalue()

from io import BytesIO
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import cm

def render_invoice_pdf(inv: dict) -> bytes:
    """
    inv: dict con claves:
      invoice_number (str|None), date (dd/mm/YYYY opcional)
      supplier: {name,cif,address,city,phone}
      client: {firstname,lastname,billing_address,billing_city,billing_postal_code,phone,cif}
      shipping: {same_as_billing(bool), address, city, postal_code}
      lines: [ {name, alto, ancho, anclaje, color, qty, unit_price} ]
      totals: {shipping_cost, iva_rate(0.21), total (opcional)}
    Devuelve: bytes del PDF
    """
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    pdf.setTitle(f"Factura_{inv.get('invoice_number') or 'PREVIEW'}")

    # Encabezado
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 800, f"Factura No: {inv.get('invoice_number') or 'PREVIEW'}")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 780, f"Fecha: {inv.get('date') or datetime.now().strftime('%d/%m/%Y')}")

    # Proveedor
    s = inv.get('supplier', {})
    pdf.setFont("Helvetica-Bold", 12); pdf.drawString(400, 700, "PROVEEDOR")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(400, 680, s.get('name', ''))
    pdf.drawString(400, 665, s.get('cif', ''))
    pdf.drawString(400, 650, s.get('address', ''))
    pdf.drawString(400, 635, s.get('city', ''))
    pdf.drawString(400, 620, s.get('phone', ''))

    # Cliente
    c = inv.get('client', {})
    pdf.setFont("Helvetica-Bold", 12); pdf.drawString(50, 700, "CLIENTE")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 680, f"{c.get('firstname','')} {c.get('lastname','')}".strip())
    pdf.drawString(50, 665, f"{c.get('billing_address','')}, {c.get('billing_city','')} ({c.get('billing_postal_code','')})")
    if c.get('cif'):   pdf.drawString(50, 650, c['cif'])
    if c.get('phone'): pdf.drawString(50, 635, c['phone'])

    # Envío
    sh = inv.get('shipping', {}) or {}
    pdf.setFont("Helvetica-Bold", 12); pdf.drawString(50, 580, "Dirección de Envío")
    pdf.setFont("Helvetica", 10)
    if sh.get('same_as_billing', False) or not sh.get('address'):
        pdf.drawString(50, 560, "La misma que la de facturación")
    else:
        pdf.drawString(50, 560, f"{sh.get('address','')}, {sh.get('city','')} ({sh.get('postal_code','')})")

    # Líneas
    pdf.setFont("Helvetica-Bold", 12); pdf.drawString(50, 510, "Detalles del Pedido")
    data = [["Prod.", "Alto", "Ancho", "Anc.", "Col.", "Ud.", "Importe (€)"]]
    total_lineas = 0.0
    for ln in inv.get('lines', []):
        qty = int(ln.get('qty', 1))
        unit = float(ln.get('unit_price', 0))
        importe = unit * qty
        total_lineas += importe
        data.append([
            (ln.get('name','') or '')[:20],
            str(ln.get('alto','') or ''),
            str(ln.get('ancho','') or ''),
            ln.get('anclaje','') or '',
            (ln.get('color','') or '')[:10],
            str(qty),
            f"{importe:.2f}",
        ])

    table = Table(data, colWidths=[4*cm,1.5*cm,1.5*cm,5*cm,2*cm,1*cm,3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.Color(1,0.196,0.302)),
        ('TEXTCOLOR',(0,0),(-1,0), colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('GRID',(0,0),(-1,-1),1, colors.black),
    ]))
    y = 480; table.wrapOn(pdf, 50, y); h = table._height; table.drawOn(pdf, 50, y - h)

    ypos = y - h - 30
    if ypos < 50:
        pdf.showPage()
        ypos = 750

    # Totales
    totals = inv.get('totals', {}) or {}
    iva_rate = float(totals.get('iva_rate', 0.21))
    shipping_cost = float(totals.get('shipping_cost', 0.0))
    total = float(totals.get('total', total_lineas + shipping_cost))
    base_total = total / (1 + iva_rate)
    base_envio = shipping_cost / (1 + iva_rate)
    base_prod = base_total - base_envio
    iva_calc = total - base_total

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, ypos,       f"Base Imponible: {base_total:.2f} €")
    pdf.drawString(50, ypos - 15,  f"Envío (base): {base_envio:.2f} €")
    pdf.drawString(50, ypos - 30,  f"IVA ({int(iva_rate*100)}%): {iva_calc:.2f} €")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, ypos - 50,  f"Total: {total:.2f} €")

    # Marca PREVIEW si no hay número
    if not inv.get('invoice_number'):
        pdf.setFont("Helvetica-Bold", 40)
        pdf.setFillGray(0.85)
        pdf.drawString(150, 400, "PREVIEW")

    pdf.save()
    buf.seek(0)
    return buf.getvalue()

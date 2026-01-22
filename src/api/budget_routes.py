from flask import Blueprint, request, send_file, current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from datetime import datetime
import os
import uuid

budget_bp = Blueprint("budget", __name__)


@budget_bp.route("/budget/pdf", methods=["POST"])
def generate_budget_pdf():

    data = request.get_json()

    cart = data["cart"]
    subtotal = float(data["subtotal"])
    shipping = float(data["shipping"])
    discount_percent = float(data.get("discount_percent", 0))
    discount_amount = float(data.get("discount_amount", 0))
    total = float(data["total"])

    now = datetime.now()

    filename = f"presupuesto_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.pdf"
    output_dir = os.path.join(current_app.root_path, "assets", "budgets")
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - 55 * mm

        # --- LOGO ---
    logo_url = "https://res.cloudinary.com/dewanllxn/image/upload/v1740167674/logo_uxlqof.png"

    try:
        c.drawImage(
            logo_url,
            width - 310,   # más a la izquierda
            height - 90,   # un pelín más abajo para centrarlo visualmente
            width=190,     # más pequeño
            height=48,
            mask='auto'
        )
    except Exception as e:
        current_app.logger.warning(f"No se pudo cargar el logo: {e}")


    c.setFont("Helvetica-Bold", 14)
    c.drawString(30 * mm, y, "PRESUPUESTO")
    y -= 10 * mm

    c.setFont("Helvetica", 9)
    c.drawString(30 * mm, y, f"Fecha: {now.strftime('%d/%m/%Y %H:%M')}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(30 * mm, y, "MetalWolft")
    y -= 5 * mm

    c.setFont("Helvetica", 9)
    c.drawString(30 * mm, y, "Fabricación a medida")
    y -= 4 * mm
    c.drawString(30 * mm, y, "Ciudad Real, España")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(30 * mm, y, "Producto")
    c.drawString(95 * mm, y, "Medidas")
    c.drawString(125 * mm, y, "Cant.")
    c.drawString(145 * mm, y, "Total")
    y -= 4 * mm
    c.line(30 * mm, y, 180 * mm, y)
    y -= 6 * mm
    c.setFont("Helvetica", 9)

    for item in cart:
        c.drawString(30 * mm, y, item.get("nombre", "")[:40])
        c.drawString(95 * mm, y, f'{item.get("alto")} x {item.get("ancho")} cm')
        c.drawRightString(130 * mm, y, str(item.get("quantity", 1)))
        c.drawRightString(180 * mm, y, f'{float(item.get("total", 0)):.2f} €')
        y -= 6 * mm

        if y < 30 * mm:
            c.showPage()
            y = height - 30 * mm
            c.setFont("Helvetica", 9)

    y -= 10 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(160 * mm, y, "Subtotal:")
    c.drawRightString(180 * mm, y, f"{subtotal:.2f} €")
    y -= 5 * mm

    c.setFont("Helvetica", 9)
    c.drawRightString(160 * mm, y, "Envío:")
    c.drawRightString(180 * mm, y, f"{shipping:.2f} €")
    y -= 5 * mm

    if discount_percent > 0:
        c.drawRightString(160 * mm, y, f"Descuento ({discount_percent}%):")
        c.drawRightString(180 * mm, y, f"-{discount_amount:.2f} €")
        y -= 5 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(160 * mm, y, "TOTAL:")
    c.drawRightString(180 * mm, y, f"{total:.2f} €")
    y -= 10 * mm

    c.setFont("Helvetica", 8)
    c.drawString(30 * mm, y, "Precio válido únicamente en la fecha de emisión.")
    y -= 4 * mm
    c.drawString(30 * mm, y, "Documento informativo sin compromiso de compra.")

    c.showPage()
    c.save()

    return send_file(file_path, as_attachment=True)

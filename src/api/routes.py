from flask import request, jsonify, Blueprint, send_file, send_from_directory, current_app, redirect, abort, Response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from api.models import db, Users, Products, ProductImages, Categories, Subcategories, Orders, CheckoutSessions, OrderDetails, Favorites, Cart, Posts, Comments, Invoices, DeliveryEstimateConfig
from api.utils import send_email, calcular_precio_reja
from sqlalchemy.exc import SQLAlchemyError
import bcrypt
from datetime import datetime, timezone, date
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph, Frame
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import func
from flask_mail import Message
from dotenv import load_dotenv
from api.exceptions import APIException
from api.utils import mail
from sqlalchemy.exc import IntegrityError
import logging
from html import escape
from datetime import timedelta
import requests
import uuid
from urllib.parse import urljoin
from api.email_routes import send_email, get_admin_recipients
from api.checkout_service import build_checkout_quote
from api.original_invoice_renderer import render_original_order_invoice_pdf


logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

load_dotenv()


def _split_invoice_client_name(client_name):
    normalized_name = (client_name or "").strip()
    if not normalized_name:
        return "", ""

    parts = normalized_name.split()
    if len(parts) == 1:
        return parts[0], ""

    return parts[0], " ".join(parts[1:])


def _display_invoice_product_name(detail):
    if not isinstance(detail, dict):
        return "Desconocido"

    for key in ("product_name", "producto_nombre", "product", "name", "nombre"):
        value = detail.get(key)
        if value:
            return str(value)

    product_id = detail.get("product_id") or detail.get("producto_id")
    if product_id:
        product = Products.query.get(product_id)
        if product and product.nombre:
            return product.nombre

    return "Desconocido"


def _build_original_invoice_order_details(invoice):
    raw_details = invoice.order_details if isinstance(invoice.order_details, list) else []
    prepared_details = []

    for detail in raw_details:
        if not isinstance(detail, dict):
            continue

        normalized = dict(detail)
        normalized["product_name"] = _display_invoice_product_name(detail)
        prepared_details.append(normalized)

    return prepared_details


def _resolve_invoice_discount_percent(invoice):
    checkout_session = getattr(invoice.order, "checkout_session", None) if invoice.order else None
    quote_snapshot = getattr(checkout_session, "quote_snapshot", None) or {}

    try:
        return float(quote_snapshot.get("discount_percent") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _build_original_invoice_render_kwargs(invoice):
    prepared_order_details = _build_original_invoice_order_details(invoice)
    first_detail = prepared_order_details[0] if prepared_order_details else {}
    firstname, lastname = _split_invoice_client_name(invoice.client_name)

    shipping_cost = 0.0
    if invoice.order and invoice.order.shipping_cost is not None:
        shipping_cost = float(invoice.order.shipping_cost or 0.0)
    elif prepared_order_details:
        shipping_cost = float(first_detail.get("shipping_cost") or 0.0)

    return {
        "invoice_number": invoice.invoice_number,
        "customer_firstname": firstname,
        "customer_lastname": lastname,
        "customer_phone": invoice.client_phone or "",
        "customer_billing_address": invoice.client_address or first_detail.get("billing_address") or "",
        "customer_billing_city": first_detail.get("billing_city") or "",
        "customer_billing_postal_code": first_detail.get("billing_postal_code") or "",
        "customer_cif": invoice.client_cif or "",
        "customer_shipping_address": first_detail.get("shipping_address") or "",
        "customer_shipping_city": first_detail.get("shipping_city") or "",
        "customer_shipping_postal_code": first_detail.get("shipping_postal_code") or "",
        "order_details": prepared_order_details,
        "total_amount": float(invoice.amount or 0.0),
        "shipping_cost": shipping_cost,
        "discount_value": float(invoice.order.discount_value or 0.0) if invoice.order else 0.0,
        "discount_code": invoice.order.discount_code if invoice.order else None,
        "discount_percent": _resolve_invoice_discount_percent(invoice),
        "issue_date": invoice.created_at,
    }


def _regenerate_invoice_pdf_to_storage(invoice):
    pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
    file_path = os.path.join(current_app.config['INVOICE_FOLDER'], pdf_filename)
    pdf_path = f"/api/download-invoice/{pdf_filename}"

    os.makedirs(current_app.config['INVOICE_FOLDER'], exist_ok=True)

    regenerated_pdf = render_original_order_invoice_pdf(
        **_build_original_invoice_render_kwargs(invoice)
    )

    with open(file_path, "wb") as pdf_file:
        pdf_file.write(regenerated_pdf)

    if invoice.pdf_path != pdf_path:
        invoice.pdf_path = pdf_path
        db.session.commit()

    return {
        "pdf_filename": pdf_filename,
        "pdf_path": pdf_path,
        "file_path": file_path,
    }


def _format_cart_dimension(value):
    if value is None:
        return "?"

    try:
        numeric_value = float(value)
        if numeric_value.is_integer():
            return str(int(numeric_value))
        return f"{numeric_value:.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def _format_cart_color_label(color_value):
    if not color_value:
        return "Sin definir"

    normalized = str(color_value).replace("_", " ").strip()
    if not normalized:
        return "Sin definir"

    return normalized[:1].upper() + normalized[1:]


def _format_cart_mounting_label(mounting_value):
    return str(mounting_value).strip() if mounting_value else "Sin especificar"


def _resolve_cart_product_image_url(cart_item, frontend_base_url):
    product = getattr(cart_item, "product", None)
    if not product:
        return None

    image_candidate = (product.imagen or "").strip() if getattr(product, "imagen", None) else ""
    if not image_candidate:
        for image in getattr(product, "images", None) or []:
            candidate = (getattr(image, "image_url", None) or "").strip()
            if candidate:
                image_candidate = candidate
                break

    if not image_candidate:
        return None

    return urljoin(f"{frontend_base_url.rstrip('/')}/", image_candidate)


def _build_cart_reminder_product_sections(cart_items, frontend_base_url):
    product_lines_text = []
    product_lines_html = []

    for item in cart_items:
        product_name = item.product.nombre if item.product and item.product.nombre else f"Producto #{item.producto_id}"
        measures = f"{_format_cart_dimension(item.alto)} x {_format_cart_dimension(item.ancho)} cm"
        mounting = _format_cart_mounting_label(item.anclaje)
        color = _format_cart_color_label(item.color)
        quantity = int(item.quantity or 1)
        line_total = float(item.precio_total or 0.0) * quantity
        product_image_url = _resolve_cart_product_image_url(item, frontend_base_url)
        safe_product_name = escape(product_name)
        safe_measures = escape(measures)
        safe_mounting = escape(mounting)
        safe_color = escape(color)

        product_lines_text.append(
            f"- {product_name} | Medidas: {measures} | Anclaje: {mounting} | "
            f"Color: {color} | Cantidad: {quantity} | Precio: {line_total:.2f} €"
        )

        image_cell_html = ""
        if product_image_url:
            image_cell_html = (
                f'<td style="vertical-align:top; padding-right:10px; width:120px;">'
                f'<img src="{escape(product_image_url)}" alt="{safe_product_name}" width="120" '
                'style="display:block; width:100%; max-width:120px; height:auto; '
                'border-radius:12px;"></td>'
            )

        product_lines_html.append(
            f"""
            <tr>
                <td style="padding:12px 0; border-bottom: 1px solid #eceff3;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                        <tr>
                            {image_cell_html}
                            <td style="vertical-align:top; font-family:Arial,Helvetica,sans-serif; font-size:14px; line-height:1.5; color:#374151;">
                                <div style="font-size:17px; font-weight:700; line-height:1.4; margin-bottom:8px;">{safe_product_name}</div>
                                <div style="font-size:14px; line-height:1.5; color:#374151;">
                                    <div><strong>Medidas:</strong> {safe_measures}</div>
                                    <div><strong>Anclaje:</strong> {safe_mounting}</div>
                                    <div><strong>Color:</strong> {safe_color}</div>
                                    <div><strong>Cantidad:</strong> {quantity}</div>
                                    <div><strong>Precio:</strong> {line_total:.2f} €</div>
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            """
        )

    return product_lines_text, product_lines_html


def _build_cart_reminder_email_payload(user, cart_items, cart_url):
    customer_name = (user.firstname or "").strip() or "cliente"
    subject = "¿Quieres terminar tu pedido en Metal Wolft?"
    frontend_base_url = cart_url.rsplit("/cart", 1)[0] if "/cart" in cart_url else cart_url.rstrip("/")
    product_lines_text = []
    product_lines_html = []

    for item in cart_items:
        product_name = item.product.nombre if item.product and item.product.nombre else f"Producto #{item.producto_id}"
        measures = f"{_format_cart_dimension(item.alto)} x {_format_cart_dimension(item.ancho)} cm"
        mounting = _format_cart_mounting_label(item.anclaje)
        color = _format_cart_color_label(item.color)
        quantity = int(item.quantity or 1)
        line_total = float(item.precio_total or 0.0) * quantity
        product_image_url = _resolve_cart_product_image_url(item, frontend_base_url)
        safe_product_name = escape(product_name)
        safe_measures = escape(measures)
        safe_mounting = escape(mounting)
        safe_color = escape(color)

        product_lines_text.append(
            f"- {product_name} | Medidas: {measures} | Anclaje: {mounting} | "
            f"Color: {color} | Cantidad: {quantity} | Precio: {line_total:.2f} €"
        )

        product_lines_html.append(
            "<li>"
            f"<strong>{escape(product_name)}</strong><br>"
            f"Medidas: {escape(measures)}<br>"
            f"Anclaje: {escape(mounting)}<br>"
            f"Color: {escape(color)}<br>"
            f"Cantidad: {quantity}<br>"
            f"Precio: {line_total:.2f} €"
            "</li>"
        )

    body = (
        f"Hola {customer_name},\n\n"
        "Hemos visto que dejaste algunos productos configurados en tu carrito.\n\n"
        "Resumen del carrito:\n"
        f"{chr(10).join(product_lines_text)}\n\n"
        f"Puedes volver a tu carrito desde aquí: {cart_url}\n\n"
        "Si tienes dudas con medidas o instalación, puedes responder a este correo.\n\n"
        "Gracias,\n"
        "Metal Wolft"
    )

    html = f"""
    <p>Hola {escape(customer_name)},</p>
    <p>Hemos visto que dejaste algunos productos configurados en tu carrito.</p>
    <p><strong>Resumen del carrito:</strong></p>
    <ul>
        {''.join(product_lines_html)}
    </ul>
    <p>Puedes volver a tu carrito desde aquí:
        <a href="{escape(cart_url)}">{escape(cart_url)}</a>
    </p>
    <p>Si tienes dudas con medidas o instalación, puedes responder a este correo.</p>
    <p>Gracias,<br>Metal Wolft</p>
    """

    subject = "¿Quieres terminar tu pedido en Metal Wolft?"
    product_lines_text, product_lines_html = _build_cart_reminder_product_sections(cart_items, frontend_base_url)
    body = (
        f"Hola {customer_name},\n\n"
        "Hemos visto que dejaste algunos productos configurados en tu carrito.\n\n"
        "Resumen del carrito:\n"
        f"{chr(10).join(product_lines_text)}\n\n"
        f"Puedes volver a tu carrito desde aquí: {cart_url}\n\n"
        "Si tienes dudas con medidas o instalación, puedes responder a este correo.\n\n"
        "Recibes este correo porque tienes una cuenta en Metal Wolft o has configurado productos en nuestro sitio.\n"
        "Puedes solicitar la eliminación de tus datos o dejar de recibir comunicaciones respondiendo a este email.\n\n"
        "Gracias,\n"
        "Metal Wolft"
    )

    html = f"""
    <div style="margin:0; padding:24px 0; background:#f4f6f8;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:680px; background:#ffffff; border-radius:20px; overflow:hidden;">
                        <tr>
                            <td style="padding:36px 32px 18px; font-family:Arial,Helvetica,sans-serif; color:#111827;">
                                <div style="font-size:28px; font-weight:700; line-height:1.2; margin-bottom:14px;">Tu carrito sigue listo</div>
                                <p style="margin:0 0 14px; font-size:16px; line-height:1.7;">Hola {escape(customer_name)},</p>
                                <p style="margin:0; font-size:16px; line-height:1.7; color:#374151;">
                                    Hemos visto que dejaste algunos productos configurados en tu carrito.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:0 32px 10px; font-family:Arial,Helvetica,sans-serif; color:#111827;">
                                <div style="font-size:18px; font-weight:700; margin-bottom:8px;">Resumen del carrito</div>
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                    {''.join(product_lines_html)}
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:18px 32px 0; font-family:Arial,Helvetica,sans-serif;">
                                <a
                                    href="{escape(cart_url)}"
                                    style="display:inline-block; background:#ff324d; color:#ffffff; text-decoration:none; font-size:16px; font-weight:700; padding:14px 24px; border-radius:999px;"
                                >
                                    Volver a mi carrito
                                </a>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:20px 32px 0; font-family:Arial,Helvetica,sans-serif; color:#374151;">
                                <p style="margin:0; font-size:15px; line-height:1.7;">
                                    Si tienes dudas con medidas o instalación, puedes responder a este correo.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:26px 32px 32px; font-family:Arial,Helvetica,sans-serif; color:#6b7280;">
                                <p style="margin:0 0 12px; font-size:14px; line-height:1.7;">
                                    Gracias,<br>Metal Wolft
                                </p>
                                <p style="margin:0; font-size:12px; line-height:1.7; color:#9ca3af;">
                                    Recibes este correo porque tienes una cuenta en Metal Wolft o has configurado productos en nuestro sitio.
                                    Puedes solicitar la eliminación de tus datos o dejar de recibir comunicaciones respondiendo a este email.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </div>
    """

    return {
        "subject": subject,
        "body": body,
        "html": html
    }


def _serialize_user_for_admin(user):
    serialized_user = user.serialize()
    active_cart_count = len(user.cart_items or [])
    serialized_user["has_active_cart"] = active_cart_count > 0
    serialized_user["cart_item_count"] = active_cart_count
    return serialized_user



redirect_map = {
    "/rejas/rejas-para-ventanas-pittsburgh": "/rejas-para-ventanas",
    "/rejas/rejas-para-ventanas-livingston": "/rejas-para-ventanas",
    "/rejas/rejas-para-ventanas-delhi": "/rejas-para-ventanas",
    "/rejas/rejas-para-ventanas-lancaster": "/rejas-para-ventanas",
    "/puertas-correderas/puerta-corredera-perth": "/puertas-correderas-metalicas",
    "/puertas-correderas/puerta-corredera-adelaida": "/puertas-correderas-metalicas",
    "/puertas-correderas/puerta-corredera-canberra": "/puertas-correderas-metalicas",
    "/puertas-correderas-interiores": "/puertas-correderas-metalicas",
    "/puertas-correderas-exteriores": "/puertas-correderas-metalicas",
    "/puertas-peatonales": "/puertas-peatonales-metalicas",
    "/vallados-metalicos-exteriores": "/vallados-metalicos",
    "/vallados-metalicos/vallado-metalico-geelong": "/vallados-metalicos",
    "/vallados-metalicos": "/vallados-metalicos",
    "/preguntas-frecuentes": "/faq",
}

gone_list = [
    "/blog/instalation-rejas-para-ventanas",
    "/index.php",
    "/blog/medir_hueco_rejas_para_ventanas.php",
    "/blog/medir-hueco-rejas-para-ventanas.php",
    "/blog/instalation-rejas-para-ventanas.php",
    "/rejas-para-ventanas.php",
    "/blog/blog-metal-wolft.php",
    "/",
    "/vallados-metalicos",
    "/puertas-correderas/puerta-corredera-adelaida",
    "/puertas-correderas/puerta-corredera-canberra",
    "/rejas/rejas-para-ventanas-delhi",
    "/rejas/rejas-para-ventanas-lancaster",
    "/puertas-peatonales",
    "/preguntas-frecuentes",
    "/vallados-metalicos/vallado-metalico-geelong",
]


@api.before_request
def handle_legacy_urls():
    if request.path in redirect_map:
        return redirect(redirect_map[request.path], code=301)
    if request.path in gone_list:
        return "Página obsoleta", 410


def _get_checkout_raw_products(current_user, data):
    raw_products = data.get('products')
    if raw_products is None:
        cart_items = Cart.query.filter_by(usuario_id=current_user['user_id']).all()
        raw_products = [item.serialize() for item in cart_items]
    return raw_products


def _build_checkout_quote_from_request(current_user, data):
    raw_products = _get_checkout_raw_products(current_user, data)
    return build_checkout_quote(
        raw_products=raw_products,
        discount_code=data.get('discount_code'),
        requested_discount_percent=data.get('discount_percent'),
        frontend_total=data.get('total_amount'),
        frontend_shipping_cost=data.get('shipping_cost')
    )


def _to_optional_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_discount_code(value):
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    return normalized or None


def _checkout_line_key(item):
    product_id = item.get("producto_id")
    if product_id is None:
        product_id = item.get("product_id")

    return (
        product_id,
        _to_optional_float(item.get("alto")),
        _to_optional_float(item.get("ancho")),
        item.get("anclaje"),
        item.get("color")
    )


def _build_checkout_comparison_from_request(checkout_quote, data):
    frontend_total = _to_optional_float(data.get('total_amount'))
    backend_total = _to_optional_float(checkout_quote.get('total_amount'))
    frontend_shipping = _to_optional_float(data.get('shipping_cost'))
    backend_shipping = _to_optional_float(checkout_quote.get('shipping_cost'))
    frontend_discount_percent = _to_optional_float(data.get('discount_percent')) or 0.0
    backend_discount_percent = _to_optional_float(checkout_quote.get('discount_percent')) or 0.0
    frontend_discount_code = _normalize_discount_code(data.get('discount_code'))
    backend_discount_code = checkout_quote.get('discount_code')

    total_difference = None
    shipping_difference = None

    if frontend_total is not None and backend_total is not None:
        total_difference = round(frontend_total - backend_total, 2)

    if frontend_shipping is not None and backend_shipping is not None:
        shipping_difference = round(frontend_shipping - backend_shipping, 2)

    line_differences = []
    snapshot_lines = checkout_quote.get("lines") or []
    frontend_lines = data.get("products") or []
    snapshot_lines_by_key = {
        _checkout_line_key(line): line for line in snapshot_lines
    }

    for frontend_line in frontend_lines:
        snapshot_line = snapshot_lines_by_key.get(_checkout_line_key(frontend_line))
        if not snapshot_line:
            continue

        frontend_unit_price = _to_optional_float(frontend_line.get("precio_total"))
        backend_unit_price = _to_optional_float(snapshot_line.get("unit_price"))
        if (
            frontend_unit_price is not None and
            backend_unit_price is not None and
            abs(frontend_unit_price - backend_unit_price) >= 0.01
        ):
            line_differences.append({
                "product_id": snapshot_line.get("product_id"),
                "frontend_unit_price": frontend_unit_price,
                "backend_unit_price": backend_unit_price,
                "difference": round(frontend_unit_price - backend_unit_price, 2)
            })

    comparison = {
        "frontend_total": frontend_total,
        "backend_total": backend_total,
        "total_difference": total_difference,
        "frontend_shipping_cost": frontend_shipping,
        "backend_shipping_cost": backend_shipping,
        "shipping_difference": shipping_difference,
        "frontend_discount_code": frontend_discount_code,
        "backend_discount_code": backend_discount_code,
        "frontend_discount_percent": frontend_discount_percent,
        "backend_discount_percent": backend_discount_percent,
        "line_differences": line_differences,
    }
    comparison["has_difference"] = any([
        total_difference is not None and abs(total_difference) >= 0.01,
        shipping_difference is not None and abs(shipping_difference) >= 0.01,
        abs(frontend_discount_percent - backend_discount_percent) >= 0.01,
        frontend_discount_code != backend_discount_code,
        bool(line_differences),
    ])
    return comparison


def _build_order_details_from_checkout_quote(checkout_quote):
    return [
        {
            "producto_id": line["product_id"],
            "quantity": line["quantity"],
            "alto": line["alto"],
            "ancho": line["ancho"],
            "anclaje": line.get("anclaje"),
            "color": line.get("color"),
            "precio_total": line["unit_price"],
            "shipping_type": line.get("shipping_type"),
            "shipping_cost": line.get("shipping_cost")
        }
        for line in (checkout_quote.get("lines") or [])
    ]


def _extract_customer_snapshot(data):
    source = data.get("customer_data")
    if not isinstance(source, dict):
        source = data

    fields = [
        "firstname",
        "lastname",
        "phone",
        "shipping_address",
        "shipping_city",
        "shipping_postal_code",
        "billing_address",
        "billing_city",
        "billing_postal_code",
        "CIF"
    ]
    snapshot = {}
    for field in fields:
        value = source.get(field) if isinstance(source, dict) else None
        if value is not None and value != "":
            snapshot[field] = value
    return snapshot


def _merge_customer_snapshot(existing_snapshot, new_snapshot):
    merged_snapshot = dict(existing_snapshot or {})
    for field, value in (new_snapshot or {}).items():
        if value is not None and value != "":
            merged_snapshot[field] = value
    return merged_snapshot


def _get_customer_value(request_data, customer_snapshot, field_name):
    request_value = request_data.get(field_name)
    if request_value is not None and request_value != "":
        return request_value
    return (customer_snapshot or {}).get(field_name)


def _normalize_checkout_session_status(provider_status, payment_provider="stripe"):
    if payment_provider == "stripe":
        if provider_status == "succeeded":
            return "paid"
        if provider_status in ("processing", "requires_capture"):
            return "processing"
        if provider_status == "requires_payment_method":
            return "payment_failed"
        if provider_status == "canceled":
            return "canceled"
        return "pending_payment"

    normalized_status = str(provider_status or "").upper()
    if normalized_status in ("COMPLETED", "SUCCEEDED", "PAID"):
        return "paid"
    if normalized_status in ("PENDING", "PROCESSING", "APPROVED"):
        return "processing"
    if normalized_status in ("FAILED", "DECLINED", "DENIED"):
        return "payment_failed"
    if normalized_status in ("VOIDED", "CANCELED", "CANCELLED"):
        return "canceled"
    return "pending_payment"


def _generate_public_checkout_token():
    for _ in range(5):
        token = CheckoutSessions.generate_public_checkout_token()
        if not CheckoutSessions.query.filter_by(public_checkout_token=token).first():
            return token
    raise ValueError("Unable to generate a unique public checkout token.")


def _upsert_checkout_session(current_user, intent, existing_intent_id, idempotency_key, checkout_quote, customer_snapshot, payment_provider="stripe"):
    checkout_session = None

    if existing_intent_id and payment_provider == "stripe":
        checkout_session = CheckoutSessions.query.filter_by(
            payment_intent_id=existing_intent_id,
            user_id=current_user['user_id']
        ).first()

    if not checkout_session and payment_provider == "stripe":
        checkout_session = CheckoutSessions.query.filter_by(
            payment_intent_id=intent["id"],
            user_id=current_user['user_id']
        ).first()

    if not checkout_session:
        checkout_session = CheckoutSessions(
            user_id=current_user['user_id'],
            payment_intent_id=intent["id"] if payment_provider == "stripe" else None,
            public_checkout_token=_generate_public_checkout_token()
        )
        db.session.add(checkout_session)

    if checkout_session.status == "order_created" and checkout_session.order_id:
        return checkout_session

    if payment_provider == "stripe":
        checkout_session.payment_intent_id = intent["id"]
    if not checkout_session.public_checkout_token:
        checkout_session.public_checkout_token = _generate_public_checkout_token()
    checkout_session.payment_provider = payment_provider
    checkout_session.provider_status = intent.get("status")
    checkout_session.idempotency_key = idempotency_key
    checkout_session.status = _normalize_checkout_session_status(
        intent.get("status"),
        payment_provider=payment_provider
    )
    checkout_session.subtotal = float(checkout_quote["subtotal"])
    checkout_session.shipping_cost = float(checkout_quote["shipping_cost"])
    checkout_session.discount_code = checkout_quote.get("discount_code")
    checkout_session.discount_percent = float(checkout_quote.get("discount_percent") or 0.0)
    checkout_session.discount_amount = float(checkout_quote.get("discount_amount") or 0.0)
    checkout_session.total_amount = float(checkout_quote["total_amount"])
    checkout_session.quote_snapshot = checkout_quote
    if customer_snapshot:
        checkout_session.customer_snapshot = customer_snapshot

    return checkout_session


def _get_checkout_session_by_payment_intent(payment_intent_id, user_id=None, for_update=False):
    if not payment_intent_id:
        return None

    query = CheckoutSessions.query.filter_by(payment_intent_id=payment_intent_id)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if for_update:
        query = query.with_for_update()
    return query.first()


def _get_checkout_session_by_public_token(public_checkout_token, user_id=None, for_update=False):
    if not public_checkout_token:
        return None

    query = CheckoutSessions.query.filter_by(public_checkout_token=public_checkout_token)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if for_update:
        query = query.with_for_update()
    return query.first()


def _get_checkout_session_by_provider_order_id(provider_order_id, user_id=None, for_update=False):
    if not provider_order_id:
        return None

    query = CheckoutSessions.query.filter_by(provider_order_id=provider_order_id)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if for_update:
        query = query.with_for_update()
    return query.first()


def _get_checkout_session_by_provider_capture_id(provider_capture_id, user_id=None, for_update=False):
    if not provider_capture_id:
        return None

    query = CheckoutSessions.query.filter_by(provider_capture_id=provider_capture_id)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if for_update:
        query = query.with_for_update()
    return query.first()


def _get_paypal_api_base_url():
    explicit_base_url = (os.getenv("PAYPAL_API_BASE_URL") or "").strip().rstrip("/")
    if explicit_base_url:
        return explicit_base_url

    paypal_env = (os.getenv("PAYPAL_ENV") or os.getenv("PAYPAL_MODE") or "sandbox").strip().lower()
    if paypal_env in ("live", "production", "prod"):
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def _get_paypal_access_token():
    paypal_client_id = os.getenv("PAYPAL_CLIENT_ID")
    paypal_client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

    if not paypal_client_id or not paypal_client_secret:
        raise ValueError("PayPal credentials are not configured.")

    response = requests.post(
        f"{_get_paypal_api_base_url()}/v1/oauth2/token",
        data={"grant_type": "client_credentials"},
        auth=(paypal_client_id, paypal_client_secret),
        headers={
            "Accept": "application/json",
            "Accept-Language": "en_US",
        },
        timeout=20
    )

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if not response.ok or not payload.get("access_token"):
        logger.error(
            "Error obteniendo access token de PayPal: status=%s payload=%s",
            response.status_code,
            payload
        )
        raise RuntimeError("Unable to authenticate with PayPal.")

    return payload["access_token"]


def _paypal_request(method, path, payload=None, request_id=None):
    access_token = _get_paypal_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if request_id:
        headers["PayPal-Request-Id"] = request_id

    response = requests.request(
        method,
        f"{_get_paypal_api_base_url()}{path}",
        headers=headers,
        json=payload,
        timeout=30
    )

    try:
        response_payload = response.json() if response.content else {}
    except ValueError:
        response_payload = {}

    if response.status_code >= 400:
        logger.error(
            "Error en PayPal API %s %s: status=%s payload=%s",
            method,
            path,
            response.status_code,
            response_payload
        )
        raise RuntimeError(response_payload.get("message") or "PayPal API request failed.")

    return response_payload


def _verify_paypal_webhook_signature(webhook_event):
    webhook_id = os.getenv("PAYPAL_WEBHOOK_ID")
    if not webhook_id:
        raise ValueError("PAYPAL_WEBHOOK_ID is not configured.")

    verification_payload = {
        "transmission_id": request.headers.get("PAYPAL-TRANSMISSION-ID"),
        "transmission_time": request.headers.get("PAYPAL-TRANSMISSION-TIME"),
        "cert_url": request.headers.get("PAYPAL-CERT-URL"),
        "auth_algo": request.headers.get("PAYPAL-AUTH-ALGO"),
        "transmission_sig": request.headers.get("PAYPAL-TRANSMISSION-SIG"),
        "webhook_id": webhook_id,
        "webhook_event": webhook_event,
    }

    missing_fields = [key for key, value in verification_payload.items() if not value]
    if missing_fields:
        raise ValueError(f"Missing PayPal webhook verification data: {', '.join(missing_fields)}")

    verification_response = _paypal_request(
        "POST",
        "/v1/notifications/verify-webhook-signature",
        payload=verification_payload
    )
    return verification_response.get("verification_status") == "SUCCESS"


def _build_paypal_order_request(checkout_session):
    total_amount = round(float(checkout_session.total_amount or 0.0), 2)
    return {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": str(checkout_session.id),
                "custom_id": checkout_session.public_checkout_token,
                "description": f"MetalWolft checkout {checkout_session.public_checkout_token}",
                "amount": {
                    "currency_code": "EUR",
                    "value": f"{total_amount:.2f}"
                }
            }
        ]
    }


def _get_paypal_approve_url(paypal_response):
    for link in paypal_response.get("links") or []:
        if link.get("rel") in ("approve", "payer-action"):
            return link.get("href")
    return None


def _extract_paypal_capture(paypal_response):
    for purchase_unit in paypal_response.get("purchase_units") or []:
        payments = purchase_unit.get("payments") or {}
        captures = payments.get("captures") or []
        if captures:
            return captures[0]
    return None


def _extract_paypal_resource_details(resource):
    resource = resource or {}
    supplementary_data = resource.get("supplementary_data") or {}
    related_ids = supplementary_data.get("related_ids") or {}
    amount = resource.get("amount") or {}

    return {
        "provider_order_id": related_ids.get("order_id") or resource.get("order_id"),
        "provider_capture_id": resource.get("id"),
        "provider_status": resource.get("status"),
        "amount_value": _to_optional_float(amount.get("value")),
        "currency_code": (amount.get("currency_code") or "").upper() or None,
    }


def _paypal_resource_matches_checkout_session(checkout_session, resource_details):
    incoming_order_id = resource_details.get("provider_order_id")
    incoming_capture_id = resource_details.get("provider_capture_id")

    if (
        incoming_order_id and
        checkout_session.provider_order_id and
        checkout_session.provider_order_id != incoming_order_id
    ):
        return False, (
            f"PayPal order mismatch: incoming={incoming_order_id} "
            f"session={checkout_session.provider_order_id}"
        )

    if (
        incoming_capture_id and
        checkout_session.provider_capture_id and
        checkout_session.provider_capture_id != incoming_capture_id
    ):
        return False, (
            f"PayPal capture mismatch: incoming={incoming_capture_id} "
            f"session={checkout_session.provider_capture_id}"
        )

    return True, None


def _get_paypal_checkout_session_from_resource(resource, for_update=False):
    resource_details = _extract_paypal_resource_details(resource)
    checkout_session = None

    if resource_details["provider_order_id"]:
        checkout_session = _get_checkout_session_by_provider_order_id(
            resource_details["provider_order_id"],
            for_update=for_update
        )

    if not checkout_session and resource_details["provider_capture_id"]:
        checkout_session = _get_checkout_session_by_provider_capture_id(
            resource_details["provider_capture_id"],
            for_update=for_update
        )

    return checkout_session, resource_details


def _paypal_capture_matches_checkout_session(checkout_session, resource_details):
    capture_amount = resource_details.get("amount_value")
    if capture_amount is not None:
        backend_total = round(float(checkout_session.total_amount or 0.0), 2)
        if abs(capture_amount - backend_total) >= 0.01:
            return False, (
                f"PayPal capture amount mismatch: capture={capture_amount:.2f} "
                f"backend={backend_total:.2f}"
            )

    currency_code = resource_details.get("currency_code")
    if currency_code and currency_code != "EUR":
        return False, f"Unexpected PayPal currency: {currency_code}"

    return True, None


def _upsert_paypal_checkout_session(current_user, checkout_quote, customer_snapshot, checkout_token=None, for_update=False):
    checkout_session = None
    if checkout_token:
        checkout_session = _get_checkout_session_by_public_token(
            checkout_token,
            user_id=current_user['user_id'],
            for_update=for_update
        )
        if not checkout_session:
            raise ValueError("Checkout session not found.")

        if checkout_session.order_id:
            raise ValueError("Checkout session already finalized.")

        if checkout_session.payment_provider not in ("paypal", None, ""):
            raise ValueError("Checkout session belongs to a different payment provider.")
    else:
        checkout_session = CheckoutSessions(
            user_id=current_user['user_id'],
            payment_provider="paypal",
            public_checkout_token=_generate_public_checkout_token()
        )
        db.session.add(checkout_session)

    if checkout_session.status == "order_created" and checkout_session.order_id:
        raise ValueError("Checkout session already finalized.")

    checkout_session.payment_provider = "paypal"
    checkout_session.payment_intent_id = None
    if not checkout_session.public_checkout_token:
        checkout_session.public_checkout_token = _generate_public_checkout_token()
    if not checkout_session.idempotency_key:
        checkout_session.idempotency_key = str(uuid.uuid4())

    checkout_session.subtotal = float(checkout_quote["subtotal"])
    checkout_session.shipping_cost = float(checkout_quote["shipping_cost"])
    checkout_session.discount_code = checkout_quote.get("discount_code")
    checkout_session.discount_percent = float(checkout_quote.get("discount_percent") or 0.0)
    checkout_session.discount_amount = float(checkout_quote.get("discount_amount") or 0.0)
    checkout_session.total_amount = float(checkout_quote["total_amount"])
    checkout_session.quote_snapshot = checkout_quote
    if customer_snapshot:
        checkout_session.customer_snapshot = customer_snapshot

    return checkout_session


def _serialize_checkout_session_payment_state(checkout_session):
    return {
        "checkout_session_id": checkout_session.id,
        "checkout_session_status": checkout_session.status,
        "payment_provider": checkout_session.payment_provider,
        "payment_intent_id": checkout_session.payment_intent_id,
        "provider_order_id": checkout_session.provider_order_id,
        "provider_capture_id": checkout_session.provider_capture_id,
        "provider_status": checkout_session.provider_status,
        "public_checkout_token": checkout_session.public_checkout_token,
        "checkout_summary": checkout_session.quote_snapshot,
    }


def _build_customer_context(request_data, customer_snapshot):
    return {
        "firstname": _get_customer_value(request_data, customer_snapshot, 'firstname'),
        "lastname": _get_customer_value(request_data, customer_snapshot, 'lastname'),
        "phone": _get_customer_value(request_data, customer_snapshot, 'phone'),
        "shipping_address": _get_customer_value(request_data, customer_snapshot, 'shipping_address'),
        "shipping_city": _get_customer_value(request_data, customer_snapshot, 'shipping_city'),
        "shipping_postal_code": _get_customer_value(request_data, customer_snapshot, 'shipping_postal_code'),
        "billing_address": _get_customer_value(request_data, customer_snapshot, 'billing_address'),
        "billing_city": _get_customer_value(request_data, customer_snapshot, 'billing_city'),
        "billing_postal_code": _get_customer_value(request_data, customer_snapshot, 'billing_postal_code'),
        "CIF": _get_customer_value(request_data, customer_snapshot, 'CIF'),
    }


def _sync_user_from_customer_context(user, customer_context):
    if not user:
        return False

    updated = False
    field_mapping = [
        ("firstname", "firstname"),
        ("lastname", "lastname"),
        ("shipping_address", "shipping_address"),
        ("shipping_city", "shipping_city"),
        ("shipping_postal_code", "shipping_postal_code"),
        ("billing_address", "billing_address"),
        ("billing_city", "billing_city"),
        ("billing_postal_code", "billing_postal_code"),
        ("CIF", "CIF"),
    ]

    for user_field, context_field in field_mapping:
        context_value = customer_context.get(context_field)
        if not getattr(user, user_field) and context_value:
            setattr(user, user_field, context_value)
            updated = True

    return updated


def _finalize_order_from_checkout_quote(user, checkout_quote, customer_snapshot, checkout_session=None):
    if checkout_session and checkout_session.order_id:
        existing_order = Orders.query.filter_by(
            id=checkout_session.order_id,
            user_id=user.id
        ).first()
        if existing_order:
            checkout_session.status = "order_created"
            return existing_order, False

        logger.warning(
            "Checkout session %s apunta a una order inexistente (%s). Se reintentará el cierre.",
            checkout_session.id,
            checkout_session.order_id
        )
        checkout_session.order_id = None

    if not checkout_quote or not checkout_quote.get("lines"):
        raise ValueError("Checkout snapshot not available for this payment intent.")

    order_details = _build_order_details_from_checkout_quote(checkout_quote)
    customer_snapshot = customer_snapshot or {}
    customer_context = _build_customer_context({}, customer_snapshot)

    customer_firstname = customer_context["firstname"]
    customer_lastname = customer_context["lastname"]
    customer_phone = customer_context["phone"]
    customer_shipping_address = customer_context["shipping_address"]
    customer_shipping_city = customer_context["shipping_city"]
    customer_shipping_postal_code = customer_context["shipping_postal_code"]
    customer_billing_address = customer_context["billing_address"]
    customer_billing_city = customer_context["billing_city"]
    customer_billing_postal_code = customer_context["billing_postal_code"]
    customer_cif = customer_context["CIF"]

    new_order = Orders(
        user_id=user.id,
        total_amount=0,
        locator=Orders.generate_locator(),
        order_status="pendiente"
    )
    db.session.add(new_order)
    db.session.flush()

    subtotal = 0.0
    discount_percent = float(checkout_quote.get('discount_percent') or 0)
    discount_code = checkout_quote.get('discount_code') or None

    for detail in order_details:
        precio_recalculado = float(detail.get('precio_total') or 0.0)
        existing_detail = OrderDetails.query.filter_by(
            order_id=new_order.id,
            product_id=detail['producto_id'],
            alto=detail.get('alto'),
            ancho=detail.get('ancho'),
            anclaje=detail.get('anclaje'),
            color=detail.get('color')
        ).first()

        if existing_detail:
            logger.info(f"Detalle ya existente: {existing_detail.serialize()}")
            existing_detail.quantity += detail['quantity']
            existing_detail.precio_total = precio_recalculado
            subtotal += precio_recalculado * detail['quantity']
            continue

        new_detail = OrderDetails(
            order_id=new_order.id,
            product_id=detail['producto_id'],
            quantity=detail['quantity'],
            alto=detail.get('alto'),
            ancho=detail.get('ancho'),
            anclaje=detail.get('anclaje'),
            color=detail.get('color'),
            precio_total=precio_recalculado,
            firstname=customer_firstname,
            lastname=customer_lastname,
            shipping_address=customer_shipping_address,
            shipping_city=customer_shipping_city,
            shipping_postal_code=customer_shipping_postal_code,
            billing_address=customer_billing_address,
            billing_city=customer_billing_city,
            billing_postal_code=customer_billing_postal_code,
            CIF=customer_cif,
            shipping_type=detail.get('shipping_type'),
            shipping_cost=detail.get('shipping_cost')
        )

        db.session.add(new_detail)
        subtotal += precio_recalculado * detail.get("quantity", 1)

    shipping_cost = float(checkout_quote["shipping_cost"])
    backend_total = float(checkout_quote["total_amount"])
    gross_sum = subtotal + float(shipping_cost or 0.0)
    discount_value_iva = round(float(checkout_quote["discount_amount"]), 2)

    new_order.discount_code = discount_code
    new_order.discount_value = discount_value_iva
    new_order.shipping_cost = round(float(shipping_cost or 0.0), 2)
    new_order.total_amount = round(backend_total, 2)

    logger.info(
        "Cálculo final autoritativo backend → "
        f"Bruto: {gross_sum:.2f} € | Descuento: {discount_value_iva:.2f} € | "
        f"Envío: {shipping_cost:.2f} € | Total guardado: {backend_total:.2f} €"
    )

    invoice_number = Invoices.generate_next_invoice_number()
    pdf_filename = f"invoice_{invoice_number}.pdf"
    file_path = os.path.join(current_app.config['INVOICE_FOLDER'], pdf_filename)
    pdf_path = f"/api/download-invoice/{pdf_filename}"
    os.makedirs(current_app.config['INVOICE_FOLDER'], exist_ok=True)

    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)

    image_url = "https://res.cloudinary.com/dewanllxn/image/upload/v1740167674/logo_uxlqof.png"
    pdf.drawImage(image_url, 300, 750, width=250, height=64)

    pdf.setTitle(f"Factura_{invoice_number}")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 800, f"Factura No: {invoice_number}")

    pdf.setFont("Helvetica", 10)
    fecha_emision = datetime.now().strftime("%d/%m/%Y")
    pdf.drawString(50, 780, f"Fecha: {fecha_emision}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(400, 700, "PROVEEDOR")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(400, 680, "Sergio Arias Fernández")
    pdf.drawString(400, 665, "05703874N")
    pdf.drawString(400, 650, "Francisco Fernández Ordoñez 32")
    pdf.drawString(400, 635, "13170 Miguelturra")
    pdf.drawString(400, 620, "634112604")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 700, "CLIENTE")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 680, f"{customer_firstname or ''} {customer_lastname or ''}".strip())
    pdf.drawString(50, 665, f"{customer_billing_address or ''}, {customer_billing_city or ''} ({customer_billing_postal_code or ''})")
    pdf.drawString(50, 650, f"{customer_cif or ''}")
    pdf.drawString(50, 635, f"{customer_phone or 'No proporcionado'}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 580, "Dirección de Envío")
    pdf.setFont("Helvetica", 10)

    if not customer_shipping_address or customer_shipping_address == customer_billing_address:
        pdf.drawString(50, 560, "La misma que la de facturación")
    else:
        pdf.drawString(50, 560, f"{customer_shipping_address or ''}, {customer_shipping_city or ''} ({customer_shipping_postal_code or ''})")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 510, "Detalles del Pedido")
    pdf.setFont("Helvetica", 10)

    from collections import defaultdict

    color_labels = {
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
        "blanco": "Blanco",
        "negro": "Negro",
        "gris": "Gris",
        "marrón": "Marrón",
        "verde": "Verde"
    }

    data_table = [["Prod.", "Alto", "Ancho", "Anc.", "Col.", "Ud.", "Importe (€)"]]
    grouped_details = defaultdict(lambda: {"quantity": 0, "precio_unitario": 0.0})

    for detail in order_details:
        key = (
            detail['producto_id'],
            detail.get('alto'),
            detail.get('ancho'),
            detail.get('anclaje'),
            detail.get('color')
        )
        grouped_details[key]["quantity"] += detail.get("quantity", 1)
        grouped_details[key]["precio_unitario"] = float(detail["precio_total"])

    for (producto_id, alto, ancho, anclaje, color), values in grouped_details.items():
        prod = Products.query.get(producto_id)
        cantidad = values["quantity"]
        precio_unitario = values["precio_unitario"]
        importe_total = precio_unitario * cantidad

        row = [
            prod.nombre[:24] if prod else "Desconocido",
            f"{alto} cm",
            f"{ancho} cm",
            (anclaje[:20] if anclaje else ''),
            color_labels.get(color, color)[:18] if color else '',
            str(cantidad),
            f"{importe_total:.2f}"
        ]
        data_table.append(row)

    table = Table(data_table, colWidths=[4*cm, 1.5*cm, 1.5*cm, 4.2*cm, 3.2*cm, 1*cm, 2.3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(1, 0.196, 0.302)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    y_position = 480
    table.wrapOn(pdf, 50, y_position)
    table_height = table._height
    table.drawOn(pdf, 50, y_position - table_height)

    totals_y_position = y_position - table_height - 30
    if totals_y_position < 50:
        pdf.showPage()
        totals_y_position = 750

    total = new_order.total_amount
    base_total = total / 1.21
    iva_calculado = total - base_total
    base_envio = new_order.shipping_cost / 1.21
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

    if new_order.discount_value and new_order.discount_value > 0:
        pdf.setFont("Helvetica-Bold", 11)
        pdf.setFillColor(colors.green)
        pdf.drawString(
            50,
            totals_y_position - 100,
            f"Descuento comercial ({discount_code or ''} {discount_percent:.0f}%): -{new_order.discount_value:.2f} €"
        )
        pdf.setFillColor(colors.black)

    pdf.line(50, totals_y_position - 105, 200, totals_y_position - 105)

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, totals_y_position - 120, f"TOTAL A PAGAR: {total:.2f} €")

    pdf.setFont("Helvetica", 10)
    if new_order.shipping_cost == 49:
        envio_text = "Tarifa A (49 €)"
    elif shipping_cost == 99:
        envio_text = "Tarifa B (99 €)"
    elif shipping_cost == 17:
        envio_text = "Estándar (17 €)"
    else:
        envio_text = "Gratuito"

    pdf.drawString(50, totals_y_position - 140, f"Tipo de envío: {envio_text}")
    if discount_code:
        pdf.drawString(50, totals_y_position - 155, f"Código descuento: {discount_code}")

    pdf.save()
    pdf_buffer.seek(0)
    with open(file_path, "wb") as f:
        f.write(pdf_buffer.getvalue())

    new_invoice = Invoices(
        invoice_number=invoice_number,
        order_id=new_order.id,
        pdf_path=pdf_path,
        client_name=f"{customer_firstname or ''} {customer_lastname or ''}".strip(),
        client_address=customer_billing_address or "",
        client_cif=customer_cif or "",
        client_phone=customer_phone or "",
        amount=new_order.total_amount,
        order_details=[detail.serialize() for detail in new_order.order_details]
    )
    db.session.add(new_invoice)
    new_order.invoice_number = invoice_number

    if checkout_session:
        checkout_session.order_id = new_order.id
        checkout_session.status = "order_created"
        if customer_snapshot:
            checkout_session.customer_snapshot = customer_snapshot

    db.session.commit()

    try:
        persisted_user = Users.query.get(user.id)
        if _sync_user_from_customer_context(persisted_user, customer_context):
            db.session.commit()
            logger.info("Datos del usuario %s actualizados desde la compra", persisted_user.email)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar datos del usuario: {str(e)}")

    try:
        email_sent = send_email(
            subject=f"Factura de tu pedido #{invoice_number}",
            recipients=[user.email, current_app.config['MAIL_USERNAME']],
            body=f"Hola {(customer_firstname or '').strip()} {(customer_lastname or '').strip()},\n\nAdjuntamos la factura {invoice_number} de tu compra.\n\nGracias por tu confianza.",
            attachment_path=file_path
        )
        if not email_sent:
            logger.error(f"Error al enviar el correo con la factura {invoice_number}.")
        else:
            logger.info(f"Correo enviado correctamente con la factura {invoice_number}.")
    except Exception as e:
        logger.error(f"Error al enviar el correo con la factura {invoice_number}: {str(e)}")

    return new_order, True


@api.route('/delivery-estimate', methods=['GET'])
def get_delivery_estimate():
    try:
        config = DeliveryEstimateConfig.query.filter_by(is_active=True).first()
        if not config:
            response = jsonify({"is_active": False})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 404

        response = jsonify(config.to_dict())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except Exception as e:
        response = jsonify({"message": "Error al obtener la estimación", "error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 500


@api.route('/create-payment-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    import stripe, os
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}

        # --- 1) Valores recibidos ---
        payment_method_id = data.get("payment_method_id")
        existing_intent_id = data.get("payment_intent_id")
        idempotency_key = data.get("idempotency_key") or str(uuid.uuid4())
        receipt_email = data.get("email") or current_user.get("email")
        metadata = data.get("metadata") or {}
        frontend_amount = data.get("amount")

        if not payment_method_id:
            return jsonify({"error": "Missing required data"}), 400

        quote_request_data = {
            **data,
            "products": None
        }
        checkout_quote = _build_checkout_quote_from_request(current_user, quote_request_data)
        if not checkout_quote["lines"]:
            return jsonify({"error": "Cart is empty"}), 400

        amount = int(round(checkout_quote["total_amount"] * 100))

        try:
            frontend_amount_cents = int(frontend_amount) if frontend_amount is not None else None
        except (TypeError, ValueError):
            frontend_amount_cents = None

        amount_comparison = {
            "frontend_amount_cents": frontend_amount_cents,
            "backend_amount_cents": amount,
            "has_difference": frontend_amount_cents is not None and frontend_amount_cents != amount
        }

        if amount_comparison["has_difference"]:
            logger.warning(
                "Checkout mismatch detectado en /create-payment-intent → "
                f"frontend_amount_cents={frontend_amount_cents} | "
                f"backend_amount_cents={amount} | "
                f"backend_total={checkout_quote['total_amount']:.2f} | "
                f"backend_shipping={checkout_quote['shipping_cost']:.2f} | "
                f"backend_discount_code={checkout_quote['discount_code']} | "
                f"backend_discount_percent={checkout_quote['discount_percent']}"
            )
        else:
            logger.info(
                "Checkout alineado en /create-payment-intent → "
                f"backend_amount_cents={amount} | "
                f"backend_total={checkout_quote['total_amount']:.2f}"
            )

        metadata = {
            **metadata,
            "user_id": str(current_user["user_id"]),
            "checkout_total": f"{checkout_quote['total_amount']:.2f}",
            "checkout_shipping": f"{checkout_quote['shipping_cost']:.2f}",
            "discount_code": checkout_quote["discount_code"] or "",
            "discount_percent": f"{checkout_quote['discount_percent']:.2f}"
        }
        customer_snapshot = _extract_customer_snapshot(data)

        # --- 2) Si existe PaymentIntent previo, lo modificamos ---
        if existing_intent_id:
            try:
                intent = stripe.PaymentIntent.modify(
                    existing_intent_id,
                    amount=amount,
                    payment_method=payment_method_id,
                    metadata=metadata,
                    receipt_email=receipt_email
                )
            except Exception:
                # Si falla (intent cancelado, expirado o no válido), creamos uno nuevo
                intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency='eur',
                    payment_method=payment_method_id,
                    confirm=False,
                    metadata=metadata,
                    receipt_email=receipt_email,
                    idempotency_key=idempotency_key
                )
        else:
            # --- 3) Crear PaymentIntent por primera vez ---
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='eur',
                payment_method=payment_method_id,
                confirm=False,
                metadata=metadata,
                receipt_email=receipt_email,
                idempotency_key=idempotency_key
            )

        checkout_session = _upsert_checkout_session(
            current_user=current_user,
            intent=intent,
            existing_intent_id=existing_intent_id,
            idempotency_key=idempotency_key,
            checkout_quote=checkout_quote,
            customer_snapshot=customer_snapshot,
            payment_provider="stripe"
        )
        db.session.commit()

        # --- 4) Devolver clientSecret y PaymentIntent completo ---
        return jsonify({
            "clientSecret": intent["client_secret"],
            "paymentIntent": intent,
            "amount_source": "backend_quote",
            "amount_used_cents": amount,
            "checkout_summary": checkout_quote,
            "amount_comparison": amount_comparison,
            "checkout_session_id": checkout_session.id,
            "checkout_session_status": checkout_session.status,
            "payment_provider": checkout_session.payment_provider,
            "provider_status": checkout_session.provider_status,
            "public_checkout_token": checkout_session.public_checkout_token
        }), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@api.route('/paypal/create-order', methods=['POST'])
@jwt_required()
def create_paypal_order():
    current_user = get_jwt_identity()
    data = request.get_json() or {}

    try:
        checkout_token = data.get("checkout_token") or data.get("public_checkout_token")
        customer_snapshot = _extract_customer_snapshot(data)
        existing_checkout_session = None

        logger.info(
            "PayPal create-order solicitado por user_id=%s checkout_token=%s",
            current_user.get("user_id"),
            checkout_token
        )

        if checkout_token:
            existing_checkout_session = _get_checkout_session_by_public_token(
                checkout_token,
                user_id=current_user['user_id'],
                for_update=True
            )
            if not existing_checkout_session:
                logger.warning(
                    "PayPal create-order sin checkout_session para user_id=%s checkout_token=%s",
                    current_user.get("user_id"),
                    checkout_token
                )
                return jsonify({"error": "Checkout session not found."}), 404

            if existing_checkout_session.order_id:
                logger.info(
                    "PayPal create-order idempotente/finalizado para checkout_session=%s order_id=%s",
                    existing_checkout_session.id,
                    existing_checkout_session.order_id
                )
                return jsonify({"error": "Checkout session already finalized."}), 409

            if existing_checkout_session.payment_provider not in ("paypal", None, ""):
                logger.warning(
                    "PayPal create-order rechazado por provider mismatch en checkout_session=%s provider=%s",
                    existing_checkout_session.id,
                    existing_checkout_session.payment_provider
                )
                return jsonify({"error": "Checkout session belongs to a different payment provider."}), 409

            existing_paypal_status = str(existing_checkout_session.provider_status or "").upper()

            if existing_checkout_session.provider_capture_id:
                if customer_snapshot:
                    existing_checkout_session.customer_snapshot = _merge_customer_snapshot(
                        existing_checkout_session.customer_snapshot,
                        customer_snapshot
                    )
                logger.info(
                    "PayPal create-order idempotente: checkout_session=%s ya tenía capture_id=%s",
                    existing_checkout_session.id,
                    existing_checkout_session.provider_capture_id
                )
                db.session.commit()
                response_payload = {
                    **_serialize_checkout_session_payment_state(existing_checkout_session),
                    "approve_url": None,
                    "provider": "paypal",
                    "created_via": "already_captured"
                }
                return jsonify(response_payload), 200

            if (
                existing_checkout_session.provider_order_id and
                existing_paypal_status not in ("VOIDED", "CANCELED", "CANCELLED", "FAILED", "DECLINED", "DENIED")
            ):
                if customer_snapshot:
                    existing_checkout_session.customer_snapshot = _merge_customer_snapshot(
                        existing_checkout_session.customer_snapshot,
                        customer_snapshot
                    )
                logger.info(
                    "PayPal create-order reutiliza provider_order_id=%s para checkout_session=%s status=%s",
                    existing_checkout_session.provider_order_id,
                    existing_checkout_session.id,
                    existing_paypal_status
                )
                db.session.commit()
                response_payload = {
                    **_serialize_checkout_session_payment_state(existing_checkout_session),
                    "approve_url": None,
                    "provider": "paypal",
                    "created_via": "existing_checkout_session"
                }
                return jsonify(response_payload), 200

        quote_request_data = {
            **data,
            "products": None
        }
        checkout_quote = _build_checkout_quote_from_request(current_user, quote_request_data)
        if not checkout_quote["lines"]:
            logger.warning(
                "PayPal create-order rechazado por carrito vacío para user_id=%s",
                current_user.get("user_id")
            )
            return jsonify({"error": "Cart is empty"}), 400

        checkout_session = _upsert_paypal_checkout_session(
            current_user=current_user,
            checkout_quote=checkout_quote,
            customer_snapshot=customer_snapshot,
            checkout_token=checkout_token,
            for_update=True
        )

        paypal_order = _paypal_request(
            "POST",
            "/v2/checkout/orders",
            payload=_build_paypal_order_request(checkout_session),
            request_id=f"paypal-create-{checkout_session.public_checkout_token}"
        )

        checkout_session.provider_order_id = paypal_order.get("id")
        checkout_session.provider_capture_id = None
        checkout_session.provider_status = paypal_order.get("status")
        checkout_session.status = _normalize_checkout_session_status(
            checkout_session.provider_status,
            payment_provider="paypal"
        )

        logger.info(
            "PayPal create-order creado: checkout_session=%s provider_order_id=%s status=%s total=%.2f",
            checkout_session.id,
            checkout_session.provider_order_id,
            checkout_session.provider_status,
            checkout_session.total_amount
        )

        db.session.commit()

        response_payload = {
            **_serialize_checkout_session_payment_state(checkout_session),
            "approve_url": _get_paypal_approve_url(paypal_order),
            "provider": "paypal",
        }
        return jsonify(response_payload), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        db.session.rollback()
        logger.error("Error creando orden PayPal: %s", str(e))
        return jsonify({"error": "Unable to create PayPal order"}), 500


@api.route('/paypal/capture-order', methods=['POST'])
@jwt_required()
def capture_paypal_order():
    current_user = get_jwt_identity()
    data = request.get_json() or {}

    try:
        checkout_token = data.get("checkout_token") or data.get("public_checkout_token")
        provider_order_id = data.get("provider_order_id") or data.get("order_id")
        customer_snapshot = _extract_customer_snapshot(data)

        logger.info(
            "PayPal capture-order solicitado por user_id=%s checkout_token=%s provider_order_id=%s",
            current_user.get("user_id"),
            checkout_token,
            provider_order_id
        )

        if not checkout_token and not provider_order_id:
            logger.warning("PayPal capture-order sin identificador de checkout.")
            return jsonify({"error": "Missing checkout identifier."}), 400

        checkout_session = None
        if checkout_token:
            checkout_session = _get_checkout_session_by_public_token(
                checkout_token,
                user_id=current_user['user_id'],
                for_update=True
            )
        elif provider_order_id:
            checkout_session = _get_checkout_session_by_provider_order_id(
                provider_order_id,
                user_id=current_user['user_id'],
                for_update=True
            )

        if not checkout_session:
            logger.warning(
                "PayPal capture-order sin checkout_session para user_id=%s checkout_token=%s provider_order_id=%s",
                current_user.get("user_id"),
                checkout_token,
                provider_order_id
            )
            return jsonify({"error": "Checkout session not found."}), 404

        if checkout_session.payment_provider != "paypal":
            logger.warning(
                "PayPal capture-order rechazado por provider mismatch en checkout_session=%s provider=%s",
                checkout_session.id,
                checkout_session.payment_provider
            )
            return jsonify({"error": "Checkout session does not belong to PayPal."}), 409

        if customer_snapshot:
            checkout_session.customer_snapshot = _merge_customer_snapshot(
                checkout_session.customer_snapshot,
                customer_snapshot
            )

        if checkout_session.order_id:
            logger.info(
                "PayPal capture-order idempotente: checkout_session=%s ya finalizada con order_id=%s",
                checkout_session.id,
                checkout_session.order_id
            )
            response_payload = {
                **_serialize_checkout_session_payment_state(checkout_session),
                "provider": "paypal",
                "message": "Checkout session already finalized."
            }
            db.session.commit()
            return jsonify(response_payload), 200

        if not checkout_session.provider_order_id:
            logger.warning(
                "PayPal capture-order rechazado: checkout_session=%s no tiene provider_order_id",
                checkout_session.id
            )
            return jsonify({"error": "PayPal order has not been created yet."}), 409

        if provider_order_id and checkout_session.provider_order_id != provider_order_id:
            logger.error(
                "PayPal capture-order con mismatch de provider_order_id en checkout_session=%s incoming=%s stored=%s",
                checkout_session.id,
                provider_order_id,
                checkout_session.provider_order_id
            )
            return jsonify({"error": "PayPal order does not match checkout session."}), 409

        if checkout_session.provider_capture_id:
            logger.info(
                "PayPal capture-order idempotente: checkout_session=%s ya tenía capture_id=%s",
                checkout_session.id,
                checkout_session.provider_capture_id
            )
            response_payload = {
                **_serialize_checkout_session_payment_state(checkout_session),
                "provider": "paypal",
                "message": "PayPal order was already captured."
            }
            db.session.commit()
            return jsonify(response_payload), 200

        paypal_capture = _paypal_request(
            "POST",
            f"/v2/checkout/orders/{checkout_session.provider_order_id}/capture",
            payload=None,
            request_id=f"paypal-capture-{checkout_session.public_checkout_token}"
        )

        capture = _extract_paypal_capture(paypal_capture)
        capture_status = (capture or {}).get("status") or paypal_capture.get("status")

        checkout_session.provider_order_id = paypal_capture.get("id") or checkout_session.provider_order_id
        checkout_session.provider_capture_id = (capture or {}).get("id") or checkout_session.provider_capture_id
        checkout_session.provider_status = capture_status
        checkout_session.status = (
            "order_created"
            if checkout_session.order_id else
            _normalize_checkout_session_status(capture_status, payment_provider="paypal")
        )

        logger.info(
            "PayPal capture-order completado: checkout_session=%s provider_order_id=%s capture_id=%s provider_status=%s",
            checkout_session.id,
            checkout_session.provider_order_id,
            checkout_session.provider_capture_id,
            checkout_session.provider_status
        )

        db.session.commit()

        response_payload = {
            **_serialize_checkout_session_payment_state(checkout_session),
            "provider": "paypal",
        }
        return jsonify(response_payload), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        db.session.rollback()
        logger.error("Error capturando orden PayPal: %s", str(e))
        return jsonify({"error": "Unable to capture PayPal order"}), 500


@api.route('/paypal/webhook', methods=['POST'])
def paypal_webhook():
    payload = request.get_json(silent=True)

    if not payload:
        return jsonify({"error": "Invalid PayPal webhook payload"}), 400

    try:
        if not _verify_paypal_webhook_signature(payload):
            logger.error("Firma de webhook PayPal no verificada correctamente.")
            return jsonify({"error": "Invalid PayPal webhook signature"}), 400
    except ValueError as e:
        logger.error("Configuración/verificación inválida de webhook PayPal: %s", str(e))
        return jsonify({"error": str(e)}), 500
    except RuntimeError as e:
        logger.error("Error verificando webhook PayPal: %s", str(e))
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        logger.error("Error inesperado verificando webhook PayPal: %s", str(e))
        return jsonify({"error": "Unable to verify PayPal webhook"}), 400

    try:
        event_type = payload.get("event_type")
        resource = payload.get("resource") or {}

        logger.info(
            "Webhook PayPal recibido: event_type=%s resource_id=%s",
            event_type,
            resource.get("id")
        )

        if event_type not in (
            "PAYMENT.CAPTURE.COMPLETED",
            "PAYMENT.CAPTURE.PENDING",
            "PAYMENT.CAPTURE.DENIED",
            "PAYMENT.CAPTURE.DECLINED"
        ):
            logger.info("Webhook PayPal ignorado por tipo no gestionado: %s", event_type)
            return "", 200

        checkout_session, resource_details = _get_paypal_checkout_session_from_resource(
            resource,
            for_update=True
        )

        if not checkout_session:
            logger.warning(
                "Webhook PayPal %s recibido sin checkout_session para order_id=%s capture_id=%s",
                event_type,
                resource_details.get("provider_order_id"),
                resource_details.get("provider_capture_id")
            )
            return "", 200

        if checkout_session.payment_provider != "paypal":
            logger.error(
                "Webhook PayPal recibido para checkout_session %s ligada a provider %s",
                checkout_session.id,
                checkout_session.payment_provider
            )
            db.session.rollback()
            return "", 200

        resource_matches_session, resource_mismatch_reason = _paypal_resource_matches_checkout_session(
            checkout_session,
            resource_details
        )
        if not resource_matches_session:
            db.session.rollback()
            logger.error(
                "Webhook PayPal descartado para checkout_session %s por mismatch de IDs: %s",
                checkout_session.id,
                resource_mismatch_reason
            )
            return "", 200

        checkout_session.payment_provider = "paypal"
        checkout_session.provider_order_id = (
            resource_details.get("provider_order_id") or checkout_session.provider_order_id
        )
        checkout_session.provider_capture_id = (
            resource_details.get("provider_capture_id") or checkout_session.provider_capture_id
        )
        checkout_session.provider_status = (
            resource_details.get("provider_status") or event_type
        )

        resource_status = (resource_details.get("provider_status") or "").upper()
        is_final_capture = bool(resource.get("final_capture"))
        pending_completed_final_capture = (
            event_type == "PAYMENT.CAPTURE.PENDING" and
            resource_status == "COMPLETED" and
            is_final_capture
        )

        if event_type == "PAYMENT.CAPTURE.PENDING" and not pending_completed_final_capture:
            if checkout_session.order_id:
                checkout_session.status = "order_created"
            else:
                checkout_session.status = "processing"
            db.session.commit()
            logger.info(
                "Webhook PayPal pending ignorado para checkout_session %s: status=%s provider_status=%s final_capture=%s",
                checkout_session.id,
                checkout_session.status,
                resource_status or checkout_session.provider_status,
                is_final_capture
            )
            return "", 200

        if event_type in ("PAYMENT.CAPTURE.DENIED", "PAYMENT.CAPTURE.DECLINED"):
            if checkout_session.order_id:
                logger.error(
                    "Webhook %s recibido para checkout_session %s que ya tenía order %s",
                    event_type,
                    checkout_session.id,
                    checkout_session.order_id
                )
                checkout_session.status = "order_created"
            else:
                checkout_session.status = "payment_failed"
            db.session.commit()
            logger.info(
                "Checkout session %s marcada como %s tras %s",
                checkout_session.id,
                checkout_session.status,
                event_type
            )
            return "", 200

        is_valid_capture, mismatch_reason = _paypal_capture_matches_checkout_session(
            checkout_session,
            resource_details
        )
        if not is_valid_capture:
            logger.error(
                "Webhook PayPal mismatch para checkout_session %s: event_type=%s reason=%s",
                checkout_session.id,
                event_type,
                mismatch_reason
            )
            checkout_session.status = "processing"
            db.session.commit()
            logger.error(
                "Webhook PayPal no cerró checkout_session %s por mismatch: %s",
                checkout_session.id,
                mismatch_reason
            )
            return "", 200

        if checkout_session.order_id:
            existing_order = Orders.query.get(checkout_session.order_id)
            if existing_order:
                checkout_session.status = "order_created"
                db.session.commit()
                logger.info(
                    "Webhook PayPal idempotente para checkout_session %s: la order %s ya existía.",
                    checkout_session.id,
                    existing_order.id
                )
                return "", 200

            logger.warning(
                "Checkout session %s tenía order_id=%s pero la order ya no existe. Se reintentará el cierre.",
                checkout_session.id,
                checkout_session.order_id
            )
            checkout_session.order_id = None

        if not checkout_session.quote_snapshot or not checkout_session.quote_snapshot.get("lines"):
            logger.error(
                "Webhook PayPal PAYMENT.CAPTURE.COMPLETED sin snapshot válido para checkout_session %s",
                checkout_session.id
            )
            db.session.rollback()
            return "", 200

        user = checkout_session.user or Users.query.get(checkout_session.user_id)
        if not user:
            logger.error(
                "Webhook PayPal PAYMENT.CAPTURE.COMPLETED sin usuario válido para checkout_session %s",
                checkout_session.id
            )
            db.session.rollback()
            return "", 200

        checkout_session.status = "paid"
        order, created = _finalize_order_from_checkout_quote(
            user=user,
            checkout_quote=checkout_session.quote_snapshot,
            customer_snapshot=checkout_session.customer_snapshot,
            checkout_session=checkout_session
        )
        if pending_completed_final_capture:
            logger.info(
                "Webhook PayPal pending con resource.status completed finalizado: checkout_session=%s order=%s created=%s provider_order_id=%s capture_id=%s",
                checkout_session.id,
                order.id,
                created,
                checkout_session.provider_order_id,
                checkout_session.provider_capture_id
            )
        else:
            logger.info(
                "Webhook PayPal completed finalizado: checkout_session=%s order=%s created=%s provider_order_id=%s capture_id=%s",
                checkout_session.id,
                order.id,
                created,
                checkout_session.provider_order_id,
                checkout_session.provider_capture_id
            )
        logger.info(
            "Webhook PayPal %s cerró checkout_session %s → order %s (created=%s)",
            checkout_session.provider_capture_id or checkout_session.provider_order_id,
            checkout_session.id,
            order.id,
            created
        )
        return "", 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error de base de datos procesando webhook PayPal: %s", str(e))
        return jsonify({"error": "database error"}), 500
    except Exception as e:
        db.session.rollback()
        logger.error("Error inesperado procesando webhook PayPal: %s", str(e))
        return jsonify({"error": "unexpected error"}), 500



@api.route('/webhook', methods=['POST'])
def stripe_webhook():
    import stripe, os
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    if not endpoint_secret:
        logger.error("STRIPE_WEBHOOK_SECRET no está configurado.")
        return jsonify({'error': 'Webhook secret not configured'}), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        logger.info("Webhook Stripe recibido: %s", event['type'])
    except Exception as e:
        logger.error("Error validando webhook Stripe: %s", str(e))
        return jsonify({'error': str(e)}), 400

    try:
        event_type = event['type']

        if event_type == 'payment_intent.succeeded':
            intent = event['data']['object']
            payment_intent_id = intent.get('id')

            checkout_session = _get_checkout_session_by_payment_intent(
                payment_intent_id,
                for_update=True
            )

            if not checkout_session:
                logger.warning(
                    "Webhook payment_intent.succeeded recibido sin checkout_session para %s",
                    payment_intent_id
                )
                return '', 200

            if checkout_session.order_id:
                existing_order = Orders.query.get(checkout_session.order_id)
                if existing_order:
                    checkout_session.status = "order_created"
                    db.session.commit()
                    logger.info(
                        "Webhook idempotente para %s: la order %s ya existía.",
                        payment_intent_id,
                        existing_order.id
                    )
                    return '', 200

                logger.warning(
                    "Checkout session %s tenía order_id=%s pero la order ya no existe. Se reintentará el cierre.",
                    checkout_session.id,
                    checkout_session.order_id
                )
                checkout_session.order_id = None

            if not checkout_session.quote_snapshot or not checkout_session.quote_snapshot.get("lines"):
                logger.error(
                    "Webhook payment_intent.succeeded sin snapshot válido para checkout_session %s",
                    checkout_session.id
                )
                db.session.rollback()
                return '', 200

            user = checkout_session.user or Users.query.get(checkout_session.user_id)
            if not user:
                logger.error(
                    "Webhook payment_intent.succeeded sin usuario válido para checkout_session %s",
                    checkout_session.id
                )
                db.session.rollback()
                return '', 200

            checkout_session.status = "paid"
            order, created = _finalize_order_from_checkout_quote(
                user=user,
                checkout_quote=checkout_session.quote_snapshot,
                customer_snapshot=checkout_session.customer_snapshot,
                checkout_session=checkout_session
            )
            logger.info(
                "Webhook %s cerró checkout_session %s → order %s (created=%s)",
                payment_intent_id,
                checkout_session.id,
                order.id,
                created
            )

        elif event_type == 'payment_intent.payment_failed':
            intent = event['data']['object']
            payment_intent_id = intent.get('id')

            checkout_session = _get_checkout_session_by_payment_intent(
                payment_intent_id,
                for_update=True
            )

            if not checkout_session:
                logger.warning(
                    "Webhook payment_intent.payment_failed recibido sin checkout_session para %s",
                    payment_intent_id
                )
                return '', 200

            if checkout_session.order_id:
                checkout_session.status = "order_created"
            else:
                checkout_session.status = "payment_failed"

            db.session.commit()
            logger.info(
                "Checkout session %s marcada como %s tras payment_intent.payment_failed",
                checkout_session.id,
                checkout_session.status
            )

        return '', 200

    except ValueError as e:
        db.session.rollback()
        logger.error("Webhook Stripe descartado por datos inválidos: %s", str(e))
        return '', 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error de base de datos procesando webhook Stripe: %s", str(e))
        return jsonify({'error': 'database error'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error("Error inesperado procesando webhook Stripe: %s", str(e))
        return jsonify({'error': 'unexpected error'}), 500


@api.route('/checkout/quote', methods=['POST'])
@jwt_required()
def checkout_quote():
    current_user = get_jwt_identity()
    data = request.get_json() or {}

    try:
        quote = _build_checkout_quote_from_request(current_user, data)

        response = jsonify(quote)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error calculando checkout quote: {str(e)}")
        return jsonify({"message": "Error calculating checkout quote", "error": str(e)}), 500


@api.route('/checkout/status', methods=['GET'])
@jwt_required()
def checkout_status():
    current_user = get_jwt_identity()
    checkout_token = request.args.get('checkout_token') or request.args.get('public_checkout_token')
    payment_intent_id = request.args.get('payment_intent_id')

    if not checkout_token and not payment_intent_id:
        return jsonify({
            "state": "not_found",
            "message": "Missing checkout identifier."
        }), 400

    if current_user.get("is_admin"):
        checkout_session = (
            _get_checkout_session_by_public_token(checkout_token)
            if checkout_token else
            _get_checkout_session_by_payment_intent(payment_intent_id)
        )
    else:
        checkout_session = (
            _get_checkout_session_by_public_token(
                checkout_token,
                user_id=current_user['user_id']
            )
            if checkout_token else
            _get_checkout_session_by_payment_intent(
                payment_intent_id,
                user_id=current_user['user_id']
            )
        )

    if not checkout_session:
        response = jsonify({
            "state": "not_found",
            "public_checkout_token": checkout_token,
            "payment_intent_id": payment_intent_id,
            "message": "Checkout not found."
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200

    order = checkout_session.order
    if checkout_session.order_id and not order:
        order = Orders.query.get(checkout_session.order_id)

    session_status = checkout_session.status
    if order:
        state = "confirmed"
        message = "Pedido confirmado."
    elif session_status in ("payment_failed", "canceled"):
        state = "failed"
        message = "El pago no se completó correctamente."
    else:
        state = "processing"
        message = "Estamos confirmando tu pedido."

    response = jsonify({
        "state": state,
        "message": message,
        "public_checkout_token": checkout_session.public_checkout_token,
        "payment_intent_id": checkout_session.payment_intent_id,
        "checkout_session_id": checkout_session.id,
        "checkout_session_status": session_status,
        "payment_provider": checkout_session.payment_provider,
        "provider_order_id": checkout_session.provider_order_id,
        "provider_capture_id": checkout_session.provider_capture_id,
        "provider_status": checkout_session.provider_status,
        "order_id": checkout_session.order_id,
        "order": order.serialize() if order else None,
        "email": (checkout_session.user.email if checkout_session.user else current_user.get("email")),
        "total_amount": checkout_session.total_amount,
        "shipping_cost": checkout_session.shipping_cost,
        "discount_code": checkout_session.discount_code,
        "discount_percent": checkout_session.discount_percent
    })
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Expose-Headers'] = 'Authorization'
    return response, 200


@api.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    try:
        comments = Comments.query.filter_by(post_id=post_id).all()
        if not comments:
            response = jsonify([])
        else:
            response = jsonify([comment.serialize() for comment in comments])
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except Exception as e:
        return jsonify({"message": "Error al obtener los comentarios", "error": str(e)}), 500


@api.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    try:
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({"message": "Autenticación requerida"}), 401

        user_id = current_user['user_id']  # Extraer el user_id del token

        data = request.get_json()
        if not data or not data.get("content"):
            return jsonify({"msg": "El contenido es requerido"}), 422

        new_comment = Comments(
            content=data["content"],
            post_id=post_id,
            user_id=user_id  
        )
        db.session.add(new_comment)
        db.session.commit()
        response = jsonify(new_comment.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error al agregar el comentario", "error": str(e)}), 500


@api.route('/posts', methods=['GET'])
@jwt_required(optional=True)
def get_posts():
    try:
        posts = Posts.query.order_by(Posts.created_at.asc()).all()
        total_count = len(posts)

        response = jsonify([post.serialize() for post in posts])
        response.headers['X-Total-Count'] = total_count
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count, Authorization'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200
    except Exception as e:
        return jsonify({"message": "Error al obtener los posts", "error": str(e)}), 500


@api.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required(optional=True)
def get_post(post_id):
    try:
        post = Posts.query.get(post_id)
        if post:
            response = jsonify(post.serialize())
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 200
        return jsonify({"message": "Post no encontrado"}), 404
    except Exception as e:
        return jsonify({"message": "Error al obtener el post", "error": str(e)}), 500


@api.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    try:
        current_user = get_jwt_identity()
        if not current_user.get("is_admin"):
            return jsonify({"message": "Acceso prohibido: Solo administradores"}), 403

        data = request.json
        new_post = Posts(
            title=data.get('title'),
            content=data.get('content'),
            author_id=current_user.get('id'),
            image_url=data.get('image_url')
        )
        db.session.add(new_post)
        db.session.commit()
        response = jsonify(new_post.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "Error al crear el post", "error": str(e)}), 500


@api.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    try:
        current_user = get_jwt_identity()
        if not current_user.get("is_admin"):
            return jsonify({"message": "Acceso prohibido: Solo administradores"}), 403

        post = Posts.query.get(post_id)
        if not post:
            return jsonify({"message": "Post no encontrado"}), 404

        data = request.json
        post.title = data.get('title', post.title)
        post.content = data.get('content', post.content)
        post.image_url = data.get('image_url', post.image_url)
        post.updated_at = datetime.utcnow()

        db.session.commit()
        response = jsonify(post.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "Error al actualizar el post", "error": str(e)}), 500


@api.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    try:
        current_user = get_jwt_identity()
        if not current_user.get("is_admin"):
            return jsonify({"message": "Acceso prohibido: Solo administradores"}), 403

        post = Posts.query.get(post_id)
        if not post:
            return jsonify({"message": "Post no encontrado"}), 404

        db.session.delete(post)
        db.session.commit()
        response = jsonify({"message": "Post eliminado"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "Error al eliminar el post", "error": str(e)}), 500


@api.route("/login", methods=["OPTIONS", "POST"])
def login():
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200

    data = request.json or {}

    raw_email = data.get("email")
    email = raw_email.strip().lower() if isinstance(raw_email, str) else None
    password = data.get("password")

    if not email or not password:
        response = jsonify({"message": "Correo o contraseña incorrectos"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 401

    user = db.session.execute(
        db.select(Users).where(Users.email == email)
    ).scalar()

    if not user or not bcrypt.checkpw(
        password.encode("utf-8"),
        user.password.encode("utf-8")
    ):
        response = jsonify({"message": "Correo o contraseña incorrectos"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 401

    access_token = create_access_token(
        identity={
            "user_id": user.id,
            "email": user.email,
            "is_admin": user.is_admin
        },
        expires_delta=timedelta(hours=24)
    )

    response = jsonify({
        "results": user.serialize(),
        "message": "Bienvenido",
        "access_token": access_token
    })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, 200


@api.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    response_body = {}
    current_user = get_jwt_identity()
    if current_user and current_user.get("is_admin") is True:
        response_body['message'] = f'Access granted {current_user["email"]}'
        response_body['results'] = current_user
        return jsonify(response_body), 200

    response_body['message'] = 'Acceso denegado: se requieren permisos de administrador'
    response_body['results'] = {}
    return jsonify(response_body), 403


@api.route("/signup", methods=["OPTIONS", "POST"])
def signup():
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200

    data = request.json or {}

    # 🔒 Normalizar email
    raw_email = data.get("email")
    email = raw_email.strip().lower() if isinstance(raw_email, str) else None
    password = data.get("password")

    if not email or "@" not in email:
        response = jsonify({"message": "Email inválido"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 400

    if not password:
        response = jsonify({"message": "Contraseña requerida"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 400

    # 🔎 Comprobar duplicados
    existing_user = db.session.execute(
        db.select(Users).where(Users.email == email)
    ).scalar()

    if existing_user:
        response = jsonify({"message": "Ya existe un usuario registrado con este correo"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 409

    # 🔐 Hash password
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    # 👤 Crear usuario normal (NO admin)
    user = Users(
        email=email,
        password=hashed_password.decode("utf-8"),
        is_admin=False
    )

    db.session.add(user)
    db.session.commit()

    # --- Emails ---
    # 1) Bienvenida al usuario
    html_body_user = f"""
    <h2 style="color:#ff324d; font-family:Arial, sans-serif; text-align:center;">
    ¡Bienvenido a Metal Wolft!
    </h2>

    <p style="font-size:16px; font-family:Arial, sans-serif;">
    Hola,
    </p>

    <p style="font-size:16px; font-family:Arial, sans-serif;">
    Tu cuenta ha sido creada correctamente. Ahora puedes iniciar sesión, explorar nuestros productos y seguir tus pedidos en todo momento.
    </p>

    <p style="font-size:16px; font-family:Arial, sans-serif;">
    Para comenzar, accede a tu cuenta haciendo clic aquí:
    </p>

    <p style="text-align:center;">
    <a href="https://www.metalwolft.com/login" 
        style="display:inline-block; padding:10px 20px; background-color:#ff324d; color:white; 
                text-decoration:none; border-radius:5px; font-weight:bold;">
        Iniciar Sesión
    </a>
    </p>

    <p style="font-size:16px; font-family:Arial, sans-serif;">
    Gracias por registrarte en <strong>Metal Wolft</strong>.  
    Si tienes alguna pregunta, responde directamente a este correo o visita nuestra sección de ayuda.
    </p>

    <hr style="border:none; border-top:1px solid #ddd; margin:20px 0;">

    <p style="font-size:12px; color:#777; font-family:Arial, sans-serif; text-align:center;">
    Metal Wolft © 2025 España
    </p>

    """
    try:
        send_email(
            subject="¡Bienvenido a Metal Wolft!",
            recipients=[email],
            body="Gracias por registrarte en Metal Wolft.",
            html=html_body_user
        )
    except Exception as e:
        current_app.logger.warning(
            f"No se pudo enviar el email de bienvenida a {email}: {e}"
        )

    try:
        admin_recipients = get_admin_recipients()
        if admin_recipients:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            html_body_admin = f"""
            <h3>Nuevo registro</h3>
            <ul>
              <li>Email: <b>{email}</b></li>
              <li>IP: {ip}</li>
              <li>User ID: {user.id}</li>
            </ul>
            """
            send_email(
                subject="Nuevo registro en la web",
                recipients=admin_recipients,
                body=f"Nuevo registro: {email}",
                html=html_body_admin
            )
    except Exception as e:
        current_app.logger.warning(
            f"No se pudo notificar a admins del registro de {email}: {e}"
        )

    access_token = create_access_token(identity={
        "user_id": user.id,
        "email": user.email,
        "is_admin": user.is_admin
    })
    response = jsonify({
        "results": user.serialize(),
        "message": "Usuario registrado",
        "access_token": access_token
    })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, 201


@api.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    # Parámetros para paginación y orden desde React-Admin
    start = request.args.get('_start', type=int, default=0)
    end   = request.args.get('_end', type=int, default=10)
    sort  = request.args.get('_sort', default='id')
    order = request.args.get('_order', default='DESC').upper()

    # 🔥 Fuerza DESC cuando el sort es por ID
    if sort == 'id':
        order = 'DESC'

    sort_col = getattr(Users, sort, Users.id)
    query = Users.query.order_by(
        sort_col.desc() if order == 'DESC' else sort_col.asc()
    )

    total_count = query.count()

    if start is not None and end is not None and end > start:
        query = query.offset(start).limit(end - start)

    users = query.all()

    response = jsonify([_serialize_user_for_admin(user) for user in users])
    response.headers['X-Total-Count'] = str(total_count)
    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200


@api.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    data = request.json or {}
    raw_email = data.get('email')
    email = raw_email.strip().lower() if isinstance(raw_email, str) else None
    password = data.get('password')

    if not email or "@" not in email:
        return jsonify({"message": "Email inválido"}), 400

    if not password:
        return jsonify({"message": "Contraseña requerida"}), 400

    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    new_user = Users(
        email=email,
        password=hashed_password.decode("utf-8"),
        firstname=data.get('firstname'),
        lastname=data.get('lastname'),
        is_admin=data.get('is_admin', False)
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.serialize()), 201


@api.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    response = jsonify(_serialize_user_for_admin(user))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200


@api.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user = get_jwt_identity()

    # 🔒 Permisos: solo el propio usuario o admin
    if current_user.get("user_id") != user_id and not current_user.get("is_admin"):
        response = jsonify({
            "message": "Access forbidden: Only admins or the user themselves can update the profile"
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 403

    user = Users.query.get(user_id)
    if not user:
        response = jsonify({"message": "User not found"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 404

    data = request.json or {}

    # 🧾 Campos que el USUARIO puede editar
    editable_fields_user = [
        "firstname",
        "lastname",
        "shipping_address",
        "shipping_city",
        "shipping_postal_code",
        "billing_address",
        "billing_city",
        "billing_postal_code",
        "CIF",
    ]

    # 🛠️ Admin: puede editar email (normalizado) y flags
    if current_user.get("is_admin"):
        raw_email = data.get("email")
        if isinstance(raw_email, str):
            email = raw_email.strip().lower()
            if email and "@" in email:
                user.email = email

        if "is_admin" in data:
            user.is_admin = bool(data.get("is_admin"))

        if "is_active" in data:
            user.is_active = bool(data.get("is_active"))

    # 👤 Usuario (y admin): solo campos de perfil
    for field in editable_fields_user:
        if field in data:
            setattr(user, field, data[field])

    try:
        db.session.commit()
        response = jsonify({
            "message": "User updated",
            "results": user.serialize()
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'PUT, OPTIONS'
        return response, 200

    except Exception as e:
        db.session.rollback()
        response = jsonify({
            "message": "An error occurred while updating user",
            "error": str(e)
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@api.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        response = jsonify({"message": "Access forbidden: Admins only"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 403
    user = Users.query.get(user_id)
    if not user:
        response = jsonify({"message": "User not found!"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 404
    db.session.delete(user)
    db.session.commit()
    response = jsonify({"message": "User deleted!"})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200


@api.route('/categories', methods=['GET'])
def get_all_categories():
    try:
        categories = Categories.query.all()
        response_data = []
        for category in categories:
            product_count = Products.query.filter(Products.categoria_id == category.id).count()
            subcategories = Subcategories.query.filter_by(categoria_id=category.id).all()
            subcategories_data = []
            for subcat in subcategories:
                subcat_product_count = Products.query.filter(Products.subcategoria_id == subcat.id).count()
                subcategories_data.append({
                    **subcat.serialize(),
                    "product_count": subcat_product_count
                })
            response_data.append({
                **category.serialize(),
                "product_count": product_count,
                "subcategories": subcategories_data
            })
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        response = jsonify({"message": "Error retrieving categories", "error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@api.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        response = jsonify({"message": "Acceso prohibido: Solo administradores"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 403

    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    parent_id = data.get('parent_id')

    if not nombre:
        response = jsonify({"message": "El nombre de la categoría es obligatorio"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 400

    new_category = Categories(nombre=nombre, descripcion=descripcion, parent_id=parent_id)
    db.session.add(new_category)
    db.session.commit()

    response = jsonify(new_category.serialize())
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Expose-Headers'] = 'Authorization'
    return response, 201


@api.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        response = jsonify({"message": "Acceso prohibido: Solo administradores"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 403

    category = Categories.query.get(category_id)
    if not category:
        response = jsonify({"message": "Categoría no encontrada"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 404

    data = request.get_json()
    category.nombre = data.get('nombre', category.nombre)
    category.descripcion = data.get('descripcion', category.descripcion)
    category.parent_id = data.get('parent_id', category.parent_id)

    db.session.commit()

    response = jsonify(category.serialize())
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Expose-Headers'] = 'Authorization'
    return response, 200


@api.route('/categories/<int:category_id>/subcategories', methods=['GET'])
def get_subcategories(category_id):
    try:
        subcategories = Categories.query.filter_by(parent_id=category_id).all()
        print("Subcategories fetched from database:", subcategories)
        response = jsonify([subcategory.serialize() for subcategory in subcategories])
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        response = jsonify({"message": "Error retrieving subcategories", "error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 500


@api.route("/category/<string:slug>/products", methods=["GET"])
def get_products_by_category(slug):
    category = Categories.query.filter_by(slug=slug).first()
    if not category:
        return jsonify({"message": "Categoría no encontrada"}), 404

    products = (
        Products.query
        .filter_by(categoria_id=category.id)
        .order_by(Products.sort_order.asc(), Products.id.asc())    
        .all()
    )
    return jsonify([p.serialize() for p in products]), 200


@api.route('/products', methods=['GET'])
def get_products():
    category_id = request.args.get('category_id', type=int)
    subcategory_id = request.args.get('subcategory_id', type=int)
    try:
        query = Products.query
        if subcategory_id:
            query = query.filter(Products.subcategoria_id == subcategory_id)
        elif category_id:
            subcategory_ids = [sub.id for sub in Subcategories.query.filter_by(categoria_id=category_id).all()]
            ids_to_filter = [category_id] + subcategory_ids
            query = query.filter(
                (Products.categoria_id == category_id) |
                (Products.subcategoria_id.in_(subcategory_ids))
            )

        total_count = query.count()
        
        products = query.order_by(
            Products.sort_order.asc(),
            Products.id.asc()
        ).all()
        response = jsonify([product.serialize_with_images() for product in products])
        
        response.headers['X-Total-Count'] = total_count
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count, Authorization'
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        return response, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        response = jsonify({"message": "Error retrieving products", "error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@api.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    current_user = get_jwt_identity()
    if not current_user or not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    data = request.form  
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    precio = data.get('precio')
    imagen = data.get('imagen')
    categoria_id = data.get('categoria_id')
    subcategoria_id = data.get('subcategoria_id')
    subcategoria = Subcategories.query.get(subcategoria_id)
    if not subcategoria:
        return jsonify({"message": "La subcategoría especificada no existe"}), 400
    categoria_id = subcategoria.categoria_id
    new_product = Products(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        imagen=imagen,
        categoria_id=categoria_id,
        subcategoria_id=subcategoria_id
    )
    try:
        db.session.add(new_product)
        db.session.commit()
        return jsonify(new_product.serialize_with_images()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "Error al crear el producto", "error": str(e)}), 500


@api.route('/<string:category_slug>/<string:product_slug>', methods=['GET'])
def get_product_by_category_and_slug(category_slug, product_slug):
    try:
        category = Categories.query.filter_by(slug=category_slug).first()
        if not category:
            return jsonify({"message": "Category not found"}), 404
        product = Products.query.filter_by(slug=product_slug, categoria_id=category.id).first()

        if not product:
            return jsonify({"message": "Product not found in this category"}), 404
        response = jsonify(product.serialize_with_images())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except Exception as e:
        logger.error(f"Error al obtener el producto por categoría y slug: {str(e)}")
    return jsonify({"message": "Error fetching product", "error": str(e)}), 500


@api.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Products.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    response = jsonify(product.serialize_with_images())
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Expose-Headers'] = 'Authorization'
    return response, 200


@api.route('/products/<int:product_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def handle_product(product_id):
    product = Products.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    current_user = get_jwt_identity()
    if request.method == 'PUT':
        if not current_user or not current_user.get("is_admin"):
            return jsonify({"message": "Access forbidden: Admins only"}), 403
        data = request.json
        try:
            product.nombre = data.get('nombre', product.nombre)
            product.descripcion = data.get('descripcion', product.descripcion)
            product.precio = data.get('precio', product.precio)
            product.categoria_id = data.get('categoria_id', product.categoria_id)
            product.imagen = data.get('imagen', product.imagen)
            if 'images' in data:
                images_urls = data.get('images', [])
                ProductImages.query.filter_by(product_id=product_id).delete()
                for image_url in images_urls:
                    new_image = ProductImages(product_id=product_id, image_url=image_url)
                    db.session.add(new_image)
            db.session.commit()
            response = jsonify(product.serialize_with_images())
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred while updating the product.", "error": str(e)}), 500
    elif request.method == 'DELETE':
        if not current_user or not current_user.get("is_admin"):
            return jsonify({"message": "Access forbidden: Admins only"}), 403
        try:
            db.session.delete(product)
            db.session.commit()
            response = jsonify({"message": "Product deleted successfully."})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred while deleting the product.", "error": str(e)}), 500


@api.route('/products/<int:product_id>/images', methods=['POST'])
@jwt_required()
def add_product_images(product_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403
    product = Products.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    data = request.get_json()
    image_urls = data.get('images', [])
    if not isinstance(image_urls, list) or not all(isinstance(url, str) for url in image_urls):
        return jsonify({"message": "Invalid images format. Expected a list of URLs."}), 400
    try:
        for image_url in image_urls:
            new_image = ProductImages(product_id=product_id, image_url=image_url)
            db.session.add(new_image)
        db.session.commit()
        response = jsonify({"message": "Images added successfully.", "product": product.serialize_with_images()})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while adding images.", "error": str(e)}), 500


@api.route('/product_images', methods=['GET'])
@jwt_required()
def get_product_images():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403
    product_images = ProductImages.query.all()
    total_count = len(product_images)
    response = jsonify([image.serialize() for image in product_images])
    response.headers['X-Total-Count'] = total_count
    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count, Authorization'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200

@api.route('/orders', methods=['GET', 'POST'])
@jwt_required()
def handle_orders():
    current_user = get_jwt_identity()

    if request.method == 'GET':
        try:
            # 🔥 Soporte de paginación y orden
            start = request.args.get('_start', type=int, default=0)
            end = request.args.get('_end', type=int, default=10)
            sort = request.args.get('_sort', default='id')
            order = request.args.get('_order', default='DESC').upper()

            # 🔥 Si el sort es por ID, forzamos DESC
            if sort == 'id':
                order = 'DESC'

            sort_col = getattr(Orders, sort, Orders.id)

            # 🔑 Admin ve todo, usuarios solo lo suyo
            if current_user.get("is_admin"):
                query = Orders.query
            else:
                query = Orders.query.filter_by(user_id=current_user['user_id'])

            query = query.order_by(
                sort_col.desc() if order == 'DESC' else sort_col.asc()
            )

            total_count = query.count()

            # 🔥 Paginación real
            if start is not None and end is not None and end > start:
                query = query.offset(start).limit(end - start)

            orders = query.all()
            results = [order.serialize() for order in orders]

            # Respuesta con headers para React-Admin
            response = jsonify(results)
            response.headers['X-Total-Count'] = str(total_count)
            response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 200
        except Exception as e:
            logger.error(f"Error al obtener las órdenes: {str(e)}")
            return jsonify({"message": "Error fetching orders", "error": str(e)}), 500

    if request.method == 'POST':
        data = request.get_json() or {}
        logger.info(f"Datos recibidos para crear la orden: {data}")
        try:
            payment_intent_id = data.get("payment_intent_id")
            if not payment_intent_id:
                logger.warning(
                    "Intento bloqueado de crear order sin payment_intent_id para user_id=%s",
                    current_user['user_id']
                )
                return jsonify({
                    "message": "payment_intent_id is required to finalize an order."
                }), 400

            customer_snapshot = _extract_customer_snapshot(data)
            checkout_session = None

            checkout_session = _get_checkout_session_by_payment_intent(
                payment_intent_id,
                user_id=current_user['user_id'],
                for_update=True
            )

            if not checkout_session:
                return jsonify({"message": "Checkout session not found for this payment intent."}), 409

            if checkout_session.order_id:
                existing_order = Orders.query.filter_by(
                    id=checkout_session.order_id,
                    user_id=current_user['user_id']
                ).first()
                if existing_order:
                    db.session.commit()
                    response = jsonify({
                        "data": existing_order.serialize(),
                        "message": "Order already created for this payment intent."
                    })
                    response.headers['Access-Control-Allow-Origin'] = '*'
                    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
                    return response, 200

                logger.warning(
                    "Checkout session %s apunta a una order inexistente (%s) desde /orders. Se reintentará el cierre.",
                    checkout_session.id,
                    checkout_session.order_id
                )
                checkout_session.order_id = None

            import stripe
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            checkout_session.status = _normalize_checkout_session_status(intent.get("status"))

            if customer_snapshot:
                checkout_session.customer_snapshot = {
                    **(checkout_session.customer_snapshot or {}),
                    **customer_snapshot
                }
                customer_snapshot = checkout_session.customer_snapshot

            if checkout_session.status != "paid":
                db.session.commit()
                return jsonify({"message": "PaymentIntent is not completed yet."}), 409

            if not checkout_session.quote_snapshot or not checkout_session.quote_snapshot.get("lines"):
                db.session.rollback()
                return jsonify({"message": "Checkout snapshot not available for this payment intent."}), 409

            logger.info(
                "Cierre de pedido en /orders actuando como fallback controlado para payment_intent %s",
                payment_intent_id
            )
            checkout_quote = checkout_session.quote_snapshot

            comparison = _build_checkout_comparison_from_request(checkout_quote, data)

            if comparison.get("has_difference"):
                logger.warning(
                    "Checkout mismatch detectado en /orders → "
                    f"frontend_total={comparison.get('frontend_total')} | "
                    f"backend_total={comparison.get('backend_total')} | "
                    f"frontend_shipping={comparison.get('frontend_shipping_cost')} | "
                    f"backend_shipping={comparison.get('backend_shipping_cost')} | "
                    f"frontend_discount_code={comparison.get('frontend_discount_code')} | "
                    f"backend_discount_code={comparison.get('backend_discount_code')} | "
                    f"frontend_discount_percent={comparison.get('frontend_discount_percent')} | "
                    f"backend_discount_percent={comparison.get('backend_discount_percent')} | "
                    f"line_differences={comparison.get('line_differences')}"
                )
            else:
                logger.info(
                    "Checkout alineado en /orders → "
                    f"backend_total={comparison.get('backend_total')} | "
                    f"backend_shipping={comparison.get('backend_shipping_cost')} | "
                    f"backend_discount_code={comparison.get('backend_discount_code')} | "
                    f"backend_discount_percent={comparison.get('backend_discount_percent')}"
                )

            user = Users.query.get(current_user['user_id'])
            if not user:
                db.session.rollback()
                return jsonify({"message": "User not found"}), 404

            new_order, created = _finalize_order_from_checkout_quote(
                user=user,
                checkout_quote=checkout_quote,
                customer_snapshot=customer_snapshot,
                checkout_session=checkout_session
            )

            response = jsonify({
                "data": new_order.serialize(),
                "message": "Order, details, and invoice created successfully." if created else "Order already created for this payment intent."
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
            return response, 201 if created else 200

            if payment_intent_id:
                checkout_session = CheckoutSessions.query.filter_by(
                    payment_intent_id=payment_intent_id,
                    user_id=current_user['user_id']
                ).first()

                if not checkout_session:
                    return jsonify({"message": "Checkout session not found for this payment intent."}), 409

                if checkout_session.status == "order_created" and checkout_session.order_id:
                    existing_order = Orders.query.filter_by(
                        id=checkout_session.order_id,
                        user_id=current_user['user_id']
                    ).first()
                    if existing_order:
                        response = jsonify({
                            "data": existing_order.serialize(),
                            "message": "Order already created for this payment intent."
                        })
                        response.headers['Access-Control-Allow-Origin'] = '*'
                        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
                        return response, 200

                import stripe
                stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                checkout_session.status = _normalize_checkout_session_status(intent.get("status"))

                if checkout_session.status != "paid":
                    db.session.commit()
                    return jsonify({"message": "PaymentIntent is not completed yet."}), 409

                if not checkout_session.quote_snapshot or not checkout_session.quote_snapshot.get("lines"):
                    return jsonify({"message": "Checkout snapshot not available for this payment intent."}), 409

                checkout_quote = checkout_session.quote_snapshot
                order_details = _build_order_details_from_checkout_quote(checkout_quote)
                if checkout_session.customer_snapshot:
                    customer_snapshot = {
                        **checkout_session.customer_snapshot,
                        **customer_snapshot
                    }
            else:
                quote_request_data = {
                    **data,
                    "products": None
                }
                checkout_quote = _build_checkout_quote_from_request(current_user, quote_request_data)
                if not checkout_quote["lines"]:
                    return jsonify({"message": "Cart is empty"}), 400
                order_details = _build_order_details_from_checkout_quote(checkout_quote)

            comparison = _build_checkout_comparison_from_request(checkout_quote, data)

            if comparison.get("has_difference"):
                logger.warning(
                    "Checkout mismatch detectado en /orders → "
                    f"frontend_total={comparison.get('frontend_total')} | "
                    f"backend_total={comparison.get('backend_total')} | "
                    f"frontend_shipping={comparison.get('frontend_shipping_cost')} | "
                    f"backend_shipping={comparison.get('backend_shipping_cost')} | "
                    f"frontend_discount_code={comparison.get('frontend_discount_code')} | "
                    f"backend_discount_code={comparison.get('backend_discount_code')} | "
                    f"frontend_discount_percent={comparison.get('frontend_discount_percent')} | "
                    f"backend_discount_percent={comparison.get('backend_discount_percent')} | "
                    f"line_differences={comparison.get('line_differences')}"
                )
            else:
                logger.info(
                    "Checkout alineado en /orders → "
                    f"backend_total={comparison.get('backend_total')} | "
                    f"backend_shipping={comparison.get('backend_shipping_cost')} | "
                    f"backend_discount_code={comparison.get('backend_discount_code')} | "
                    f"backend_discount_percent={comparison.get('backend_discount_percent')}"
                )

            customer_firstname = _get_customer_value(data, customer_snapshot, 'firstname')
            customer_lastname = _get_customer_value(data, customer_snapshot, 'lastname')
            customer_phone = _get_customer_value(data, customer_snapshot, 'phone')
            customer_shipping_address = _get_customer_value(data, customer_snapshot, 'shipping_address')
            customer_shipping_city = _get_customer_value(data, customer_snapshot, 'shipping_city')
            customer_shipping_postal_code = _get_customer_value(data, customer_snapshot, 'shipping_postal_code')
            customer_billing_address = _get_customer_value(data, customer_snapshot, 'billing_address')
            customer_billing_city = _get_customer_value(data, customer_snapshot, 'billing_city')
            customer_billing_postal_code = _get_customer_value(data, customer_snapshot, 'billing_postal_code')
            customer_cif = _get_customer_value(data, customer_snapshot, 'CIF')

            # Crear la orden inicialmente sin total_amount definitivo
            new_order = Orders(
                user_id=current_user['user_id'],
                total_amount=0,  # Temporalmente 0, lo recalcularemos
                locator=Orders.generate_locator(),
                order_status="pendiente"
            )
            db.session.add(new_order)
            db.session.flush()  # Nos da el id de la orden

            # Crear los detalles de la orden y calcular subtotal
            subtotal = 0.0
            discount_percent = float(checkout_quote.get('discount_percent') or 0)
            discount_code = checkout_quote.get('discount_code') or None

            for detail in order_details:
                precio_recalculado = float(detail.get('precio_total') or 0.0)
                existing_detail = OrderDetails.query.filter_by(
                    order_id=new_order.id,
                    product_id=detail['producto_id'],
                    alto=detail.get('alto'),
                    ancho=detail.get('ancho'),
                    anclaje=detail.get('anclaje'),
                    color=detail.get('color')
                ).first()

                if existing_detail:
                    logger.info(f"Detalle ya existente: {existing_detail.serialize()}")
                    existing_detail.quantity += detail['quantity']
                    existing_detail.precio_total = precio_recalculado  
                    subtotal += precio_recalculado * detail['quantity']
                    continue


                # Crear detalle usando la línea canónica ya validada por backend
                new_detail = OrderDetails(
                    order_id=new_order.id,
                    product_id=detail['producto_id'],
                    quantity=detail['quantity'],
                    alto=detail.get('alto'),
                    ancho=detail.get('ancho'),
                    anclaje=detail.get('anclaje'),
                    color=detail.get('color'),
                    precio_total=precio_recalculado,
                    firstname=customer_firstname,
                    lastname=customer_lastname,
                    shipping_address=customer_shipping_address,
                    shipping_city=customer_shipping_city,
                    shipping_postal_code=customer_shipping_postal_code,
                    billing_address=customer_billing_address,
                    billing_city=customer_billing_city,
                    billing_postal_code=customer_billing_postal_code,
                    CIF=customer_cif,
                    shipping_type=detail.get('shipping_type'),
                    shipping_cost=detail.get('shipping_cost')
                )

                db.session.add(new_detail)
                subtotal += precio_recalculado * detail.get("quantity", 1)


            # El envío global del pedido sale de la quote canónica backend.
            shipping_cost = float(checkout_quote["shipping_cost"])

            backend_total = float(checkout_quote["total_amount"])

            # Calculamos el total bruto del pedido (producto + envío)
            #    Este subtotal ya incluye IVA en tu flujo actual
            gross_sum = subtotal + float(shipping_cost or 0.0)

            # El descuento mostrado en factura sale de la quote canónica backend.
            discount_value_iva = round(float(checkout_quote["discount_amount"]), 2)

            # 🔹 Guardamos en la BD los valores autoritativos del backend
            new_order.discount_code = discount_code
            new_order.discount_value = discount_value_iva
            new_order.shipping_cost = round(float(shipping_cost or 0.0), 2)
            new_order.total_amount = round(backend_total, 2)

            # Logging detallado para depuración contable
            logger.info(
                f"🧾 Cálculo final autoritativo backend → "
                f"Bruto: {gross_sum:.2f} € | Descuento: {discount_value_iva:.2f} € | "
                f"Envío: {shipping_cost:.2f} € | Total guardado: {backend_total:.2f} €"
            )

            if checkout_session:
                checkout_session.order_id = new_order.id
                checkout_session.status = "order_created"
                if customer_snapshot:
                    checkout_session.customer_snapshot = customer_snapshot

            db.session.commit()

            # Intentar actualizar datos del usuario sin bloquear la compra
            try:
                user = Users.query.get(current_user['user_id'])
                if user:
                    updated = False

                    # Solo completar campos vacíos con datos del pedido
                    if not user.firstname and customer_firstname:
                        user.firstname = customer_firstname
                        updated = True
                    if not user.lastname and customer_lastname:
                        user.lastname = customer_lastname
                        updated = True
                    if not user.shipping_address and customer_shipping_address:
                        user.shipping_address = customer_shipping_address
                        updated = True
                    if not user.shipping_city and customer_shipping_city:
                        user.shipping_city = customer_shipping_city
                        updated = True
                    if not user.shipping_postal_code and customer_shipping_postal_code:
                        user.shipping_postal_code = customer_shipping_postal_code
                        updated = True
                    if not user.billing_address and customer_billing_address:
                        user.billing_address = customer_billing_address
                        updated = True
                    if not user.billing_city and customer_billing_city:
                        user.billing_city = customer_billing_city
                        updated = True
                    if not user.billing_postal_code and customer_billing_postal_code:
                        user.billing_postal_code = customer_billing_postal_code
                        updated = True
                    if not user.CIF and customer_cif:
                        user.CIF = customer_cif
                        updated = True

                    # Guardar cambios solo si hay algo nuevo
                    if updated:
                        db.session.commit()
                        logger.info(f"Datos del usuario {user.email} actualizados desde la compra")

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error al actualizar datos del usuario: {str(e)}")

            # Generar la factura
            try:
                invoice_number = Invoices.generate_next_invoice_number()
                pdf_filename = f"invoice_{invoice_number}.pdf"
                file_path = os.path.join(current_app.config['INVOICE_FOLDER'], pdf_filename)
                pdf_path = f"/api/download-invoice/{pdf_filename}"
                os.makedirs(current_app.config['INVOICE_FOLDER'], exist_ok=True)

                pdf_buffer = BytesIO()
                pdf = canvas.Canvas(pdf_buffer, pagesize=A4)

                # Agregar logo
                image_url = "https://res.cloudinary.com/dewanllxn/image/upload/v1740167674/logo_uxlqof.png"
                pdf.drawImage(image_url, 300, 750, width=250, height=64)

                # Información de la factura
                pdf.setTitle(f"Factura_{invoice_number}")
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, 800, f"Factura No: {invoice_number}")

                pdf.setFont("Helvetica", 10)
                fecha_emision = datetime.now().strftime("%d/%m/%Y")
                pdf.drawString(50, 780, f"Fecha: {fecha_emision}")

                # Información del proveedor
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(400, 700, "PROVEEDOR")
                pdf.setFont("Helvetica", 10)
                pdf.drawString(400, 680, "Sergio Arias Fernández")
                pdf.drawString(400, 665, "05703874N")
                pdf.drawString(400, 650, "Francisco Fernández Ordoñez 32")
                pdf.drawString(400, 635, "13170 Miguelturra")
                pdf.drawString(400, 620, "634112604")

                # Información del cliente
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, 700, "CLIENTE")
                pdf.setFont("Helvetica", 10)
                pdf.drawString(50, 680, f"{customer_firstname or ''} {customer_lastname or ''}".strip())
                pdf.drawString(50, 665, f"{customer_billing_address or ''}, {customer_billing_city or ''} ({customer_billing_postal_code or ''})")
                pdf.drawString(50, 650, f"{customer_cif or ''}")
                pdf.drawString(50, 635, f"{customer_phone or 'No proporcionado'}")

                # Dirección de envío
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, 580, "Dirección de Envío")
                pdf.setFont("Helvetica", 10)

                # Verificar si la dirección de envío es igual a la de facturación o está vacía
                if not customer_shipping_address or customer_shipping_address == customer_billing_address:
                    pdf.drawString(50, 560, "La misma que la de facturación")
                else:
                    pdf.drawString(50, 560, f"{customer_shipping_address or ''}, {customer_shipping_city or ''} ({customer_shipping_postal_code or ''})")

                # Detalles del pedido
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, 510, "Detalles del Pedido")
                pdf.setFont("Helvetica", 10)

                from collections import defaultdict

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

                    # compatibilidad pedidos antiguos
                    "blanco": "Blanco",
                    "negro": "Negro",
                    "gris": "Gris",
                    "marrón": "Marrón",
                    "verde": "Verde"
                }

                data_table = [["Prod.", "Alto", "Ancho", "Anc.", "Col.", "Ud.", "Importe (€)"]]

                # Agrupar productos iguales
                grouped_details = defaultdict(lambda: {"quantity": 0, "precio_unitario": 0.0})

                for detail in order_details:
                    key = (
                        detail['producto_id'],
                        detail.get('alto'),
                        detail.get('ancho'),
                        detail.get('anclaje'),
                        detail.get('color')
                    )
                    grouped_details[key]["quantity"] += detail.get("quantity", 1)
                    grouped_details[key]["precio_unitario"] = float(detail["precio_total"])

                # Añadir filas agrupadas a la tabla
                for (producto_id, alto, ancho, anclaje, color), values in grouped_details.items():
                    prod = Products.query.get(producto_id)
                    cantidad = values["quantity"]
                    precio_unitario = values["precio_unitario"]
                    importe_total = precio_unitario * cantidad

                    row = [
                        prod.nombre[:24] if prod else "Desconocido",
                        f"{alto} cm",
                        f"{ancho} cm",
                        (anclaje[:20] if anclaje else ''),
                        COLOR_LABELS.get(color, color)[:18] if color else '',
                        str(cantidad),
                        f"{importe_total:.2f}"
                    ]
                    data_table.append(row)



                # Crear la tabla
                table = Table(data_table, colWidths=[4*cm, 1.5*cm, 1.5*cm, 4.2*cm, 3.2*cm, 1*cm, 2.3*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.Color(1, 0.196, 0.302)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                y_position = 480
                table.wrapOn(pdf, 50, y_position)
                table_height = table._height
                table.drawOn(pdf, 50, y_position - table_height)

                totals_y_position = y_position - table_height - 30
                if (totals_y_position < 50):
                    pdf.showPage()
                    totals_y_position = 750

                # Totales (basados en el total real con descuento aplicado)
                total = new_order.total_amount
                base_total = total / 1.21
                iva_calculado = total - base_total
                base_envio = new_order.shipping_cost / 1.21
                base_productos = base_total - base_envio

                # DEBUG - Verifica valores reales antes de escribir el PDF
                print("🧾 DEBUG FACTURA")
                print("Subtotal productos:", subtotal)
                print("Coste de envío:", shipping_cost)
                print("Descuento aplicado:", new_order.discount_value)
                print("Total final (con envío y descuento):", total)
                print("Base imponible total:", base_total)
                print("Base envío:", base_envio)
                print("Base productos:", base_productos)
                print("IVA calculado:", iva_calculado)

                # --- Bloque visual y contable optimizado ---
                pdf.setFont("Helvetica-Bold", 11)
                pdf.drawString(50, totals_y_position, "DETALLE FISCAL")
                pdf.setFont("Helvetica", 10)

                # Bloque de bases e IVA
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

                # Descuento comercial
                if new_order.discount_value and new_order.discount_value > 0:
                    pdf.setFont("Helvetica-Bold", 11)
                    pdf.setFillColor(colors.green)
                    pdf.drawString(50, totals_y_position - 100,
                                f"Descuento comercial ({discount_code or ''} {discount_percent:.0f}%): -{new_order.discount_value:.2f} €")
                    pdf.setFillColor(colors.black)

                pdf.line(50, totals_y_position - 105, 200, totals_y_position - 105)

                # Total final
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, totals_y_position - 120, f"TOTAL A PAGAR: {total:.2f} €")

                # Información adicional
                pdf.setFont("Helvetica", 10)
                if new_order.shipping_cost == 49:
                    envio_text = "Tarifa A (49 €)"
                elif shipping_cost == 99:
                    envio_text = "Tarifa B (99 €)"
                elif shipping_cost == 17:
                    envio_text = "Estándar (17 €)"
                else:
                    envio_text = "Gratuito"

                pdf.drawString(50, totals_y_position - 140, f"Tipo de envío: {envio_text}")
                if discount_code:
                    pdf.drawString(50, totals_y_position - 155, f"Código descuento: {discount_code}")


                # Guardar el PDF
                pdf.save()
                pdf_buffer.seek(0)
                with open(file_path, "wb") as f:
                    f.write(pdf_buffer.getvalue())

                # Guardar la factura
                new_invoice = Invoices(
                    invoice_number=invoice_number,
                    order_id=new_order.id,
                    pdf_path=pdf_path,
                    client_name=f"{customer_firstname or ''} {customer_lastname or ''}".strip(),
                    client_address=customer_billing_address or "",
                    client_cif=customer_cif or "",
                    client_phone=customer_phone or "",
                    amount=new_order.total_amount,
                    order_details=[detail.serialize() for detail in new_order.order_details]
                )
                db.session.add(new_invoice)
                new_order.invoice_number = invoice_number
                db.session.commit()

                # Enviar el correo con la factura
                email_sent = send_email(
                    subject=f"Factura de tu pedido #{invoice_number}",
                    recipients=[current_user['email'], current_app.config['MAIL_USERNAME']], # <--- current_app.config aquí
                    body=f"Hola {(customer_firstname or '').strip()} {(customer_lastname or '').strip()},\n\nAdjuntamos la factura {invoice_number} de tu compra.\n\nGracias por tu confianza.",
                    attachment_path=file_path
                )

                if not email_sent:
                    logger.error(f"Error al enviar el correo con la factura {invoice_number}.")
                else:
                    logger.info(f"Correo enviado correctamente con la factura {invoice_number}.")

                # Crear la respuesta con encabezados CORS
                response = jsonify({
                    "data": new_order.serialize(),
                    "message": "Order, details, and invoice created successfully."
                })
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
                return response, 201

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error al generar la factura: {str(e)}")
                return jsonify({"message": "An error occurred while generating the invoice.", "error": str(e)}), 500

        except ValueError as e:
            db.session.rollback()
            logger.error(f"Error validando checkout en /orders: {str(e)}")
            return jsonify({"message": str(e)}), 400

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error al crear la orden: {str(e)}")
            return jsonify({"message": "An error occurred while creating the order.", "error": str(e)}), 500

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error inesperado al cerrar la orden: {str(e)}")
            return jsonify({"message": "An unexpected error occurred while creating the order.", "error": str(e)}), 500


@api.route('/orders/<int:order_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def handle_order(order_id):
    current_user = get_jwt_identity()
    # 🔑 Admin puede ver cualquiera, usuarios solo los suyos
    if current_user.get("is_admin"):
        order = Orders.query.get(order_id)
    else:
        order = Orders.query.filter_by(id=order_id, user_id=current_user['user_id']).first()

    if not order:
        return jsonify({"message": "Order not found or not authorized"}), 404

    if request.method == 'GET':
        response = jsonify(order.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
        return response, 200

    if request.method == 'PUT':
        if not current_user.get("is_admin"):
            return jsonify({"message": "Access forbidden: Admins only"}), 403

        data = request.get_json() or {}

        if "order_status" in data:
            next_status = (data.get("order_status") or "").strip()
            order.order_status = next_status or "pendiente"

        if "estimated_delivery_at" in data:
            date_str = data.get("estimated_delivery_at")
            if date_str in ("", False, None):
                order.estimated_delivery_at = None
            else:
                try:
                    y, m, d = map(int, str(date_str).split("-"))
                    order.estimated_delivery_at = date(y, m, d)
                except Exception:
                    return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

        if "estimated_delivery_note" in data:
            order.estimated_delivery_note = data.get("estimated_delivery_note") or ""

        try:
            db.session.commit()
            response = jsonify(order.serialize())
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
            return response, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred while updating the order.", "error": str(e)}), 500

    if request.method == 'DELETE':
        if not current_user.get("is_admin"):
            return jsonify({"message": "Access forbidden: Admins only"}), 403

        try:
            db.session.delete(order)
            db.session.commit()
            response = jsonify({"message": "Order deleted successfully."})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
            return response, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred while deleting the order.", "error": str(e)}), 500

        
@api.route('/orders/<int:order_id>/estimated-delivery', methods=['GET'])
@jwt_required()
def get_estimated_delivery(order_id):
    current_user = get_jwt_identity()

    order = db.session.execute(
        db.select(Orders).where(Orders.id == order_id)
    ).scalar()

    if not order:
        return jsonify({"message": "Order not found"}), 404

    # Autorización
    if not (current_user.get("is_admin") or order.user_id == current_user['user_id']):
        return jsonify({"message": "Not authorized"}), 403

    return jsonify({
        "order_id": order.id,
        "estimated_delivery_at": order.estimated_delivery_at.isoformat() if order.estimated_delivery_at else None,
        "estimated_delivery_note": order.estimated_delivery_note
    }), 200


@api.route('/orders/<int:order_id>/estimated-delivery', methods=['PATCH'])
@jwt_required()
def set_estimated_delivery(order_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    order = db.session.execute(
        db.select(Orders).where(Orders.id == order_id)
    ).scalar()

    if not order:
        return jsonify({"message": "Order not found"}), 404

    data = request.get_json() or {}
    date_str = data.get("estimated_delivery_at")  # "YYYY-MM-DD" o None
    note = data.get("estimated_delivery_note")    # str o None

    # Fecha: setear o limpiar
    if date_str is not None:
        if date_str == "" or date_str is False:
            order.estimated_delivery_at = None
        else:
            try:
                y, m, d = map(int, date_str.split("-"))
                order.estimated_delivery_at = date(y, m, d)
            except Exception:
                return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Nota: setear o limpiar
    order.estimated_delivery_note = note if (note or note == "") else order.estimated_delivery_note

    db.session.commit()

    return jsonify({
        "message": "Estimated delivery updated",
        "order_id": order.id,
        "estimated_delivery_at": order.estimated_delivery_at.isoformat() if order.estimated_delivery_at else None,
        "estimated_delivery_note": order.estimated_delivery_note
    }), 200


@api.route('/orderdetails', methods=['POST'])
@jwt_required()
def add_order_details():
    data = request.get_json()  
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    try:
        added_details = []
        shipping_assigned = False 

        for detail in data:
            # Verifica si el detalle ya existe
            existing_detail = OrderDetails.query.filter_by(
                order_id=detail['order_id'],
                product_id=detail['product_id'],
                alto=detail.get('alto'),
                ancho=detail.get('ancho'),
                anclaje=detail.get('anclaje'),
                color=detail.get('color')
            ).first()
            if existing_detail:
                continue  # Saltar si ya existe

            prod = Products.query.get(detail['producto_id'])

            precio_recalculado = calcular_precio_reja(
                alto_cm=detail.get('alto'),
                ancho_cm=detail.get('ancho'),
                precio_m2=prod.precio_rebajado or prod.precio
            )

            # Recoger el coste de envío enviado desde el frontend
            shipping_cost = float(detail.get('shipping_cost') or 0)

            # Solo permitir que una línea reciba el coste de envío
            if shipping_assigned or shipping_cost == 0:
                shipping_cost = 0
            else:
                shipping_assigned = True

            new_detail = OrderDetails(
                order_id=detail['order_id'],
                product_id=detail['product_id'],
                quantity=detail['quantity'],
                alto=detail.get('alto'),
                ancho=detail.get('ancho'),
                anclaje=detail.get('anclaje'),
                color=detail.get('color'),
                precio_total=precio_recalculado,
                firstname=detail.get('firstname'),
                lastname=detail.get('lastname'),
                shipping_address=detail.get('shipping_address'),
                shipping_city=detail.get('shipping_city'),
                shipping_postal_code=detail.get('shipping_postal_code'),
                billing_address=detail.get('billing_address'),
                billing_city=detail.get('billing_city'),
                billing_postal_code=detail.get('billing_postal_code'),
                CIF=detail.get('CIF'),
                shipping_type=detail.get('shipping_type'),
                shipping_cost=shipping_cost
            )

            db.session.add(new_detail)
            added_details.append(new_detail)

        db.session.commit()
        return jsonify([detail.serialize() for detail in added_details]), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "message": "An error occurred while adding order details.",
            "error": str(e)
        }), 500


@api.route('/orderdetails', methods=['GET'])
@jwt_required()
def get_order_details():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    # 🔥 Parámetros de paginación y orden
    start = request.args.get('_start', type=int, default=0)
    end = request.args.get('_end', type=int, default=10)
    sort = request.args.get('_sort', default='id')
    order = request.args.get('_order', default='DESC').upper()

    # 🔥 Ordenar siempre por ID descendente por defecto
    if sort == 'id':
        order = 'DESC'

    sort_col = getattr(OrderDetails, sort, OrderDetails.id)

    query = OrderDetails.query.order_by(
        sort_col.desc() if order == 'DESC' else sort_col.asc()
    )

    total_count = query.count()

    # 🔥 Paginación
    if start is not None and end is not None and end > start:
        query = query.offset(start).limit(end - start)

    order_details = query.all()
    results = [detail.serialize() for detail in order_details]

    response = jsonify(results)
    response.headers['X-Total-Count'] = str(total_count)
    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200

@api.route('/orderdetails/<int:detail_id>', methods=['GET', 'DELETE'])
@jwt_required()
def handle_order_detail(detail_id):
    current_user = get_jwt_identity()

    # 🔑 Buscar detalle
    detail = OrderDetails.query.get(detail_id)
    if not detail:
        return jsonify({"message": "OrderDetail not found"}), 404

    # 🔒 Solo admin puede ver/borrar cualquier detalle
    if not current_user.get("is_admin"):
        # Comprobar que es suyo
        if not detail.order or detail.order.user_id != current_user['user_id']:
            return jsonify({"message": "Access forbidden"}), 403

    if request.method == 'GET':
        response = jsonify(detail.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
        return response, 200

    if request.method == 'DELETE':
        if not current_user.get("is_admin"):
            return jsonify({"message": "Access forbidden: Admins only"}), 403

        try:
            db.session.delete(detail)
            db.session.commit()
            return jsonify({"message": "OrderDetail deleted successfully"}), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred while deleting", "error": str(e)}), 500


# crear una factura sin una orden asociada
@api.route('/manual-invoice', methods=['POST'])
@jwt_required()
def create_manual_invoice():
    try:
        # Verificar que el usuario sea administrador
        current_user = get_jwt_identity()
        if not current_user.get("is_admin"):
            return jsonify({"message": "Unauthorized"}), 403

        # Recibir los datos del formulario
        data = request.get_json()
        client_name = data.get("client_name")
        client_address = data.get("client_address")
        client_cif = data.get("client_cif")
        order_details = data.get("order_details", [])

        # Validar los datos requeridos
        if not client_name or not client_address or not order_details:
            return jsonify({"message": "Missing required fields"}), 400

        # Calcular el monto total de los productos
        amount = sum(
            detail.get("quantity", 1) * detail.get("price", 0.0)
            for detail in order_details
        )

        # Generar número de factura único
        invoice_number = Invoices.generate_next_invoice_number()

        # Crear el archivo PDF
        pdf_filename = f"invoice_{invoice_number}.pdf"
        file_path = os.path.join(current_app.config['INVOICE_FOLDER'], pdf_filename)
        pdf_path = f"/api/download-invoice/{pdf_filename}"
        os.makedirs(current_app.config['INVOICE_FOLDER'], exist_ok=True)

        pdf_buffer = BytesIO()
        pdf = canvas.Canvas(pdf_buffer, pagesize=A4)

        # Encabezado: Logo e información del proveedor
        image_url = "https://res.cloudinary.com/dewanllxn/image/upload/v1740167674/logo_uxlqof.png"
        pdf.drawImage(image_url, 300, 750, width=250, height=64)
        pdf.setTitle(f"Factura_{invoice_number}")
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 800, f"Factura No: {invoice_number}")
        pdf.setFont("Helvetica", 10)
        fecha_emision = datetime.now().strftime("%d/%m/%Y")
        pdf.drawString(50, 780, f"Fecha: {fecha_emision}")

        # Información del proveedor
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(400, 700, "PROVEEDOR")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(400, 680, "Sergio Arias Fernández")
        pdf.drawString(400, 665, "DNI 05703874N")
        pdf.drawString(400, 650, "Francisco Fernández Ordoñez 32")
        pdf.drawString(400, 635, "13170 Miguelturra")

        # Información del cliente
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 700, "Cliente")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 680, client_name)
        pdf.drawString(50, 665, client_address)
        pdf.drawString(50, 650, f"CIF: {client_cif}")
        pdf.drawString(50, 635, f"{data.get('phone', 'No proporcionado')}")

        # Detalles del pedido (Tabla)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 580, "Detalles del Pedido")
        pdf.setFont("Helvetica", 10)
        data_table = [["Producto", "Cantidad", "Precio Unitario", "Total"]]
        for detail in order_details:
            row = [
                detail.get("product", "Producto desconocido"),
                detail.get("quantity", 1),
                f"{detail.get('price', 0.0):.2f} €",
                f"{detail.get('quantity', 1) * detail.get('price', 0.0):.2f} €"
            ]
            data_table.append(row)

        # Crear la tabla
        table = Table(data_table, colWidths=[6*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(1, 0.196, 0.302)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        # Renderizar la tabla y calcular su altura
        y_position = 540  # Posición inicial de la tabla
        table.wrapOn(pdf, 50, y_position)
        table_height = table._height
        table.drawOn(pdf, 50, y_position - table_height)

        # Totales debajo de la tabla
        totals_y_position = y_position - table_height - 30
        if totals_y_position < 50:  # Mover a nueva página si no hay espacio
            pdf.showPage()
            totals_y_position = 750

        iva = amount - (amount / 1.21)
        base_imponible = amount - iva

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, totals_y_position, f"Base Imponible: {base_imponible:.2f} €")
        pdf.drawString(50, totals_y_position - 20, f"IVA (21%): {iva:.2f} €")
        pdf.drawString(50, totals_y_position - 40, f"Total: {amount:.2f} €")

        # Guardar el archivo PDF
        pdf.save()
        pdf_buffer.seek(0)
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.getvalue())

        # Registrar la factura en la base de datos
        new_invoice = Invoices(
            invoice_number=invoice_number,
            pdf_path=pdf_path,
            client_name=client_name,
            client_address=client_address,
            client_cif=client_cif,
            client_phone=data.get("phone"),
            amount=amount,
            order_details=order_details
        )
        db.session.add(new_invoice)
        db.session.commit()

        return jsonify({"data": new_invoice.serialize()}), 201

    except Exception as e:
        current_app.logger.error(f"Error al crear la factura manual: {str(e)}")
        return jsonify({"message": "An error occurred while creating the manual invoice.", "error": str(e)}), 500

# Descarga un archivo PDF de factura generado previamente
@api.route('/download-invoice/<filename>', methods=['GET'])
@jwt_required()
def download_invoice(filename):
    current_user = get_jwt_identity()
    try:
        safe_filename = os.path.basename(filename)
        if safe_filename != filename:
            return jsonify({"message": "Invoice not found"}), 404

        invoice = Invoices.query.filter_by(
            pdf_path=f"/api/download-invoice/{safe_filename}"
        ).first()
        if not invoice:
            return jsonify({"message": "Invoice not found"}), 404

        if not current_user.get("is_admin"):
            if not invoice.order or invoice.order.user_id != current_user['user_id']:
                return jsonify({"message": "Invoice not found"}), 404

        file_path = os.path.join(current_app.config['INVOICE_FOLDER'], safe_filename)
        current_app.logger.info(f"Buscando archivo en: {file_path}")

        if not os.path.exists(file_path):
            current_app.logger.warning(
                "No se encontró el PDF físico para la factura %s en %s.",
                invoice.invoice_number,
                file_path
            )
            if current_user.get("is_admin"):
                current_app.logger.info(
                    "Regenerando en memoria la factura %s solo para descarga admin.",
                    invoice.invoice_number
                )
                regenerated_pdf = render_original_order_invoice_pdf(
                    **_build_original_invoice_render_kwargs(invoice)
                )
                return send_file(
                    BytesIO(regenerated_pdf),
                    as_attachment=True,
                    download_name=f"factura_{invoice.invoice_number}.pdf",
                    mimetype='application/pdf'
                )
            return jsonify({"message": "No se encontró el archivo PDF para esta factura."}), 404

        return send_file(file_path, as_attachment=True, download_name=safe_filename, mimetype='application/pdf')
    except Exception as e:
        current_app.logger.error(f"Error al descargar la factura: {str(e)}")
        return jsonify({"message": "An error occurred while downloading the invoice.", "error": str(e)}), 500

# Recupera todas las facturas con paginación
@api.route('/invoices/<int:invoice_id>/regenerate-pdf', methods=['POST'])
@jwt_required()
def regenerate_invoice_pdf(invoice_id):
    current_user = get_jwt_identity()

    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    try:
        invoice = Invoices.query.get(invoice_id)
        if not invoice:
            return jsonify({"message": "Invoice not found"}), 404

        if not invoice.order_id:
            return jsonify({
                "message": "Esta acción solo está disponible para facturas asociadas a pedidos."
            }), 400

        regeneration_result = _regenerate_invoice_pdf_to_storage(invoice)

        current_app.logger.info(
            "Factura %s regenerada manualmente por admin %s en %s",
            invoice.invoice_number,
            current_user.get("email"),
            regeneration_result["file_path"]
        )

        return jsonify({
            "message": "Factura regenerada correctamente.",
            "data": invoice.serialize_admin(),
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            "Error al regenerar manualmente la factura %s: %s",
            invoice_id,
            str(e)
        )
        return jsonify({
            "message": "No se pudo regenerar la factura.",
            "error": str(e)
        }), 500


def _serialize_invoice_for_user(invoice, current_user):
    if current_user.get("is_admin"):
        return invoice.serialize_admin()
    return invoice.serialize_summary()


@api.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    current_user = get_jwt_identity()
    try:
        # Parámetros de paginación
        start = int(request.args.get('_start', 0))
        end = int(request.args.get('_end', 10))
        sort = request.args.get('_sort', 'id')
        order = request.args.get('_order', 'DESC').upper()

        # Obtener el número total de facturas
        if current_user.get("is_admin"):
            query = Invoices.query
        else:
            query = Invoices.query.join(Orders, Invoices.order_id == Orders.id).filter(
                Orders.user_id == current_user['user_id']
            )

        sort_col = getattr(Invoices, sort, Invoices.id)
        if order not in ('ASC', 'DESC'):
            order = 'DESC'

        query = query.order_by(
            sort_col.desc() if order == 'DESC' else sort_col.asc()
        )

        total_count = query.count()

        # Obtener las facturas dentro del rango solicitado
        invoices = query.slice(start, end).all()

        # Crear la respuesta con los encabezados necesarios
        response = jsonify([
            _serialize_invoice_for_user(invoice, current_user) for invoice in invoices
        ])
        response.headers['X-Total-Count'] = total_count
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'

        return response, 200
    except Exception as e:
        return jsonify({"message": "Error retrieving invoices", "error": str(e)}), 500

# Recupera una factura específica por su ID
@api.route('/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice_by_id(invoice_id):
    current_user = get_jwt_identity()
    try:
        # Obtener la factura por ID
        if current_user.get("is_admin"):
            invoice = Invoices.query.get(invoice_id)
        else:
            invoice = Invoices.query.join(Orders, Invoices.order_id == Orders.id).filter(
                Invoices.id == invoice_id,
                Orders.user_id == current_user['user_id']
            ).first()
        if not invoice:
            return jsonify({"message": "Invoice not found"}), 404

        # Crear la respuesta
        response = jsonify(_serialize_invoice_for_user(invoice, current_user))
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'

        return response, 200
    except Exception as e:
        return jsonify({"message": "Error retrieving invoice", "error": str(e)}), 500


@api.route('/favorites', methods=['OPTIONS', 'GET', 'POST'])
@jwt_required(optional=True)  
def handle_favorites():
    if request.method == "OPTIONS":
        # Manejar el preflight de CORS
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        return response, 200
    current_user = get_jwt_identity()
    if request.method == 'GET':
        # Obtener todos los favoritos del usuario actual
        if not current_user:
            return jsonify({"message": "Debe estar autenticado para acceder a los favoritos"}), 401
        favorites = db.session.execute(db.select(Favorites).where(Favorites.usuario_id == current_user['user_id'])).scalars()
        products = [Products.query.get(fav.producto_id).serialize() for fav in favorites]
        response = jsonify(products)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200
    if request.method == 'POST':
        if not current_user:
            return jsonify({"message": "Debe estar autenticado para añadir a favoritos"}), 401
        data = request.get_json()
        product_id = data.get('product_id')
        # Verificar si el producto ya está en favoritos
        existing_favorite = db.session.execute(db.select(Favorites).where(Favorites.usuario_id == current_user['user_id'], Favorites.producto_id == product_id)).scalar()
        if existing_favorite:
            return jsonify({"message": "Producto ya está en favoritos"}), 409
        # Crear nuevo favorito
        new_favorite = Favorites(usuario_id=current_user['user_id'], producto_id=product_id)
        db.session.add(new_favorite)
        db.session.commit()
        response = jsonify({"message": "Producto añadido a favoritos"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 201


@api.route('/favorites/<int:product_id>', methods=['OPTIONS', 'DELETE'])
@jwt_required(optional=True)
def remove_favorite(product_id):
    if request.method == "OPTIONS":
        # Manejar el preflight de CORS
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "DELETE, OPTIONS")
        return response, 200
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"message": "Debe estar autenticado para eliminar de favoritos"}), 401
    favorite = db.session.execute(db.select(Favorites).where(Favorites.usuario_id == current_user['user_id'], Favorites.producto_id == product_id)).scalar()
    if not favorite:
        return jsonify({"message": "Producto no encontrado en favoritos"}), 404
    db.session.delete(favorite)
    db.session.commit()
    response = jsonify({"message": "Producto eliminado de favoritos"})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200


@api.route('/cart', methods=['OPTIONS', 'GET', 'POST'])
@jwt_required()
def handle_cart():
    if request.method == "OPTIONS":
        # Manejar el preflight de CORS
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        return response, 200
    current_user = get_jwt_identity()
    if request.method == 'GET':
        # Obtener los productos en el carrito del usuario actual
        try:
            cart_items = Cart.query.filter_by(usuario_id=current_user['user_id']).all()
            products = [item.serialize() for item in cart_items]  # Ahora devuelve la información completa del producto

            response = jsonify(products)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 200
        except Exception as e:
            response = jsonify({"message": str(e)})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 500
    if request.method == 'POST':
        data = request.get_json()
        product_id = data.get('product_id')

        if not product_id:
            return jsonify({"message": "Product ID is required"}), 400

        try:
            new_cart_item = Cart(
                usuario_id=current_user['user_id'],
                producto_id=product_id,
                alto=data.get('alto'),
                ancho=data.get('ancho'),
                anclaje=data.get('anclaje'),
                color=data.get('color'),
                precio_total=data.get('precio_total'),
                quantity=data.get('quantity', 1),
                added_at=datetime.now(timezone.utc)
            )

            db.session.add(new_cart_item)
            db.session.commit()

            # 🔥 DEVOLVER CARRITO ACTUALIZADO
            updated_cart_items = Cart.query.filter_by(
                usuario_id=current_user['user_id']
            ).all()

            updated_cart = [item.serialize() for item in updated_cart_items]

            return jsonify(updated_cart), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"message": str(e)}), 500


@api.route('/cart/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(product_id):
    current_user = get_jwt_identity()
    data = request.get_json()

    try:
        cart_item = Cart.query.filter_by(
            usuario_id=current_user['user_id'],
            producto_id=product_id,
            alto=data.get('alto'),
            ancho=data.get('ancho'),
            anclaje=data.get('anclaje'),
            color=data.get('color')
        ).first()

        if not cart_item:
            response = jsonify({"message": "Producto no encontrado en el carrito con esas especificaciones"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 404

        cart_item.quantity = data.get('quantity', cart_item.quantity)
        db.session.commit()

        updated_cart_items = Cart.query.filter_by(usuario_id=current_user['user_id']).all()
        updated_cart = [item.serialize() for item in updated_cart_items]

        response = jsonify(updated_cart)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200

    except Exception as e:
        db.session.rollback()
        response = jsonify({"message": f"Error al actualizar el carrito: {str(e)}"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 500


@api.route('/cart/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(product_id):
    current_user = get_jwt_identity()
    try:
        data = request.get_json()  # Obtener las especificaciones del producto
        cart_item = Cart.query.filter_by(
            usuario_id=current_user['user_id'],
            producto_id=product_id,
            alto=data.get('alto'),
            ancho=data.get('ancho'),
            anclaje=data.get('anclaje'),
            color=data.get('color')
        ).first()
        if not cart_item:
            return jsonify({"message": "Producto no encontrado en el carrito con esas especificaciones"}), 404
        db.session.delete(cart_item)
        db.session.commit()
        # Obtener el carrito actualizado
        updated_cart_items = Cart.query.filter_by(usuario_id=current_user['user_id']).all()
        updated_cart = [item.serialize() for item in updated_cart_items]
        return jsonify({"message": "Producto eliminado del carrito", "updated_cart": updated_cart}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


@api.route('/cart/clear', methods=['POST'])
@jwt_required()
def clear_cart():
    current_user = get_jwt_identity()
    try:
        Cart.query.filter_by(usuario_id=current_user['user_id']).delete()
        db.session.commit()
        return jsonify({"message": "Carrito vaciado con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error al vaciar el carrito: {str(e)}"}), 500


@api.route('/admin/cart-reminders/<int:user_id>/send', methods=['POST'])
@jwt_required()
def send_cart_reminder(user_id):
    current_user = get_jwt_identity()

    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    try:
        target_user = Users.query.get(user_id)
        if not target_user:
            return jsonify({"message": "Usuario no encontrado"}), 404

        if not target_user.email:
            return jsonify({"message": "El usuario no tiene email registrado"}), 400

        cart_items = (
            Cart.query
            .filter_by(usuario_id=user_id)
            .order_by(Cart.added_at.desc())
            .all()
        )

        if not cart_items:
            return jsonify({"message": "El usuario no tiene productos en el carrito"}), 400

        latest_cart_added_at = next((item.added_at for item in cart_items if item.added_at), None)
        if latest_cart_added_at:
            later_order = (
                Orders.query
                .filter(
                    Orders.user_id == user_id,
                    Orders.order_date > latest_cart_added_at
                )
                .order_by(Orders.order_date.desc())
                .first()
            )

            if later_order:
                return jsonify({
                    "message": "El usuario ya tiene un pedido posterior al último movimiento del carrito. No se ha enviado el recordatorio.",
                    "order_id": later_order.id,
                    "locator": later_order.locator,
                    "order_date": later_order.order_date.isoformat() if later_order.order_date else None
                }), 409

        frontend_base_url = (current_app.config.get("FRONTEND_URL") or "https://www.metalwolft.com").rstrip("/")
        cart_url = f"{frontend_base_url}/cart"
        email_payload = _build_cart_reminder_email_payload(target_user, cart_items, cart_url)

        email_sent = send_email(
            subject=email_payload["subject"],
            recipients=[target_user.email],
            body=email_payload["body"],
            html=email_payload["html"]
        )

        if not email_sent:
            current_app.logger.error(
                "No se pudo enviar el recordatorio manual de carrito al usuario %s (%s)",
                target_user.id,
                target_user.email
            )
            return jsonify({"message": "No se pudo enviar el recordatorio del carrito"}), 500

        current_app.logger.info(
            "Recordatorio manual de carrito enviado por admin %s al usuario %s (%s) con %s líneas",
            current_user.get("email"),
            target_user.id,
            target_user.email,
            len(cart_items)
        )

        return jsonify({
            "message": "Recordatorio de carrito enviado correctamente.",
            "data": {
                "user_id": target_user.id,
                "email": target_user.email,
                "line_count": len(cart_items),
                "latest_cart_added_at": latest_cart_added_at.isoformat() if latest_cart_added_at else None
            }
        }), 200
    except Exception as e:
        current_app.logger.error(
            "Error al enviar recordatorio manual de carrito al usuario %s: %s",
            user_id,
            str(e)
        )
        return jsonify({
            "message": "No se pudo enviar el recordatorio del carrito.",
            "error": str(e)
        }), 500


@api.route('/me', methods=["GET"])
@jwt_required()
def get_me():
    identity = get_jwt_identity()
    user_id = identity.get("user_id")

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "email": user.email,  # solo lectura
        "firstname": user.firstname,
        "lastname": user.lastname,
        "shipping_address": user.shipping_address,
        "shipping_city": user.shipping_city,
        "shipping_postal_code": user.shipping_postal_code,
        "billing_address": user.billing_address,
        "billing_city": user.billing_city,
        "billing_postal_code": user.billing_postal_code,
        "CIF": user.CIF,
    }), 200


@api.route('/me', methods=["PUT"])
@jwt_required()
def update_me():
    identity = get_jwt_identity()
    user_id = identity.get("user_id")

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.json or {}

    # 1. Cambio de contraseña usando BCRYPT
    if "password" in data and data["password"].strip() != "":
        # Generamos el salt y el hash con bcrypt
        salt = bcrypt.gensalt()
        # IMPORTANTE: bcrypt necesita bytes, por eso usamos .encode('utf-8')
        hashed_password = bcrypt.hashpw(data["password"].encode('utf-8'), salt)
        # Guardamos el hash decodificado como string en la base de datos
        user.password = hashed_password.decode('utf-8')

    # 2. Whitelist de campos (lo que ya tenías)
    editable_fields = [
        "firstname", "lastname", "shipping_address", 
        "shipping_city", "shipping_postal_code", 
        "billing_address", "billing_city", 
        "billing_postal_code", "CIF"
    ]

    for field in editable_fields:
        if field in data:
            setattr(user, field, data[field])

    try:
        db.session.commit()
        return jsonify({"message": "Profile updated"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error en el servidor: {str(e)}") # Esto te dirá el error real en la terminal
        return jsonify({"message": "Error interno", "error": str(e)}), 500

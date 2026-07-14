from dataclasses import dataclass
import os
from typing import Callable, Mapping, Sequence

from api.models import Invoices, Products
from api.original_invoice_renderer import render_original_order_invoice_pdf


@dataclass
class IssuedInvoiceResult:
    invoice: Invoices
    invoice_number: str
    pdf_path: str
    pdf_filename: str
    file_path: str


def _line_product_id(detail):
    product_id = detail.get("producto_id")
    if product_id is None:
        product_id = detail.get("product_id")
    return product_id


def _prepare_invoice_order_details(order_details: Sequence[Mapping]):
    prepared_details = []

    for detail in order_details:
        prepared_detail = dict(detail)
        product_id = _line_product_id(prepared_detail)
        product = Products.query.get(product_id) if product_id is not None else None
        prepared_detail["product_name"] = product.nombre if product else "Desconocido"
        prepared_details.append(prepared_detail)

    return prepared_details


def issue_invoice_for_order(
    *,
    order,
    order_details,
    customer_context,
    checkout_quote,
    invoice_folder,
    db_session,
    renderer: Callable[..., bytes] = render_original_order_invoice_pdf,
):
    invoice_number = Invoices.generate_next_invoice_number()
    pdf_filename = f"invoice_{invoice_number}.pdf"
    file_path = os.path.join(invoice_folder, pdf_filename)
    pdf_path = f"/api/download-invoice/{pdf_filename}"
    os.makedirs(invoice_folder, exist_ok=True)

    prepared_order_details = _prepare_invoice_order_details(order_details)

    pdf_bytes = renderer(
        invoice_number=invoice_number,
        customer_firstname=customer_context["firstname"],
        customer_lastname=customer_context["lastname"],
        customer_phone=customer_context["phone"],
        customer_billing_address=customer_context["billing_address"],
        customer_billing_city=customer_context["billing_city"],
        customer_billing_postal_code=customer_context["billing_postal_code"],
        customer_cif=customer_context["CIF"],
        customer_shipping_address=customer_context["shipping_address"],
        customer_shipping_city=customer_context["shipping_city"],
        customer_shipping_postal_code=customer_context["shipping_postal_code"],
        order_details=prepared_order_details,
        total_amount=order.total_amount,
        shipping_cost=order.shipping_cost,
        discount_value=order.discount_value,
        discount_code=order.discount_code,
        discount_percent=float(checkout_quote.get("discount_percent") or 0.0),
    )

    with open(file_path, "wb") as pdf_file:
        pdf_file.write(pdf_bytes)

    invoice = Invoices(
        invoice_number=invoice_number,
        order_id=order.id,
        pdf_path=pdf_path,
        client_name=f"{customer_context['firstname'] or ''} {customer_context['lastname'] or ''}".strip(),
        client_address=customer_context["billing_address"] or "",
        client_cif=customer_context["CIF"] or "",
        client_phone=customer_context["phone"] or "",
        amount=order.total_amount,
        order_details=[detail.serialize() for detail in order.order_details],
    )
    db_session.add(invoice)
    order.invoice_number = invoice_number

    return IssuedInvoiceResult(
        invoice=invoice,
        invoice_number=invoice_number,
        pdf_path=pdf_path,
        pdf_filename=pdf_filename,
        file_path=file_path,
    )

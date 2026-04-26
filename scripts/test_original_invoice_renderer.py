"""
Script manual para comparar el renderer aislado de factura original
contra una factura real existente en BD.

Uso:
  python scripts/test_original_invoice_renderer.py --invoice-id 123
  python scripts/test_original_invoice_renderer.py --invoice-number NOV2025001

Qué hace:
- Carga una factura real desde la BD.
- Construye el payload esperado por `render_original_order_invoice_pdf(...)`.
- Genera un PDF nuevo en `tmp/invoice_renderer_test/`.
- No modifica rutas, no envía emails, no escribe en la carpeta real de facturas,
  y no sobrescribe el PDF original.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from src.app import app  # noqa: E402
from api.models import Invoices, Products  # noqa: E402
from api.original_invoice_renderer import render_original_order_invoice_pdf  # noqa: E402


def _split_client_name(full_name: str | None) -> tuple[str, str]:
    normalized = (full_name or "").strip()
    if not normalized:
        return "", ""

    parts = normalized.split()
    if len(parts) == 1:
        return parts[0], ""

    return parts[0], " ".join(parts[1:])


def _display_product_name(detail: dict[str, Any]) -> str:
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


def _build_renderer_order_details(invoice: Invoices) -> list[dict[str, Any]]:
    raw_details = invoice.order_details if isinstance(invoice.order_details, list) else []
    prepared: list[dict[str, Any]] = []

    for detail in raw_details:
        if not isinstance(detail, dict):
            continue

        normalized = dict(detail)
        normalized["product_name"] = _display_product_name(detail)
        prepared.append(normalized)

    return prepared


def _resolve_original_pdf_path(invoice: Invoices) -> Path | None:
    if not invoice.pdf_path:
        return None

    filename = Path(str(invoice.pdf_path)).name
    if not filename:
        return None

    return Path(app.config["INVOICE_FOLDER"]) / filename


def _load_invoice(invoice_id: int | None, invoice_number: str | None) -> Invoices | None:
    if invoice_id is not None:
        return Invoices.query.get(invoice_id)

    if invoice_number:
        return Invoices.query.filter_by(invoice_number=invoice_number).first()

    return None


def _resolve_discount_percent(invoice: Invoices) -> float:
    if not invoice.order or not getattr(invoice.order, "checkout_session", None):
        return 0.0

    quote_snapshot = getattr(invoice.order.checkout_session, "quote_snapshot", None) or {}
    try:
        return float(quote_snapshot.get("discount_percent") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un PDF manual de prueba usando render_original_order_invoice_pdf.")
    parser.add_argument("--invoice-id", type=int, help="ID de la factura en la BD.")
    parser.add_argument("--invoice-number", help="Número de factura en la BD.")
    args = parser.parse_args()

    if args.invoice_id is None and not args.invoice_number:
        parser.error("Debes indicar --invoice-id o --invoice-number.")

    with app.app_context():
        invoice = _load_invoice(args.invoice_id, args.invoice_number)
        if not invoice:
            print("Factura no encontrada.")
            return 1

        original_pdf_path = _resolve_original_pdf_path(invoice)
        prepared_order_details = _build_renderer_order_details(invoice)
        firstname, lastname = _split_client_name(invoice.client_name)

        shipping_cost = 0.0
        if invoice.order and invoice.order.shipping_cost is not None:
            shipping_cost = float(invoice.order.shipping_cost or 0.0)
        elif prepared_order_details:
            shipping_cost = float(prepared_order_details[0].get("shipping_cost") or 0.0)

        first_detail = prepared_order_details[0] if prepared_order_details else {}
        discount_percent = _resolve_discount_percent(invoice)

        pdf_bytes = render_original_order_invoice_pdf(
            invoice_number=invoice.invoice_number,
            customer_firstname=firstname,
            customer_lastname=lastname,
            customer_phone=invoice.client_phone or "",
            customer_billing_address=invoice.client_address or first_detail.get("billing_address") or "",
            customer_billing_city=first_detail.get("billing_city") or "",
            customer_billing_postal_code=first_detail.get("billing_postal_code") or "",
            customer_cif=invoice.client_cif or "",
            customer_shipping_address=first_detail.get("shipping_address") or "",
            customer_shipping_city=first_detail.get("shipping_city") or "",
            customer_shipping_postal_code=first_detail.get("shipping_postal_code") or "",
            order_details=prepared_order_details,
            total_amount=float(invoice.amount or 0.0),
            shipping_cost=shipping_cost,
            discount_value=float(invoice.order.discount_value or 0.0) if invoice.order else 0.0,
            discount_code=invoice.order.discount_code if invoice.order else None,
            discount_percent=discount_percent,
            issue_date=invoice.created_at,
        )

        output_dir = REPO_ROOT / "tmp" / "invoice_renderer_test"
        output_dir.mkdir(parents=True, exist_ok=True)

        identifier = invoice.invoice_number or f"id-{invoice.id}"
        output_path = output_dir / f"test_render_{identifier}.pdf"
        output_path.write_bytes(pdf_bytes)

        print(f"invoice_number: {invoice.invoice_number}")
        print(f"original_pdf_path: {original_pdf_path if original_pdf_path else 'N/A'}")
        print(f"original_pdf_exists: {bool(original_pdf_path and original_pdf_path.exists())}")
        print(f"generated_pdf_path: {output_path}")
        print(f"total: {float(invoice.amount or 0.0):.2f} EUR")
        print(f"line_count: {len(prepared_order_details)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

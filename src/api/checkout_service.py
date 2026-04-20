from api.models import Products
from api.utils import calcular_precio_reja


DISCOUNT_CODES = {
    "BIENVENIDO": 5,
    "REJAS10": 10,
    "WOLFT15": 15,
    "SERGIO99": 99,
}

SHIPPING_THRESHOLD = 150.0
STANDARD_SHIPPING_COST = 17.0
SPECIAL_SHIPPING_A_COST = 49.0
SPECIAL_SHIPPING_B_COST = 99.0


def _to_float(value, field_name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Valor inválido para {field_name}")


def _to_optional_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_product_id(item):
    product_id = item.get("producto_id")
    if product_id is None:
        product_id = item.get("product_id")
    if product_id is None:
        raise ValueError("Cada línea debe incluir producto_id o product_id")
    return int(product_id)


def _normalize_quantity(item):
    quantity = item.get("quantity", 1)
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValueError("Cantidad inválida")

    if quantity < 1:
        raise ValueError("La cantidad debe ser al menos 1")

    return quantity


def _calculate_shipping_type(alto, ancho):
    largo = max(alto, ancho)
    profundidad = 4
    peso = 10
    suma_dimensiones = largo + min(alto, ancho) + profundidad

    if peso > 60 or largo > 300 or suma_dimensiones > 500:
        return "B", SPECIAL_SHIPPING_B_COST

    if peso > 40 or largo > 175 or suma_dimensiones > 300 or largo >= 315:
        return "A", SPECIAL_SHIPPING_A_COST

    return "normal", 0.0


def _build_line(item):
    product_id = _normalize_product_id(item)
    quantity = _normalize_quantity(item)
    alto = _to_float(item.get("alto"), "alto")
    ancho = _to_float(item.get("ancho"), "ancho")

    product = Products.query.get(product_id)
    if not product:
        raise ValueError(f"Producto con ID {product_id} no encontrado")

    unit_price = calcular_precio_reja(
        alto_cm=alto,
        ancho_cm=ancho,
        precio_m2=product.precio_rebajado or product.precio
    )
    shipping_type, shipping_cost = _calculate_shipping_type(alto, ancho)
    frontend_unit_price = _to_optional_float(item.get("precio_total"))

    line = {
        "product_id": product_id,
        "producto_id": product_id,
        "product_name": product.nombre,
        "quantity": quantity,
        "alto": alto,
        "ancho": ancho,
        "anclaje": item.get("anclaje"),
        "color": item.get("color"),
        "unit_price": round(unit_price, 2),
        "line_total": round(unit_price * quantity, 2),
        "shipping_type": shipping_type,
        "shipping_cost": float(shipping_cost),
        "frontend_unit_price": frontend_unit_price,
    }

    if frontend_unit_price is not None:
        line["price_difference"] = round(frontend_unit_price - line["unit_price"], 2)
    else:
        line["price_difference"] = None

    return line


def _calculate_global_shipping(lines, subtotal):
    if not lines:
        return 0.0

    has_type_b = any(line["shipping_type"] == "B" for line in lines)
    has_type_a = any(line["shipping_type"] == "A" for line in lines)

    if has_type_b:
        return SPECIAL_SHIPPING_B_COST
    if has_type_a:
        return SPECIAL_SHIPPING_A_COST
    if subtotal >= SHIPPING_THRESHOLD:
        return 0.0
    return STANDARD_SHIPPING_COST


def _normalize_discount(discount_code, requested_discount_percent):
    requested_code = (discount_code or "").strip().upper() or None
    applied_percent = DISCOUNT_CODES.get(requested_code, 0)
    return {
        "requested_code": requested_code,
        "applied_code": requested_code if applied_percent else None,
        "is_valid": bool(requested_code and applied_percent),
        "requested_percent": _to_optional_float(requested_discount_percent) or 0.0,
        "applied_percent": float(applied_percent),
    }


def build_checkout_quote(
    raw_products,
    discount_code=None,
    requested_discount_percent=0,
    frontend_total=None,
    frontend_shipping_cost=None
):
    lines = [_build_line(item) for item in (raw_products or [])]
    subtotal = round(sum(line["line_total"] for line in lines), 2)
    shipping_cost = round(_calculate_global_shipping(lines, subtotal), 2)

    discount = _normalize_discount(discount_code, requested_discount_percent)
    gross_total = round(subtotal + shipping_cost, 2)
    discount_amount = round(gross_total * (discount["applied_percent"] / 100), 2)
    total_amount = round(gross_total - discount_amount, 2)

    frontend_total_value = _to_optional_float(frontend_total)
    frontend_shipping_value = _to_optional_float(frontend_shipping_cost)
    total_difference = None
    shipping_difference = None

    if frontend_total_value is not None:
        total_difference = round(frontend_total_value - total_amount, 2)

    if frontend_shipping_value is not None:
        shipping_difference = round(frontend_shipping_value - shipping_cost, 2)

    line_differences = [
        {
            "product_id": line["product_id"],
            "frontend_unit_price": line["frontend_unit_price"],
            "backend_unit_price": line["unit_price"],
            "difference": line["price_difference"],
        }
        for line in lines
        if line["price_difference"] is not None and abs(line["price_difference"]) >= 0.01
    ]

    comparison = {
        "frontend_total": frontend_total_value,
        "backend_total": total_amount,
        "total_difference": total_difference,
        "frontend_shipping_cost": frontend_shipping_value,
        "backend_shipping_cost": shipping_cost,
        "shipping_difference": shipping_difference,
        "frontend_discount_code": discount["requested_code"],
        "backend_discount_code": discount["applied_code"],
        "frontend_discount_percent": discount["requested_percent"],
        "backend_discount_percent": discount["applied_percent"],
        "line_differences": line_differences,
    }
    comparison["has_difference"] = any([
        total_difference is not None and abs(total_difference) >= 0.01,
        shipping_difference is not None and abs(shipping_difference) >= 0.01,
        abs(discount["requested_percent"] - discount["applied_percent"]) >= 0.01,
        discount["requested_code"] != discount["applied_code"],
        bool(line_differences),
    ])

    return {
        "lines": lines,
        "subtotal": subtotal,
        "shipping_cost": shipping_cost,
        "discount_code": discount["applied_code"],
        "discount_code_valid": discount["is_valid"],
        "discount_percent": discount["applied_percent"],
        "discount_amount": discount_amount,
        "total_amount": total_amount,
        "comparison": comparison,
    }

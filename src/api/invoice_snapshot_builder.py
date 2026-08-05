from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_UP


SNAPSHOT_SCHEMA_VERSION = 1
SNAPSHOT_GENERATOR = "invoice_snapshot_builder_v1"
SUPPORTED_CURRENCY = "EUR"
SUPPORTED_TAX_RATE = Decimal("21.00")
FINAL_CHECKOUT_STATUSES = {"paid", "order_created"}


class InvoiceSnapshotValidationError(ValueError):
    """Raised when an order cannot produce a valid fiscal snapshot."""

    def __init__(self, field, message):
        self.field = field
        super().__init__(f"{field}: {message}")


def build_invoice_snapshot(
    order,
    checkout_session,
    issuer,
    *,
    issue_date,
    source="manual",
    actor=None,
):
    """Build an immutable fiscal snapshot from an already-created order.

    This builder is intentionally pure: it reads the provided objects only and
    does not query, persist, commit, call payment SDKs, or generate documents.
    A full discount can leave all lines at zero without producing negatives;
    the future issuing service must still decide whether zero-total orders are
    eligible for fiscal invoice issuance.
    """
    if order is None:
        raise InvoiceSnapshotValidationError("order", "El pedido es obligatorio.")
    if checkout_session is None:
        raise InvoiceSnapshotValidationError("checkout_session", "La sesion de checkout es obligatoria.")

    quote = _copy_mapping(_getattr(checkout_session, "quote_snapshot"), "quote_snapshot")
    customer_snapshot = _copy_mapping(
        _getattr(checkout_session, "customer_snapshot"),
        "customer_snapshot",
    )
    issuer_snapshot = _normalize_issuer(issuer)
    customer = _normalize_customer(customer_snapshot, order, checkout_session)
    _validate_checkout_link(order, checkout_session)

    currency = _extract_currency(quote, checkout_session)
    if currency != SUPPORTED_CURRENCY:
        raise InvoiceSnapshotValidationError("operation.currency", "Moneda no soportada.")

    lines, totals = _build_lines_and_totals(quote)

    order_date = _date_string(_getattr(order, "order_date"), "operation.order_date")
    issue_date_value = _date_string(issue_date, "operation.issue_date")

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "metadata": {
            "generator": SNAPSHOT_GENERATOR,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "issuer": issuer_snapshot,
        "customer": customer,
        "operation": {
            "invoice_type": "ordinary",
            "issue_date": issue_date_value,
            "operation_date": order_date,
            "currency": currency,
            "order_id": _get_required(order, "id", "operation.order_id"),
            "order_locator": _getattr(order, "locator"),
            "order_date": order_date,
            "discount_code": quote.get("discount_code"),
        },
        "lines": lines,
        "totals": totals,
        "payment": _normalize_payment(checkout_session),
        "references": {
            "checkout_session_id": _get_required(
                checkout_session,
                "id",
                "references.checkout_session_id",
            ),
            "order_id": _get_required(order, "id", "references.order_id"),
            "source": source,
            "actor": _serialize_actor(actor),
        },
    }


def _copy_mapping(value, field):
    if not isinstance(value, dict):
        raise InvoiceSnapshotValidationError(field, "Debe existir y ser un diccionario.")
    return deepcopy(value)


def _getattr(obj, name, default=None):
    return getattr(obj, name, default)


def _get_required(obj, name, field):
    value = _getattr(obj, name)
    if value is None or value == "":
        raise InvoiceSnapshotValidationError(field, "Campo obligatorio ausente.")
    return value


def _require_mapping_value(mapping, key, field):
    value = mapping.get(key)
    if value is None or value == "":
        raise InvoiceSnapshotValidationError(field, "Campo obligatorio ausente.")
    return value


def _to_decimal(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise InvoiceSnapshotValidationError(field, "Importe no numerico.")
    if not amount.is_finite():
        raise InvoiceSnapshotValidationError(field, "Importe no numerico.")
    return amount


def _quantize_money(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _money(value, field):
    return f"{_quantize_money(_to_decimal(value, field)):.2f}"


def _quantity_string(value, field):
    quantity = _to_decimal(value, field)
    if quantity <= 0:
        raise InvoiceSnapshotValidationError(field, "La cantidad debe ser mayor que cero.")
    normalized = quantity.normalize()
    if normalized == normalized.to_integral():
        return str(int(normalized))
    return format(normalized, "f")


def _tax_from_gross(gross_amount):
    gross = _quantize_money(gross_amount)
    tax_base = _quantize_money(gross / Decimal("1.21"))
    tax_amount = _quantize_money(gross - tax_base)
    return tax_base, tax_amount


def _date_string(value, field):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            raise InvoiceSnapshotValidationError(field, "Fecha invalida.")
    raise InvoiceSnapshotValidationError(field, "Fecha obligatoria ausente.")


def _normalize_issuer(issuer):
    if not isinstance(issuer, dict):
        raise InvoiceSnapshotValidationError("issuer", "El emisor debe ser un diccionario.")

    required = {
        "legal_name": "issuer.legal_name",
        "tax_id": "issuer.tax_id",
        "address": "issuer.address",
        "postal_code": "issuer.postal_code",
        "city": "issuer.city",
        "country_code": "issuer.country_code",
    }
    for key, field in required.items():
        _require_mapping_value(issuer, key, field)

    return {
        "legal_name": issuer.get("legal_name"),
        "trade_name": issuer.get("trade_name"),
        "tax_id": issuer.get("tax_id"),
        "address": issuer.get("address"),
        "postal_code": issuer.get("postal_code"),
        "city": issuer.get("city"),
        "province": issuer.get("province"),
        "country_code": issuer.get("country_code"),
        "email": issuer.get("email"),
        "phone": issuer.get("phone"),
    }


def _normalize_customer(customer_snapshot, order, checkout_session):
    firstname = customer_snapshot.get("firstname")
    lastname = customer_snapshot.get("lastname")
    legal_name = customer_snapshot.get("legal_name") or " ".join(
        part for part in (firstname, lastname) if part
    ).strip()

    address = customer_snapshot.get("billing_address") or customer_snapshot.get("shipping_address")
    city = customer_snapshot.get("billing_city") or customer_snapshot.get("shipping_city")
    postal_code = (
        customer_snapshot.get("billing_postal_code")
        or customer_snapshot.get("shipping_postal_code")
    )
    if customer_snapshot.get("billing_address"):
        province = customer_snapshot.get("billing_province") or customer_snapshot.get("province")
        country_code = (
            customer_snapshot.get("billing_country_code")
            or customer_snapshot.get("country_code")
            or "ES"
        )
    else:
        province = customer_snapshot.get("shipping_province") or customer_snapshot.get("province")
        country_code = (
            customer_snapshot.get("shipping_country_code")
            or customer_snapshot.get("country_code")
            or "ES"
        )
    email = (
        customer_snapshot.get("email")
        or _nested_attr(order, "user", "email")
        or _nested_attr(checkout_session, "user", "email")
    )
    tax_id = customer_snapshot.get("tax_id") or customer_snapshot.get("CIF")
    if isinstance(tax_id, str):
        tax_id = tax_id.strip().upper() or None

    customer = {
        "legal_name": legal_name or None,
        "tax_id": tax_id,
        "address": address,
        "postal_code": postal_code,
        "city": city,
        "province": province,
        "country_code": country_code,
        "email": email,
        "phone": customer_snapshot.get("phone"),
    }

    required = {
        "legal_name": "customer.legal_name",
        "tax_id": "customer.tax_id",
        "address": "customer.address",
        "postal_code": "customer.postal_code",
        "city": "customer.city",
        "email": "customer.email",
    }
    for key, field in required.items():
        if not customer.get(key):
            raise InvoiceSnapshotValidationError(field, "Campo obligatorio ausente.")

    return customer


def _nested_attr(obj, parent, child):
    nested = _getattr(obj, parent)
    if nested is None:
        return None
    return _getattr(nested, child)


def _validate_checkout_link(order, checkout_session):
    order_id = _get_required(order, "id", "order.id")
    checkout_order_id = _get_required(checkout_session, "order_id", "checkout_session.order_id")
    if checkout_order_id != order_id:
        raise InvoiceSnapshotValidationError(
            "checkout_session.order_id",
            "La sesion no pertenece al pedido.",
        )

    status = _get_required(checkout_session, "status", "checkout_session.status")
    if status not in FINAL_CHECKOUT_STATUSES:
        raise InvoiceSnapshotValidationError(
            "checkout_session.status",
            "La sesion no esta finalizada ni pagada.",
        )


def _extract_currency(quote, checkout_session):
    currency = (
        quote.get("currency")
        or _getattr(checkout_session, "currency")
        or SUPPORTED_CURRENCY
    )
    return str(currency).upper()


def _build_lines_and_totals(quote):
    lines_before_discount = _build_lines_before_discount(quote)
    totals = _build_totals(quote, lines_before_discount)
    discounts = _allocate_discount(lines_before_discount, _to_decimal(totals["discount_amount"], "totals.discount_amount"))
    lines = [
        _finalize_line(line, discount)
        for line, discount in zip(lines_before_discount, discounts)
    ]
    totals = _finalize_totals(totals, lines)
    return lines, totals


def _build_lines_before_discount(quote):
    source_lines = quote.get("lines")
    if not source_lines:
        raise InvoiceSnapshotValidationError("lines", "No hay lineas facturables.")

    lines = []
    products_total = Decimal("0.00")
    for index, source_line in enumerate(source_lines, start=1):
        if not isinstance(source_line, dict):
            raise InvoiceSnapshotValidationError(f"lines.{index}", "Linea invalida.")
        line = _build_product_line(index, source_line)
        products_total += line["line_amount_before_discount"]
        lines.append(line)

    shipping_total = _to_decimal(quote.get("shipping_cost", 0), "totals.shipping_total")
    if shipping_total < 0:
        raise InvoiceSnapshotValidationError("totals.shipping_total", "El envio no puede ser negativo.")
    if _quantize_money(shipping_total) > Decimal("0.00"):
        lines.append(_build_shipping_line(len(lines) + 1, shipping_total))

    subtotal = _to_decimal(quote.get("subtotal"), "totals.products_total")
    if _quantize_money(products_total) != _quantize_money(subtotal):
        raise InvoiceSnapshotValidationError(
            "totals.products_total",
            "El subtotal no coincide con las lineas.",
        )

    return lines


def _build_product_line(line_number, source_line):
    product_id = source_line.get("product_id")
    if product_id is None:
        product_id = source_line.get("producto_id")
    if product_id is None:
        raise InvoiceSnapshotValidationError(
            f"lines.{line_number}.product_id",
            "Producto obligatorio ausente.",
        )

    quantity = _quantity_string(source_line.get("quantity", 1), f"lines.{line_number}.quantity")
    unit_total = _to_decimal(
        source_line.get("unit_price", source_line.get("precio_total")),
        f"lines.{line_number}.unit_amount_before_discount",
    )
    line_total = _to_decimal(
        source_line.get("line_total", unit_total * _to_decimal(quantity, f"lines.{line_number}.quantity")),
        f"lines.{line_number}.line_amount_before_discount",
    )
    expected_line_total = _quantize_money(unit_total * _to_decimal(quantity, f"lines.{line_number}.quantity"))
    if _quantize_money(line_total) != expected_line_total:
        raise InvoiceSnapshotValidationError(
            f"lines.{line_number}.line_amount_before_discount",
            "El total de linea no coincide con cantidad por precio unitario.",
        )

    configuration = {
        "height_cm": _measurement_string(source_line.get("alto"), f"lines.{line_number}.configuration.height_cm"),
        "width_cm": _measurement_string(source_line.get("ancho"), f"lines.{line_number}.configuration.width_cm"),
        "anchoring": source_line.get("anclaje"),
        "color": source_line.get("color"),
    }
    if source_line.get("screw_option") is not None:
        configuration.update({
            "screw_option": source_line.get("screw_option"),
            "screw_length_mm": source_line.get("screw_length_mm"),
            "screw_supplement": f"{_quantize_money(_to_decimal(source_line.get('screw_supplement', 0), f'lines.{line_number}.configuration.screw_supplement')):.2f}",
        })

    model = source_line.get("product_name")
    return {
        "line_number": line_number,
        "line_type": "product",
        "product_id": product_id,
        "model": model,
        "description": model,
        "quantity": quantity,
        "unit_amount_before_discount": _quantize_money(unit_total),
        "line_amount_before_discount": _quantize_money(line_total),
        "configuration": configuration,
    }


def _measurement_string(value, field):
    measurement = _to_decimal(value, field)
    if measurement <= 0:
        raise InvoiceSnapshotValidationError(field, "La medida debe ser mayor que cero.")
    normalized = measurement.normalize()
    if normalized == normalized.to_integral():
        return str(int(normalized))
    return format(normalized, "f")


def _build_shipping_line(line_number, shipping_total):
    return {
        "line_number": line_number,
        "line_type": "shipping",
        "product_id": None,
        "model": None,
        "description": "Gastos de envío",
        "quantity": "1",
        "unit_amount_before_discount": _quantize_money(shipping_total),
        "line_amount_before_discount": _quantize_money(shipping_total),
        "configuration": None,
    }


def _build_totals(quote, lines_before_discount):
    products_total = _to_decimal(quote.get("subtotal"), "totals.products_total")
    shipping_total = _to_decimal(quote.get("shipping_cost", 0), "totals.shipping_total")
    discount_amount = _to_decimal(quote.get("discount_amount", 0), "totals.discount_amount")
    total_amount = _to_decimal(quote.get("total_amount"), "totals.total_amount")

    if products_total < 0:
        raise InvoiceSnapshotValidationError("totals.products_total", "El subtotal no puede ser negativo.")
    if shipping_total < 0:
        raise InvoiceSnapshotValidationError("totals.shipping_total", "El envio no puede ser negativo.")
    if discount_amount < 0:
        raise InvoiceSnapshotValidationError("totals.discount_amount", "El descuento no puede ser negativo.")
    if total_amount < 0:
        raise InvoiceSnapshotValidationError("totals.total_amount", "El total no puede ser negativo.")

    products_total = _quantize_money(products_total)
    shipping_total = _quantize_money(shipping_total)
    discount_amount = _quantize_money(discount_amount)
    total_amount = _quantize_money(total_amount)
    total_amount_before_discount = _quantize_money(products_total + shipping_total)

    if discount_amount > total_amount_before_discount:
        raise InvoiceSnapshotValidationError(
            "totals.discount_amount",
            "El descuento no puede superar el total antes de descuento.",
        )

    expected_total = _quantize_money(total_amount_before_discount - discount_amount)
    if total_amount != expected_total:
        raise InvoiceSnapshotValidationError(
            "totals.total_amount",
            "El total no coincide con subtotal, envio y descuento.",
        )

    product_line_sum = sum(
        line["line_amount_before_discount"]
        for line in lines_before_discount
        if line["line_type"] == "product"
    )
    if _quantize_money(product_line_sum) != products_total:
        raise InvoiceSnapshotValidationError(
            "totals.products_total",
            "El subtotal no coincide con las lineas de producto.",
        )

    lines_total_before_discount = _quantize_money(
        sum(line["line_amount_before_discount"] for line in lines_before_discount)
    )
    if lines_total_before_discount != total_amount_before_discount:
        raise InvoiceSnapshotValidationError(
            "totals.total_amount_before_discount",
            "La base de reparto no coincide con subtotal mas envio.",
        )

    return {
        "products_amount_before_discount": _money(products_total, "totals.products_amount_before_discount"),
        "shipping_amount_before_discount": _money(shipping_total, "totals.shipping_amount_before_discount"),
        "total_amount_before_discount": _money(total_amount_before_discount, "totals.total_amount_before_discount"),
        "discount_amount": _money(discount_amount, "totals.discount_amount"),
        "total_amount": _money(total_amount, "totals.total_amount"),
    }


def _allocate_discount(lines_before_discount, total_discount):
    total_discount = _quantize_money(total_discount)
    total_amount_before_discount = _quantize_money(
        sum(line["line_amount_before_discount"] for line in lines_before_discount)
    )

    if total_discount < 0:
        raise InvoiceSnapshotValidationError("totals.discount_amount", "El descuento no puede ser negativo.")
    if total_discount > total_amount_before_discount:
        raise InvoiceSnapshotValidationError(
            "totals.discount_amount",
            "El descuento no puede superar el total antes de descuento.",
        )
    if total_amount_before_discount == Decimal("0.00"):
        if total_discount == Decimal("0.00"):
            return [Decimal("0.00") for _ in lines_before_discount]
        raise InvoiceSnapshotValidationError("totals.discount_amount", "Descuento incompatible con base cero.")

    allocations = []
    allocated = Decimal("0.00")
    for line in lines_before_discount:
        line_amount = line["line_amount_before_discount"]
        if line_amount <= 0:
            floor_discount = Decimal("0.00")
            remainder = Decimal("0.00")
        else:
            raw_discount = total_discount * line_amount / total_amount_before_discount
            floor_discount = raw_discount.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
            remainder = raw_discount - floor_discount

        allocations.append({
            "line_number": line["line_number"],
            "line_amount": line_amount,
            "discount": floor_discount,
            "remainder": remainder,
        })
        allocated += floor_discount

    residual_cents = int(((total_discount - allocated) * 100).to_integral_value(rounding=ROUND_HALF_UP))
    for allocation in sorted(
        allocations,
        key=lambda item: (-item["remainder"], item["line_number"]),
    ):
        if residual_cents <= 0:
            break
        if allocation["line_amount"] <= 0:
            continue
        candidate_discount = allocation["discount"] + Decimal("0.01")
        if candidate_discount <= allocation["line_amount"]:
            allocation["discount"] = candidate_discount
            residual_cents -= 1

    if residual_cents != 0:
        raise InvoiceSnapshotValidationError(
            "totals.discount_amount",
            "No se pudo repartir el descuento sin dejar lineas negativas.",
        )

    return [
        _quantize_money(allocation["discount"])
        for allocation in sorted(allocations, key=lambda item: item["line_number"])
    ]


def _finalize_line(line_before_discount, discount_amount):
    line_amount_before_discount = line_before_discount["line_amount_before_discount"]
    if discount_amount > line_amount_before_discount:
        raise InvoiceSnapshotValidationError(
            f"lines.{line_before_discount['line_number']}.discount_amount",
            "El descuento de linea supera su importe.",
        )

    line_total = _quantize_money(line_amount_before_discount - discount_amount)
    tax_base, tax_amount = _tax_from_gross(line_total)

    return {
        "line_number": line_before_discount["line_number"],
        "line_type": line_before_discount["line_type"],
        "product_id": line_before_discount["product_id"],
        "model": line_before_discount["model"],
        "description": line_before_discount["description"],
        "quantity": line_before_discount["quantity"],
        "unit_amount_before_discount": _money(
            line_before_discount["unit_amount_before_discount"],
            f"lines.{line_before_discount['line_number']}.unit_amount_before_discount",
        ),
        "line_amount_before_discount": _money(
            line_amount_before_discount,
            f"lines.{line_before_discount['line_number']}.line_amount_before_discount",
        ),
        "discount_amount": _money(
            discount_amount,
            f"lines.{line_before_discount['line_number']}.discount_amount",
        ),
        "line_total": _money(line_total, f"lines.{line_before_discount['line_number']}.line_total"),
        "tax_rate": _money(SUPPORTED_TAX_RATE, f"lines.{line_before_discount['line_number']}.tax_rate"),
        "tax_base": _money(tax_base, f"lines.{line_before_discount['line_number']}.tax_base"),
        "tax_amount": _money(tax_amount, f"lines.{line_before_discount['line_number']}.tax_amount"),
        "configuration": line_before_discount["configuration"],
    }


def _finalize_totals(totals, lines):
    tax_base = sum(_to_decimal(line["tax_base"], f"lines.{line['line_number']}.tax_base") for line in lines)
    tax_amount = sum(_to_decimal(line["tax_amount"], f"lines.{line['line_number']}.tax_amount") for line in lines)
    total_amount = sum(_to_decimal(line["line_total"], f"lines.{line['line_number']}.line_total") for line in lines)
    discount_amount = sum(
        _to_decimal(line["discount_amount"], f"lines.{line['line_number']}.discount_amount")
        for line in lines
    )
    amount_before_discount = sum(
        _to_decimal(line["line_amount_before_discount"], f"lines.{line['line_number']}.line_amount_before_discount")
        for line in lines
    )

    if _quantize_money(discount_amount) != _to_decimal(totals["discount_amount"], "totals.discount_amount"):
        raise InvoiceSnapshotValidationError("totals.discount_amount", "La suma de descuentos no coincide.")
    if _quantize_money(total_amount) != _to_decimal(totals["total_amount"], "totals.total_amount"):
        raise InvoiceSnapshotValidationError("totals.total_amount", "La suma de lineas no coincide con la quote.")
    if _quantize_money(amount_before_discount) != _to_decimal(
        totals["total_amount_before_discount"],
        "totals.total_amount_before_discount",
    ):
        raise InvoiceSnapshotValidationError(
            "totals.total_amount_before_discount",
            "La suma de importes antes de descuento no coincide.",
        )
    if _quantize_money(tax_base + tax_amount) != _quantize_money(total_amount):
        raise InvoiceSnapshotValidationError("totals.tax_amount", "Base e IVA no coinciden con el total.")

    return {
        **totals,
        "tax_base": _money(tax_base, "totals.tax_base"),
        "tax_amount": _money(tax_amount, "totals.tax_amount"),
        "total_amount": _money(total_amount, "totals.total_amount"),
        "rounding_adjustment": "0.00",
    }


def _normalize_payment(checkout_session):
    provider = _get_required(checkout_session, "payment_provider", "payment.provider")
    provider_reference = None
    if provider == "stripe":
        provider_reference = _getattr(checkout_session, "payment_intent_id")
    elif provider == "paypal":
        provider_reference = (
            _getattr(checkout_session, "provider_capture_id")
            or _getattr(checkout_session, "provider_order_id")
        )
    else:
        provider_reference = (
            _getattr(checkout_session, "provider_capture_id")
            or _getattr(checkout_session, "provider_order_id")
            or _getattr(checkout_session, "payment_intent_id")
        )

    return {
        "provider": provider,
        "provider_reference": provider_reference,
        "status": "paid",
        "paid_at": None,
    }


def _serialize_actor(actor):
    if actor is None:
        return None
    if isinstance(actor, dict):
        source = actor
        getter = source.get
    else:
        getter = lambda key, default=None: getattr(actor, key, default)

    payload = {}
    for key in ("id", "email", "name", "is_admin"):
        value = getter(key)
        if value is not None:
            payload[key] = value
    return payload or None

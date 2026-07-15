from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


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
    Discounts are stored in totals only; proportional fiscal allocation across
    product/shipping lines is a pending decision before real invoice issuance.
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

    lines = _build_lines(quote)
    totals = _build_totals(quote, lines)

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
    email = (
        customer_snapshot.get("email")
        or _nested_attr(order, "user", "email")
        or _nested_attr(checkout_session, "user", "email")
    )

    customer = {
        "legal_name": legal_name or None,
        "tax_id": customer_snapshot.get("CIF") or customer_snapshot.get("tax_id"),
        "address": address,
        "postal_code": postal_code,
        "city": city,
        "province": customer_snapshot.get("province"),
        "country_code": customer_snapshot.get("country_code") or "ES",
        "email": email,
        "phone": customer_snapshot.get("phone"),
    }

    required = {
        "legal_name": "customer.legal_name",
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


def _build_lines(quote):
    source_lines = quote.get("lines")
    if not source_lines:
        raise InvoiceSnapshotValidationError("lines", "No hay lineas facturables.")

    lines = []
    products_total = Decimal("0.00")
    for index, source_line in enumerate(source_lines, start=1):
        if not isinstance(source_line, dict):
            raise InvoiceSnapshotValidationError(f"lines.{index}", "Linea invalida.")
        line = _build_product_line(index, source_line)
        products_total += _to_decimal(line["line_total"], f"lines.{index}.line_total")
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
        f"lines.{line_number}.unit_total",
    )
    line_total = _to_decimal(
        source_line.get("line_total", unit_total * _to_decimal(quantity, f"lines.{line_number}.quantity")),
        f"lines.{line_number}.line_total",
    )
    expected_line_total = _quantize_money(unit_total * _to_decimal(quantity, f"lines.{line_number}.quantity"))
    if _quantize_money(line_total) != expected_line_total:
        raise InvoiceSnapshotValidationError(
            f"lines.{line_number}.line_total",
            "El total de linea no coincide con cantidad por precio unitario.",
        )

    tax_base, tax_amount = _tax_from_gross(line_total)
    model = source_line.get("product_name")
    return {
        "line_number": line_number,
        "line_type": "product",
        "product_id": product_id,
        "model": model,
        "description": model,
        "quantity": quantity,
        "unit_total": _money(unit_total, f"lines.{line_number}.unit_total"),
        "line_total": _money(line_total, f"lines.{line_number}.line_total"),
        "tax_rate": _money(SUPPORTED_TAX_RATE, f"lines.{line_number}.tax_rate"),
        "tax_base": _money(tax_base, f"lines.{line_number}.tax_base"),
        "tax_amount": _money(tax_amount, f"lines.{line_number}.tax_amount"),
        "configuration": {
            "height_cm": _measurement_string(source_line.get("alto"), f"lines.{line_number}.configuration.height_cm"),
            "width_cm": _measurement_string(source_line.get("ancho"), f"lines.{line_number}.configuration.width_cm"),
            "anchoring": source_line.get("anclaje"),
            "color": source_line.get("color"),
        },
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
    tax_base, tax_amount = _tax_from_gross(shipping_total)
    return {
        "line_number": line_number,
        "line_type": "shipping",
        "product_id": None,
        "model": None,
        "description": "Gastos de envío",
        "quantity": "1",
        "unit_total": _money(shipping_total, "shipping.unit_total"),
        "line_total": _money(shipping_total, "shipping.line_total"),
        "tax_rate": _money(SUPPORTED_TAX_RATE, "shipping.tax_rate"),
        "tax_base": _money(tax_base, "shipping.tax_base"),
        "tax_amount": _money(tax_amount, "shipping.tax_amount"),
        "configuration": None,
    }


def _build_totals(quote, lines):
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

    expected_total = _quantize_money(products_total + shipping_total - discount_amount)
    if _quantize_money(total_amount) != expected_total:
        raise InvoiceSnapshotValidationError(
            "totals.total_amount",
            "El total no coincide con subtotal, envio y descuento.",
        )

    product_line_sum = sum(
        _to_decimal(line["line_total"], f"lines.{line['line_number']}.line_total")
        for line in lines
        if line["line_type"] == "product"
    )
    if _quantize_money(product_line_sum) != _quantize_money(products_total):
        raise InvoiceSnapshotValidationError(
            "totals.products_total",
            "El subtotal no coincide con las lineas de producto.",
        )

    tax_base, tax_amount = _tax_from_gross(total_amount)
    pre_discount_line_total = product_line_sum + shipping_total
    rounding_adjustment = _quantize_money(
        total_amount - (pre_discount_line_total - discount_amount)
    )

    return {
        "products_total": _money(products_total, "totals.products_total"),
        "shipping_total": _money(shipping_total, "totals.shipping_total"),
        "discount_amount": _money(discount_amount, "totals.discount_amount"),
        "tax_base": _money(tax_base, "totals.tax_base"),
        "tax_amount": _money(tax_amount, "totals.tax_amount"),
        "total_amount": _money(total_amount, "totals.total_amount"),
        "rounding_adjustment": _money(rounding_adjustment, "totals.rounding_adjustment"),
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

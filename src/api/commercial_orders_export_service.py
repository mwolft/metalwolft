"""Administrative, non-personal commercial order export."""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from openpyxl import Workbook
from sqlalchemy.orm import joinedload, selectinload

from api.models import Orders, OrderDetails


CENT = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP) if value is not None else None


def safe_cell(value):
    if isinstance(value, str):
        value = "".join(char for char in value if char >= " " or char in "\t\n\r")
        if value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
    return value


def iter_orders(session, start=None, end=None, batch_size=250):
    """Keyset pagination avoids loading all commercial rows into the session."""
    last_id = 0
    while True:
        query = (session.query(Orders)
                 .options(selectinload(Orders.order_details).joinedload(OrderDetails.product),
                          joinedload(Orders.confirmed_order_context),
                          joinedload(Orders.checkout_session))
                 .filter(Orders.id > last_id))
        if start:
            query = query.filter(Orders.order_date >= datetime.combine(start, time.min))
        if end:
            if end == date.max:
                query = query.filter(Orders.order_date <= datetime.combine(end, time.max))
            else:
                query = query.filter(Orders.order_date < datetime.combine(end + timedelta(days=1), time.min))
        batch = query.order_by(Orders.id).limit(batch_size).all()
        if not batch:
            return
        for order in batch:
            yield order
        last_id = batch[-1].id
        session.expunge_all()


def _historical_names(order):
    context = order.confirmed_order_context
    checkout = order.checkout_session
    snapshot = context.quote_snapshot if context else checkout.quote_snapshot if checkout else None
    result = {}
    if not isinstance(snapshot, dict):
        return result
    for line in snapshot.get("lines", []):
        if not isinstance(line, dict):
            continue
        try:
            product_id = int(line.get("product_id"))
        except (TypeError, ValueError):
            continue
        name = line.get("product_name")
        if isinstance(name, str) and name.strip():
            result.setdefault(product_id, set()).add(name.strip())
    return {key: next(iter(names)) for key, names in result.items() if len(names) == 1}


def build_workbook(orders, start=None, end=None, generated_at=None):
    workbook = Workbook(write_only=True)
    pedidos = workbook.create_sheet("Pedidos")
    lineas = workbook.create_sheet("Lineas")
    control = workbook.create_sheet("Control")
    pedidos.append(["ID pedido", "Fecha", "Estado operativo", "Origen", "Evidencia de pago",
                    "Numero de lineas", "Subtotal calculado", "Descuento registrado",
                    "Envio registrado", "Total registrado", "Total reconstruido",
                    "Diferencia", "Conciliacion"])
    lineas.append(["ID pedido", "ID linea", "ID producto", "Nombre historico", "Nombre actual catalogo",
                   "Tipo de linea", "Cantidad", "Alto cm", "Ancho cm", "Superficie unitaria m2",
                   "Superficie total m2", "Color", "Anclaje", "Precio unitario registrado", "Importe linea"])
    counts = dict(orders=0, lines=0, reconciled=0, mismatch=0, provisional=0,
                  no_payment=0, complete_configuration=0)
    for order in orders:
        counts["orders"] += 1
        details = order.order_details
        counts["lines"] += len(details)
        names = _historical_names(order)
        subtotal = Decimal("0")
        for detail in details:
            unit = money(detail.precio_total)
            amount = (unit * detail.quantity).quantize(CENT, rounding=ROUND_HALF_UP) if unit is not None and detail.quantity is not None else None
            if amount is not None:
                subtotal += amount
            height = Decimal(str(detail.alto)) if detail.alto is not None else None
            width = Decimal(str(detail.ancho)) if detail.ancho is not None else None
            area = (height * width / Decimal("10000")) if height is not None and width is not None else None
            if all(value is not None for value in (height, width, detail.color, detail.anclaje, detail.quantity)):
                counts["complete_configuration"] += 1
            lineas.append([order.id, detail.id, detail.product_id, safe_cell(names.get(detail.product_id)),
                           safe_cell(detail.product.nombre if detail.product else None), safe_cell(detail.line_type),
                           detail.quantity, detail.alto, detail.ancho, float(area) if area is not None else None,
                           float(area * detail.quantity) if area is not None and detail.quantity is not None else None,
                           safe_cell(detail.color), safe_cell(detail.anclaje), float(unit) if unit is not None else None,
                           float(amount) if amount is not None else None])
        discount = money(order.discount_value)
        shipping = money(order.shipping_cost)
        registered = money(order.total_amount)
        reconstructed = (subtotal - (discount or 0) + (shipping or 0)).quantize(CENT, rounding=ROUND_HALF_UP)
        difference = (registered - reconstructed).quantize(CENT, rounding=ROUND_HALF_UP) if registered is not None else None
        provisional = discount is None or shipping is None
        if provisional:
            counts["provisional"] += 1
        if difference is not None and abs(difference) > CENT:
            status = "Descuadrado provisional" if provisional else "Descuadrado"
            counts["mismatch"] += 1
        elif provisional:
            status = "Provisional (nulos como 0)"
        else:
            status = "Conciliado"
            counts["reconciled"] += 1
        context = order.confirmed_order_context
        checkout = order.checkout_session
        origin = context.source if context else "Web (sesion)" if checkout else "Desconocido"
        evidence = "Contexto confirmado" if context and context.payment_status == "confirmed" else "Sesion checkout (no confirma cobro)" if checkout else "Sin evidencia suficiente"
        if evidence != "Contexto confirmado":
            counts["no_payment"] += 1
        pedidos.append([order.id, order.order_date, safe_cell(order.order_status), safe_cell(origin), evidence,
                        len(details), float(subtotal), float(discount) if discount is not None else None,
                        float(shipping) if shipping is not None else None,
                        float(registered) if registered is not None else None, float(reconstructed),
                        float(difference) if difference is not None else None, status])
    control.append(["Concepto", "Valor"])
    for label, value in [
        ("Generado UTC", (generated_at or datetime.now(timezone.utc)).isoformat(timespec="seconds")),
        ("Desde", start.isoformat() if start else "Sin filtro"),
        ("Hasta", end.isoformat() if end else "Sin filtro"),
        ("Pedidos", counts["orders"]), ("Lineas", counts["lines"]),
        ("Conciliados", counts["reconciled"]), ("Descuadrados", counts["mismatch"]),
        ("Con importes provisionales", counts["provisional"]),
        ("Sin evidencia suficiente de pago", counts["no_payment"]),
        ("Lineas con configuracion completa", counts["complete_configuration"]),
        ("Advertencia", "Los importes no equivalen necesariamente a ventas cobradas."),
    ]:
        control.append([label, safe_cell(value)])
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output

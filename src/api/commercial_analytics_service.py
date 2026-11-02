"""Read-only commercial order indicators for Flask-Admin."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import calendar
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from sqlalchemy import Numeric, String, and_, case, cast, func, or_, select

from api.models import OrderDetails, Orders, Products


MADRID = ZoneInfo("Europe/Madrid")
CENT = Decimal("0.01")
PERIODS = frozenset({"month", "year", "previous_year", "all", "custom"})


@dataclass(frozen=True)
class CommercialPeriod:
    kind: str
    start_utc: datetime | None
    end_utc: datetime | None
    start_date: date | None = None
    end_date: date | None = None


def _utc_naive(value):
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _iso_date(value):
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError("Introduce fechas válidas en formato AAAA-MM-DD.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Introduce fechas válidas en formato AAAA-MM-DD.") from exc
    if parsed.isoformat() != value or not 1900 <= parsed.year <= 9998:
        raise ValueError("Introduce fechas válidas en formato AAAA-MM-DD.")
    return parsed


def resolve_commercial_period(kind, date_from=None, date_to=None, *, now=None):
    if kind not in PERIODS:
        raise ValueError("Selecciona un periodo válido.")
    now_local = (now or datetime.now(timezone.utc)).astimezone(MADRID)
    year = now_local.year
    if kind == "all":
        return CommercialPeriod(kind, None, None)
    if kind == "custom":
        start_date = _iso_date(date_from)
        end_date = _iso_date(date_to)
        if start_date > end_date:
            raise ValueError("La fecha inicial no puede ser posterior a la final.")
        start = datetime.combine(start_date, time.min, MADRID)
        end = datetime.combine(end_date + timedelta(days=1), time.min, MADRID)
        return CommercialPeriod(kind, _utc_naive(start), _utc_naive(end), start_date, end_date)
    if kind == "month":
        start = datetime(year, now_local.month, 1, tzinfo=MADRID)
        end = now_local
    elif kind == "year":
        start = datetime(year, 1, 1, tzinfo=MADRID)
        end = now_local
    else:
        start = datetime(year - 1, 1, 1, tzinfo=MADRID)
        end = datetime(year, 1, 1, tzinfo=MADRID)
    return CommercialPeriod(kind, _utc_naive(start), _utc_naive(end))


def resolve_ranking_period(choice, available_years, *, now=None):
    if choice == "all":
        return resolve_commercial_period("all", now=now)
    if choice in {"year", "previous_year"}:
        return resolve_commercial_period(choice, now=now)
    if not choice.startswith("year:") or not choice[5:].isdigit():
        raise ValueError("Selecciona un periodo válido para el ranking.")
    year = int(choice[5:])
    if year not in available_years or not 1900 <= year <= 9998:
        raise ValueError("Selecciona un año disponible para el ranking.")
    return resolve_commercial_period("custom", f"{year}-01-01", f"{year}-12-31", now=now)


def _within_period(query, period):
    if period.start_utc is not None:
        query = query.where(Orders.order_date >= period.start_utc)
    if period.end_utc is not None:
        query = query.where(Orders.order_date < period.end_utc)
    return query


def commercial_indicators(session, period):
    count, recorded = session.execute(_within_period(
        select(func.count(Orders.id), func.sum(Orders.total_amount)), period,
    )).one()
    units = session.scalar(_within_period(
        select(func.sum(OrderDetails.quantity))
        .select_from(OrderDetails)
        .join(Orders, OrderDetails.order_id == Orders.id)
        .where(OrderDetails.line_type == "physical"),
        period,
    )) or 0
    amount = Decimal(str(recorded or 0)).quantize(CENT, rounding=ROUND_HALF_UP)
    ticket = (amount / count).quantize(CENT, rounding=ROUND_HALF_UP) if count else Decimal("0.00")
    return {"orders": count, "amount": amount, "ticket": ticket, "physical_units": int(units)}


def ranked_physical_models(session, period, sort_by="units", limit=10):
    if sort_by not in {"units", "amount"}:
        raise ValueError("Selecciona una ordenación válida.")
    physical = (OrderDetails.line_type == "physical")
    units = func.sum(OrderDetails.quantity)
    unit_price = func.round(cast(OrderDetails.precio_total, Numeric(18, 6)), 2)
    amount = func.sum(unit_price * OrderDetails.quantity)
    query = _within_period(
        select(OrderDetails.product_id, Products.nombre, units.label("units"),
               func.count(func.distinct(OrderDetails.order_id)).label("orders"), amount.label("amount"))
        .select_from(OrderDetails)
        .join(Orders, OrderDetails.order_id == Orders.id)
        .outerjoin(Products, OrderDetails.product_id == Products.id)
        .where(physical)
        .group_by(OrderDetails.product_id, Products.nombre), period,
    )
    ordering = units if sort_by == "units" else amount
    rows = session.execute(query.order_by(ordering.desc(), OrderDetails.product_id).limit(limit)).all()
    total_units = session.scalar(_within_period(
        select(func.sum(OrderDetails.quantity))
        .select_from(OrderDetails)
        .join(Orders, OrderDetails.order_id == Orders.id)
        .where(physical), period,
    )) or 0
    return {
        "rows": [{"product_id": product_id, "current_name": name,
                  "units": int(quantity), "orders": order_count,
                  "amount": Decimal(str(recorded or 0)).quantize(CENT, rounding=ROUND_HALF_UP)}
                 for product_id, name, quantity, order_count, recorded in rows],
        "total_units": int(total_units),
    }


COLOR_LABELS = {
    "blanco": "Blanco", "gris": "Gris", "negro": "Negro", "marrón": "Marrón",
    "satinado_blanco": "Satinado blanco", "satinado_gris": "Satinado gris",
    "satinado_negro": "Satinado negro", "satinado_verde": "Satinado verde",
    "forja_gris": "Forja gris", "forja_marron": "Forja marrón",
    "forja_negro": "Forja negro", "forja_verde": "Forja verde",
}
DIMENSION_LABELS = ("Sin dato o anómalo", "Menos de 60 cm", "60 a menos de 100 cm",
                    "100 a menos de 150 cm", "150 a menos de 200 cm", "200 cm o más")
AREA_LABELS = ("Sin dato o anómalo", "Menos de 1 m²", "1 a menos de 2 m²",
               "2 a menos de 3 m²", "3 m² o más")


def _invalid_measure(column):
    return or_(column.is_(None), column <= 0,
               func.lower(cast(column, String)).in_(("nan", "infinity", "-infinity", "inf", "-inf")))


def _measure_bucket(value, invalid, boundaries):
    return case((invalid, 0), *((value < boundary, index)
                                for index, boundary in enumerate(boundaries, 1)),
                else_=len(boundaries) + 1)


def configuration_distributions(session, period):
    """Aggregate physical units without rebuilding historical options from the catalog."""
    base = (select(OrderDetails.quantity).select_from(OrderDetails)
            .join(Orders, OrderDetails.order_id == Orders.id)
            .where(OrderDetails.line_type == "physical"))
    total = int(session.scalar(_within_period(
        base.with_only_columns(func.sum(OrderDetails.quantity)), period)) or 0)

    def grouped(expression):
        query = _within_period(
            base.with_only_columns(expression, func.sum(OrderDetails.quantity))
            .group_by(expression), period)
        return [(key, int(units)) for key, units in session.execute(query)]

    def rows(pairs, label_for):
        return [{"label": label_for(key), "units": units,
                 "percent": float((Decimal(units) * 100 / total).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
                 if total else 0.0} for key, units in sorted(pairs, key=lambda pair: (-pair[1], str(pair[0])))]

    def text_bucket(column):
        return case((or_(column.is_(None), func.trim(column) == ""), None), else_=column)

    height, width = OrderDetails.alto, OrderDetails.ancho
    area = height * width / 10000.0
    invalid_area = or_(_invalid_measure(height), _invalid_measure(width), _invalid_measure(area))
    measures = {
        "height": (_measure_bucket(height, _invalid_measure(height), (60, 100, 150, 200)), DIMENSION_LABELS),
        "width": (_measure_bucket(width, _invalid_measure(width), (60, 100, 150, 200)), DIMENSION_LABELS),
        "area": (_measure_bucket(area, invalid_area, (1, 2, 3)), AREA_LABELS),
    }
    result = {"total_units": total}
    result["colors"] = rows(grouped(text_bucket(OrderDetails.color)),
                            lambda raw: "Sin dato" if raw is None else
                            f"{COLOR_LABELS[raw]} ({raw})" if raw in COLOR_LABELS else raw)
    result["anchorages"] = rows(grouped(text_bucket(OrderDetails.anclaje)),
                                lambda raw: "Sin dato" if raw is None else raw)
    for key, (bucket, labels) in measures.items():
        counts = dict(grouped(bucket))
        result[key] = rows([(index, counts.get(index, 0)) for index in range(len(labels))],
                           lambda index: labels[index])
    return result


def monthly_order_activity(session, year, *, now=None, cutoff=None):
    """Aggregate UTC-naive order timestamps by Madrid commercial month."""
    now_local = (now or datetime.now(timezone.utc)).astimezone(MADRID)
    boundaries = [_utc_naive(datetime(year, month, 1, tzinfo=MADRID)) for month in range(1, 13)]
    boundaries.append(_utc_naive(datetime(year + 1, 1, 1, tzinfo=MADRID)))
    month_expr = case(*(
        (and_(Orders.order_date >= boundaries[index],
              Orders.order_date < boundaries[index + 1]), index + 1)
        for index in range(12)
    ))
    end_utc = min(boundaries[-1], _utc_naive(cutoff)) if cutoff else boundaries[-1]
    rows = session.execute(
        select(month_expr.label("month"), func.count(Orders.id), func.sum(Orders.total_amount))
        .where(Orders.order_date >= boundaries[0], Orders.order_date < end_utc)
        .group_by(month_expr)
    ).all()
    amounts = [0.0] * 12
    counts = [0] * 12
    for month, count, amount in rows:
        counts[month - 1] = count
        amounts[month - 1] = float(Decimal(str(amount or 0)).quantize(CENT, rounding=ROUND_HALF_UP))
    unit_rows = session.execute(
        select(month_expr.label("month"), func.sum(OrderDetails.quantity))
        .select_from(OrderDetails)
        .join(Orders, OrderDetails.order_id == Orders.id)
        .where(OrderDetails.line_type == "physical",
               Orders.order_date >= boundaries[0], Orders.order_date < end_utc)
        .group_by(month_expr)
    ).all()
    units = [0] * 12
    for month, quantity in unit_rows:
        units[month - 1] = int(quantity or 0)
    tickets = [float((Decimal(str(amount)) / count).quantize(CENT, rounding=ROUND_HALF_UP))
               if count else 0.0 for amount, count in zip(amounts, counts)]
    future = [year > now_local.year or (year == now_local.year and month > now_local.month)
              for month in range(1, 13)]
    if cutoff:
        cutoff_month = cutoff.astimezone(MADRID).month
        future = [month > cutoff_month for month in range(1, 13)]
    return {"amounts": amounts, "counts": counts, "units": units, "tickets": tickets,
            "future": future,
            "current_month": now_local.month if year == now_local.year else None}


def annual_comparison(session, year, *, now=None):
    now_local = (now or datetime.now(timezone.utc)).astimezone(MADRID)
    current_cutoff = now_local if year == now_local.year else None
    previous_cutoff = None
    if current_cutoff:
        day = min(now_local.day, calendar.monthrange(year - 1, now_local.month)[1])
        previous_cutoff = now_local.replace(year=year - 1, day=day)
    selected = monthly_order_activity(session, year, now=now_local, cutoff=current_cutoff)
    previous = monthly_order_activity(session, year - 1, now=now_local, cutoff=previous_cutoff)
    summaries = {}
    for key in ("amounts", "counts", "units"):
        current_value = sum(Decimal(str(value)) for value in selected[key])
        previous_value = sum(Decimal(str(value)) for value in previous[key])
        summaries[key] = _comparison_values(current_value, previous_value)
    current_orders = sum(selected["counts"])
    previous_orders = sum(previous["counts"])
    current_amount = Decimal(str(summaries["amounts"]["current"]))
    previous_amount = Decimal(str(summaries["amounts"]["previous"]))
    summaries["tickets"] = _comparison_values(
        (current_amount / current_orders).quantize(CENT, rounding=ROUND_HALF_UP) if current_orders else Decimal(0),
        (previous_amount / previous_orders).quantize(CENT, rounding=ROUND_HALF_UP) if previous_orders else Decimal(0),
    )
    return {"selected": selected, "previous": previous, "summaries": summaries,
            "partial": bool(current_cutoff)}


def _comparison_values(current, previous):
    delta = current - previous
    percent = ((delta / previous) * 100).quantize(CENT, rounding=ROUND_HALF_UP) if previous else None
    return {"current": float(current), "previous": float(previous),
            "delta": float(delta), "percent": float(percent) if percent is not None else None}

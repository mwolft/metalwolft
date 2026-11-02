"""Read-only commercial order indicators for Flask-Admin."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import calendar
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from sqlalchemy import and_, case, func, select

from api.models import OrderDetails, Orders


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

"""Validate and import source-backed monthly Google Ads costs."""

import calendar
import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import PurePath
from zoneinfo import ZoneInfo

from sqlalchemy import select

from api.commercial_analytics_service import monthly_order_activity, resolve_ranking_period
from api.models import GoogleAdsImportedMonthlyCost


HEADERS = (
    "mes", "fecha_inicio_fuente", "fecha_fin_fuente", "dias_en_fuente", "coste_eur",
    "coste_con_datos_producto_eur", "coste_sin_datos_producto_eur", "fuente", "estado",
)
MAX_BYTES = 1_000_000


@dataclass(frozen=True)
class MonthlyCost:
    source: str
    year: int
    month: int
    source_start: date
    source_end: date
    source_days: int
    cost_eur: Decimal
    cost_product_eur: Decimal
    cost_without_product_eur: Decimal
    status: str


def _money(value):
    if not re.fullmatch(r"\d+\.\d{2}", value or ""):
        raise ValueError("Los importes deben ser euros no negativos con dos decimales.")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Importe no válido.") from exc
    if not result.is_finite() or result > Decimal("9999999999.99"):
        raise ValueError("Importe fuera de rango.")
    return result


def parse_monthly_cost_csv(content):
    if not content or len(content) > MAX_BYTES:
        raise ValueError("El CSV está vacío o supera 1 MB.")
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if tuple(reader.fieldnames or ()) != HEADERS:
            raise ValueError("Las columnas del CSV no coinciden con el formato esperado.")
        rows = []
        seen = set()
        file_source = None
        for index, row in enumerate(reader, 2):
            if index > 501 or None in row or any(value is None for value in row.values()):
                raise ValueError("CSV incompleto o con demasiadas filas.")
            month_text = row["mes"]
            if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month_text):
                raise ValueError(f"Mes no válido en la fila {index}.")
            year, month = map(int, month_text.split("-"))
            if not 1900 <= year <= 9998:
                raise ValueError(f"Año no válido en la fila {index}.")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["fecha_inicio_fuente"]) or not re.fullmatch(
                    r"\d{4}-\d{2}-\d{2}", row["fecha_fin_fuente"]):
                raise ValueError(f"Fecha no válida en la fila {index}.")
            start = date.fromisoformat(row["fecha_inicio_fuente"])
            end = date.fromisoformat(row["fecha_fin_fuente"])
            last_day = calendar.monthrange(year, month)[1]
            if not (date(year, month, 1) <= start <= end <= date(year, month, last_day)):
                raise ValueError(f"Cobertura de fechas no válida en la fila {index}.")
            days = (end - start).days + 1
            if not row["dias_en_fuente"].isdigit() or int(row["dias_en_fuente"]) != days:
                raise ValueError(f"Días de cobertura inconsistentes en la fila {index}.")
            source, status = row["fuente"].strip(), row["estado"].strip()
            if not source or not status or len(source) > 255 or len(status) > 100:
                raise ValueError(f"Origen o estado no válido en la fila {index}.")
            if file_source is not None and source != file_source:
                raise ValueError("El CSV mezcla fuentes diferentes.")
            file_source = source
            key = (year, month)
            if key in seen:
                raise ValueError("El CSV contiene un mes duplicado.")
            seen.add(key)
            total = _money(row["coste_eur"])
            product = _money(row["coste_con_datos_producto_eur"])
            without = _money(row["coste_sin_datos_producto_eur"])
            if total != product + without:
                raise ValueError(f"El desglose no suma el coste del mes en la fila {index}.")
            rows.append(MonthlyCost(source, year, month, start, end, days,
                                    total, product, without, status))
        if not rows:
            raise ValueError("El CSV no contiene meses.")
        return rows
    except (UnicodeError, csv.Error, TypeError, ValueError) as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError("No se pudo leer el CSV UTF-8.") from exc


def import_monthly_costs(session, rows, filename, *, replace_existing=False):
    """One transaction; identical reimports are no-ops, replacements require consent."""
    if not rows:
        raise ValueError("No hay meses para importar.")
    safe_name = PurePath(str(filename).replace("\\", "/")).name
    if not safe_name or len(safe_name) > 255:
        raise ValueError("Nombre de archivo no válido.")
    keys = {(row.year, row.month) for row in rows}
    existing = session.execute(select(GoogleAdsImportedMonthlyCost).where(
        GoogleAdsImportedMonthlyCost.year.in_({key[0] for key in keys}),
        GoogleAdsImportedMonthlyCost.month.in_({key[1] for key in keys}),
    ).with_for_update()).scalars().all()
    by_key = {(row.year, row.month): row for row in existing}
    if any(by_key[(row.year, row.month)].source != row.source for row in rows
           if (row.year, row.month) in by_key):
        raise ValueError("El mes ya pertenece a otra fuente. No se pueden sumar orígenes solapados.")
    fields = ("source_start", "source_end", "source_days", "cost_eur",
              "cost_product_eur", "cost_without_product_eur", "status")
    changes = [row for row in rows if (key := (row.year, row.month)) in by_key
               and any(getattr(by_key[key], field) != getattr(row, field) for field in fields)]
    if changes and not replace_existing:
        raise ValueError("Hay meses con importes o cobertura diferentes. Confirma su sustitución explícitamente.")
    inserted = updated = 0
    try:
        for row in rows:
            key = (row.year, row.month)
            target = by_key.get(key)
            if target is None:
                target = GoogleAdsImportedMonthlyCost(source=row.source, year=row.year, month=row.month)
                session.add(target)
                inserted += 1
            elif row in changes:
                updated += 1
            else:
                continue
            for field in fields:
                setattr(target, field, getattr(row, field))
            target.import_filename = safe_name
            target.imported_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"inserted": inserted, "updated": updated, "unchanged": len(rows) - inserted - updated}


def ads_dashboard_data(session, choice, available_years):
    resolve_ranking_period(choice, available_years)
    query = select(GoogleAdsImportedMonthlyCost).order_by(
        GoogleAdsImportedMonthlyCost.year, GoogleAdsImportedMonthlyCost.month)
    year = None
    if choice == "year":
        year = datetime.now(ZoneInfo('Europe/Madrid')).year
    elif choice == "previous_year":
        year = datetime.now(ZoneInfo('Europe/Madrid')).year - 1
    elif choice.startswith("year:"):
        year = int(choice[5:])
    if year is not None:
        query = query.where(GoogleAdsImportedMonthlyCost.year == year)
    records = session.execute(query).scalars().all()
    if choice == "all":
        if not records:
            return {"total": Decimal('0.00'), "product": Decimal('0.00'),
                    "without": Decimal('0.00'), "labels": [], "costs": [],
                    "sales": [], "orders": [], "coverage": None, "missing": 0, "partial": []}
        start = date(records[0].year, records[0].month, 1)
        end = date(records[-1].year, records[-1].month, 1)
    else:
        start, end = date(year, 1, 1), date(year, 12, 1)
    months = []
    cursor = start
    while cursor <= end:
        months.append((cursor.year, cursor.month))
        cursor = date(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)
    by_month = {(record.year, record.month): record for record in records}
    activity = {year: monthly_order_activity(session, year) for year in {y for y, _ in months}}
    future = [activity[year]['future'][month - 1] for year, month in months]
    costs = [float(by_month[key].cost_eur) if key in by_month and not future[index] else None
             for index, key in enumerate(months)]
    partial = [key in by_month and (by_month[key].source_start.day != 1 or
               by_month[key].source_end.day != calendar.monthrange(*key)[1]) for key in months]
    return {
        "total": sum((record.cost_eur for record in records), Decimal('0.00')),
        "product": sum((record.cost_product_eur for record in records), Decimal('0.00')),
        "without": sum((record.cost_without_product_eur for record in records), Decimal('0.00')),
        "labels": [f"{year}-{month:02d}" for year, month in months],
        "costs": costs,
        "sales": [None if activity[year]['future'][month - 1] else activity[year]['amounts'][month - 1]
                  for year, month in months],
        "orders": [None if activity[year]['future'][month - 1] else activity[year]['counts'][month - 1]
                   for year, month in months],
        "future": future,
        "partial": partial,
        "missing": sum(key not in by_month and not future[index]
                       for index, key in enumerate(months)),
        "coverage": (min(record.source_start for record in records),
                     max(record.source_end for record in records)) if records else None,
    }

"""Monthly Google Ads purchase attribution, separate from store orders."""

import calendar
import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import PurePath

from sqlalchemy import select

from api.models import GoogleAdsPurchaseMonthly


CAMPAIGN = "2 Merchant"
ACTION = "Compra (Evento de Google Analytics purchase)"
HEADERS = ("Mes", "Campaña", "Acción de conversión", "Todas las conversiones",
           "Valor de todas las conversiones")
MONTHS = {name: number for number, name in enumerate((
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
    "septiembre", "octubre", "noviembre", "diciembre"), 1)}
MAX_BYTES = 1_000_000


@dataclass(frozen=True)
class PurchaseMonth:
    year: int
    month: int
    conversions: Decimal
    value_eur: Decimal
    source_start: date
    source_end: date


def _decimal(value):
    if not re.fullmatch(r"(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{1,2})?", value or ""):
        raise ValueError("Conversiones y valor deben ser no negativos con hasta dos decimales.")
    try:
        result = Decimal(value.replace(".", "").replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("Valor numérico no válido.") from exc
    if not result.is_finite() or result > Decimal("9999999999.99"):
        raise ValueError("Valor fuera de rango.")
    return result.quantize(Decimal("0.01"))


def _span(value):
    match = re.fullmatch(r"(\d{1,2}) de ([a-z]+) de (\d{4})", value)
    if not match or match[2] not in MONTHS:
        raise ValueError("Periodo del informe no válido.")
    return date(int(match[3]), MONTHS[match[2]], int(match[1]))


def parse_purchase_csv(content):
    if not content or len(content) > MAX_BYTES:
        raise ValueError("El CSV está vacío o supera 1 MB.")
    try:
        reader = csv.reader(io.StringIO(content.decode("utf-8-sig"), newline=""), strict=True)
        title = next(reader)
        period = next(reader)
        if len(title) != 1 or "Google Ads" not in title[0] or len(period) != 1:
            raise ValueError("Cabecera del informe de Google Ads no válida.")
        dates = re.fullmatch(r"(.+?) - (.+)", period[0])
        if not dates:
            raise ValueError("El informe no indica el intervalo de fechas.")
        start, end = _span(dates[1]), _span(dates[2])
        if start > end:
            raise ValueError("Intervalo del informe no válido.")
        if tuple(next(reader)) != HEADERS:
            raise ValueError("Las columnas no coinciden con el CSV de conversiones esperado.")
        rows, seen = [], set()
        for index, fields in enumerate(reader, 4):
            if index > 503 or len(fields) != len(HEADERS):
                raise ValueError("CSV incompleto o con demasiadas filas.")
            month_match = re.fullmatch(r"([a-z]+) de (\d{4})", fields[0])
            if not month_match or month_match[1] not in MONTHS:
                raise ValueError(f"Mes no válido en la fila {index}.")
            year, month = int(month_match[2]), MONTHS[month_match[1]]
            month_start = date(year, month, 1)
            month_end = date(year, month, calendar.monthrange(year, month)[1])
            if month_start > end or month_end < start:
                raise ValueError(f"Mes fuera del periodo en la fila {index}.")
            if fields[1] != CAMPAIGN or fields[2] != ACTION:
                continue
            if (year, month) in seen:
                raise ValueError("El CSV contiene compras duplicadas para un mes.")
            seen.add((year, month))
            rows.append(PurchaseMonth(year, month, _decimal(fields[3]), _decimal(fields[4]),
                                      max(start, month_start), min(end, month_end)))
        if not rows:
            raise ValueError("No hay conversiones purchase de 2 Merchant en el CSV.")
        return rows
    except (UnicodeError, csv.Error, StopIteration, TypeError) as exc:
        raise ValueError("No se pudo leer el CSV UTF-8 de Google Ads.") from exc


def import_purchase_months(session, rows, filename, *, replace_existing=False):
    if not rows:
        raise ValueError("No hay meses para importar.")
    safe_name = PurePath(str(filename).replace("\\", "/")).name
    if not safe_name or len(safe_name) > 255:
        raise ValueError("Nombre de archivo no válido.")
    existing = session.execute(select(GoogleAdsPurchaseMonthly).where(
        GoogleAdsPurchaseMonthly.year.in_({row.year for row in rows}),
        GoogleAdsPurchaseMonthly.month.in_({row.month for row in rows}),
    ).with_for_update()).scalars().all()
    by_key = {(row.year, row.month): row for row in existing}
    fields = ("conversions", "value_eur", "source_start", "source_end")
    changed = [row for row in rows if (row.year, row.month) in by_key and any(
        getattr(by_key[(row.year, row.month)], field) != getattr(row, field) for field in fields)]
    if changed and not replace_existing:
        raise ValueError("Hay meses diferentes. Confirma la sustitución explícitamente.")
    inserted = updated = 0
    try:
        for row in rows:
            target = by_key.get((row.year, row.month))
            if target is None:
                target = GoogleAdsPurchaseMonthly(year=row.year, month=row.month)
                session.add(target)
                inserted += 1
            elif row in changed:
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


def save_manual_purchase(session, month, conversions, value, *, editing=False):
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month or ""):
        raise ValueError("Indica un mes válido (AAAA-MM).")
    year, number = map(int, month.split("-"))
    if not 1900 <= year <= 9998:
        raise ValueError("Año fuera de rango.")
    count, amount = _decimal(conversions), _decimal(value)
    target = session.execute(select(GoogleAdsPurchaseMonthly).where(
        GoogleAdsPurchaseMonthly.year == year, GoogleAdsPurchaseMonthly.month == number
    ).with_for_update()).scalar_one_or_none()
    if editing != (target is not None):
        raise ValueError("El mes ha cambiado; actualiza la lista.")
    try:
        if target is None:
            target = GoogleAdsPurchaseMonthly(year=year, month=number,
                source_start=date(year, number, 1),
                source_end=date(year, number, calendar.monthrange(year, number)[1]))
            session.add(target)
        target.manual_conversions = count
        target.manual_value_eur = amount
        target.manual_updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.commit()
    except Exception:
        session.rollback()
        raise


def purchase_dashboard_data(session, ads_data):
    rows = session.execute(select(GoogleAdsPurchaseMonthly)).scalars().all()
    by_month = {(row.year, row.month): row for row in rows}
    conversions, values, incomplete, monthly_roas, monthly_cpa = [], [], [], [], []
    for index, label in enumerate(ads_data["labels"]):
        year, month = map(int, label.split("-"))
        row = by_month.get((year, month))
        full = bool(row and row.source_start == date(year, month, 1) and
                    row.source_end == date(year, month, calendar.monthrange(year, month)[1]))
        valid = full and not ads_data["future"][index]
        conversions.append((row.manual_conversions if row.manual_conversions is not None else row.conversions)
                           if valid else None)
        values.append((row.manual_value_eur if row.manual_value_eur is not None else row.value_eur)
                      if valid else None)
        incomplete.append(bool(row and not full))
        cost = ads_data["costs"][index]
        comparable_month = (valid and conversions[-1] is not None and values[-1] is not None
                            and cost is not None and not ads_data["partial"][index])
        monthly_roas.append(values[-1] / Decimal(str(cost)) if comparable_month and cost > 0 else None)
        monthly_cpa.append(Decimal(str(cost)) / conversions[-1]
                           if comparable_month and conversions[-1] > 0 else None)
    comparable = bool(conversions) and all(
        ads_data["future"][index] or (
            conversions[index] is not None and values[index] is not None and
            ads_data["costs"][index] is not None and not ads_data["partial"][index])
        for index in range(len(conversions)))
    total_count = sum((value for value in conversions if value is not None), Decimal("0.00"))
    total_value = sum((value for value in values if value is not None), Decimal("0.00"))
    cost = ads_data["total"]
    return {"conversions": conversions, "values": values, "incomplete": incomplete,
            "monthly_roas": monthly_roas, "monthly_cpa": monthly_cpa,
            "count": total_count, "value": total_value, "comparable": comparable,
            "roas": total_value / cost if comparable and cost > 0 else None,
            "cost_per_purchase": cost / total_count if comparable and total_count > 0 else None}

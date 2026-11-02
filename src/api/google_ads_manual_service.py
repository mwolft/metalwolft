"""Manual Google Ads monthly costs and their effective monthly view."""

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from api.models import GoogleAdsImportedMonthlyCost, GoogleAdsMonthlySpend, GoogleAdsMonthlySpendChange


def parse_month_and_amount(month, amount):
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month or ""):
        raise ValueError("Indica un mes válido (AAAA-MM).")
    year, number = map(int, month.split("-"))
    if not 1900 <= year <= 9998:
        raise ValueError("El año está fuera de rango.")
    if not re.fullmatch(r"\d+(?:[.,]\d{1,2})?", amount or ""):
        raise ValueError("Indica un importe no negativo con hasta dos decimales.")
    try:
        value = Decimal(amount.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("El importe no es válido.") from exc
    if not value.is_finite() or value > Decimal("9999999999.99"):
        raise ValueError("El importe está fuera de rango.")
    return year, number, value.quantize(Decimal("0.01"))


def effective_monthly_costs(session, *, include_manual=True):
    imported = session.execute(select(GoogleAdsImportedMonthlyCost)).scalars().all()
    confirmed = set(session.execute(select(GoogleAdsMonthlySpendChange.year,
        GoogleAdsMonthlySpendChange.month).distinct()).all()) if include_manual else set()
    manual = session.execute(select(GoogleAdsMonthlySpend)).scalars().all() if confirmed else []
    by_month = {(row.year, row.month): ("CSV", row.cost_eur, row) for row in imported}
    by_month.update({(row.year, row.month): ("Manual", row.amount, row) for row in manual
                     if (row.year, row.month) in confirmed})
    return sorted(((date(year, month, 1), source, amount, row)
                   for (year, month), (source, amount, row) in by_month.items()), reverse=True)


def unconfirmed_manual_costs(session):
    confirmed = set(session.execute(select(GoogleAdsMonthlySpendChange.year,
        GoogleAdsMonthlySpendChange.month).distinct()).all())
    return [row for row in session.execute(select(GoogleAdsMonthlySpend).order_by(
        GoogleAdsMonthlySpend.year.desc(), GoogleAdsMonthlySpend.month.desc())).scalars()
        if (row.year, row.month) not in confirmed]


def save_manual_cost(session, month, amount, *, editing=False):
    year, number, value = parse_month_and_amount(month, amount)
    existing = session.execute(select(GoogleAdsMonthlySpend).where(
        GoogleAdsMonthlySpend.year == year, GoogleAdsMonthlySpend.month == number
    ).with_for_update()).scalar_one_or_none()
    imported = session.execute(select(GoogleAdsImportedMonthlyCost).where(
        GoogleAdsImportedMonthlyCost.year == year, GoogleAdsImportedMonthlyCost.month == number
    )).scalar_one_or_none()
    confirmed = session.execute(select(GoogleAdsMonthlySpendChange.id).where(
        GoogleAdsMonthlySpendChange.year == year, GoogleAdsMonthlySpendChange.month == number
    ).limit(1)).scalar_one_or_none() is not None
    if editing and existing is None and imported is None:
        raise ValueError("El mes ya no existe; actualiza la lista.")
    if not editing and (existing is not None or imported is not None):
        raise ValueError("El mes ya existe; utiliza Editar para sustituir su importe efectivo.")
    previous = (existing.amount if confirmed else imported.cost_eur if imported is not None else
                existing.amount if existing is not None else None)
    if previous == value and existing is not None and confirmed:
        return False
    try:
        if existing is None:
            session.add(GoogleAdsMonthlySpend(year=year, month=number, amount=value))
        else:
            existing.amount = value
        session.add(GoogleAdsMonthlySpendChange(year=year, month=number,
                                                old_amount=previous, new_amount=value))
        session.commit()
    except Exception:
        session.rollback()
        raise
    return True

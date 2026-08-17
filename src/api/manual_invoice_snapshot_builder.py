"""Pure InvoiceSnapshot v2 builder for manually captured ordinary invoices."""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from api.invoice_snapshot_builder import (
    InvoiceSnapshotValidationError,
    RECTIFICATION_REASON_TEXTS,
    RECTIFICATION_SNAPSHOT_SCHEMA_VERSION,
    SNAPSHOT_SCHEMA_VERSION,
    SUPPORTED_CURRENCY,
)


MANUAL_SNAPSHOT_GENERATOR = "manual_invoice_snapshot_builder_v2"
MANUAL_CORRECTIVE_SNAPSHOT_GENERATOR = "manual_invoice_snapshot_builder_v3"
MONEY = Decimal("0.01")
SUPPORTED_MANUAL_RECTIFICATION_AEAT_TYPES = {"R1", "R4"}


def build_manual_invoice_snapshot(draft, issuer, *, issue_date, actor=None, original_invoice=None):
    """Build an immutable manual ordinary v2 or corrective partial v3 snapshot."""
    _required_text(draft, "client_name", "customer.legal_name")
    _required_text(draft, "client_tax_id", "customer.tax_id")
    _required_text(draft, "client_address", "customer.address")
    _required_text(draft, "client_postal_code", "customer.postal_code")
    _required_text(draft, "client_city", "customer.city")
    if str(getattr(draft, "client_country_code", "")).upper() != "ES":
        raise InvoiceSnapshotValidationError("customer.country_code", "Solo se admiten destinatarios espanoles.")
    if str(getattr(draft, "currency", "")).upper() != SUPPORTED_CURRENCY:
        raise InvoiceSnapshotValidationError("operation.currency", "Moneda no soportada.")

    issuer_snapshot = _issuer(issuer)
    issue_date_value = _date_value(issue_date, "operation.issue_date")
    operation_date_value = _date_value(
        getattr(draft, "operation_date", None) or issue_date,
        "operation.operation_date",
    )
    document_nature = _document_nature(draft)
    lines = _lines(draft, document_nature=document_nature)
    tax_base = sum((_decimal(line["tax_base"], "lines.tax_base") for line in lines), Decimal("0.00"))
    tax_amount = sum((_decimal(line["tax_amount"], "lines.tax_amount") for line in lines), Decimal("0.00"))
    total_amount = sum((_decimal(line["line_total"], "lines.line_total") for line in lines), Decimal("0.00"))
    if document_nature == "ordinary" and total_amount <= 0:
        raise InvoiceSnapshotValidationError("totals.total_amount", "El total debe ser mayor que cero.")
    if document_nature == "corrective" and total_amount >= 0:
        raise InvoiceSnapshotValidationError("totals.total_amount", "El abono debe tener un total negativo.")

    customer = {
        "legal_name": str(draft.client_name).strip(),
        "tax_id": str(draft.client_tax_id).strip().upper(),
        "address": str(draft.client_address).strip(),
        "postal_code": str(draft.client_postal_code).strip(),
        "city": str(draft.client_city).strip(),
        "province": _optional_text(getattr(draft, "client_province", None)),
        "country_code": "ES",
        "email": _optional_text(getattr(draft, "client_email", None)),
        "phone": None,
    }

    if document_nature == "corrective":
        return _corrective_snapshot(
            draft,
            issuer_snapshot=issuer_snapshot,
            customer=customer,
            issue_date=issue_date,
            operation_date=operation_date_value,
            lines=lines,
            tax_base=tax_base,
            tax_amount=tax_amount,
            total_amount=total_amount,
            original_invoice=original_invoice,
            actor=actor,
        )

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "metadata": {
            "generator": MANUAL_SNAPSHOT_GENERATOR,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "issuer": issuer_snapshot,
        "customer": customer,
        "operation": {
            "invoice_type": "ordinary",
            "issue_date": issue_date_value,
            "operation_date": operation_date_value,
            "currency": SUPPORTED_CURRENCY,
            "order_id": None,
            "order_locator": None,
            "order_date": None,
            "discount_code": None,
        },
        "lines": lines,
        "totals": {
            "products_amount_before_discount": _money(tax_base, "totals.tax_base"),
            "shipping_amount_before_discount": "0.00",
            "total_amount_before_discount": _money(total_amount, "totals.total_amount"),
            "discount_amount": "0.00",
            "tax_base": _money(tax_base, "totals.tax_base"),
            "tax_amount": _money(tax_amount, "totals.tax_amount"),
            "total_amount": _money(total_amount, "totals.total_amount"),
            "rounding_adjustment": "0.00",
        },
        "payment": {"provider": "manual", "provider_reference": None},
        "references": {
            "source": "manual_invoice_draft",
            "manual_invoice_draft_id": getattr(draft, "id", None),
            "external_reference": _optional_text(getattr(draft, "external_reference", None)),
            "actor": _actor(actor),
        },
    }


def _corrective_snapshot(
    draft,
    *,
    issuer_snapshot,
    customer,
    issue_date,
    operation_date,
    lines,
    tax_base,
    tax_amount,
    total_amount,
    original_invoice,
    actor,
):
    rectification = _rectification_reference(draft, original_invoice)
    issue_date_value = _date_value(issue_date, "operation.issue_date")
    return {
        "schema_version": RECTIFICATION_SNAPSHOT_SCHEMA_VERSION,
        "metadata": {
            "generator": MANUAL_CORRECTIVE_SNAPSHOT_GENERATOR,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "issuer": issuer_snapshot,
        "customer": customer,
        "operation": {
            "invoice_type": "corrective",
            "issue_date": issue_date_value,
            "operation_date": operation_date,
            "currency": SUPPORTED_CURRENCY,
            "order_id": None,
            "order_locator": None,
            "order_date": None,
            "discount_code": None,
            "rectification": rectification,
        },
        "lines": lines,
        "totals": {
            "products_amount_before_discount": _money(total_amount, "totals.total_amount"),
            "shipping_amount_before_discount": "0.00",
            "total_amount_before_discount": _money(total_amount, "totals.total_amount"),
            "discount_amount": "0.00",
            "tax_base": _money(tax_base, "totals.tax_base"),
            "tax_amount": _money(tax_amount, "totals.tax_amount"),
            "total_amount": _money(total_amount, "totals.total_amount"),
            "rounding_adjustment": "0.00",
        },
        "payment": {"provider": "manual", "provider_reference": None},
        "references": {
            "source": "manual_invoice_draft",
            "manual_invoice_draft_id": getattr(draft, "id", None),
            "external_reference": _optional_text(getattr(draft, "external_reference", None)),
            "actor": _actor(actor),
            "original_reference_type": rectification["original_reference_type"],
            "original_invoice_id": rectification.get("original_invoice_id"),
            "original_invoice_number": rectification["original_invoice_number"],
            "original_invoice_issued_at": rectification["original_invoice_issued_at"],
        },
    }


def _rectification_reference(draft, original_invoice):
    reason = _optional_text(getattr(draft, "rectification_reason", None))
    if reason not in RECTIFICATION_REASON_TEXTS:
        raise InvoiceSnapshotValidationError(
            "operation.rectification.rectification_reason",
            "Motivo de rectificacion obligatorio o no soportado.",
        )
    aeat_type = _optional_text(getattr(draft, "rectification_aeat_type", None))
    if aeat_type not in SUPPORTED_MANUAL_RECTIFICATION_AEAT_TYPES:
        raise InvoiceSnapshotValidationError(
            "operation.rectification.aeat_type",
            "Tipo fiscal AEAT R1/R4 obligatorio.",
        )

    draft_original_id = getattr(draft, "original_invoice_id", None)
    external_number = _optional_text(getattr(draft, "external_original_invoice_number", None))
    external_date = getattr(draft, "external_original_issue_date", None)
    if draft_original_id and (external_number or external_date):
        raise InvoiceSnapshotValidationError(
            "operation.rectification",
            "Indica una factura original moderna o una referencia externa, pero no ambas.",
        )
    if draft_original_id:
        if original_invoice is None or getattr(original_invoice, "id", None) != draft_original_id:
            raise InvoiceSnapshotValidationError(
                "operation.rectification.original_invoice_id",
                "La factura original moderna no está disponible.",
            )
        if getattr(original_invoice, "invoice_type", None) != "ordinary" or not getattr(original_invoice, "issued_at", None):
            raise InvoiceSnapshotValidationError(
                "operation.rectification.original_invoice_id",
                "La factura original moderna debe ser ordinaria y estar emitida.",
            )
        if not isinstance(getattr(original_invoice, "invoice_snapshot", None), dict):
            raise InvoiceSnapshotValidationError(
                "operation.rectification.original_invoice_id",
                "La factura original moderna no tiene snapshot fiscal válido.",
            )
        if getattr(original_invoice, "invoice_snapshot_schema_version", None) != SNAPSHOT_SCHEMA_VERSION:
            raise InvoiceSnapshotValidationError(
                "operation.rectification.original_invoice_id",
                "La factura original moderna debe usar snapshot fiscal v2.",
            )
        return {
            "rectification_type": "differences",
            "rectification_scope": "partial",
            "rectification_reason": reason,
            "rectification_reason_text": RECTIFICATION_REASON_TEXTS[reason],
            "aeat_type": aeat_type,
            "original_reference_type": "invoice",
            "original_invoice_id": draft_original_id,
            "original_invoice_number": _required_text_value(
                getattr(original_invoice, "invoice_number", None),
                "operation.rectification.original_invoice_number",
            ),
            "original_invoice_issued_at": _date_value(
                getattr(original_invoice, "issued_at", None),
                "operation.rectification.original_invoice_issued_at",
            ),
            "affected_line_numbers": [1],
        }

    if not external_number or not external_date:
        raise InvoiceSnapshotValidationError(
            "operation.rectification.external_original",
            "La referencia externa requiere número y fecha de factura original.",
        )
    return {
        "rectification_type": "differences",
        "rectification_scope": "partial",
        "rectification_reason": reason,
        "rectification_reason_text": RECTIFICATION_REASON_TEXTS[reason],
        "aeat_type": aeat_type,
        "original_reference_type": "external",
        "original_invoice_id": None,
        "original_invoice_number": external_number,
        "original_invoice_issued_at": _date_value(
            external_date,
            "operation.rectification.original_invoice_issued_at",
        ),
        "affected_line_numbers": [1],
    }


def _lines(draft, *, document_nature):
    source_lines = sorted(list(getattr(draft, "lines", None) or []), key=lambda line: (line.position, line.id or 0))
    if len(source_lines) != 1:
        raise InvoiceSnapshotValidationError("lines", "Este hito requiere exactamente una linea con un unico IVA.")
    line = source_lines[0]
    concept = _required_text(line, "concept", "lines.1.description")
    tax_base = _money_decimal(getattr(line, "tax_base", None), "lines.1.tax_base")
    tax_rate = _money_decimal(getattr(line, "tax_rate", None), "lines.1.tax_rate")
    if document_nature == "ordinary" and tax_base <= 0:
        raise InvoiceSnapshotValidationError("lines.1.tax_base", "La base imponible debe ser mayor que cero.")
    if document_nature == "corrective" and tax_base >= 0:
        raise InvoiceSnapshotValidationError("lines.1.tax_base", "La base imponible del abono debe ser negativa.")
    if tax_rate < 0:
        raise InvoiceSnapshotValidationError("lines.1.tax_rate", "El tipo de IVA no puede ser negativo.")
    tax_amount = _round(tax_base * tax_rate / Decimal("100"))
    line_total = _round(tax_base + tax_amount)
    return [{
        "line_number": 1,
        "line_type": "manual",
        "product_id": None,
        "model": None,
        "description": concept,
        "quantity": "1",
        "unit_price_net": f"{tax_base.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP):.6f}",
        "unit_amount_before_discount": _money(line_total, "lines.1.line_total"),
        "line_amount_before_discount": _money(line_total, "lines.1.line_total"),
        "discount_amount": "0.00",
        "line_tax_base_before_discount": _money(tax_base, "lines.1.tax_base"),
        "discount_tax_base": "0.00",
        "line_total": _money(line_total, "lines.1.line_total"),
        "tax_rate": _money(tax_rate, "lines.1.tax_rate"),
        "tax_base": _money(tax_base, "lines.1.tax_base"),
        "tax_amount": _money(tax_amount, "lines.1.tax_amount"),
        "configuration": None,
    }]


def _issuer(value):
    if not isinstance(value, dict):
        raise InvoiceSnapshotValidationError("issuer", "El emisor debe ser un diccionario.")
    required = ("legal_name", "tax_id", "address", "postal_code", "city", "country_code")
    for field in required:
        if not _optional_text(value.get(field)):
            raise InvoiceSnapshotValidationError(f"issuer.{field}", "Campo obligatorio ausente.")
    return {field: _optional_text(value.get(field)) for field in (
        "legal_name", "trade_name", "tax_id", "address", "postal_code", "city", "province", "country_code", "email", "phone"
    )}


def _required_text(obj, attribute, field):
    value = _optional_text(getattr(obj, attribute, None))
    if not value:
        raise InvoiceSnapshotValidationError(field, "Campo obligatorio ausente.")
    return value


def _required_text_value(value, field):
    normalized = _optional_text(value)
    if not normalized:
        raise InvoiceSnapshotValidationError(field, "Campo obligatorio ausente.")
    return normalized


def _document_nature(draft):
    nature = _optional_text(getattr(draft, "document_nature", None)) or "ordinary"
    if nature not in {"ordinary", "corrective"}:
        raise InvoiceSnapshotValidationError("document_nature", "Naturaleza de documento no soportada.")
    return nature


def _optional_text(value):
    return str(value).strip() or None if value is not None else None


def _decimal(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise InvoiceSnapshotValidationError(field, "Importe no numerico.") from exc
    if not result.is_finite():
        raise InvoiceSnapshotValidationError(field, "Importe no numerico.")
    return result


def _money_decimal(value, field):
    return _round(_decimal(value, field))


def _round(value):
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _money(value, field):
    return f"{_round(_decimal(value, field)):.2f}"


def _date_value(value, field):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError as exc:
            raise InvoiceSnapshotValidationError(field, "Fecha invalida.") from exc
    raise InvoiceSnapshotValidationError(field, "Fecha obligatoria ausente.")


def _actor(actor):
    if actor is None:
        return None
    if isinstance(actor, dict):
        return actor.get("email") or actor.get("id")
    return getattr(actor, "email", None) or getattr(actor, "id", None) or str(actor)

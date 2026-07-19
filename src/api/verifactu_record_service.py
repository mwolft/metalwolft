import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Mapping

from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash
from api.models import VeriFactuRecord, db


RECORD_TYPE_ALTA = VeriFactuRecord.RECORD_TYPE_ALTA
PROVIDER_VERIFACTU = VeriFactuRecord.PROVIDER_VERIFACTU
MODE_VERIFACTU = VeriFactuRecord.MODE_VERIFACTU
STATUS_BUILT = VeriFactuRecord.STATUS_BUILT
FINGERPRINT_STATUS_NOT_CALCULATED = "NOT_CALCULATED"
SUPPORTED_INVOICE_SCHEMA_VERSION = 1
SUPPORTED_CURRENCY = "EUR"
SUPPORTED_INVOICE_TYPE = "ordinary"


class VeriFactuRecordError(Exception):
    """Base error for persisted VeriFactu records."""


class VeriFactuRecordValidationError(VeriFactuRecordError):
    """Raised when an issued invoice cannot produce a VeriFactu record."""


class VeriFactuRecordIntegrityError(VeriFactuRecordError):
    """Raised when the source invoice snapshot integrity is invalid."""


class VeriFactuRecordUnsupportedSchema(VeriFactuRecordError):
    """Raised when the invoice snapshot schema is not supported."""


@dataclass(frozen=True)
class VeriFactuRecordResult:
    record: object
    created: bool


def create_verifactu_registration_record(
    invoice,
    *,
    db_session=None,
    system_id,
    software_name,
    software_version,
):
    """Create the deterministic VeriFactu registration record for an issued invoice.

    This service deliberately does not transmit, sign, calculate the official
    VeriFactu fingerprint, commit, rollback, or mutate the invoice.
    It freezes the fiscal content that a later serializer/transmitter will use.
    """
    session = db_session or db.session
    invoice_id = _required_invoice_id(invoice)

    existing_record = (
        session.query(VeriFactuRecord)
        .filter_by(invoice_id=invoice_id, record_type=RECORD_TYPE_ALTA)
        .one_or_none()
    )
    if existing_record:
        return VeriFactuRecordResult(record=existing_record, created=False)

    system = _validated_system(
        system_id=system_id,
        software_name=software_name,
        software_version=software_version,
    )
    snapshot = _validated_snapshot(invoice)
    _validate_snapshot_hash(invoice, snapshot)

    payload = build_verifactu_registration_payload(
        invoice,
        snapshot=snapshot,
        system=system,
    )
    payload_hash = calculate_verifactu_record_payload_hash(payload)
    totals = payload["totals"]
    issuer = payload["issuer"]
    recipient = payload["recipient"]

    record = VeriFactuRecord(
        invoice_id=invoice_id,
        provider=PROVIDER_VERIFACTU,
        mode=MODE_VERIFACTU,
        record_type=RECORD_TYPE_ALTA,
        status=STATUS_BUILT,
        schema_version=1,
        invoice_number=payload["invoice"]["invoice_number"],
        invoice_issued_at=_invoice_issued_at(invoice),
        invoice_snapshot_hash=getattr(invoice, "invoice_snapshot_hash"),
        record_payload=payload,
        record_payload_hash=payload_hash,
        fingerprint=None,
        fingerprint_algorithm=None,
        fingerprint_status=FINGERPRINT_STATUS_NOT_CALCULATED,
        system_id=system["system_id"],
        software_name=system["software_name"],
        software_version=system["software_version"],
        issuer_tax_id=issuer["tax_id"],
        recipient_tax_id=recipient.get("tax_id"),
        total_amount=_money(totals["total_amount"], "totals.total_amount"),
        currency=payload["operation"]["currency"],
    )
    session.add(record)
    session.flush()
    return VeriFactuRecordResult(record=record, created=True)


def build_verifactu_registration_payload(invoice, *, snapshot, system):
    """Build the deterministic internal payload for a future VeriFactu Alta."""
    issuer = _required_mapping(snapshot, "issuer")
    recipient = _required_mapping(snapshot, "customer")
    operation = _required_mapping(snapshot, "operation")
    totals = _required_mapping(snapshot, "totals")

    currency = _required_text(operation.get("currency"), "operation.currency").upper()
    if currency != SUPPORTED_CURRENCY:
        raise VeriFactuRecordValidationError("Moneda no soportada para VeriFactu v1.")

    invoice_type = operation.get("invoice_type") or getattr(invoice, "invoice_type", None)
    if invoice_type != SUPPORTED_INVOICE_TYPE:
        raise VeriFactuRecordValidationError("Solo se soportan facturas ordinarias para registros de alta v1.")

    tax_breakdown = _tax_breakdown(snapshot)
    payload = {
        "schema_version": 1,
        "provider": PROVIDER_VERIFACTU,
        "mode": MODE_VERIFACTU,
        "record_type": RECORD_TYPE_ALTA,
        "fingerprint": None,
        "fingerprint_status": FINGERPRINT_STATUS_NOT_CALCULATED,
        "source": {
            "invoice_id": _required_invoice_id(invoice),
            "invoice_snapshot_hash": _required_text(
                getattr(invoice, "invoice_snapshot_hash", None),
                "invoice.invoice_snapshot_hash",
            ),
        },
        "system": dict(system),
        "invoice": {
            "invoice_number": _required_invoice_number(invoice),
            "invoice_type": invoice_type,
            "issued_at": _datetime_string(_invoice_issued_at(invoice), "invoice.issued_at"),
            "issue_date": _date_string(operation.get("issue_date"), "operation.issue_date"),
            "operation_date": _date_string(
                operation.get("operation_date") or operation.get("issue_date"),
                "operation.operation_date",
            ),
        },
        "operation": {
            "currency": currency,
            "order_id": operation.get("order_id"),
            "order_locator": operation.get("order_locator"),
        },
        "issuer": {
            "legal_name": _required_text(issuer.get("legal_name"), "issuer.legal_name"),
            "tax_id": _required_text(issuer.get("tax_id"), "issuer.tax_id"),
            "country_code": _required_text(issuer.get("country_code"), "issuer.country_code").upper(),
        },
        "recipient": {
            "legal_name": _required_text(recipient.get("legal_name"), "customer.legal_name"),
            "tax_id": _required_text(recipient.get("tax_id"), "customer.tax_id"),
            "country_code": _required_text(recipient.get("country_code"), "customer.country_code").upper(),
        },
        "totals": {
            "tax_base": _money_string(totals.get("tax_base"), "totals.tax_base"),
            "tax_amount": _money_string(totals.get("tax_amount"), "totals.tax_amount"),
            "total_amount": _money_string(totals.get("total_amount"), "totals.total_amount"),
        },
        "tax_breakdown": tax_breakdown,
    }
    return payload


def calculate_verifactu_record_payload_hash(payload):
    canonical_payload = json.dumps(
        _normalize_json_value(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _validated_snapshot(invoice):
    if not getattr(invoice, "issued_at", None):
        raise VeriFactuRecordValidationError("La factura debe estar emitida antes de crear el registro VeriFactu.")
    if not getattr(invoice, "invoice_number", None):
        raise VeriFactuRecordValidationError("La factura debe tener numero fiscal.")

    snapshot = getattr(invoice, "invoice_snapshot", None)
    if not isinstance(snapshot, dict):
        raise VeriFactuRecordValidationError("La factura debe tener snapshot fiscal.")
    if snapshot.get("schema_version") != SUPPORTED_INVOICE_SCHEMA_VERSION:
        raise VeriFactuRecordUnsupportedSchema("Version de snapshot fiscal no soportada.")
    return snapshot


def _validate_snapshot_hash(invoice, snapshot):
    stored_hash = getattr(invoice, "invoice_snapshot_hash", None)
    if not stored_hash:
        raise VeriFactuRecordIntegrityError("La factura no tiene hash interno de snapshot.")
    if calculate_invoice_snapshot_hash(snapshot) != stored_hash:
        raise VeriFactuRecordIntegrityError("El hash interno de snapshot no coincide.")


def _validated_system(*, system_id, software_name, software_version):
    return {
        "system_id": _required_text(system_id, "system_id"),
        "software_name": _required_text(software_name, "software_name"),
        "software_version": _required_text(software_version, "software_version"),
    }


def _tax_breakdown(snapshot):
    lines = snapshot.get("lines")
    if not isinstance(lines, list) or not lines:
        totals = _required_mapping(snapshot, "totals")
        return [
            {
                "tax_rate": _derived_tax_rate(totals),
                "tax_base": _money_string(totals.get("tax_base"), "totals.tax_base"),
                "tax_amount": _money_string(totals.get("tax_amount"), "totals.tax_amount"),
            }
        ]

    breakdown = {}
    for index, line in enumerate(lines, start=1):
        if not isinstance(line, Mapping):
            raise VeriFactuRecordValidationError(f"Linea fiscal invalida: {index}.")
        rate = _money_string(line.get("tax_rate"), f"lines.{index}.tax_rate")
        tax_base = _money(line.get("tax_base"), f"lines.{index}.tax_base")
        tax_amount = _money(line.get("tax_amount"), f"lines.{index}.tax_amount")
        current = breakdown.setdefault(rate, {"tax_base": Decimal("0.00"), "tax_amount": Decimal("0.00")})
        current["tax_base"] += tax_base
        current["tax_amount"] += tax_amount

    return [
        {
            "tax_rate": rate,
            "tax_base": _money_to_string(values["tax_base"]),
            "tax_amount": _money_to_string(values["tax_amount"]),
        }
        for rate, values in sorted(breakdown.items(), key=lambda item: item[0])
    ]


def _derived_tax_rate(totals):
    tax_base = _money(totals.get("tax_base"), "totals.tax_base")
    tax_amount = _money(totals.get("tax_amount"), "totals.tax_amount")
    if tax_base <= Decimal("0.00"):
        raise VeriFactuRecordValidationError("No se puede derivar IVA con base imponible cero.")
    return _money_to_string((tax_amount / tax_base * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _required_invoice_id(invoice):
    invoice_id = getattr(invoice, "id", None)
    if not invoice_id:
        raise VeriFactuRecordValidationError("El id de factura es obligatorio.")
    return invoice_id


def _required_invoice_number(invoice):
    invoice_number = getattr(invoice, "invoice_number", None)
    return _required_text(invoice_number, "invoice.invoice_number")


def _invoice_issued_at(invoice):
    issued_at = getattr(invoice, "issued_at", None)
    if isinstance(issued_at, datetime):
        return issued_at
    raise VeriFactuRecordValidationError("La fecha de emision de factura es obligatoria.")


def _required_mapping(snapshot, key):
    value = snapshot.get(key)
    if not isinstance(value, Mapping):
        raise VeriFactuRecordValidationError(f"Bloque de snapshot obligatorio ausente: {key}.")
    return value


def _required_text(value, field):
    text = _optional_text(value)
    if not text:
        raise VeriFactuRecordValidationError(f"Campo obligatorio ausente: {field}.")
    return text


def _optional_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _money(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise VeriFactuRecordValidationError(f"Importe no valido en {field}.") from exc
    if not amount.is_finite():
        raise VeriFactuRecordValidationError(f"Importe no valido en {field}.")
    if amount < Decimal("0.00"):
        raise VeriFactuRecordValidationError(f"Importe negativo en {field}.")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _money_string(value, field):
    return _money_to_string(_money(value, field))


def _money_to_string(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _date_string(value, field):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError as exc:
            raise VeriFactuRecordValidationError(f"Fecha invalida en {field}.") from exc
    raise VeriFactuRecordValidationError(f"Fecha obligatoria ausente: {field}.")


def _datetime_string(value, field):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.isoformat()
        return value.astimezone(timezone.utc).isoformat()
    raise VeriFactuRecordValidationError(f"Fecha/hora obligatoria ausente: {field}.")


def _normalize_json_value(value):
    if isinstance(value, Decimal):
        return _money_to_string(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _normalize_json_value(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_json_value(child) for child in value]
    return value

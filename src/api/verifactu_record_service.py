import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Mapping

from sqlalchemy.exc import IntegrityError

from api.invoice_snapshot_integrity import calculate_invoice_snapshot_hash
from api.models import VeriFactuChainState, VeriFactuRecord, db
from api.verifactu_fingerprint import (
    OfficialRegistrationData,
    VERIFACTU_FINGERPRINT_ALGORITHM,
    VERIFACTU_FINGERPRINT_STATUS_CALCULATED,
    VERIFACTU_OFFICIAL_PAYLOAD_SCHEMA_VERSION,
    VERIFACTU_ORDINARY_INVOICE_TYPE_CODE,
    VeriFactuFingerprintError,
    VeriFactuSystemIdentity,
    build_official_registration_payload,
    build_registration_fingerprint_input,
    calculate_verifactu_fingerprint,
    normalize_system_identity,
)


RECORD_TYPE_ALTA = VeriFactuRecord.RECORD_TYPE_ALTA
PROVIDER_VERIFACTU = VeriFactuRecord.PROVIDER_VERIFACTU
MODE_VERIFACTU = VeriFactuRecord.MODE_VERIFACTU
STATUS_BUILT = VeriFactuRecord.STATUS_BUILT
STATUS_READY = VeriFactuRecord.STATUS_READY
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


class VeriFactuRecordConcurrencyError(VeriFactuRecordError):
    """Raised when the local VeriFactu chain cannot be advanced safely."""


@dataclass(frozen=True)
class VeriFactuRecordResult:
    record: object
    created: bool


@dataclass(frozen=True)
class VeriFactuRecordReadyResult:
    record: object
    prepared: bool
    chain_key: str | None
    chain_sequence: int | None
    previous_record_id: int | None
    is_first_record: bool


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


def prepare_verifactu_record_for_submission(
    record,
    *,
    db_session=None,
    system_identity: VeriFactuSystemIdentity,
    generation_timestamp=None,
):
    """Calculate and persist the official local fingerprint for a registration record."""
    session = db_session or db.session
    _required_record_id(record)

    if record.status == STATUS_READY and record.fingerprint:
        return VeriFactuRecordReadyResult(
            record=record,
            prepared=False,
            chain_key=record.chain_key,
            chain_sequence=record.chain_sequence,
            previous_record_id=record.previous_record_id,
            is_first_record=bool(record.is_first_record),
        )
    if record.fingerprint:
        raise VeriFactuRecordIntegrityError("El registro ya tiene huella pero no esta en estado READY.")
    if record.status not in {STATUS_BUILT, "generated", "GENERATED"}:
        raise VeriFactuRecordValidationError("Solo se pueden preparar registros generados.")

    system = _validated_official_system_identity(system_identity)
    if record.system_id != system.system_id:
        raise VeriFactuRecordValidationError("La instalacion configurada no coincide con el registro.")

    _validate_record_payload_hash(record)
    generated_at = _generation_timestamp(generation_timestamp)
    chain_key = build_verifactu_chain_key(
        issuer_tax_id=record.issuer_tax_id,
        mode=record.mode,
        system_identity=system,
    )
    chain_state = _locked_chain_state(session, chain_key=chain_key, record=record, system=system)

    session.refresh(record)
    if record.status == STATUS_READY and record.fingerprint:
        return VeriFactuRecordReadyResult(
            record=record,
            prepared=False,
            chain_key=record.chain_key,
            chain_sequence=record.chain_sequence,
            previous_record_id=record.previous_record_id,
            is_first_record=bool(record.is_first_record),
        )
    if record.fingerprint:
        raise VeriFactuRecordIntegrityError("El registro ya tiene huella pero no esta en estado READY.")

    previous_record = _validated_chain_head(session, chain_state)
    previous_fingerprint = chain_state.last_fingerprint
    chain_sequence = chain_state.next_sequence
    is_first_record = previous_record is None
    official_data = _official_registration_data_from_record(
        record,
        previous_fingerprint=previous_fingerprint,
        generation_timestamp=generated_at,
    )
    try:
        fingerprint_input = build_registration_fingerprint_input(official_data)
        fingerprint = calculate_verifactu_fingerprint(fingerprint_input)
        official_payload = build_official_registration_payload(
            official_data,
            system=system,
            fingerprint_input=fingerprint_input,
            fingerprint=fingerprint,
            is_first_record=is_first_record,
        )
    except VeriFactuFingerprintError as exc:
        raise VeriFactuRecordValidationError(str(exc)) from exc

    record.official_payload = official_payload
    record.official_payload_schema_version = VERIFACTU_OFFICIAL_PAYLOAD_SCHEMA_VERSION
    record.fingerprint_input = fingerprint_input.value
    record.fingerprint = fingerprint
    record.fingerprint_algorithm = VERIFACTU_FINGERPRINT_ALGORITHM
    record.fingerprint_status = VERIFACTU_FINGERPRINT_STATUS_CALCULATED
    record.fingerprint_calculated_at = generated_at
    record.chain_key = chain_key
    record.chain_sequence = chain_sequence
    record.previous_record_id = previous_record.id if previous_record else None
    record.previous_fingerprint = previous_fingerprint
    record.is_first_record = is_first_record
    record.installation_id = system.installation_id
    record.producer_name = system.producer_name
    record.producer_tax_id = system.producer_tax_id
    record.generation_timestamp = generated_at
    record.generation_timezone = _timezone_suffix(generated_at)
    record.ready_at = generated_at
    record.software_name = system.system_name
    record.software_version = system.system_version
    record.status = STATUS_READY
    chain_state.last_record_id = record.id
    chain_state.last_fingerprint = fingerprint
    chain_state.next_sequence = chain_sequence + 1
    session.add(record)
    session.add(chain_state)
    session.flush()

    return VeriFactuRecordReadyResult(
        record=record,
        prepared=True,
        chain_key=record.chain_key,
        chain_sequence=record.chain_sequence,
        previous_record_id=record.previous_record_id,
        is_first_record=record.is_first_record,
    )


def build_verifactu_chain_key(*, issuer_tax_id, mode, system_identity: VeriFactuSystemIdentity):
    system = _validated_official_system_identity(system_identity)
    parts = (
        _required_text(issuer_tax_id, "issuer_tax_id").upper(),
        _required_text(mode, "mode").upper(),
        system.producer_tax_id.upper(),
        system.system_id,
        system.installation_id,
    )
    return "|".join(parts)


def verifactu_system_identity_from_config(config):
    try:
        return normalize_system_identity(
            system_id=config.get("VERIFACTU_SYSTEM_ID"),
            system_name=config.get("VERIFACTU_SYSTEM_NAME"),
            system_version=config.get("VERIFACTU_SYSTEM_VERSION"),
            installation_id=config.get("VERIFACTU_INSTALLATION_ID"),
            producer_name=config.get("VERIFACTU_PRODUCER_NAME"),
            producer_tax_id=config.get("VERIFACTU_PRODUCER_TAX_ID"),
        )
    except VeriFactuFingerprintError as exc:
        raise VeriFactuRecordValidationError(str(exc)) from exc


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


def _validated_official_system_identity(system_identity):
    if not isinstance(system_identity, VeriFactuSystemIdentity):
        raise VeriFactuRecordValidationError("La identidad del sistema VeriFactu no es valida.")
    try:
        return normalize_system_identity(
            system_id=system_identity.system_id,
            system_name=system_identity.system_name,
            system_version=system_identity.system_version,
            installation_id=system_identity.installation_id,
            producer_name=system_identity.producer_name,
            producer_tax_id=system_identity.producer_tax_id,
        )
    except VeriFactuFingerprintError as exc:
        raise VeriFactuRecordValidationError(str(exc)) from exc


def _locked_chain_state(session, *, chain_key, record, system):
    chain_state = (
        session.query(VeriFactuChainState)
        .filter_by(chain_key=chain_key)
        .with_for_update()
        .one_or_none()
    )
    if chain_state is not None:
        _validate_chain_state_identity(chain_state, record=record, system=system)
        return chain_state

    chain_state = VeriFactuChainState(
        chain_key=chain_key,
        issuer_tax_id=_required_text(record.issuer_tax_id, "issuer_tax_id"),
        provider=PROVIDER_VERIFACTU,
        mode=MODE_VERIFACTU,
        system_id=system.system_id,
        installation_id=system.installation_id,
        producer_tax_id=system.producer_tax_id,
        last_record_id=None,
        last_fingerprint=None,
        next_sequence=1,
    )
    session.add(chain_state)
    try:
        session.flush()
    except IntegrityError as exc:
        raise VeriFactuRecordConcurrencyError("Conflicto creando la cabeza de cadena VeriFactu.") from exc
    return chain_state


def _validate_chain_state_identity(chain_state, *, record, system):
    expected = {
        "issuer_tax_id": _required_text(record.issuer_tax_id, "issuer_tax_id"),
        "provider": PROVIDER_VERIFACTU,
        "mode": MODE_VERIFACTU,
        "system_id": system.system_id,
        "installation_id": system.installation_id,
        "producer_tax_id": system.producer_tax_id,
    }
    for field, expected_value in expected.items():
        if getattr(chain_state, field) != expected_value:
            raise VeriFactuRecordIntegrityError("La cabeza de cadena VeriFactu no coincide con el registro.")


def _validated_chain_head(session, chain_state):
    if chain_state.next_sequence < 1:
        raise VeriFactuRecordIntegrityError("La secuencia VeriFactu no es valida.")
    if chain_state.next_sequence == 1:
        if chain_state.last_record_id is not None or chain_state.last_fingerprint is not None:
            raise VeriFactuRecordIntegrityError("La primera posicion de cadena tiene anterior.")
        return None

    if not chain_state.last_record_id or not chain_state.last_fingerprint:
        raise VeriFactuRecordIntegrityError("La cabeza de cadena VeriFactu esta incompleta.")

    previous_record = session.get(VeriFactuRecord, chain_state.last_record_id)
    if previous_record is None:
        raise VeriFactuRecordIntegrityError("El registro anterior de cadena no existe.")
    if previous_record.chain_key != chain_state.chain_key:
        raise VeriFactuRecordIntegrityError("El registro anterior pertenece a otra cadena.")
    if previous_record.chain_sequence != chain_state.next_sequence - 1:
        raise VeriFactuRecordIntegrityError("El registro anterior no es la posicion inmediata.")
    if previous_record.fingerprint != chain_state.last_fingerprint:
        raise VeriFactuRecordIntegrityError("La huella anterior no coincide con la cabeza de cadena.")
    if previous_record.status != STATUS_READY:
        raise VeriFactuRecordIntegrityError("El registro anterior no esta preparado.")
    return previous_record


def _required_record_id(record):
    record_id = getattr(record, "id", None)
    if not record_id:
        raise VeriFactuRecordValidationError("El id del registro VeriFactu es obligatorio.")
    return record_id


def _validate_record_payload_hash(record):
    payload = getattr(record, "record_payload", None)
    if not isinstance(payload, dict):
        raise VeriFactuRecordValidationError("El registro VeriFactu debe tener payload interno.")
    stored_hash = getattr(record, "record_payload_hash", None)
    if not stored_hash:
        raise VeriFactuRecordIntegrityError("El registro VeriFactu no tiene hash interno.")
    if calculate_verifactu_record_payload_hash(payload) != stored_hash:
        raise VeriFactuRecordIntegrityError("El hash interno del registro VeriFactu no coincide.")


def _official_registration_data_from_record(record, *, previous_fingerprint, generation_timestamp):
    payload = getattr(record, "record_payload", None)
    issuer = _required_mapping(payload, "issuer")
    invoice = _required_mapping(payload, "invoice")
    totals = _required_mapping(payload, "totals")

    invoice_type = invoice.get("invoice_type")
    if invoice_type != SUPPORTED_INVOICE_TYPE:
        raise VeriFactuRecordValidationError("Solo se soporta RegistroAlta F1 para facturas ordinarias.")

    return OfficialRegistrationData(
        issuer_tax_id=_required_text(issuer.get("tax_id"), "issuer.tax_id"),
        invoice_number=_required_text(invoice.get("invoice_number"), "invoice.invoice_number"),
        issue_date=_parse_date(invoice.get("issue_date"), "invoice.issue_date"),
        invoice_type_code=VERIFACTU_ORDINARY_INVOICE_TYPE_CODE,
        tax_amount=_money(totals.get("tax_amount"), "totals.tax_amount"),
        total_amount=_money(totals.get("total_amount"), "totals.total_amount"),
        previous_fingerprint=previous_fingerprint,
        generation_timestamp=generation_timestamp,
    )


def _generation_timestamp(value):
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0)
    if not isinstance(value, datetime):
        raise VeriFactuRecordValidationError("La fecha de generacion debe ser fecha/hora.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise VeriFactuRecordValidationError("La fecha de generacion debe incluir huso horario.")
    return value.replace(microsecond=0)


def _parse_date(value, field):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date()
        except ValueError as exc:
            raise VeriFactuRecordValidationError(f"Fecha invalida en {field}.") from exc
    raise VeriFactuRecordValidationError(f"Fecha obligatoria ausente: {field}.")


def _timezone_suffix(value):
    text = value.isoformat()
    if text.endswith("+00:00"):
        return "+00:00"
    return text[-6:]


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

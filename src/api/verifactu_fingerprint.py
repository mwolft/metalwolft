import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


VERIFACTU_FINGERPRINT_ALGORITHM = "SHA-256"
VERIFACTU_FINGERPRINT_STATUS_CALCULATED = "CALCULATED"
VERIFACTU_OFFICIAL_PAYLOAD_SCHEMA_VERSION = 1
VERIFACTU_ORDINARY_INVOICE_TYPE_CODE = "F1"


class VeriFactuFingerprintError(ValueError):
    """Raised when official VeriFactu fingerprint input cannot be built."""


@dataclass(frozen=True)
class VeriFactuSystemIdentity:
    system_id: str
    system_name: str
    system_version: str
    installation_id: str
    producer_name: str
    producer_tax_id: str


@dataclass(frozen=True)
class OfficialRegistrationData:
    issuer_tax_id: str
    invoice_number: str
    issue_date: date
    invoice_type_code: str
    tax_amount: Decimal
    total_amount: Decimal
    previous_fingerprint: str | None
    generation_timestamp: datetime


@dataclass(frozen=True)
class FingerprintInput:
    value: str


def build_registration_fingerprint_input(data: OfficialRegistrationData) -> FingerprintInput:
    """Build the exact ordered string defined for RegistroAlta fingerprints."""
    parts = [
        ("IDEmisorFactura", _required_text(data.issuer_tax_id, "IDEmisorFactura")),
        ("NumSerieFactura", _required_text(data.invoice_number, "NumSerieFactura")),
        ("FechaExpedicionFactura", _date_dd_mm_yyyy(data.issue_date, "FechaExpedicionFactura")),
        ("TipoFactura", _required_text(data.invoice_type_code, "TipoFactura")),
        ("CuotaTotal", _money_string(data.tax_amount, "CuotaTotal")),
        ("ImporteTotal", _money_string(data.total_amount, "ImporteTotal")),
        ("Huella", _optional_text(data.previous_fingerprint) or ""),
        (
            "FechaHoraHusoGenRegistro",
            _datetime_with_timezone(data.generation_timestamp, "FechaHoraHusoGenRegistro"),
        ),
    ]
    return FingerprintInput("&".join(f"{name}={value}" for name, value in parts))


def calculate_verifactu_fingerprint(fingerprint_input: FingerprintInput | str) -> str:
    value = fingerprint_input.value if isinstance(fingerprint_input, FingerprintInput) else fingerprint_input
    if not isinstance(value, str) or not value:
        raise VeriFactuFingerprintError("La cadena de huella VeriFactu es obligatoria.")
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def build_official_registration_payload(
    data: OfficialRegistrationData,
    *,
    system: VeriFactuSystemIdentity,
    fingerprint_input: FingerprintInput,
    fingerprint: str,
    is_first_record: bool,
) -> dict:
    """Build a logical official RegistroAlta DTO; XML serialization is a later phase."""
    previous = (
        {"PrimerRegistro": "S"}
        if is_first_record
        else {"RegistroAnterior": {"Huella": _required_text(data.previous_fingerprint, "Huella")}}
    )

    return {
        "schema_version": VERIFACTU_OFFICIAL_PAYLOAD_SCHEMA_VERSION,
        "record": "RegistroAlta",
        "RegistroAlta": {
            "IDFactura": {
                "IDEmisorFactura": _required_text(data.issuer_tax_id, "IDEmisorFactura"),
                "NumSerieFactura": _required_text(data.invoice_number, "NumSerieFactura"),
                "FechaExpedicionFactura": _date_dd_mm_yyyy(data.issue_date, "FechaExpedicionFactura"),
            },
            "TipoFactura": _required_text(data.invoice_type_code, "TipoFactura"),
            "CuotaTotal": _money_string(data.tax_amount, "CuotaTotal"),
            "ImporteTotal": _money_string(data.total_amount, "ImporteTotal"),
            "Encadenamiento": previous,
            "SistemaInformatico": {
                "NombreRazon": _required_text(system.producer_name, "producer_name"),
                "NIF": _required_text(system.producer_tax_id, "producer_tax_id"),
                "NombreSistemaInformatico": _required_text(system.system_name, "system_name"),
                "IdSistemaInformatico": _required_text(system.system_id, "system_id"),
                "Version": _required_text(system.system_version, "system_version"),
                "NumeroInstalacion": _required_text(system.installation_id, "installation_id"),
            },
            "FechaHoraHusoGenRegistro": _datetime_with_timezone(
                data.generation_timestamp,
                "FechaHoraHusoGenRegistro",
            ),
            "TipoHuella": VERIFACTU_FINGERPRINT_ALGORITHM,
            "Huella": _required_text(fingerprint, "Huella"),
        },
        "fingerprint_input": fingerprint_input.value,
    }


def normalize_system_identity(
    *,
    system_id,
    system_name,
    system_version,
    installation_id,
    producer_name,
    producer_tax_id,
) -> VeriFactuSystemIdentity:
    return VeriFactuSystemIdentity(
        system_id=_required_text(system_id, "system_id"),
        system_name=_required_text(system_name, "system_name"),
        system_version=_required_text(system_version, "system_version"),
        installation_id=_required_text(installation_id, "installation_id"),
        producer_name=_required_text(producer_name, "producer_name"),
        producer_tax_id=_required_text(producer_tax_id, "producer_tax_id"),
    )


def _required_text(value, field):
    text = _optional_text(value)
    if not text:
        raise VeriFactuFingerprintError(f"Campo obligatorio ausente: {field}.")
    if field == "NumSerieFactura":
        _validate_invoice_number(text)
    return text


def _optional_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validate_invoice_number(value):
    forbidden = {'"', "'", "<", ">", "="}
    if any(character in forbidden for character in value):
        raise VeriFactuFingerprintError("NumSerieFactura contiene caracteres no permitidos.")
    if any(ord(character) < 32 or ord(character) > 126 for character in value):
        raise VeriFactuFingerprintError("NumSerieFactura debe usar caracteres ASCII imprimibles.")


def _date_dd_mm_yyyy(value, field):
    if isinstance(value, datetime):
        value = value.date()
    if not isinstance(value, date):
        raise VeriFactuFingerprintError(f"Fecha invalida en {field}.")
    return value.strftime("%d-%m-%Y")


def _datetime_with_timezone(value, field):
    if not isinstance(value, datetime):
        raise VeriFactuFingerprintError(f"Fecha/hora invalida en {field}.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise VeriFactuFingerprintError(f"{field} debe incluir huso horario.")
    return value.replace(microsecond=0).isoformat()


def _money_string(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise VeriFactuFingerprintError(f"Importe no valido en {field}.") from exc
    if not amount.is_finite():
        raise VeriFactuFingerprintError(f"Importe no valido en {field}.")
    return str(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

"""Amazon Textract AnalyzeExpense adapter for reviewable supplier invoices."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
import re

from pypdf import PdfReader

from api.supplier_invoice_extraction_provider import (
    SupplierInvoiceExtractionProvider,
    SupplierInvoiceExtractionProviderError,
    build_empty_supplier_invoice_extraction_payload,
)

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError, ReadTimeoutError
except ImportError:  # pragma: no cover - raised explicitly when textract is configured.
    boto3 = None
    Config = None

    class BotoCoreError(Exception):
        pass

    class ClientError(Exception):
        pass

    class EndpointConnectionError(Exception):
        pass

    class ReadTimeoutError(Exception):
        pass


TEXTRACT_MAX_SYNC_BYTES = 10 * 1024 * 1024
TEXTRACT_SUPPORTED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
_SPANISH_TAX_ID = re.compile(r"(?<![A-Z0-9])(?:[0-9]{8}[A-Z]|[A-HJ-NP-SUVW][0-9]{7}[0-9A-J])(?![A-Z0-9])", re.I)
_PERCENT = re.compile(r"([0-9]+(?:[.,][0-9]+)?)\s*%")


@dataclass(frozen=True)
class TextractSupplierInvoiceExtractionSettings:
    region: str
    access_key_id: str
    secret_access_key: str
    connect_timeout_seconds: int = 5
    read_timeout_seconds: int = 30

    @classmethod
    def from_app_config(cls, config):
        values = {
            "region": str(config.get("AWS_TEXTRACT_REGION") or "").strip(),
            "access_key_id": str(config.get("AWS_TEXTRACT_ACCESS_KEY_ID") or "").strip(),
            "secret_access_key": str(config.get("AWS_TEXTRACT_SECRET_ACCESS_KEY") or "").strip(),
        }
        if not all(values.values()) or boto3 is None:
            raise SupplierInvoiceExtractionProviderError(
                "La configuración de Amazon Textract no está disponible.", code="provider_unavailable"
            )
        try:
            connect_timeout = int(config.get("AWS_TEXTRACT_CONNECT_TIMEOUT_SECONDS", 5))
            read_timeout = int(config.get("AWS_TEXTRACT_READ_TIMEOUT_SECONDS", 30))
        except (TypeError, ValueError) as exc:
            raise SupplierInvoiceExtractionProviderError(
                "La configuración de tiempo de espera de Textract no es válida.", code="provider_unavailable"
            ) from exc
        if connect_timeout <= 0 or read_timeout <= 0:
            raise SupplierInvoiceExtractionProviderError(
                "La configuración de tiempo de espera de Textract no es válida.", code="provider_unavailable"
            )
        return cls(**values, connect_timeout_seconds=connect_timeout, read_timeout_seconds=read_timeout)


class TextractSupplierInvoiceExtractionProvider(SupplierInvoiceExtractionProvider):
    """Calls AnalyzeExpense and retains only the canonical proposal, never raw OCR."""

    provider_name = "textract"
    extractor_version = "analyze-expense-v1"

    def __init__(self, settings, *, client=None):
        self.settings = settings
        self.client = client or boto3.client(
            "textract",
            region_name=settings.region,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
            config=Config(
                connect_timeout=settings.connect_timeout_seconds,
                read_timeout=settings.read_timeout_seconds,
                retries={"max_attempts": 2, "mode": "standard"},
            ),
        )

    def extract(self, document_bytes, mime_type):
        _validate_document(document_bytes, mime_type)
        try:
            response = self.client.analyze_expense(Document={"Bytes": document_bytes})
        except (ReadTimeoutError, EndpointConnectionError) as exc:
            raise SupplierInvoiceExtractionProviderError(
                "Amazon Textract no ha respondido a tiempo.", code="provider_timeout"
            ) from exc
        except ClientError as exc:
            raise _client_error(exc) from exc
        except (BotoCoreError, OSError) as exc:
            raise SupplierInvoiceExtractionProviderError(
                "Amazon Textract no está disponible.", code="provider_unavailable"
            ) from exc
        return build_textract_supplier_invoice_extraction_payload(response)


def _validate_document(document_bytes, mime_type):
    if mime_type not in TEXTRACT_SUPPORTED_MIME_TYPES:
        raise SupplierInvoiceExtractionProviderError(
            "El formato del documento no es compatible con Textract.", code="unsupported_document"
        )
    if not isinstance(document_bytes, bytes) or not document_bytes:
        raise SupplierInvoiceExtractionProviderError("El documento no es válido para Textract.", code="unsupported_document")
    if len(document_bytes) > TEXTRACT_MAX_SYNC_BYTES:
        raise SupplierInvoiceExtractionProviderError("El documento supera el límite de Textract.", code="document_too_large")
    if mime_type == "application/pdf":
        try:
            pages = len(PdfReader(BytesIO(document_bytes)).pages)
        except Exception as exc:
            raise SupplierInvoiceExtractionProviderError("El PDF no es válido para Textract.", code="unsupported_document") from exc
        if pages != 1:
            raise SupplierInvoiceExtractionProviderError(
                "Textract solo admite PDFs de una página en esta extracción.", code="unsupported_document"
            )


def _client_error(error):
    source_code = str(error.response.get("Error", {}).get("Code") or "")
    mapping = {
        "AccessDeniedException": ("La cuenta no tiene permiso para usar Textract.", "access_denied"),
        "ThrottlingException": ("Amazon Textract está temporalmente ocupado.", "throttled"),
        "ProvisionedThroughputExceededException": ("Amazon Textract está temporalmente ocupado.", "throttled"),
        "DocumentTooLargeException": ("El documento supera el límite de Textract.", "document_too_large"),
        "UnsupportedDocumentException": ("El formato del documento no es compatible con Textract.", "unsupported_document"),
        "BadDocumentException": ("Textract no puede leer el documento.", "unsupported_document"),
        "InvalidParameterException": ("El documento no es válido para Textract.", "unsupported_document"),
    }
    message, code = mapping.get(source_code, ("Amazon Textract no está disponible.", "provider_unavailable"))
    return SupplierInvoiceExtractionProviderError(message, code=code)


def build_textract_supplier_invoice_extraction_payload(response):
    """Reduce an AnalyzeExpense response to canonical schema v1 without raw OCR data."""
    if not isinstance(response, dict) or not isinstance(response.get("ExpenseDocuments"), list):
        raise SupplierInvoiceExtractionProviderError("Textract ha devuelto una respuesta no válida.", code="invalid_response")
    payload = build_empty_supplier_invoice_extraction_payload()
    payload["warnings"] = []
    # AnalyzeExpense cannot safely determine these fiscal classifications.
    payload["fields"]["fiscal_invoice_type"] = {"value": None, "confidence": None, "source": None}
    payload["fields"]["tax_treatment"] = {"value": None, "confidence": None, "source": None}
    documents = response["ExpenseDocuments"]
    if len(documents) != 1:
        payload["warnings"].append("El documento contiene varias facturas y requiere revisión manual.")
        return payload
    fields = documents[0].get("SummaryFields")
    if not isinstance(fields, list):
        raise SupplierInvoiceExtractionProviderError("Textract ha devuelto una respuesta no válida.", code="invalid_response")

    _set_text(payload, "supplier_legal_name", _select_single(fields, {"VENDOR_NAME"}, vendor_only=True))
    _set_text(payload, "supplier_invoice_number", _select_single(fields, {"INVOICE_RECEIPT_ID"}))
    _set_date(payload, _select_single(fields, {"INVOICE_RECEIPT_DATE"}))
    total = _select_total(fields)
    _set_money(payload, "total_amount", total)
    _set_currency(payload, total)
    _set_vendor_tax_id(payload, [field for field in fields if _is_vendor_field(field)])
    payload["tax_breakdowns"] = _extract_tax_breakdowns(fields, payload)
    payload["warnings"].extend((
        "El tipo fiscal requiere revisión manual.",
        "El tratamiento fiscal requiere revisión manual.",
    ))
    return payload


def _set_text(payload, name, candidate):
    if candidate:
        payload["fields"][name] = _canonical(candidate["value"], candidate)


def _set_date(payload, candidate):
    if not candidate:
        return
    value = _parse_date(candidate["value"])
    if value is None:
        payload["warnings"].append("La fecha detectada es ambigua y requiere revisión manual.")
    else:
        payload["fields"]["issue_date"] = _canonical(value, candidate)


def _set_money(payload, name, candidate):
    if not candidate:
        return
    value = _parse_money(candidate["value"])
    if value is None:
        payload["warnings"].append("El total detectado no tiene un formato válido.")
    else:
        payload["fields"][name] = _canonical(_money(value), candidate)
    if candidate.get("multiple"):
        payload["warnings"].append("Se han detectado varios totales; revisa el importe propuesto.")


def _set_currency(payload, candidate):
    code = (candidate or {}).get("raw", {}).get("Currency", {}).get("Code")
    if isinstance(code, str) and code.strip():
        payload["fields"]["currency"] = _canonical(code.strip().upper(), candidate)


def _set_vendor_tax_id(payload, fields):
    matches = []
    source = None
    for field in fields:
        for text in (_field_value(field), _field_label(field)):
            if text:
                found = _SPANISH_TAX_ID.findall(text.upper())
                if found:
                    matches.extend(found)
                    source = source or field
    matches = list(dict.fromkeys(matches))
    if len(matches) == 1:
        payload["fields"]["supplier_tax_id"] = _canonical(matches[0], _candidate(source))
    elif len(matches) > 1:
        payload["warnings"].append("Se han detectado varios NIF/CIF de proveedor.")


def _extract_tax_breakdowns(fields, payload):
    total = payload["fields"]["total_amount"]["value"]
    if total is None:
        return []
    taxes, bases = [], []
    for field in fields:
        label = f"{_field_label(field)} {_field_type(field)}".lower()
        value = _parse_money(_field_value(field))
        rate = _first_rate(_field_label(field), _field_value(field))
        if value is None:
            continue
        if (_field_type(field) == "TAX" or "iva" in label or "vat" in label) and rate is not None:
            taxes.append((value, rate, field))
        if _field_type(field) == "SUBTOTAL" or "base imponible" in label:
            bases.append((value, rate, field))
    results = []
    for tax_amount, rate, tax_field in taxes:
        matches = [(base, base_field) for base, base_rate, base_field in bases
                   if base_rate in {None, rate} and _tax_matches(base, rate, tax_amount)]
        if len(matches) != 1:
            payload["warnings"].append("No se ha podido identificar una base imponible de IVA de forma inequívoca.")
            continue
        base, base_field = matches[0]
        results.append({
            "tax_base": _money(base), "tax_rate": _money(rate), "tax_amount": _money(tax_amount),
            "deductible_tax_amount": None, "confidence": _minimum_confidence(base_field, tax_field),
            "source": {"page": _page(tax_field) or _page(base_field)},
        })
    if results:
        calculated = sum((Decimal(row["tax_base"]) + Decimal(row["tax_amount"]) for row in results), Decimal("0.00"))
        if calculated != Decimal(total):
            payload["warnings"].append("Los desgloses de IVA detectados no coinciden con el total de la factura.")
            return []
    elif taxes:
        payload["warnings"].append("Se ha detectado un tipo de IVA sin base y cuota verificables.")
    return results


def _select_total(fields):
    items = [_candidate(field) for field in fields if _field_type(field) == "TOTAL" and _field_value(field)]
    if not items:
        return None
    values = {item["value"] for item in items}
    items.sort(key=lambda item: ("total factura" in item["label"].lower(), "total" in item["label"].lower(), item["confidence"] or 0), reverse=True)
    if len(values) > 1:
        items[0]["multiple"] = True
    return items[0]


def _select_single(fields, field_types, *, vendor_only=False):
    items = [_candidate(field) for field in fields if _field_type(field) in field_types and _field_value(field)
             and (not vendor_only or _is_vendor_field(field))]
    if not items or len({item["value"] for item in items}) != 1:
        return None
    return max(items, key=lambda item: item["confidence"] or 0)


def _candidate(field):
    return {"value": _field_value(field), "label": _field_label(field), "confidence": _confidence(field), "page": _page(field), "raw": field}


def _canonical(value, candidate):
    return {"value": value, "confidence": candidate["confidence"], "source": {"page": candidate["page"]} if candidate["page"] else None}


def _field_type(field):
    return str((field.get("Type") or {}).get("Text") or "").upper()


def _field_value(field):
    value = (field.get("ValueDetection") or {}).get("Text")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _field_label(field):
    value = (field.get("LabelDetection") or {}).get("Text")
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _confidence(field):
    value = (field.get("ValueDetection") or {}).get("Confidence")
    if not isinstance(value, (int, float)):
        return None
    return round(float(value) / 100 if value > 1 else float(value), 6)


def _page(field):
    value = field.get("PageNumber")
    return value if isinstance(value, int) and value > 0 else None


def _is_vendor_field(field):
    return any("VENDOR" in (group.get("Types") or []) for group in (field.get("GroupProperties") or []) if isinstance(group, dict))


def _parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        pass
    match = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", value.strip())
    if not match:
        return None
    day, month, year = map(int, match.groups())
    if day <= 12 and month <= 12:
        return None
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return None


def _parse_money(value):
    if not isinstance(value, str):
        return None
    value = re.sub(r"[^0-9,.-]", "", value)
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".") if value.rfind(",") > value.rfind(".") else value.replace(",", "")
    elif "," in value:
        value = value.replace(",", ".")
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() and result >= 0 else None


def _parse_rate(value):
    match = _PERCENT.search(value or "")
    return _parse_money(match.group(1)) if match else None


def _first_rate(*values):
    for value in values:
        rate = _parse_rate(value)
        if rate is not None:
            return rate
    return None


def _money(value):
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def _tax_matches(base, rate, tax_amount):
    return (base * rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == tax_amount


def _minimum_confidence(*fields):
    values = [_confidence(field) for field in fields]
    values = [value for value in values if value is not None]
    return min(values) if values else None

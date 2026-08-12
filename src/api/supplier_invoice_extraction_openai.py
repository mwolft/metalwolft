"""OpenAI benchmark provider for non-fiscal supplier invoice extraction."""

import base64
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json

from api.supplier_invoice_extraction_provider import (
    SupplierInvoiceExtractionProvider,
    SupplierInvoiceExtractionProviderError,
    build_empty_supplier_invoice_extraction_payload,
)

try:
    from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError
except ImportError:  # pragma: no cover - reported explicitly when the provider is configured.
    OpenAI = None

    class APIConnectionError(Exception):
        pass

    class APIStatusError(Exception):
        pass

    class APITimeoutError(Exception):
        pass

    class RateLimitError(Exception):
        pass


OPENAI_SUPPORTED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
OPENAI_MAX_DOCUMENT_BYTES = 15 * 1024 * 1024
DEFAULT_OPENAI_SUPPLIER_INVOICE_MODEL = "gpt-4.1-mini"

_REVIEW_WARNINGS = (
    "El tipo fiscal requiere revisión manual.",
    "El tratamiento fiscal requiere revisión manual.",
)
_EXTRACTION_INSTRUCTIONS = """Extrae una propuesta de una factura recibida española.

Identifica siempre el emisor/proveedor, nunca el receptor, cliente o destinatario.
Devuelve solo la razón social o nombre comercial del proveedor, sin etiquetas como
"Responsable" ni texto explicativo. Asocia el NIF/CIF al proveedor correcto. Distingue
el número de factura de códigos internos, de cliente, pedido o albarán. Interpreta las
fechas como españolas; operation_date solo puede aparecer si está explícita e
inequívocamente diferenciada de la fecha de expedición. Usa importes decimales con punto
y exactamente dos decimales. Identifica base imponible, tipo y cuota de IVA, y el total.
No confundas recargo de equivalencia con cuota de IVA. Puede haber varios tipos de IVA.
No inventes: cuando un dato no sea seguro, devuelve null. deductible_tax_amount siempre
es null. fiscal_invoice_type y tax_treatment siempre son null. concept solo si el
documento permite una descripción objetiva y breve."""

_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "supplier_legal_name",
        "supplier_tax_id",
        "supplier_invoice_number",
        "issue_date",
        "operation_date",
        "concept",
        "currency",
        "total_amount",
        "tax_breakdowns",
    ],
    "properties": {
        "supplier_legal_name": {"type": ["string", "null"]},
        "supplier_tax_id": {"type": ["string", "null"]},
        "supplier_invoice_number": {"type": ["string", "null"]},
        "issue_date": {"type": ["string", "null"]},
        "operation_date": {"type": ["string", "null"]},
        "concept": {"type": ["string", "null"]},
        "currency": {"type": ["string", "null"]},
        "total_amount": {"type": ["string", "null"]},
        "tax_breakdowns": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["tax_base", "tax_rate", "tax_amount"],
                "properties": {
                    "tax_base": {"type": "string"},
                    "tax_rate": {"type": "string"},
                    "tax_amount": {"type": "string"},
                },
            },
        },
    },
}


@dataclass(frozen=True)
class OpenAISupplierInvoiceExtractionSettings:
    api_key: str
    model: str = DEFAULT_OPENAI_SUPPLIER_INVOICE_MODEL
    timeout_seconds: int = 45

    @classmethod
    def from_app_config(cls, config):
        api_key = str(config.get("OPENAI_API_KEY") or "").strip()
        model = str(config.get("OPENAI_SUPPLIER_INVOICE_MODEL") or DEFAULT_OPENAI_SUPPLIER_INVOICE_MODEL).strip()
        try:
            timeout_seconds = int(config.get("OPENAI_SUPPLIER_INVOICE_TIMEOUT_SECONDS", 45))
        except (TypeError, ValueError) as exc:
            raise SupplierInvoiceExtractionProviderError(
                "La configuración de OpenAI no es válida.", code="provider_unavailable"
            ) from exc
        if not api_key or not model or timeout_seconds <= 0 or OpenAI is None:
            raise SupplierInvoiceExtractionProviderError(
                "La configuración de OpenAI no está disponible.", code="provider_unavailable"
            )
        return cls(api_key=api_key, model=model, timeout_seconds=timeout_seconds)


class OpenAISupplierInvoiceExtractionProvider(SupplierInvoiceExtractionProvider):
    """Responses API provider that returns a reviewable canonical proposal only."""

    provider_name = "openai"
    extractor_version = "responses-structured-v1"

    def __init__(self, settings, *, client=None):
        self.settings = settings
        self.client = client or OpenAI(
            api_key=settings.api_key,
            timeout=settings.timeout_seconds,
            max_retries=0,
        )
        self.last_usage = None

    def extract(self, document_bytes, mime_type):
        _validate_document(document_bytes, mime_type)
        try:
            response = self.client.responses.create(
                model=self.settings.model,
                instructions=_EXTRACTION_INSTRUCTIONS,
                input=[{
                    "role": "user",
                    "content": [_document_input(document_bytes, mime_type)],
                }],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "supplier_invoice_extraction",
                        "strict": True,
                        "schema": _RESPONSE_SCHEMA,
                    },
                },
                store=False,
            )
        except APITimeoutError as exc:
            raise SupplierInvoiceExtractionProviderError(
                "OpenAI no ha respondido a tiempo.", code="provider_timeout"
            ) from exc
        except RateLimitError as exc:
            raise SupplierInvoiceExtractionProviderError(
                "OpenAI está temporalmente ocupado.", code="throttled"
            ) from exc
        except APIConnectionError as exc:
            raise SupplierInvoiceExtractionProviderError(
                "OpenAI no está disponible.", code="provider_unavailable"
            ) from exc
        except APIStatusError as exc:
            raise SupplierInvoiceExtractionProviderError(
                "OpenAI no ha podido procesar el documento.", code="provider_error"
            ) from exc
        except OSError as exc:
            raise SupplierInvoiceExtractionProviderError(
                "OpenAI no está disponible.", code="provider_unavailable"
            ) from exc

        self.last_usage = _safe_usage(response)
        try:
            proposal = json.loads(str(getattr(response, "output_text", "")))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SupplierInvoiceExtractionProviderError(
                "OpenAI ha devuelto una respuesta no válida.", code="invalid_response"
            ) from exc
        return build_openai_supplier_invoice_extraction_payload(proposal)


def build_openai_supplier_invoice_extraction_payload(proposal):
    """Convert strict model output into canonical schema v1 without persisting it."""
    if not isinstance(proposal, dict) or set(proposal) != set(_RESPONSE_SCHEMA["required"]):
        raise SupplierInvoiceExtractionProviderError(
            "OpenAI ha devuelto una respuesta no válida.", code="invalid_response"
        )
    payload = build_empty_supplier_invoice_extraction_payload()
    payload["warnings"] = list(_REVIEW_WARNINGS)
    fields = payload["fields"]
    fields["fiscal_invoice_type"]["value"] = None
    fields["tax_treatment"]["value"] = None
    for name in (
        "supplier_legal_name",
        "supplier_tax_id",
        "supplier_invoice_number",
        "concept",
    ):
        fields[name]["value"] = _optional_text(proposal[name], name)
    fields["supplier_tax_id"]["value"] = _uppercase(fields["supplier_tax_id"]["value"])
    fields["currency"]["value"] = _uppercase(_optional_text(proposal["currency"], "currency"))
    fields["issue_date"]["value"] = _optional_date(proposal["issue_date"], "issue_date")
    fields["operation_date"]["value"] = _optional_date(proposal["operation_date"], "operation_date")
    fields["total_amount"]["value"] = _optional_money(proposal["total_amount"], "total_amount")

    breakdowns = []
    try:
        for item in proposal["tax_breakdowns"]:
            if not isinstance(item, dict) or set(item) != {"tax_base", "tax_rate", "tax_amount"}:
                raise ValueError("invalid breakdown")
            breakdowns.append({
                "tax_base": _money(item["tax_base"], "tax_base"),
                "tax_rate": _money(item["tax_rate"], "tax_rate"),
                "tax_amount": _money(item["tax_amount"], "tax_amount"),
                "deductible_tax_amount": None,
                "confidence": None,
                "source": None,
            })
    except (TypeError, ValueError, InvalidOperation):
        payload["warnings"].append("El desglose de IVA propuesto requiere revisión manual.")
        return payload

    if breakdowns and not _breakdowns_reconcile(breakdowns, fields["total_amount"]["value"]):
        payload["warnings"].append("El desglose de IVA propuesto no coincide con el total de la factura.")
    else:
        payload["tax_breakdowns"] = breakdowns
    return payload


def _document_input(document_bytes, mime_type):
    encoded = base64.b64encode(document_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{encoded}"
    if mime_type == "application/pdf":
        return {"type": "input_file", "filename": "supplier-invoice.pdf", "file_data": data_url}
    return {"type": "input_image", "image_url": data_url}


def _validate_document(document_bytes, mime_type):
    if mime_type not in OPENAI_SUPPORTED_MIME_TYPES:
        raise SupplierInvoiceExtractionProviderError(
            "El formato del documento no es compatible con OpenAI.", code="unsupported_document"
        )
    if not isinstance(document_bytes, bytes) or not document_bytes:
        raise SupplierInvoiceExtractionProviderError("El documento no es válido para OpenAI.", code="unsupported_document")
    if len(document_bytes) > OPENAI_MAX_DOCUMENT_BYTES:
        raise SupplierInvoiceExtractionProviderError("El documento supera el límite de OpenAI.", code="document_too_large")


def _optional_text(value, field):
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise SupplierInvoiceExtractionProviderError(
            "OpenAI ha devuelto una respuesta no válida.", code="invalid_response"
        )
    return value.strip()


def _uppercase(value):
    return value.upper() if value else None


def _optional_date(value, field):
    value = _optional_text(value, field)
    if value is None:
        return None
    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue
    raise SupplierInvoiceExtractionProviderError(
        "OpenAI ha devuelto una respuesta no válida.", code="invalid_response"
    )


def _optional_money(value, field):
    if value is None:
        return None
    return _money(value, field)


def _money(value, field):
    if not isinstance(value, str):
        raise ValueError(field)
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(field) from exc
    if not amount.is_finite() or amount < Decimal("0.00") or amount.as_tuple().exponent < -2:
        raise ValueError(field)
    return f"{amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def _breakdowns_reconcile(breakdowns, total_amount):
    if total_amount is None:
        return False
    total = Decimal(total_amount)
    calculated_total = Decimal("0.00")
    for item in breakdowns:
        base = Decimal(item["tax_base"])
        rate = Decimal(item["tax_rate"])
        tax = Decimal(item["tax_amount"])
        if (base * rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) != tax:
            return False
        calculated_total += base + tax
    return calculated_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == total


def _safe_usage(response):
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    return {
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }

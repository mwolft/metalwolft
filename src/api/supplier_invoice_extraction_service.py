"""Build, persist and apply reviewable supplier invoice extraction proposals."""

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
import os

from flask import current_app

from api.models import (
    SupplierInvoice,
    SupplierInvoiceDocument,
    SupplierInvoiceExtraction,
    SupplierInvoiceTaxBreakdown,
    db,
)
from api.supplier_invoice_document_storage import get_supplier_invoice_document_storage
from api.supplier_invoice_extraction_provider import (
    FakeSupplierInvoiceExtractionProvider,
    SupplierInvoiceExtractionProviderError,
)
from api.supplier_invoice_extraction_textract import (
    TextractSupplierInvoiceExtractionProvider,
    TextractSupplierInvoiceExtractionSettings,
)
from api.supplier_invoice_extraction_openai import (
    OpenAISupplierInvoiceExtractionProvider,
    OpenAISupplierInvoiceExtractionSettings,
)
from api.supplier_invoice_registration_service import (
    apply_supplier_invoice_expense_classification_defaults,
)


EXTRACTION_SCHEMA_VERSION = 1
EXTRACTION_FIELD_NAMES = (
    "supplier_legal_name",
    "supplier_tax_id",
    "supplier_invoice_number",
    "issue_date",
    "operation_date",
    "concept",
    "currency",
    "total_amount",
    "fiscal_invoice_type",
    "tax_treatment",
)
EDITABLE_SUPPLIER_INVOICE_STATUSES = {
    SupplierInvoice.STATUS_DRAFT,
    SupplierInvoice.STATUS_NEEDS_REVIEW,
}


class SupplierInvoiceExtractionError(Exception):
    """Base error for the non-fiscal extraction workflow."""


class SupplierInvoiceExtractionEligibilityError(SupplierInvoiceExtractionError):
    """Raised when a document cannot be processed or applied."""


class SupplierInvoiceExtractionPayloadError(SupplierInvoiceExtractionError):
    """Raised when a provider proposal is not canonical schema v1."""


class SupplierInvoiceExtractionApplyError(SupplierInvoiceExtractionError):
    """Raised when reviewed values cannot be safely copied to a draft."""


@dataclass(frozen=True)
class SupplierInvoiceExtractionResult:
    extraction: SupplierInvoiceExtraction
    succeeded: bool


def get_supplier_invoice_extraction_provider(app):
    provider = str(app.config.get("SUPPLIER_INVOICE_EXTRACTION_PROVIDER") or "fake").strip().lower()
    if provider == "fake":
        if os.getenv("APP_ENV", "").strip().lower() == "production":
            raise SupplierInvoiceExtractionEligibilityError(
                "Configura Amazon Textract antes de extraer documentos en producción."
            )
        return FakeSupplierInvoiceExtractionProvider(
            payload=app.config.get("SUPPLIER_INVOICE_EXTRACTION_FAKE_PAYLOAD"),
        )
    if provider == "textract":
        return TextractSupplierInvoiceExtractionProvider(
            TextractSupplierInvoiceExtractionSettings.from_app_config(app.config)
        )
    if provider == "openai":
        return OpenAISupplierInvoiceExtractionProvider(
            OpenAISupplierInvoiceExtractionSettings.from_app_config(app.config)
        )
    else:
        raise SupplierInvoiceExtractionEligibilityError(
            "El proveedor de extracción configurado no está disponible."
        )


def run_supplier_invoice_extraction(
    document,
    *,
    provider,
    db_session=None,
    storage=None,
    now=None,
):
    """Persist one explicit extraction attempt without modifying its draft invoice."""
    session = db_session or db.session
    _validate_document_eligibility(document)
    timestamp = _normalized_datetime(now or datetime.now(timezone.utc))
    extraction = SupplierInvoiceExtraction(
        supplier_invoice_document=document,
        provider=str(provider.provider_name),
        extractor_version=str(provider.extractor_version),
        status=SupplierInvoiceExtraction.STATUS_EXTRACTING,
        payload_schema_version=EXTRACTION_SCHEMA_VERSION,
        started_at=timestamp,
    )
    document.processing_status = SupplierInvoiceDocument.STATUS_EXTRACTING
    session.add(extraction)
    session.flush()

    try:
        storage = storage or get_supplier_invoice_document_storage(current_app)
        document_bytes = storage.get_document(storage_key=document.storage_key)
        payload = normalize_supplier_invoice_extraction_payload(
            provider.extract(document_bytes, document.mime_type)
        )
        payload["warnings"] = _merge_warnings(
            payload["warnings"],
            _find_extraction_duplicate_warnings(document, payload, db_session=session),
        )
    except SupplierInvoiceExtractionProviderError as error:
        return _mark_failed_extraction(extraction, document, error.code, timestamp)
    except SupplierInvoiceExtractionPayloadError:
        return _mark_failed_extraction(extraction, document, "invalid_payload", timestamp)
    except Exception:
        # Storage and unexpected provider failures remain traceable without logging document content.
        return _mark_failed_extraction(extraction, document, "extraction_failed", timestamp)

    extraction.extraction_payload = payload
    extraction.payload_hash = calculate_supplier_invoice_extraction_payload_hash(payload)
    extraction.completed_at = timestamp
    extraction.error_code = None
    if payload["warnings"]:
        extraction.status = SupplierInvoiceExtraction.STATUS_NEEDS_REVIEW
        document.processing_status = SupplierInvoiceDocument.STATUS_NEEDS_REVIEW
    else:
        extraction.status = SupplierInvoiceExtraction.STATUS_EXTRACTED
        document.processing_status = SupplierInvoiceDocument.STATUS_EXTRACTED
    session.flush()
    return SupplierInvoiceExtractionResult(extraction=extraction, succeeded=True)


def apply_supplier_invoice_extraction(
    extraction,
    supplier_invoice,
    *,
    replace_existing_fields=False,
    replace_tax_breakdowns=False,
    deductible_tax_amounts=None,
    db_session=None,
):
    """Copy a reviewed proposal to an editable draft, never to fiscal state."""
    session = db_session or db.session
    _validate_extraction_application(extraction, supplier_invoice)
    payload = extraction.extraction_payload
    fields = payload["fields"]
    updates = _collect_scalar_updates(supplier_invoice, fields, bool(replace_existing_fields))

    breakdowns = payload["tax_breakdowns"]
    if breakdowns and not replace_tax_breakdowns:
        raise SupplierInvoiceExtractionApplyError(
            "Confirma expresamente el reemplazo de los desgloses de IVA."
        )
    prepared_breakdowns = []
    if breakdowns:
        prepared_breakdowns = _prepare_tax_breakdowns_for_application(
            breakdowns,
            deductible_tax_amounts,
        )

    for attribute, value in updates.items():
        setattr(supplier_invoice, attribute, value)
    extracted_issue_date = fields["issue_date"]["value"]
    if extracted_issue_date is not None:
        extracted_issue_date = _convert_field_value("issue_date", extracted_issue_date)
        if supplier_invoice.operation_date is None:
            supplier_invoice.operation_date = extracted_issue_date
        supplier_invoice.received_at = datetime.combine(extracted_issue_date, time.min)
    if breakdowns:
        for item in list(supplier_invoice.tax_breakdowns):
            session.delete(item)
        for item in prepared_breakdowns:
            session.add(SupplierInvoiceTaxBreakdown(supplier_invoice=supplier_invoice, **item))

    # Classify only after the extracted supplier and VAT bases are on the draft.
    apply_supplier_invoice_expense_classification_defaults(supplier_invoice)

    # An extracted proposal always requires an explicit human registration step.
    supplier_invoice.status = SupplierInvoice.STATUS_NEEDS_REVIEW
    extraction.status = SupplierInvoiceExtraction.STATUS_APPLIED
    extraction.supplier_invoice_document.processing_status = SupplierInvoiceDocument.STATUS_APPLIED
    session.flush()
    return supplier_invoice


def normalize_supplier_invoice_extraction_payload(payload):
    if not isinstance(payload, dict) or payload.get("schema_version") != EXTRACTION_SCHEMA_VERSION:
        raise SupplierInvoiceExtractionPayloadError("El esquema de extracción no es compatible.")
    raw_fields = payload.get("fields")
    if not isinstance(raw_fields, dict) or set(raw_fields) != set(EXTRACTION_FIELD_NAMES):
        raise SupplierInvoiceExtractionPayloadError("Los campos de extracción no son completos.")

    fields = {}
    for name in EXTRACTION_FIELD_NAMES:
        fields[name] = _normalize_field(name, raw_fields[name])

    breakdowns = payload.get("tax_breakdowns")
    if not isinstance(breakdowns, list):
        raise SupplierInvoiceExtractionPayloadError("Los desgloses de IVA no son válidos.")
    normalized_breakdowns = [_normalize_breakdown(item) for item in breakdowns]
    warnings = _normalize_warnings(payload.get("warnings", []))
    if not normalized_breakdowns:
        warnings.append("No se ha detectado ningún desglose de IVA.")
    _append_financial_warnings(fields, normalized_breakdowns, warnings)
    return {
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "fields": fields,
        "tax_breakdowns": normalized_breakdowns,
        "warnings": _merge_warnings(warnings),
    }


def calculate_supplier_invoice_extraction_payload_hash(payload):
    normalized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(normalized).hexdigest()


def _validate_document_eligibility(document):
    if not isinstance(document, SupplierInvoiceDocument) or not getattr(document, "id", None):
        raise SupplierInvoiceExtractionEligibilityError("El documento recibido no existe.")
    invoice = document.supplier_invoice
    if invoice and invoice.status == SupplierInvoice.STATUS_REGISTERED:
        raise SupplierInvoiceExtractionEligibilityError(
            "No se puede extraer una factura recibida ya registrada."
        )


def _mark_failed_extraction(extraction, document, error_code, timestamp):
    extraction.status = SupplierInvoiceExtraction.STATUS_FAILED
    extraction.error_code = error_code
    extraction.completed_at = timestamp
    document.processing_status = SupplierInvoiceDocument.STATUS_FAILED
    return SupplierInvoiceExtractionResult(extraction=extraction, succeeded=False)


def _normalize_field(name, field):
    if not isinstance(field, dict) or set(field) != {"value", "confidence", "source"}:
        raise SupplierInvoiceExtractionPayloadError(f"El campo {name} no es válido.")
    value = field["value"]
    if name in {"total_amount"}:
        value = None if value is None else _money_string(value, name)
    elif name in {"issue_date", "operation_date"}:
        value = None if value is None else _date_string(value, name)
    elif name == "currency":
        value = None if value is None else _required_text(value, name).upper()
    elif name == "supplier_tax_id":
        value = None if value is None else _required_text(value, name).upper()
    else:
        value = None if value is None else _required_text(value, name)
    return {
        "value": value,
        "confidence": _normalize_confidence(field["confidence"], name),
        "source": _normalize_source(field["source"], name),
    }


def _normalize_breakdown(item):
    expected = {"tax_base", "tax_rate", "tax_amount", "deductible_tax_amount", "confidence", "source"}
    if not isinstance(item, dict) or set(item) != expected:
        raise SupplierInvoiceExtractionPayloadError("El desglose de IVA no es válido.")
    if item["deductible_tax_amount"] is not None:
        raise SupplierInvoiceExtractionPayloadError(
            "La cuota deducible requiere revisión humana."
        )
    tax_base = _money_string(item["tax_base"], "tax_base")
    tax_rate = _money_string(item["tax_rate"], "tax_rate")
    tax_amount = _money_string(item["tax_amount"], "tax_amount")
    if any(Decimal(value) < Decimal("0.00") for value in (tax_base, tax_rate, tax_amount)):
        raise SupplierInvoiceExtractionPayloadError("Los importes de IVA no pueden ser negativos.")
    return {
        "tax_base": tax_base,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "deductible_tax_amount": None,
        "confidence": _normalize_confidence(item["confidence"], "tax_breakdowns"),
        "source": _normalize_source(item["source"], "tax_breakdowns"),
    }


def _append_financial_warnings(fields, breakdowns, warnings):
    currency = fields["currency"]["value"]
    if currency and currency != "EUR":
        warnings.append("La moneda extraída no está soportada en el alcance actual.")
    if fields["fiscal_invoice_type"]["value"] not in {None, "F1"}:
        warnings.append("El tipo fiscal extraído requiere revisión manual.")
    if fields["tax_treatment"]["value"] not in {None, "domestic_standard"}:
        warnings.append("El tratamiento fiscal extraído requiere revisión manual.")
    if not fields["supplier_tax_id"]["value"]:
        warnings.append("No se ha detectado un NIF/CIF de proveedor.")
    if not fields["issue_date"]["value"]:
        warnings.append("No se ha detectado una fecha de expedición.")
    if not fields["total_amount"]["value"]:
        warnings.append("No se ha detectado un total de factura.")
    if breakdowns:
        expected_total = sum(
            (Decimal(item["tax_base"]) + Decimal(item["tax_amount"]) for item in breakdowns),
            Decimal("0.00"),
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_amount = fields["total_amount"]["value"]
        if total_amount and Decimal(total_amount) != expected_total:
            warnings.append("El total extraído no coincide con la suma de las bases y cuotas de IVA.")
        for item in breakdowns:
            expected_tax = (
                Decimal(item["tax_base"]) * Decimal(item["tax_rate"]) / Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if Decimal(item["tax_amount"]) != expected_tax:
                warnings.append("Una cuota de IVA extraída no coincide con su base y tipo.")
                break


def _find_extraction_duplicate_warnings(document, payload, *, db_session):
    warnings = []
    same_hash = (
        db_session.query(SupplierInvoiceDocument)
        .filter(SupplierInvoiceDocument.sha256 == document.sha256)
        .filter(SupplierInvoiceDocument.id != document.id)
        .count()
    )
    if same_hash:
        warnings.append("Existe otro documento recibido con el mismo hash.")
    fields = payload["fields"]
    tax_id = fields["supplier_tax_id"]["value"]
    invoice_number = fields["supplier_invoice_number"]["value"]
    if tax_id and invoice_number:
        if (
            db_session.query(SupplierInvoice)
            .filter(SupplierInvoice.supplier_tax_id == tax_id)
            .filter(SupplierInvoice.supplier_invoice_number == invoice_number)
            .count()
        ):
            warnings.append("Existe una factura recibida con el mismo proveedor y número.")
    issue_date = fields["issue_date"]["value"]
    total_amount = fields["total_amount"]["value"]
    if issue_date and total_amount:
        if (
            db_session.query(SupplierInvoice)
            .filter(SupplierInvoice.issue_date == date.fromisoformat(issue_date))
            .filter(SupplierInvoice.total_amount == Decimal(total_amount))
            .count()
        ):
            warnings.append("Existe una factura recibida con la misma fecha e importe total.")
    return warnings


def _validate_extraction_application(extraction, supplier_invoice):
    if not isinstance(extraction, SupplierInvoiceExtraction) or not getattr(extraction, "id", None):
        raise SupplierInvoiceExtractionApplyError("La extracción no existe.")
    if extraction.status not in {
        SupplierInvoiceExtraction.STATUS_EXTRACTED,
        SupplierInvoiceExtraction.STATUS_NEEDS_REVIEW,
    }:
        raise SupplierInvoiceExtractionApplyError("La extracción no está disponible para aplicar.")
    if not isinstance(supplier_invoice, SupplierInvoice) or not getattr(supplier_invoice, "id", None):
        raise SupplierInvoiceExtractionApplyError("La factura recibida no existe.")
    if supplier_invoice.status not in EDITABLE_SUPPLIER_INVOICE_STATUSES:
        raise SupplierInvoiceExtractionApplyError("La factura recibida no puede modificarse desde su estado actual.")
    if extraction.supplier_invoice_document.supplier_invoice_id != supplier_invoice.id:
        raise SupplierInvoiceExtractionApplyError("La extracción no pertenece a esta factura recibida.")
    if not isinstance(extraction.extraction_payload, dict):
        raise SupplierInvoiceExtractionApplyError("La propuesta de extracción no es válida.")


def _collect_scalar_updates(supplier_invoice, fields, replace_existing_fields):
    mappings = {
        "supplier_legal_name": "supplier_legal_name",
        "supplier_tax_id": "supplier_tax_id",
        "supplier_invoice_number": "supplier_invoice_number",
        "issue_date": "issue_date",
        "operation_date": "operation_date",
        "concept": "concept",
        "currency": "currency",
        "total_amount": "total_amount",
        "fiscal_invoice_type": "fiscal_invoice_type",
        "tax_treatment": "tax_treatment",
    }
    updates = {}
    conflicts = []
    for field_name, attribute in mappings.items():
        value = fields[field_name]["value"]
        if value is None:
            continue
        converted = _convert_field_value(field_name, value)
        existing = getattr(supplier_invoice, attribute)
        if existing is not None and existing != converted and not replace_existing_fields:
            conflicts.append(field_name)
        elif existing != converted:
            updates[attribute] = converted
    if conflicts:
        raise SupplierInvoiceExtractionApplyError(
            "Confirma expresamente el reemplazo de los datos ya informados."
        )
    return updates


def _prepare_tax_breakdowns_for_application(breakdowns, deductible_tax_amounts):
    if not isinstance(deductible_tax_amounts, (list, tuple)) or len(deductible_tax_amounts) != len(breakdowns):
        raise SupplierInvoiceExtractionApplyError(
            "Indica la cuota deducible de cada desglose antes de aplicarlo."
        )
    prepared = []
    for position, (item, deductible_value) in enumerate(zip(breakdowns, deductible_tax_amounts), start=1):
        try:
            deductible = Decimal(_money_string(deductible_value, "deductible_tax_amount"))
        except SupplierInvoiceExtractionPayloadError as exc:
            raise SupplierInvoiceExtractionApplyError(
                "Indica la cuota deducible de cada desglose antes de aplicarlo."
            ) from exc
        tax_amount = Decimal(item["tax_amount"])
        if deductible > tax_amount:
            raise SupplierInvoiceExtractionApplyError(
                "La cuota deducible no puede superar la cuota soportada."
            )
        prepared.append(
            {
                "position": position,
                "tax_base": Decimal(item["tax_base"]),
                "tax_rate": Decimal(item["tax_rate"]),
                "tax_amount": tax_amount,
                "deductible_tax_amount": deductible,
            }
        )
    return prepared


def _convert_field_value(name, value):
    if name in {"issue_date", "operation_date"}:
        return date.fromisoformat(value)
    if name == "total_amount":
        return Decimal(value)
    return value


def _money_string(value, field):
    if isinstance(value, float) or not isinstance(value, str):
        raise SupplierInvoiceExtractionPayloadError(f"El importe {field} debe ser un decimal serializado.")
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise SupplierInvoiceExtractionPayloadError(f"El importe {field} no es válido.") from exc
    if not amount.is_finite() or amount.as_tuple().exponent < -2:
        raise SupplierInvoiceExtractionPayloadError(f"El importe {field} no es válido.")
    return f"{amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def _date_string(value, field):
    if not isinstance(value, str):
        raise SupplierInvoiceExtractionPayloadError(f"La fecha {field} no es válida.")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise SupplierInvoiceExtractionPayloadError(f"La fecha {field} no es válida.") from exc


def _required_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise SupplierInvoiceExtractionPayloadError(f"El valor {field} no es válido.")
    return value.strip()


def _normalize_confidence(value, field):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise SupplierInvoiceExtractionPayloadError(f"La confianza {field} no es válida.")
    return float(value)


def _normalize_source(value, field):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"page"}:
        raise SupplierInvoiceExtractionPayloadError(f"La fuente {field} no es válida.")
    page = value["page"]
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise SupplierInvoiceExtractionPayloadError(f"La fuente {field} no es válida.")
    return {"page": page}


def _normalize_warnings(value):
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise SupplierInvoiceExtractionPayloadError("Las advertencias no son válidas.")
    return [item.strip() for item in value]


def _merge_warnings(*groups):
    return list(dict.fromkeys(item for group in groups for item in group if item))


def _normalized_datetime(value):
    if not isinstance(value, datetime):
        raise SupplierInvoiceExtractionEligibilityError("La fecha de extracción no es válida.")
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value

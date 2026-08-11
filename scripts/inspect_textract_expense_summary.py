"""Print selected AnalyzeExpense SummaryFields for a private supplier document.

This is an operational diagnostic. It never persists the Textract response and
does not invoke the extraction workflow, so it cannot modify SupplierInvoice.
"""

import argparse
import hashlib
import inspect
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from app import app  # noqa: E402
from api.models import SupplierInvoiceDocument, SupplierInvoiceExtraction, db  # noqa: E402
from api.supplier_invoice_document_storage import get_supplier_invoice_document_storage  # noqa: E402
import api.supplier_invoice_extraction_textract as textract_mapper  # noqa: E402
from api.supplier_invoice_extraction_textract import (  # noqa: E402
    TextractSupplierInvoiceExtractionProvider,
    TextractSupplierInvoiceExtractionSettings,
    _validate_document,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Inspect Textract SummaryFields without persisting OCR data.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--document-id", type=int)
    group.add_argument("--extraction-id", type=int)
    group.add_argument("--latest-needs-review", action="store_true")
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize the in-memory AnalyzeExpense response through the production mapper.",
    )
    return parser.parse_args()


def resolve_document(args):
    if args.document_id:
        document = db.session.get(SupplierInvoiceDocument, args.document_id)
        if not document:
            raise RuntimeError("SupplierInvoiceDocument no encontrado.")
        return document
    if args.extraction_id:
        extraction = db.session.get(SupplierInvoiceExtraction, args.extraction_id)
    else:
        extraction = (
            db.session.query(SupplierInvoiceExtraction)
            .filter(SupplierInvoiceExtraction.status == SupplierInvoiceExtraction.STATUS_NEEDS_REVIEW)
            .order_by(SupplierInvoiceExtraction.id.desc())
            .first()
        )
    if not extraction:
        raise RuntimeError("No existe ninguna extracción en needs_review.")
    return extraction.supplier_invoice_document


def summary_field_row(field):
    value = field.get("ValueDetection") or {}
    label = field.get("LabelDetection") or {}
    groups = [
        ",".join(str(item) for item in group.get("Types", []))
        for group in field.get("GroupProperties", [])
        if isinstance(group, dict)
    ]
    return {
        "type": (field.get("Type") or {}).get("Text"),
        "label": label.get("Text"),
        "value": value.get("Text"),
        "confidence": value.get("Confidence"),
        "page": field.get("PageNumber"),
        "groups": groups or None,
        "field_keys": sorted(field.keys()),
        "type_keys": sorted((field.get("Type") or {}).keys()),
        "label_keys": sorted((field.get("LabelDetection") or {}).keys()),
        "value_keys": sorted((field.get("ValueDetection") or {}).keys()),
    }


def print_canonical_payload(payload):
    fields = payload["fields"]
    print("[Canonical payload via build_textract_supplier_invoice_extraction_payload]")
    for name in (
        "supplier_legal_name",
        "supplier_tax_id",
        "supplier_invoice_number",
        "issue_date",
        "total_amount",
    ):
        print(f"{name}={fields[name]['value']!r}")
    print(f"tax_breakdowns={payload['tax_breakdowns']!r}")
    print(f"warnings={payload['warnings']!r}")


def trace_normalize_response(response):
    """Trace mapper decisions in memory and restore every helper immediately."""
    mapper_path = inspect.getsourcefile(textract_mapper.build_textract_supplier_invoice_extraction_payload)
    mapper_source = Path(mapper_path).read_bytes() if mapper_path else b""
    print(
        "[Mapper trace] file={!r} sha256={} helpers={}".format(
            mapper_path,
            hashlib.sha256(mapper_source).hexdigest()[:12],
            ",".join(
                name
                for name in (
                    "_select_single",
                    "_select_vendor_name",
                    "_select_invoice_number",
                    "_set_vendor_tax_id",
                    "_set_date",
                    "_extract_tax_breakdowns",
                )
                if hasattr(textract_mapper, name)
            ),
        )
    )
    originals = {}

    def wrap(name, renderer):
        original = getattr(textract_mapper, name, None)
        if original is None:
            print(f"[Mapper trace] helper_missing={name}")
            return
        originals[name] = original

        def traced(*args, **kwargs):
            result = original(*args, **kwargs)
            print(renderer(args, kwargs, result))
            return result

        setattr(textract_mapper, name, traced)

    def candidate_value(candidate):
        return None if candidate is None else {
            "value": candidate.get("value"),
            "label": candidate.get("label"),
            "page": candidate.get("page"),
        }

    wrap(
        "_select_single",
        lambda args, kwargs, result: "[Mapper trace] select_single types={!r} vendor_only={!r} result={!r}".format(
            args[1] if len(args) > 1 else None,
            kwargs.get("vendor_only", False),
            candidate_value(result),
        ),
    )
    wrap(
        "_select_vendor_name",
        lambda args, kwargs, result: f"[Mapper trace] vendor_candidate={candidate_value(result)!r}",
    )
    wrap(
        "_select_invoice_number",
        lambda args, kwargs, result: f"[Mapper trace] invoice_candidate={candidate_value(result)!r}",
    )
    wrap(
        "_set_vendor_tax_id",
        lambda args, kwargs, result: "[Mapper trace] supplier_tax_id_after={!r}".format(
            args[0]["fields"]["supplier_tax_id"]["value"]
        ),
    )
    wrap(
        "_set_date",
        lambda args, kwargs, result: "[Mapper trace] issue_date_after={!r} spanish_context={!r}".format(
            args[0]["fields"]["issue_date"]["value"], kwargs.get("spanish_context")
        ),
    )
    wrap(
        "_extract_tax_breakdowns",
        lambda args, kwargs, result: f"[Mapper trace] tax_breakdowns={result!r}",
    )
    try:
        return textract_mapper.build_textract_supplier_invoice_extraction_payload(response)
    finally:
        for name, original in originals.items():
            setattr(textract_mapper, name, original)


def main():
    args = parse_args()
    with app.app_context():
        document = resolve_document(args)
        storage = get_supplier_invoice_document_storage(app)
        content = storage.get_document(storage_key=document.storage_key)
        _validate_document(content, document.mime_type)
        provider = TextractSupplierInvoiceExtractionProvider(
            TextractSupplierInvoiceExtractionSettings.from_app_config(app.config)
        )
        response = provider.client.analyze_expense(Document={"Bytes": content})
        # This is the exact in-memory normalizer used by provider.extract after AnalyzeExpense.
        canonical_payload = trace_normalize_response(response) if args.normalize else None

    expense_documents = response.get("ExpenseDocuments") if isinstance(response, dict) else None
    if not isinstance(expense_documents, list):
        raise RuntimeError("Textract no devolvió ExpenseDocuments.")
    print(f"document_id={document.id} mime_type={document.mime_type} expense_documents={len(expense_documents)}")
    for expense_index, expense_document in enumerate(expense_documents, start=1):
        fields = expense_document.get("SummaryFields") or []
        print(f"[ExpenseDocument {expense_index}] summary_fields={len(fields)}")
        for field in fields:
            row = summary_field_row(field)
            print(
                "type={type!r} label={label!r} value={value!r} confidence={confidence!r} "
                "page={page!r} groups={groups!r} field_keys={field_keys!r} type_keys={type_keys!r} "
                "label_keys={label_keys!r} value_keys={value_keys!r}".format(**row)
            )
    if canonical_payload is not None:
        print_canonical_payload(canonical_payload)


if __name__ == "__main__":
    main()

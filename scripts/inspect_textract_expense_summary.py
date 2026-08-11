"""Print selected AnalyzeExpense SummaryFields for a private supplier document.

This is an operational diagnostic. It never persists the Textract response and
does not invoke the extraction workflow, so it cannot modify SupplierInvoice.
"""

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from app import app  # noqa: E402
from api.models import SupplierInvoiceDocument, SupplierInvoiceExtraction, db  # noqa: E402
from api.supplier_invoice_document_storage import get_supplier_invoice_document_storage  # noqa: E402
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
    }


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
                "page={page!r} groups={groups!r}".format(**row)
            )


if __name__ == "__main__":
    main()

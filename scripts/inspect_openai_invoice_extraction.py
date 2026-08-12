"""Run one private OpenAI supplier-invoice benchmark without persistence."""

import argparse
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from app import app  # noqa: E402
from api.models import SupplierInvoiceDocument, SupplierInvoiceExtraction, db  # noqa: E402
from api.supplier_invoice_document_storage import get_supplier_invoice_document_storage  # noqa: E402
from api.supplier_invoice_extraction_openai import (  # noqa: E402
    OpenAISupplierInvoiceExtractionProvider,
    OpenAISupplierInvoiceExtractionSettings,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark OpenAI on one private supplier invoice.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--document-id", type=int)
    group.add_argument("--extraction-id", type=int)
    return parser.parse_args()


def resolve_document(args):
    if args.document_id:
        document = db.session.get(SupplierInvoiceDocument, args.document_id)
        if document:
            return document
    else:
        extraction = db.session.get(SupplierInvoiceExtraction, args.extraction_id)
        if extraction:
            return extraction.supplier_invoice_document
    raise RuntimeError("No se ha encontrado el documento recibido solicitado.")


def main():
    args = parse_args()
    with app.app_context():
        document = resolve_document(args)
        content = get_supplier_invoice_document_storage(app).get_document(storage_key=document.storage_key)
        provider = OpenAISupplierInvoiceExtractionProvider(
            OpenAISupplierInvoiceExtractionSettings.from_app_config(app.config)
        )
        payload = provider.extract(content, document.mime_type)

    # The private document and model response are never stored by this script.
    print(json.dumps({"payload": payload, "usage": provider.last_usage}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

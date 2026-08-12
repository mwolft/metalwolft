"""Provider boundary for non-fiscal supplier invoice document extraction."""

from abc import ABC, abstractmethod
from copy import deepcopy


class SupplierInvoiceExtractionProviderError(Exception):
    """Raised when an extraction provider cannot return a proposal."""

    def __init__(self, message="No se ha podido extraer una propuesta.", *, code="provider_error"):
        super().__init__(message)
        self.code = code


class SupplierInvoiceExtractionProvider(ABC):
    provider_name = "unknown"
    extractor_version = "unknown"

    @abstractmethod
    def extract(self, document_bytes, mime_type):
        """Return a canonical extraction proposal without persisting anything."""


def build_empty_supplier_invoice_extraction_payload():
    def field(value=None):
        return {"value": value, "confidence": None, "source": None}

    return {
        "schema_version": 1,
        "fields": {
            "supplier_legal_name": field(),
            "supplier_tax_id": field(),
            "supplier_invoice_number": field(),
            "issue_date": field(),
            "operation_date": field(),
            "concept": field(),
            "currency": field("EUR"),
            "total_amount": field(),
            "fiscal_invoice_type": field("F1"),
            "tax_treatment": field("domestic_standard"),
        },
        "tax_breakdowns": [],
        "warnings": ["El proveedor de desarrollo no ha devuelto datos para revisar."],
    }


class FakeSupplierInvoiceExtractionProvider(SupplierInvoiceExtractionProvider):
    """Deterministic provider used only by tests and local development."""

    provider_name = "fake"
    extractor_version = "fake-v1"

    def __init__(self, *, payload=None, error=None, error_code="provider_error"):
        self.payload = payload or build_empty_supplier_invoice_extraction_payload()
        self.error = error
        self.error_code = error_code

    def extract(self, document_bytes, mime_type):
        if self.error:
            raise SupplierInvoiceExtractionProviderError(str(self.error), code=self.error_code)
        return deepcopy(self.payload)

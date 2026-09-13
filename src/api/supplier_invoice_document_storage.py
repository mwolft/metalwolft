"""Backward-compatible supplier-document facade over private object storage."""

from api.private_object_storage import (
    PrivateObjectStorageConfigurationError as SupplierInvoiceDocumentStorageConfigurationError,
    PrivateObjectStorageError as SupplierInvoiceDocumentStorageError,
    PrivateObjectStorageOperationError as SupplierInvoiceDocumentStorageOperationError,
    PrivateObjectStorageSettings as SupplierInvoiceDocumentStorageSettings,
    R2PrivateObjectStorage,
)


class R2SupplierInvoiceDocumentStorage(R2PrivateObjectStorage):
    """Supplier-facing method names retained for existing invoice services."""

    def put_document(self, *, storage_key, content, mime_type):
        return self.put_object(storage_key=storage_key, content=content, mime_type=mime_type)

    def get_document(self, *, storage_key):
        return self.get_object(storage_key=storage_key)

    def head_document(self, *, storage_key):
        return self.head_object(storage_key=storage_key)

    def delete_document(self, *, storage_key):
        return self.delete_object(storage_key=storage_key)


def get_supplier_invoice_document_storage(app):
    settings = SupplierInvoiceDocumentStorageSettings.from_app_config(app.config)
    return R2SupplierInvoiceDocumentStorage(settings)

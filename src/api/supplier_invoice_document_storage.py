"""Private object storage adapter for supplier invoice source documents."""

from dataclasses import dataclass

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover - reported explicitly at runtime.
    boto3 = None

    class BotoCoreError(Exception):
        pass

    class ClientError(Exception):
        pass


class SupplierInvoiceDocumentStorageError(Exception):
    """Base error for supplier document object storage."""


class SupplierInvoiceDocumentStorageConfigurationError(SupplierInvoiceDocumentStorageError):
    """Raised when private R2 storage has not been configured."""


class SupplierInvoiceDocumentStorageOperationError(SupplierInvoiceDocumentStorageError):
    """Raised when the storage provider cannot complete an operation."""


@dataclass(frozen=True)
class SupplierInvoiceDocumentStorageSettings:
    provider: str
    bucket_name: str
    endpoint_url: str
    access_key_id: str
    secret_access_key: str

    @classmethod
    def from_app_config(cls, config):
        provider = str(config.get("SUPPLIER_DOCUMENT_STORAGE_PROVIDER") or "").strip().lower()
        if provider != "r2":
            raise SupplierInvoiceDocumentStorageConfigurationError(
                "El almacenamiento privado de documentos recibidos no está configurado."
            )

        values = {
            "bucket_name": str(config.get("R2_BUCKET_NAME") or "").strip(),
            "endpoint_url": str(config.get("R2_ENDPOINT_URL") or "").strip(),
            "access_key_id": str(config.get("R2_ACCESS_KEY_ID") or "").strip(),
            "secret_access_key": str(config.get("R2_SECRET_ACCESS_KEY") or "").strip(),
        }
        if not all(values.values()):
            raise SupplierInvoiceDocumentStorageConfigurationError(
                "Faltan variables de configuración de R2 para documentos recibidos."
            )
        if boto3 is None:
            raise SupplierInvoiceDocumentStorageConfigurationError(
                "La dependencia boto3 no está instalada para documentos recibidos."
            )
        return cls(provider=provider, **values)


class R2SupplierInvoiceDocumentStorage:
    """Small S3-compatible adapter with no Flask or domain concerns."""

    def __init__(self, settings, *, client=None):
        self.settings = settings
        self.client = client or boto3.client(
            "s3",
            endpoint_url=settings.endpoint_url,
            aws_access_key_id=settings.access_key_id,
            aws_secret_access_key=settings.secret_access_key,
            region_name="auto",
        )

    def put_document(self, *, storage_key, content, mime_type):
        try:
            self.client.put_object(
                Bucket=self.settings.bucket_name,
                Key=storage_key,
                Body=content,
                ContentType=mime_type,
            )
        except (BotoCoreError, ClientError, OSError) as exc:
            raise SupplierInvoiceDocumentStorageOperationError(
                "No se ha podido guardar el documento privado."
            ) from exc

    def get_document(self, *, storage_key):
        try:
            response = self.client.get_object(
                Bucket=self.settings.bucket_name,
                Key=storage_key,
            )
            return response["Body"].read()
        except (BotoCoreError, ClientError, KeyError, OSError) as exc:
            raise SupplierInvoiceDocumentStorageOperationError(
                "No se ha podido descargar el documento privado."
            ) from exc

    def head_document(self, *, storage_key):
        try:
            return self.client.head_object(Bucket=self.settings.bucket_name, Key=storage_key)
        except (BotoCoreError, ClientError, OSError) as exc:
            raise SupplierInvoiceDocumentStorageOperationError(
                "No se ha podido consultar el documento privado."
            ) from exc

    def delete_document(self, *, storage_key):
        try:
            self.client.delete_object(Bucket=self.settings.bucket_name, Key=storage_key)
        except (BotoCoreError, ClientError, OSError) as exc:
            raise SupplierInvoiceDocumentStorageOperationError(
                "No se ha podido eliminar el documento privado."
            ) from exc


def get_supplier_invoice_document_storage(app):
    settings = SupplierInvoiceDocumentStorageSettings.from_app_config(app.config)
    return R2SupplierInvoiceDocumentStorage(settings)

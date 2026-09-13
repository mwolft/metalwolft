"""Small private R2 object-storage adapter shared by non-public documents."""

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


class PrivateObjectStorageError(Exception):
    """Base error for private object storage."""


class PrivateObjectStorageConfigurationError(PrivateObjectStorageError):
    """Raised when private R2 storage has not been configured."""


class PrivateObjectStorageOperationError(PrivateObjectStorageError):
    """Raised when the storage provider cannot complete an operation."""


@dataclass(frozen=True)
class PrivateObjectStorageSettings:
    provider: str
    bucket_name: str
    endpoint_url: str
    access_key_id: str
    secret_access_key: str

    @classmethod
    def from_app_config(cls, config):
        # Keep the supplier-document setting as the deployed compatibility source
        # until a generic setting is introduced deliberately.
        provider = str(
            config.get("PRIVATE_OBJECT_STORAGE_PROVIDER")
            or config.get("SUPPLIER_DOCUMENT_STORAGE_PROVIDER")
            or ""
        ).strip().lower()
        if provider != "r2":
            raise PrivateObjectStorageConfigurationError(
                "El almacenamiento privado R2 no está configurado."
            )

        values = {
            "bucket_name": str(config.get("R2_BUCKET_NAME") or "").strip(),
            "endpoint_url": str(config.get("R2_ENDPOINT_URL") or "").strip(),
            "access_key_id": str(config.get("R2_ACCESS_KEY_ID") or "").strip(),
            "secret_access_key": str(config.get("R2_SECRET_ACCESS_KEY") or "").strip(),
        }
        if not all(values.values()):
            raise PrivateObjectStorageConfigurationError(
                "Faltan variables de configuración de R2 para el almacenamiento privado."
            )
        if boto3 is None:
            raise PrivateObjectStorageConfigurationError(
                "La dependencia boto3 no está instalada para el almacenamiento privado."
            )
        return cls(provider=provider, **values)


class R2PrivateObjectStorage:
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

    def put_object(self, *, storage_key, content, mime_type):
        try:
            self.client.put_object(
                Bucket=self.settings.bucket_name,
                Key=storage_key,
                Body=content,
                ContentType=mime_type,
            )
        except (BotoCoreError, ClientError, OSError) as exc:
            raise PrivateObjectStorageOperationError(
                "No se ha podido guardar el archivo privado."
            ) from exc

    def get_object(self, *, storage_key):
        try:
            response = self.client.get_object(
                Bucket=self.settings.bucket_name,
                Key=storage_key,
            )
            return response["Body"].read()
        except (BotoCoreError, ClientError, KeyError, OSError) as exc:
            raise PrivateObjectStorageOperationError(
                "No se ha podido descargar el archivo privado."
            ) from exc

    def head_object(self, *, storage_key):
        try:
            return self.client.head_object(Bucket=self.settings.bucket_name, Key=storage_key)
        except (BotoCoreError, ClientError, OSError) as exc:
            raise PrivateObjectStorageOperationError(
                "No se ha podido consultar el archivo privado."
            ) from exc

    def delete_object(self, *, storage_key):
        try:
            self.client.delete_object(Bucket=self.settings.bucket_name, Key=storage_key)
        except (BotoCoreError, ClientError, OSError) as exc:
            raise PrivateObjectStorageOperationError(
                "No se ha podido eliminar el archivo privado."
            ) from exc


def get_private_object_storage(app):
    settings = PrivateObjectStorageSettings.from_app_config(app.config)
    return R2PrivateObjectStorage(settings)

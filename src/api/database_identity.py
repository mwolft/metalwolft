from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from urllib.parse import parse_qsl, unquote, urlparse


SUPPORTED_DATABASE_SCHEMES = {"postgres", "postgresql"}
NORMALIZED_POSTGRES_SCHEME = "postgresql"
ALLOWED_QUERY_PARAMETERS = {"channel_binding", "sslmode"}


class DatabaseIdentityError(RuntimeError):
    """Raised when a database URL or expected identity is unsafe or inconsistent."""


@dataclass(frozen=True)
class DatabaseIdentity:
    scheme: str
    host: str
    port: int | None
    database_name: str
    username: str


def normalize_database_url_scheme(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return NORMALIZED_POSTGRES_SCHEME + "://" + database_url[len("postgres://"):]
    return database_url


def _validate_database_query(query: str) -> None:
    if not query:
        return

    for raw_entry in query.split("&"):
        if not raw_entry or raw_entry.startswith("="):
            raise DatabaseIdentityError("DATABASE_URL contains query parameter without a name.")

    seen_parameters = set()
    for parameter_name, parameter_value in parse_qsl(query, keep_blank_values=True):
        if not parameter_name:
            raise DatabaseIdentityError("DATABASE_URL contains query parameter without a name.")
        if parameter_name in seen_parameters:
            raise DatabaseIdentityError(
                f"DATABASE_URL contains duplicate query parameter: {parameter_name}."
            )
        seen_parameters.add(parameter_name)
        if parameter_name not in ALLOWED_QUERY_PARAMETERS:
            raise DatabaseIdentityError(
                f"DATABASE_URL contains unsupported query parameter: {parameter_name}."
            )
        if not parameter_value:
            raise DatabaseIdentityError(
                f"DATABASE_URL contains empty value for query parameter: {parameter_name}."
            )


def parse_database_identity(database_url: str | None) -> DatabaseIdentity:
    if database_url is None:
        raise DatabaseIdentityError("DATABASE_URL is required.")

    normalized_url = normalize_database_url_scheme(database_url.strip())
    if not normalized_url:
        raise DatabaseIdentityError("DATABASE_URL is required.")

    try:
        parsed = urlparse(normalized_url)
        port = parsed.port
    except ValueError as exc:
        raise DatabaseIdentityError("DATABASE_URL is invalid.") from exc

    if parsed.scheme not in SUPPORTED_DATABASE_SCHEMES:
        raise DatabaseIdentityError("DATABASE_URL must use a PostgreSQL scheme.")
    if not parsed.hostname:
        raise DatabaseIdentityError("DATABASE_URL must include a database host.")
    if "," in parsed.hostname:
        raise DatabaseIdentityError("DATABASE_URL must include exactly one database host.")
    if parsed.fragment:
        raise DatabaseIdentityError("DATABASE_URL must not include a fragment.")
    _validate_database_query(parsed.query)

    database_name = unquote((parsed.path or "").lstrip("/"))
    if not database_name:
        raise DatabaseIdentityError("DATABASE_URL must include a database name.")

    username = unquote(parsed.username or "")
    if not username:
        raise DatabaseIdentityError("DATABASE_URL must include a database user.")

    return DatabaseIdentity(
        scheme=NORMALIZED_POSTGRES_SCHEME,
        host=parsed.hostname,
        port=port,
        database_name=database_name,
        username=username,
    )


def _require_expected_value(value: str | None, variable_name: str) -> str:
    if value is None or not value.strip():
        raise DatabaseIdentityError(f"{variable_name} is required.")
    return value.strip()


def validate_database_identity(
    identity: DatabaseIdentity,
    *,
    expected_host: str | None,
    expected_name: str | None,
    expected_user: str | None,
) -> None:
    required_host = _require_expected_value(expected_host, "DATABASE_EXPECTED_HOST")
    required_name = _require_expected_value(expected_name, "DATABASE_EXPECTED_NAME")
    required_user = _require_expected_value(expected_user, "DATABASE_EXPECTED_USER")

    if identity.host != required_host:
        raise DatabaseIdentityError("database host does not match DATABASE_EXPECTED_HOST.")
    if identity.database_name != required_name:
        raise DatabaseIdentityError("database name does not match DATABASE_EXPECTED_NAME.")
    if identity.username != required_user:
        raise DatabaseIdentityError("database user does not match DATABASE_EXPECTED_USER.")


def mask_database_identity(identity: DatabaseIdentity) -> Mapping[str, str]:
    return {
        "scheme": identity.scheme,
        "host": identity.host,
        "port": str(identity.port) if identity.port is not None else "",
        "database_name": identity.database_name,
        "username": identity.username,
    }

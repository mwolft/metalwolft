"""Safely bootstrap an empty local development database.

This script is intentionally explicit and never runs from application startup.
It is only for an empty Codespaces/dev PostgreSQL database where the historical
Alembic chain cannot be replayed from scratch.
"""

from __future__ import annotations

import argparse
import os
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence
from urllib.parse import unquote, urlparse


SAFE_DATABASE_NAME = "example"
SAFE_DATABASE_HOSTS = {"db", "localhost", "127.0.0.1", "::1"}
PRODUCTION_ENVIRONMENT_KEYS = (
    "RENDER",
    "RENDER_SERVICE_ID",
    "RENDER_EXTERNAL_URL",
    "NEON_PROJECT_ID",
    "NEON_BRANCH",
)
DANGEROUS_HOST_FRAGMENTS = (
    "neon.tech",
    "render.com",
    "render.internal",
)


class BootstrapSafetyError(RuntimeError):
    """Raised when the target database is not safe to initialize."""


class BootstrapExecutionError(RuntimeError):
    """Raised when the bootstrap starts but cannot complete cleanly."""


@dataclass(frozen=True)
class DatabaseTarget:
    scheme: str
    host: str
    port: int | None
    database: str

    def safe_description(self) -> str:
        port = f":{self.port}" if self.port else ""
        return f"{self.scheme}://{self.host}{port}/{self.database}"


@dataclass(frozen=True)
class BootstrapResult:
    target: DatabaseTarget
    existing_tables: tuple[str, ...]
    confirmed: bool
    executed: bool


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return "postgresql://" + database_url[len("postgres://"):]
    return database_url


def parse_database_url(database_url: str) -> DatabaseTarget:
    normalized_url = normalize_database_url((database_url or "").strip())
    if not normalized_url:
        raise BootstrapSafetyError("DATABASE_URL is required.")

    parsed = urlparse(normalized_url)
    database = unquote((parsed.path or "").lstrip("/"))

    if parsed.scheme not in {"postgres", "postgresql"}:
        raise BootstrapSafetyError("Only PostgreSQL development databases can be bootstrapped.")
    if not parsed.hostname:
        raise BootstrapSafetyError("DATABASE_URL must include a database host.")
    if not database:
        raise BootstrapSafetyError("DATABASE_URL must include a database name.")

    return DatabaseTarget(
        scheme=parsed.scheme,
        host=parsed.hostname.lower(),
        port=parsed.port,
        database=database,
    )


def validate_target(target: DatabaseTarget, environ: Mapping[str, str]) -> None:
    if target.host not in SAFE_DATABASE_HOSTS:
        raise BootstrapSafetyError(
            f"Refusing to bootstrap non-local database host: {target.host!r}."
        )
    if target.database != SAFE_DATABASE_NAME:
        raise BootstrapSafetyError(
            f"Refusing to bootstrap database {target.database!r}; expected {SAFE_DATABASE_NAME!r}."
        )

    host_for_detection = target.host.lower()
    if any(fragment in host_for_detection for fragment in DANGEROUS_HOST_FRAGMENTS):
        raise BootstrapSafetyError("Refusing to bootstrap a Neon/Render/external database host.")

    active_production_keys = [
        key for key in PRODUCTION_ENVIRONMENT_KEYS
        if str(environ.get(key, "")).strip()
    ]
    if active_production_keys:
        raise BootstrapSafetyError(
            "Refusing to bootstrap with production environment markers: "
            + ", ".join(sorted(active_production_keys))
        )

    flask_env = str(environ.get("FLASK_ENV", "")).strip().lower()
    if flask_env == "production":
        raise BootstrapSafetyError("Refusing to bootstrap when FLASK_ENV=production.")


def validate_database_url(database_url: str, environ: Mapping[str, str]) -> DatabaseTarget:
    target = parse_database_url(database_url)
    validate_target(target, environ)
    return target


def load_application():
    root_dir = Path(__file__).resolve().parents[1]
    src_dir = root_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from app import app
    from api.models import db

    return app, db


def inspect_existing_tables(db) -> tuple[str, ...]:
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    return tuple(sorted(inspector.get_table_names()))


def stamp_alembic_head() -> None:
    from flask_migrate import stamp

    stamp(directory="src/migrations", revision="head")


def _app_context(app):
    app_context = getattr(app, "app_context", None)
    if app_context is None:
        return nullcontext()
    return app_context()


def bootstrap_dev_database(
    *,
    confirm: bool = False,
    environ: Mapping[str, str] | None = None,
    app_loader: Callable[[], tuple[object, object]] = load_application,
    table_inspector: Callable[[object], tuple[str, ...]] = inspect_existing_tables,
    alembic_stamper: Callable[[], None] = stamp_alembic_head,
    output: Callable[[str], None] = print,
) -> BootstrapResult:
    safe_environ = dict(os.environ if environ is None else environ)
    target = validate_database_url(safe_environ.get("DATABASE_URL", ""), safe_environ)

    app, db = app_loader()
    with _app_context(app):
        existing_tables = tuple(sorted(table_inspector(db)))
        if existing_tables:
            raise BootstrapSafetyError(
                "Refusing to bootstrap a database that already has tables: "
                + ", ".join(existing_tables)
            )

        if not confirm:
            output(
                "DRY RUN: empty development database verified. "
                f"Target: {target.safe_description()}. "
                "Run again with --confirm to create all tables and stamp Alembic head."
            )
            return BootstrapResult(
                target=target,
                existing_tables=existing_tables,
                confirmed=False,
                executed=False,
            )

        try:
            output(f"Creating current schema in {target.safe_description()}...")
            db.create_all()
            output("Stamping Alembic revision head without replaying historical migrations...")
            alembic_stamper()
        except Exception as exc:
            raise BootstrapExecutionError(
                "Development database bootstrap failed. Review the local database before retrying."
            ) from exc

    output(
        "Development database bootstrap completed. "
        f"Target: {target.safe_description()}. No production data was loaded."
    )
    return BootstrapResult(
        target=target,
        existing_tables=existing_tables,
        confirmed=True,
        executed=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap an empty local Codespaces PostgreSQL database safely.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually run db.create_all() and stamp Alembic head. Without this, dry-run only.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bootstrap_dev_database(confirm=args.confirm)
    except BootstrapSafetyError as exc:
        print(f"ABORTED: {exc}", file=sys.stderr)
        return 2
    except BootstrapExecutionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

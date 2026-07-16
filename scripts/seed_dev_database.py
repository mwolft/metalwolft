"""Safely seed the local Codespaces development database with fake data.

This script is intentionally explicit and never runs from application startup.
It only targets the isolated development PostgreSQL database used by Codespaces.
"""

from __future__ import annotations

import argparse
import os
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from scripts.bootstrap_dev_database import (
    BootstrapSafetyError,
    DatabaseTarget,
    validate_database_url,
)


DEV_CATEGORY_SLUG = "rejas-para-ventanas"
DEV_PRODUCT_SLUG = "reja-fija-pittsburgh"
DEV_SUBCATEGORY_NAME = "Rejas fijas de desarrollo"
DEV_CUSTOMER_EMAIL_DEFAULT = "dev.customer@metalwolft.local"
DEV_ADMIN_EMAIL_DEFAULT = "dev.admin@metalwolft.local"
DEV_CUSTOMER_PASSWORD_ENV = "DEV_CUSTOMER_PASSWORD"
DEV_ADMIN_PASSWORD_ENV = "DEV_ADMIN_PASSWORD"


class SeedSafetyError(RuntimeError):
    """Raised when seeding the target database would be unsafe."""


class SeedExecutionError(RuntimeError):
    """Raised when the seed starts but cannot complete cleanly."""


@dataclass(frozen=True)
class SeedResult:
    target: DatabaseTarget
    created: tuple[str, ...]
    reused: tuple[str, ...]
    confirmed: bool
    executed: bool


def load_application():
    root_dir = Path(__file__).resolve().parents[1]
    src_dir = root_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from app import app
    from api.models import (
        Categories,
        DeliveryEstimateConfig,
        Products,
        Subcategories,
        Users,
        db,
    )

    models = {
        "Categories": Categories,
        "DeliveryEstimateConfig": DeliveryEstimateConfig,
        "Products": Products,
        "Subcategories": Subcategories,
        "Users": Users,
    }
    return app, db, models


def _app_context(app):
    app_context = getattr(app, "app_context", None)
    if app_context is None:
        return nullcontext()
    return app_context()


def _normalize_email(value: str | None, default: str) -> str:
    email = (value or default).strip().lower()
    if "@" not in email:
        raise SeedSafetyError(f"Invalid development email address: {email!r}.")
    return email


def _require_password(environ: Mapping[str, str], key: str) -> str:
    password = str(environ.get(key, "")).strip()
    if not password:
        raise SeedSafetyError(
            f"{key} is required when running with --confirm. "
            "Use a local-only development password."
        )
    return password


def _hash_password(password: str) -> str:
    import bcrypt

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _first_by(session, model, **filters):
    return session.query(model).filter_by(**filters).first()


def _ensure_category(session, models, *, confirm: bool, created: list[str], reused: list[str]):
    Categories = models["Categories"]
    category = _first_by(session, Categories, slug=DEV_CATEGORY_SLUG)
    if category:
        reused.append(f"category:{DEV_CATEGORY_SLUG}")
        return category

    if not confirm:
        created.append(f"category:{DEV_CATEGORY_SLUG}")
        return None

    category = Categories(
        nombre="Rejas para ventanas",
        descripcion=(
            "Categoria ficticia de desarrollo para probar el shell publico, "
            "fichas de producto y checkout local."
        ),
        slug=DEV_CATEGORY_SLUG,
        sort_order=1,
    )
    session.add(category)
    session.flush()
    created.append(f"category:{DEV_CATEGORY_SLUG}")
    return category


def _ensure_subcategory(session, models, category, *, confirm: bool, created: list[str], reused: list[str]):
    Subcategories = models["Subcategories"]
    category_id = getattr(category, "id", None)
    subcategory = None
    if category_id is not None:
        subcategory = _first_by(
            session,
            Subcategories,
            nombre=DEV_SUBCATEGORY_NAME,
            categoria_id=category_id,
        )
    if subcategory:
        reused.append(f"subcategory:{DEV_SUBCATEGORY_NAME}")
        return subcategory

    if not confirm:
        created.append(f"subcategory:{DEV_SUBCATEGORY_NAME}")
        return None

    subcategory = Subcategories(
        nombre=DEV_SUBCATEGORY_NAME,
        descripcion="Subcategoria ficticia para productos configurables de desarrollo.",
        categoria_id=category.id,
        sort_order=1,
    )
    session.add(subcategory)
    session.flush()
    created.append(f"subcategory:{DEV_SUBCATEGORY_NAME}")
    return subcategory


def _ensure_product(
    session,
    models,
    category,
    subcategory,
    *,
    confirm: bool,
    created: list[str],
    reused: list[str],
):
    Products = models["Products"]
    product = _first_by(session, Products, slug=DEV_PRODUCT_SLUG)
    if product:
        reused.append(f"product:{DEV_PRODUCT_SLUG}")
        return product

    if not confirm:
        created.append(f"product:{DEV_PRODUCT_SLUG}")
        return None

    product = Products(
        nombre="Reja fija Pittsburgh",
        slug=DEV_PRODUCT_SLUG,
        descripcion=(
            "Producto ficticio de desarrollo para validar configurador, carrito, "
            "checkout, descuentos y flujo documental local."
        ),
        descripcion_seo=(
            "Reja fija ficticia de desarrollo para probar MetalWolft en Codespaces."
        ),
        titulo_seo="Reja fija Pittsburgh de desarrollo",
        h1_seo="Reja fija Pittsburgh",
        precio=120.0,
        precio_rebajado=100.0,
        porcentaje_rebaja=None,
        categoria_id=category.id,
        subcategoria_id=getattr(subcategory, "id", None),
        imagen="/placeholder-reja-dev.jpg",
        has_abatible=False,
        has_door_model=False,
        es_mas_vendido=True,
        es_nuevo_diseno=False,
        sort_order=1,
    )
    session.add(product)
    session.flush()
    created.append(f"product:{DEV_PRODUCT_SLUG}")
    return product


def _ensure_user(
    session,
    models,
    *,
    email: str,
    password: str | None,
    password_hasher: Callable[[str], str],
    is_admin: bool,
    confirm: bool,
    created: list[str],
    reused: list[str],
):
    Users = models["Users"]
    user = _first_by(session, Users, email=email)
    label = "admin" if is_admin else "customer"
    if user:
        reused.append(f"{label}:{email}")
        return user

    if not confirm:
        created.append(f"{label}:{email}")
        return None

    user = Users(
        email=email,
        password=password_hasher(password or ""),
        firstname="Admin" if is_admin else "Cliente",
        lastname="Desarrollo",
        is_active=True,
        is_admin=is_admin,
        shipping_address="Calle Ficticia 1",
        shipping_city="Madrid",
        shipping_postal_code="28000",
        billing_address="Calle Ficticia 1",
        billing_city="Madrid",
        billing_postal_code="28000",
        CIF="B00000000" if is_admin else "00000000T",
    )
    session.add(user)
    session.flush()
    created.append(f"{label}:{email}")
    return user


def _ensure_delivery_config(session, models, *, confirm: bool, created: list[str], reused: list[str]):
    DeliveryEstimateConfig = models["DeliveryEstimateConfig"]
    config = _first_by(session, DeliveryEstimateConfig, is_active=True)
    if config:
        reused.append("delivery_estimate_config:active")
        return config

    if not confirm:
        created.append("delivery_estimate_config:active")
        return None

    config = DeliveryEstimateConfig(
        delivery_days=15,
        range_days=7,
        is_active=True,
    )
    session.add(config)
    session.flush()
    created.append("delivery_estimate_config:active")
    return config


def seed_dev_database(
    *,
    confirm: bool = False,
    environ: Mapping[str, str] | None = None,
    app_loader: Callable[[], tuple[object, object, Mapping[str, object]]] = load_application,
    password_hasher: Callable[[str], str] | None = None,
    output: Callable[[str], None] = print,
) -> SeedResult:
    safe_environ = dict(os.environ if environ is None else environ)
    try:
        target = validate_database_url(safe_environ.get("DATABASE_URL", ""), safe_environ)
    except BootstrapSafetyError as exc:
        raise SeedSafetyError(str(exc)) from exc

    customer_email = _normalize_email(
        safe_environ.get("DEV_CUSTOMER_EMAIL"),
        DEV_CUSTOMER_EMAIL_DEFAULT,
    )
    admin_email = _normalize_email(
        safe_environ.get("DEV_ADMIN_EMAIL"),
        DEV_ADMIN_EMAIL_DEFAULT,
    )

    customer_password = None
    admin_password = None
    if confirm:
        customer_password = _require_password(safe_environ, DEV_CUSTOMER_PASSWORD_ENV)
        admin_password = _require_password(safe_environ, DEV_ADMIN_PASSWORD_ENV)
    active_password_hasher = password_hasher or _hash_password

    app, db, models = app_loader()
    created: list[str] = []
    reused: list[str] = []

    with _app_context(app):
        session = db.session
        try:
            category = _ensure_category(
                session,
                models,
                confirm=confirm,
                created=created,
                reused=reused,
            )
            subcategory = _ensure_subcategory(
                session,
                models,
                category,
                confirm=confirm,
                created=created,
                reused=reused,
            )
            _ensure_product(
                session,
                models,
                category,
                subcategory,
                confirm=confirm,
                created=created,
                reused=reused,
            )
            _ensure_user(
                session,
                models,
                email=customer_email,
                password=customer_password,
                password_hasher=active_password_hasher,
                is_admin=False,
                confirm=confirm,
                created=created,
                reused=reused,
            )
            _ensure_user(
                session,
                models,
                email=admin_email,
                password=admin_password,
                password_hasher=active_password_hasher,
                is_admin=True,
                confirm=confirm,
                created=created,
                reused=reused,
            )
            _ensure_delivery_config(
                session,
                models,
                confirm=confirm,
                created=created,
                reused=reused,
            )

            if not confirm:
                output(
                    "DRY RUN: development seed verified. "
                    f"Target: {target.safe_description()}. "
                    "Run again with --confirm and local password env vars to write fake data."
                )
                return SeedResult(
                    target=target,
                    created=tuple(created),
                    reused=tuple(reused),
                    confirmed=False,
                    executed=False,
                )

            session.commit()
        except Exception as exc:
            rollback = getattr(db.session, "rollback", None)
            if callable(rollback):
                rollback()
            raise SeedExecutionError(
                "Development database seed failed. No production data was copied."
            ) from exc

    output(
        "Development seed completed. "
        f"Target: {target.safe_description()}. "
        f"Created: {len(created)}. Reused: {len(reused)}. "
        "Only fictitious local data was used."
    )
    return SeedResult(
        target=target,
        created=tuple(created),
        reused=tuple(reused),
        confirmed=True,
        executed=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed an isolated local Codespaces database with fake development data.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually write fake development records. Without this, dry-run only.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        seed_dev_database(confirm=args.confirm)
    except SeedSafetyError as exc:
        print(f"ABORTED: {exc}", file=sys.stderr)
        return 2
    except SeedExecutionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

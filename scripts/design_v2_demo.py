"""Prepare and serve a Design V2 demo in Codespaces only.

The database and object store are local. This script never reads project .env files.
Run ``prepare`` first. Optional V1 import requires a dedicated SELECT-only Neon
role, independent connection details copied from that branch's Connect panel,
and the original owner's email for filtering. Set V1_READONLY_DATABASE_URL,
V1_EXPECTED_HOST, V1_EXPECTED_PORT, V1_EXPECTED_DATABASE, V1_EXPECTED_USER,
and V1_SOURCE_CUSTOMER_EMAIL only in the import process environment. Never use
DATABASE_URL or a production owner role for the source.

For each delivered V1 request, download its existing result through the owner's
authenticated download flow and place the file in
~/.local/share/metalwolft-design-v2-demo/import-inputs/ (private mode). Its
size and SHA-256 must match the source metadata. Then run, for example:

  python scripts/design_v2_demo.py import-v1 --reference DP-EXAMPLE \
    --result DP-EXAMPLE=legacy-result.pdf

Omit --result for a paid request not yet delivered. Repeat --reference and
--result for more requests (up to ten). Import is never part of ``prepare``.
"""

from __future__ import annotations

import argparse
import base64
import hmac
import ipaddress
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = Path.home() / ".local" / "share" / "metalwolft-design-v2-demo"
ACCESS_FILE = STATE_DIR / "access.json"
DATABASE_NAME = "metalwolft_design_v2_demo"


def safe_target():
    if os.name == "nt" or os.getenv("CODESPACES", "").lower() != "true":
        raise RuntimeError("This demo runs only inside GitHub Codespaces on Linux.")
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True
    ).strip()
    if branch != "develop":
        raise RuntimeError("Switch to develop before preparing the demo.")

    raw_url = os.getenv("TEST_DATABASE_URL", "")
    if not raw_url:
        raise RuntimeError("TEST_DATABASE_URL is required for the local demo database.")
    return validate_test_database_url(raw_url)


def validate_test_database_url(raw_url, *, lookup=socket.getaddrinfo):
    from sqlalchemy.engine import make_url

    normalized = "postgresql://" + raw_url[len("postgres://"):] if raw_url.startswith("postgres://") else raw_url
    url = make_url(normalized)
    if (url.drivername not in {"postgresql", "postgresql+psycopg2"}
            or url.host != "db" or (url.port or 5432) != 5432
            or url.database != DATABASE_NAME or url.username != "gitpod"):
        raise RuntimeError("Refusing a database outside the dedicated local demo target.")
    addresses = {row[4][0] for row in lookup("db", 5432)}
    if not addresses or any(not ipaddress.ip_address(address).is_private for address in addresses):
        raise RuntimeError("The db service does not resolve exclusively to private addresses.")
    return url


def isolate_process(url, access):
    keep = {key: value for key, value in os.environ.items()
            if key in {"PATH", "HOME", "USER", "LANG", "LC_ALL", "TZ", "VIRTUAL_ENV", "PYTHONPATH"}}
    os.environ.clear()
    os.environ.update(keep)
    os.environ.update({
        "TEST_DATABASE_URL": url.render_as_string(hide_password=False),
        "DATABASE_URL": url.render_as_string(hide_password=False),
        "APP_ENV": "test",
        "PIPENV_DONT_LOAD_ENV": "1",
        "FLASK_SKIP_DOTENV": "1",
        "PYTHON_DOTENV_DISABLED": "1",
        "FORCE_HTTPS": "false",
        "MAIL_SUPPRESS_SEND": "true",
        "MAIL_SERVER": "127.0.0.1",
        "MAIL_PORT": "1",
        "MAIL_USERNAME": "demo-admin@example.test",
        "MAIL_DEFAULT_SENDER": "demo-admin@example.test",
        "FRONTEND_URL": "http://127.0.0.1:3002",
        "ADMIN_USER": access["admin_user"],
        "ADMIN_PW": access["admin_password"],
        "FLASK_APP_KEY": access["flask_secret"],
        "JWT_SECRET_KEY": access["jwt_secret"],
    })
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))


def load_or_create_access(*, create):
    if ACCESS_FILE.exists():
        return json.loads(ACCESS_FILE.read_text(encoding="utf-8"))
    if not create:
        raise RuntimeError("Demo access file is missing; run prepare first.")
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    access = {
        "admin_user": "demo-admin",
        "admin_password": secrets.token_urlsafe(18),
        "customer_email": "cliente-diseno-v2@example.test",
        "customer_password": secrets.token_urlsafe(18),
        "flask_secret": secrets.token_urlsafe(32),
        "jwt_secret": secrets.token_urlsafe(32),
    }
    descriptor = os.open(ACCESS_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(access, handle)
    return access


def ensure_database(url):
    from sqlalchemy import create_engine, text

    engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 4})
    try:
        with engine.connect() as connection:
            server_version = connection.execute(text("SHOW server_version_num")).scalar_one()
            database, current_user, server_address = connection.execute(text(
                "SELECT current_database(), current_user, inet_server_addr()"
            )).one()
            resolved = {row[4][0] for row in socket.getaddrinfo("db", 5432)}
            if (int(server_version) < 160000 or database != "postgres" or current_user != "gitpod"
                    or str(server_address) not in resolved):
                raise RuntimeError("Unexpected local PostgreSQL server or role.")
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": DATABASE_NAME}
            ).scalar_one_or_none()
            if not exists:
                connection.execute(text(f"CREATE DATABASE {DATABASE_NAME}"))
    finally:
        engine.dispose()


def load_app():
    from app import app
    from api.models import db
    app.config["MAIL_SUPPRESS_SEND"] = True
    if app.config["SQLALCHEMY_DATABASE_URI"] != os.environ["TEST_DATABASE_URL"]:
        raise RuntimeError("Flask did not select the local demo database.")
    return app, db


def verify_connection(app, db):
    from sqlalchemy import text

    with app.app_context():
        database, user, server_address = db.session.execute(text(
            "SELECT current_database(), current_user, inet_server_addr()"
        )).one()
        if database != DATABASE_NAME or user != "gitpod" or not server_address:
            raise RuntimeError("The effective Flask connection is not the local demo database.")
        address = ipaddress.ip_address(str(server_address))
        resolved = {row[4][0] for row in socket.getaddrinfo("db", 5432)}
        if str(address) not in resolved or (not address.is_private and not address.is_loopback):
            raise RuntimeError("The effective PostgreSQL server address is not private.")
        db.session.rollback()
    print("PASS: Flask uses the dedicated local PostgreSQL database and role.")


def ensure_schema(app, db, *, create):
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from flask_migrate import stamp
    from sqlalchemy import inspect, text

    config = Config(str(ROOT / "src" / "migrations" / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "src" / "migrations"))
    head = ScriptDirectory.from_config(config).get_current_head()
    with app.app_context():
        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())
        expected = set(db.metadata.tables)
        if tables - expected - {"alembic_version"}:
            raise RuntimeError("Demo database contains unexpected tables; refusing to modify it.")
        if "alembic_version" in tables:
            revision = db.session.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
            db.session.rollback()
            if revision is not None and revision != head:
                raise RuntimeError("Demo schema revision differs from the single repository head.")
            if revision == head and not expected.issubset(tables):
                raise RuntimeError("Stamped demo schema is incomplete; refusing automatic repair.")
        else:
            revision = None
        if revision is None and create:
            # A failed create_all can leave an unstamped subset. Repair only an empty,
            # structurally recognizable schema in the dedicated local database.
            for name in tables - {"alembic_version"}:
                model_columns = {column.name for column in db.metadata.tables[name].columns}
                actual_columns = {column["name"] for column in inspector.get_columns(name)}
                if actual_columns != model_columns:
                    raise RuntimeError("Partial demo schema differs from current models; refusing repair.")
                quoted = db.engine.dialect.identifier_preparer.quote(name)
                if db.session.execute(text(f"SELECT 1 FROM {quoted} LIMIT 1")).first():
                    raise RuntimeError("Unstamped demo database contains data; refusing repair.")
            db.session.rollback()
            constraint = next(c for c in db.metadata.tables["supplier_invoices"].constraints
                              if c.name == "ck_supplier_invoices_legacy_expense_classification_audit_complete")
            original_name = constraint.name
            try:
                constraint.name = "ck_supplier_invoices_legacy_expense_audit_complete"
                db.create_all()
            finally:
                constraint.name = original_name
            tables = set(inspect(db.engine).get_table_names())
            if not expected.issubset(tables):
                raise RuntimeError("Synthetic schema creation was incomplete; refusing to stamp.")
            stamp(directory=str(ROOT / "src" / "migrations"), revision=head)
        elif revision is None:
            raise RuntimeError("Existing demo schema is incomplete; run prepare first.")
        if "design_deliverables" not in set(inspect(db.engine).get_table_names()):
            raise RuntimeError("Demo schema lacks design deliverables.")
    print("PASS: local synthetic schema matches the Alembic head.")


def seed_demo(app, db, access):
    import bcrypt
    from api.models import Categories, DesignRequest, DesignRequestItem, OrderDetails, Orders, Products, Users

    with app.app_context():
        existing = DesignRequest.query.filter_by(reference="DEMO-V2-001").one_or_none()
        if existing:
            if existing.user.email != access["customer_email"]:
                raise RuntimeError("Demo request belongs to an unexpected user.")
            print("PASS: synthetic request already exists; no records changed.")
            return
        if db.session.query(Users.id).first() or db.session.query(Orders.id).first():
            raise RuntimeError("Demo database contains unexpected users or orders; refusing to seed.")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        user = Users(
            email=access["customer_email"],
            password=bcrypt.hashpw(access["customer_password"].encode(), bcrypt.gensalt()).decode(),
            firstname="Cliente", lastname="Ficticio",
        )
        category = Categories(nombre="Rejas de prueba", descripcion="Catalogo sintetico", slug="rejas-para-ventanas")
        db.session.add_all((user, category))
        db.session.flush()
        product = Products(
            slug="reja-fija-demo-v2", nombre="Reja fija demo V2", descripcion="Producto sintetico para validar disenos",
            precio=180, categoria_id=category.id, published=True, available_for_sale=True,
        )
        db.session.add(product)
        db.session.flush()
        order = Orders(user_id=user.id, locator="DV2DEMO1", total_amount=24.95,
                       order_status="pendiente", order_date=now)
        db.session.add(order)
        db.session.flush()
        detail = OrderDetails(order_id=order.id, product_id=product.id, quantity=1,
                              line_type="design_service", alto=95, ancho=80,
                              precio_total=24.95, shipping_cost=0,
                              screw_option="not_applicable", screw_supplement=0)
        request = DesignRequest(
            reference="DEMO-V2-001", creation_key="demo-design-v2-only", user_id=user.id,
            order_id=order.id, subtotal_gross=24.95, price_gross=24.95,
            discount_amount=0, currency="EUR", lead_time_hours=24,
            status=DesignRequest.STATUS_IN_PROGRESS, paid_at=now, started_at=now,
        )
        db.session.add_all((detail, request))
        db.session.flush()
        db.session.add(DesignRequestItem(
            design_request_id=request.id, product_id=product.id, product_name=product.nombre,
            width_cm=80, height_cm=95, order_detail_id=detail.id,
        ))
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        print(f"PASS: synthetic paid/in-progress request created (order {order.id}).")


class LocalDemoStorage:
    def __init__(self):
        self.root = (STATE_DIR / "objects").resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def _path(self, storage_key):
        from api.private_object_storage import PrivateObjectStorageOperationError
        key = str(storage_key or "")
        if not key or "\\" in key or ":" in key or any(part in {"", ".", ".."} for part in key.split("/")):
            raise PrivateObjectStorageOperationError("Invalid local demo object key.")
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise PrivateObjectStorageOperationError("Invalid local demo object path.")
        return path

    def put_object(self, *, storage_key, content, mime_type):
        path = self._path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        created = False
        try:
            with path.open("xb") as handle:
                created = True
                handle.write(content)
        except Exception:
            if created:
                path.unlink(missing_ok=True)
            raise

    def get_object(self, *, storage_key):
        return self._path(storage_key).read_bytes()

    def head_object(self, *, storage_key):
        return {"ContentLength": self._path(storage_key).stat().st_size}

    def delete_object(self, *, storage_key):
        self._path(storage_key).unlink(missing_ok=True)


def serve(app):
    import api.admin as admin_module
    import api.design_result_service as result_module
    import api.email_routes as email_module
    import api.routes as routes_module
    storage = LocalDemoStorage()
    for module in (admin_module, result_module, routes_module):
        module.get_private_object_storage = lambda _app: storage
    email_module.send_email = lambda **_kwargs: False
    enable_demo_admin_browser_login(app, load_or_create_access(create=False))
    print("PASS: private files use local demo storage; email delivery is suppressed.")
    app.run(host="0.0.0.0", port=3001, debug=False, use_reloader=False)


def enable_demo_admin_browser_login(app, access):
    """Bridge browser sessions to existing Basic Auth only in the demo server."""
    from datetime import timedelta
    from flask import make_response, redirect, render_template_string, request, session

    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
    )
    browser_token = secrets.token_urlsafe(32)
    failed_attempts = []
    login_form = """<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Acceso a la demo</title><body style="font:16px sans-serif;max-width:25rem;margin:4rem auto;padding:1rem">
<h1>Administrador de demostración</h1><p>{{ message }}</p>
<form method="post" action="/demo-admin-login">
<input type="hidden" name="csrf" value="{{ csrf }}">
<label>Usuario <input name="username" required autocomplete="username"></label><br><br>
<label>Contraseña <input type="password" name="password" required autocomplete="current-password"></label><br><br>
<button type="submit">Acceder</button></form></body></html>"""

    def authenticated():
        token = session.get("demo_admin_session")
        return isinstance(token, str) and hmac.compare_digest(token, browser_token)

    @app.route("/demo-admin-login", methods=["GET", "POST"])
    def demo_admin_login():
        now = time.monotonic()
        failed_attempts[:] = [attempt for attempt in failed_attempts if now - attempt < 900]
        message = "Introduce las credenciales creadas por la demo."
        status = 200
        if request.method == "POST":
            csrf = session.get("demo_admin_csrf")
            if not isinstance(csrf, str) or not hmac.compare_digest(request.form.get("csrf", ""), csrf):
                status, message = 403, "Formulario caducado; vuelve a intentarlo."
            elif len(failed_attempts) >= 5:
                status, message = 429, "Demasiados intentos. Espera 15 minutos."
            else:
                username = request.form.get("username", "")
                password = request.form.get("password", "")
                if (hmac.compare_digest(username.encode("utf-8"), access["admin_user"].encode("utf-8"))
                        and hmac.compare_digest(password.encode("utf-8"), access["admin_password"].encode("utf-8"))):
                    session.clear()
                    session.permanent = True
                    session["demo_admin_session"] = browser_token
                    response = redirect("/admin/", code=303)
                    response.headers["Cache-Control"] = "no-store"
                    return response
                failed_attempts.append(now)
                status, message = 401, "Credenciales incorrectas."
        if not session.get("demo_admin_csrf"):
            session["demo_admin_csrf"] = secrets.token_urlsafe(32)
        response = make_response(render_template_string(login_form, csrf=session["demo_admin_csrf"], message=message), status)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.before_request
    def demo_admin_auth_bridge():
        if not request.path.startswith("/admin/"):
            return None
        if authenticated():
            credentials = f"{access['admin_user']}:{access['admin_password']}".encode("utf-8")
            request.environ["HTTP_AUTHORIZATION"] = "Basic " + base64.b64encode(credentials).decode("ascii")
            return None
        basic_auth = request.authorization
        if (basic_auth and basic_auth.type.lower() == "basic"
                and hmac.compare_digest((basic_auth.username or "").encode("utf-8"), access["admin_user"].encode("utf-8"))
                and hmac.compare_digest((basic_auth.password or "").encode("utf-8"), access["admin_password"].encode("utf-8"))):
            return None
        return redirect("/demo-admin-login")


def main():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "serve", "access", "import-v1"))
    parser.add_argument("--reference", action="append", default=[], help="Exact DP reference to import (repeatable).")
    parser.add_argument("--result", action="append", default=[], help="DP reference and local result filename: DP-...=file.pdf")
    args = parser.parse_args()
    url = safe_target()
    if args.action == "import-v1":
        from scripts.design_v1_demo_import import normalize_references, source_configuration
        references = normalize_references(args.reference)
        source_url, owner_email = source_configuration(os.environ)
    if args.action == "access":
        access = load_or_create_access(create=False)
        print(f"Admin: {access['admin_user']} / {access['admin_password']}")
        print(f"Customer: {access['customer_email']} / {access['customer_password']}")
        return
    access = load_or_create_access(create=args.action == "prepare")
    isolate_process(url, access)
    if args.action == "prepare":
        ensure_database(url)
    app, db = load_app()
    verify_connection(app, db)
    ensure_schema(app, db, create=args.action == "prepare")
    if args.action == "prepare":
        seed_demo(app, db, access)
    elif args.action == "import-v1":
        from scripts.design_v1_demo_import import (
            import_into_demo, read_source, resolve_input_files, validate_source_rows,
        )
        files = resolve_input_files(references, args.result, STATE_DIR / "import-inputs")
        requests, items = read_source(source_url, owner_email, references)
        validate_source_rows(requests, items, files)
        imported = import_into_demo(app, db, access, requests, items, files, LocalDemoStorage())
        print(f"PASS: {imported} V1 requests imported; {len(references) - imported} already present.")
    else:
        serve(app)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:
        print(f"BLOCKED: {type(error).__name__}; no connection details printed.", file=sys.stderr)
        raise SystemExit(1)

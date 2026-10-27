"""Validate credential migration and races on the disposable Codespaces database.

Run with the virtualenv Python directly; do not use ``pipenv run`` or Flask CLI.
The script never bootstraps, resets, or cleans up the database.
"""

from __future__ import annotations

import os
import secrets
import socket
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COMMIT = "1c37bc9056280336015d6720352422ebb14c33f8"
EXPECTED_BRANCH = "test/credential-security-postgres"
EXPECTED_HOST = "db"
EXPECTED_PORT = 5432
EXPECTED_DATABASE = "metalwolft_auth_test"
PREVIOUS_REVISION = "c3d4e5f6a7b8"
NEW_REVISION = "b4c5d6e7f8a9"


class ValidationBlocked(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationBlocked(message)


def git_value(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
    ).strip()


def prepare_environment():
    require(os.getenv("CODESPACES", "").lower() == "true", "not running in Codespaces")
    require(os.getenv("PIPENV_DONT_LOAD_ENV") == "1", "Pipenv dotenv loading is not disabled")
    require(git_value("branch", "--show-current") == EXPECTED_BRANCH, "unexpected branch")
    require(git_value("rev-parse", "HEAD") == EXPECTED_COMMIT, "unexpected commit")

    from sqlalchemy.engine import make_url

    raw_url = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
    require(bool(raw_url), "DATABASE_URL is missing")
    source = make_url(raw_url)
    require(
        (source.host, source.port, source.database)
        in {
            (EXPECTED_HOST, EXPECTED_PORT, "example"),
            (EXPECTED_HOST, EXPECTED_PORT, EXPECTED_DATABASE),
        },
        "DATABASE_URL does not name the local Compose server",
    )
    require(bool(source.username and source.password), "local database credentials are missing")
    require(source.drivername in {"postgresql", "postgresql+psycopg2"}, "unexpected database driver")

    # Discard URL-level connection overrides and libpq environment overrides.
    target = source.set(database=EXPECTED_DATABASE, query={})
    for key in (
        "PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGPORT",
        "PGDATABASE", "PGUSER", "PGPASSWORD", "PGOPTIONS",
    ):
        os.environ.pop(key, None)
    os.environ.update(
        DATABASE_URL=target.render_as_string(hide_password=False),
        APP_ENV="test",
        FORCE_HTTPS="false",
        FLASK_SKIP_DOTENV="1",
        JWT_SECRET_KEY=secrets.token_urlsafe(32),
        CUSTOMER_PHOTOS_ENABLED="false",
        CUSTOMER_PHOTOS_INCENTIVE_ENABLED="false",
    )
    sys.path.insert(0, str(ROOT / "src"))

    # routes.py calls load_dotenv() at import time; prevent even reading .env.
    with patch("dotenv.load_dotenv", return_value=False):
        import app as app_module
    from api.models import db

    app = app_module.app
    require(app.extensions["migrate"].db is db, "Flask-Migrate uses another SQLAlchemy instance")
    with app.app_context():
        effective = db.engine.url
        require(
            (effective.host, effective.port, effective.database)
            == (EXPECTED_HOST, EXPECTED_PORT, EXPECTED_DATABASE) and not effective.query,
            "Flask engine points somewhere unexpected",
        )
        with db.engine.connect() as connection:
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            identity = connection.exec_driver_sql(
                "SELECT current_database(), inet_server_port(), inet_server_addr(), "
                "current_setting('server_version_num')"
            ).one()
            require(
                identity[0] == EXPECTED_DATABASE and identity[1] == EXPECTED_PORT,
                "connected to the wrong PostgreSQL database",
            )
            resolved = {item[4][0] for item in socket.getaddrinfo(EXPECTED_HOST, EXPECTED_PORT)}
            require(str(identity[2]) in resolved, "server address does not match local db service")
            require(160000 <= int(identity[3]) < 170000, "PostgreSQL is not version 16")
    return app, db


def read_state(db):
    from sqlalchemy import inspect, text

    with db.engine.connect() as connection:
        connection.exec_driver_sql("SET TRANSACTION READ ONLY")
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        require("alembic_version" in tables and "users" in tables, "baseline tables are missing")
        revisions = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
        columns = {column["name"] for column in inspector.get_columns("users")}
        user_count = connection.scalar(text("SELECT count(*) FROM users"))
        return tables, revisions, columns, user_count


def require_previous_state(db):
    tables, revisions, columns, user_count = read_state(db)
    expected_tables = set(db.metadata.tables) | {"alembic_version"}
    require(
        tables == expected_tables,
        f"unexpected baseline tables (missing={sorted(expected_tables - tables)}, "
        f"extra={sorted(tables - expected_tables)})",
    )
    require(revisions == [PREVIOUS_REVISION], f"unexpected Alembic revision count/value: {len(revisions)}")
    require("credential_version" not in columns, "credential_version already exists")
    require(user_count == 0, f"expected zero users, found {user_count}")


def require_new_state(db, *, expected_users: int | None = None):
    tables, revisions, columns, user_count = read_state(db)
    expected_tables = set(db.metadata.tables) | {"alembic_version"}
    require(tables == expected_tables, "table set changed unexpectedly")
    require(revisions == [NEW_REVISION], "new Alembic revision is not current")
    require("credential_version" in columns, "credential_version is missing")
    if expected_users is not None:
        require(user_count == expected_users, f"expected {expected_users} test users, found {user_count}")


def insert_test_user(db, email: str, password: str) -> int:
    import bcrypt
    from sqlalchemy import text

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
    with db.engine.begin() as connection:
        return connection.execute(
            text(
                "INSERT INTO users (email, password, is_active, is_admin) "
                "VALUES (:email, :password, true, false) RETURNING id"
            ),
            {"email": email, "password": hashed},
        ).scalar_one()


def validate_migration(db):
    import bcrypt
    from flask_migrate import upgrade
    from sqlalchemy import inspect, text

    require_previous_state(db)
    password = secrets.token_urlsafe(18)
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")
    with db.engine.begin() as connection:
        user_id = connection.execute(
            text(
                "INSERT INTO users (email, password, is_active, is_admin) "
                "VALUES (:email, :password, true, false) RETURNING id"
            ),
            {"email": "migration-check@example.test", "password": hashed},
        ).scalar_one()
    print("PASS baseline: exactly the completed Block A state")

    upgrade(directory=str(ROOT / "src" / "migrations"), revision=NEW_REVISION)
    require_new_state(db, expected_users=1)
    with db.engine.connect() as connection:
        connection.exec_driver_sql("SET TRANSACTION READ ONLY")
        columns = {item["name"]: item for item in inspect(connection).get_columns("users")}
        require(not columns["credential_version"]["nullable"], "new column is nullable")
        row = connection.execute(
            text("SELECT password, credential_version FROM users WHERE id = :id"),
            {"id": user_id},
        ).one()
        require(row[0] == hashed and row[1] == 0, "hash changed or initial version is not zero")
        require(bcrypt.checkpw(password.encode("utf-8"), row[0].encode("ascii")), "bcrypt hash invalid")
    print("PASS migration: revision, initial version and bcrypt hash preserved")


def test_password_race(app, db):
    from api.credential_security import replace_password_if_version
    from api.models import Users
    from sqlalchemy import text

    user_id = insert_test_user(db, f"race-{uuid.uuid4().hex}@example.test", secrets.token_urlsafe(18))
    barrier = Barrier(2)

    def worker(_):
        with app.app_context():
            user = db.session.get(Users, user_id)
            backend_pid = db.session.execute(text("SELECT pg_backend_pid()")).scalar_one()
            barrier.wait(timeout=15)
            try:
                changed = replace_password_if_version(user, secrets.token_urlsafe(18), user.credential_version)
                return changed, backend_pid
            finally:
                db.session.remove()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, range(2)))
    require(len({pid for _, pid in results}) == 2, "workers did not use independent connections")
    require(sorted(changed for changed, _ in results) == [False, True], "two changes both succeeded or failed")
    with db.engine.connect() as connection:
        require(
            connection.scalar(text("SELECT credential_version FROM users WHERE id = :id"), {"id": user_id}) == 1,
            "concurrent changes did not increment exactly once",
        )


def test_change_against_reset(app, db):
    import bcrypt
    from api.jwt_utils import create_user_access_token
    from api.models import Users
    from flask_jwt_extended import create_access_token
    from sqlalchemy import text

    email = f"change-reset-{uuid.uuid4().hex}@example.test"
    current = secrets.token_urlsafe(18)
    user_id = insert_test_user(db, email, current)
    with app.app_context():
        user = db.session.get(Users, user_id)
        access = create_user_access_token(user)
        reset = create_access_token(
            identity=email,
            additional_claims={"purpose": "password_reset", "credential_version": 0},
            expires_delta=timedelta(minutes=15),
        )
        db.session.remove()
    changed = secrets.token_urlsafe(18)
    restored = secrets.token_urlsafe(18)
    barrier = Barrier(2)

    def change():
        barrier.wait(timeout=15)
        return app.test_client().post(
            "/api/auth/change-password",
            json={"current_password": current, "new_password": changed},
            headers={"Authorization": f"Bearer {access}"},
        ).status_code

    def recover():
        barrier.wait(timeout=15)
        return app.test_client().post(
            "/api/auth/reset-password", json={"token": reset, "password": restored}
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(change)
        b = pool.submit(recover)
        statuses = (a.result(), b.result())
    require(statuses.count(200) == 1, f"expected one successful change/reset, got {statuses}")
    require(all(code in {200, 400, 401, 403, 409} for code in statuses), f"unexpected status: {statuses}")
    with db.engine.connect() as connection:
        row = connection.execute(
            text("SELECT password, credential_version FROM users WHERE id = :id"), {"id": user_id}
        ).one()
        require(row[1] == 1, "change/reset race incremented version incorrectly")
        winner = changed if statuses[0] == 200 else restored
        require(bcrypt.checkpw(winner.encode("utf-8"), row[0].encode("ascii")), "winner hash not stored")


def test_single_use_reset(app, db):
    from flask_jwt_extended import create_access_token
    from sqlalchemy import text

    email = f"single-use-{uuid.uuid4().hex}@example.test"
    user_id = insert_test_user(db, email, secrets.token_urlsafe(18))
    with app.app_context():
        token = create_access_token(
            identity=email,
            additional_claims={"purpose": "password_reset", "credential_version": 0},
            expires_delta=timedelta(minutes=15),
        )
    barrier = Barrier(2)

    def consume(_):
        barrier.wait(timeout=15)
        return app.test_client().post(
            "/api/auth/reset-password",
            json={"token": token, "password": secrets.token_urlsafe(18)},
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(consume, range(2)))
    require(sorted(statuses) == [200, 400], f"reset token outcomes were {statuses}")
    with db.engine.connect() as connection:
        require(
            connection.scalar(text("SELECT credential_version FROM users WHERE id = :id"), {"id": user_id}) == 1,
            "reset token changed version more than once",
        )


def test_shared_limit(app, db):
    from api.credential_security import _bucket_key, reserve_password_attempt
    from sqlalchemy import text

    user_id = insert_test_user(db, f"limit-{uuid.uuid4().hex}@example.test", secrets.token_urlsafe(18))
    barrier = Barrier(6)

    def reserve(_):
        with app.app_context():
            barrier.wait(timeout=15)
            return reserve_password_attempt(user_id)

    with ThreadPoolExecutor(max_workers=6) as pool:
        allowed = list(pool.map(reserve, range(6)))
    require(sum(allowed) == 5, f"expected five accepted attempts, got {sum(allowed)}")
    with db.engine.connect() as connection:
        hits = connection.scalar(
            text("SELECT hits FROM customer_photo_rate_limits WHERE bucket_key = :key"),
            {"key": _bucket_key(user_id)},
        )
        require(hits == 6, f"shared counter recorded {hits} instead of six attempts")


def test_rollback(db):
    from sqlalchemy import text

    user_id = insert_test_user(db, f"rollback-{uuid.uuid4().hex}@example.test", secrets.token_urlsafe(18))
    query = text("SELECT password, credential_version FROM users WHERE id = :id")
    with db.engine.connect() as connection:
        before = connection.execute(query, {"id": user_id}).one()
    try:
        with db.engine.begin() as connection:
            connection.execute(
                text("UPDATE users SET password = 'discarded', credential_version = 99 WHERE id = :id"),
                {"id": user_id},
            )
            raise RuntimeError("injected rollback")
    except RuntimeError:
        pass
    with db.engine.connect() as connection:
        after = connection.execute(query, {"id": user_id}).one()
    require(before == after, "rollback left a partial password or version change")


def run_test(label: str, test, *args) -> None:
    try:
        test(*args)
    except ValidationBlocked as exc:
        print(f"BLOCKED {label}: {exc}")
        raise SystemExit(2) from None
    except Exception as exc:
        print(f"FAIL {label}: {type(exc).__name__}")
        raise SystemExit(1) from None
    print(f"PASS {label}")


def main() -> None:
    try:
        app, db = prepare_environment()
    except ValidationBlocked as exc:
        print(f"BLOCKED preflight: {exc}")
        raise SystemExit(2) from None
    except Exception as exc:
        print(f"BLOCKED preflight: {type(exc).__name__}")
        raise SystemExit(2) from None
    print("PASS preflight: Codespaces, branch, local PostgreSQL 16 and Flask-Migrate engine")

    with app.app_context():
        run_test("migration", validate_migration, db)
        run_test("concurrent password changes", test_password_race, app, db)
        run_test("change versus reset", test_change_against_reset, app, db)
        run_test("single-use recovery token", test_single_use_reset, app, db)
        run_test("shared rate limit", test_shared_limit, app, db)
        run_test("transaction rollback", test_rollback, db)
    print("PASS complete: PostgreSQL validation finished; historical Alembic replay was not tested")


if __name__ == "__main__":
    main()

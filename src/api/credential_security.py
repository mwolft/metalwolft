"""Shared credential policy, JWT revocation and atomic password updates."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256

import bcrypt
from sqlalchemy import text, update
from sqlalchemy.exc import SQLAlchemyError

from api.models import Users, db


class CredentialRateLimitUnavailable(RuntimeError):
    pass


def valid_new_password(value):
    if not isinstance(value, str):
        return False
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        return False
    return 8 <= size <= 72


def token_credential_version(claims):
    version = claims.get("credential_version", 0)
    return version if type(version) is int and version >= 0 else None


def register_credential_revocation(jwt_manager):
    @jwt_manager.token_in_blocklist_loader
    def revoked(_header, claims):
        if claims.get("purpose") is not None:
            return True
        identity = claims.get("sub")
        if isinstance(identity, dict):
            identity = identity.get("user_id")
        if isinstance(identity, str) and identity.isdigit():
            identity = int(identity)
        if type(identity) is not int or identity <= 0:
            return True
        version = token_credential_version(claims)
        if version is None:
            return True
        try:
            user = db.session.get(Users, identity)
            return user is None or user.is_active is False or user.credential_version != version
        except SQLAlchemyError:
            db.session.rollback()
            return True


_RESERVE_ATTEMPT = text("""
    INSERT INTO customer_photo_rate_limits (bucket_key, window_started_at, hits)
    VALUES (:key, :now, 1)
    ON CONFLICT (bucket_key) DO UPDATE SET
        hits = CASE
            WHEN customer_photo_rate_limits.window_started_at <= :cutoff THEN 1
            ELSE customer_photo_rate_limits.hits + 1
        END,
        window_started_at = CASE
            WHEN customer_photo_rate_limits.window_started_at <= :cutoff THEN :now
            ELSE customer_photo_rate_limits.window_started_at
        END
    RETURNING hits
""")

_RELEASE_SUCCESS = text("""
    UPDATE customer_photo_rate_limits
    SET hits = CASE WHEN hits > 0 THEN hits - 1 ELSE 0 END
    WHERE bucket_key = :key
""")


def _bucket_key(user_id):
    return sha256(f"auth:password-change:{user_id}".encode()).hexdigest()


def reserve_password_attempt(user_id):
    """Reserve before bcrypt, across workers; count only failed attempts."""
    now = datetime.now(timezone.utc)
    try:
        with db.engine.begin() as connection:
            hits = connection.execute(_RESERVE_ATTEMPT, {
                "key": _bucket_key(user_id),
                "now": now,
                "cutoff": now - timedelta(minutes=15),
            }).scalar_one()
    except SQLAlchemyError as exc:
        raise CredentialRateLimitUnavailable() from exc
    return hits <= 5


def release_successful_attempt(user_id):
    try:
        with db.engine.begin() as connection:
            connection.execute(_RELEASE_SUCCESS, {"key": _bucket_key(user_id)})
    except SQLAlchemyError as exc:
        raise CredentialRateLimitUnavailable() from exc


def replace_password_if_version(user, new_password, version):
    """Password hash and revocation version commit together, or neither does."""
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    result = db.session.execute(
        update(Users)
        .where(Users.id == user.id, Users.credential_version == version)
        .values(password=hashed, credential_version=Users.credential_version + 1)
    )
    if result.rowcount != 1:
        db.session.rollback()
        return False
    db.session.commit()
    return True

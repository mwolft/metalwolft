"""Database-backed limits for the token-scoped customer photo API."""

from datetime import timedelta
from hashlib import sha256

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from api.customer_photo_service import utcnow
from api.models import db


class CustomerPhotoRateLimitUnavailable(RuntimeError):
    pass


_UPSERT = text("""
    INSERT INTO customer_photo_rate_limits (bucket_key, window_started_at, hits)
    VALUES (:bucket_key, :now, 1)
    ON CONFLICT (bucket_key) DO UPDATE SET
        hits = CASE
            WHEN customer_photo_rate_limits.window_started_at <= :cutoff THEN 1
            WHEN customer_photo_rate_limits.hits >= :max_hits THEN :max_hits
            ELSE customer_photo_rate_limits.hits + 1
        END,
        window_started_at = CASE
            WHEN customer_photo_rate_limits.window_started_at <= :cutoff THEN :now
            ELSE customer_photo_rate_limits.window_started_at
        END
    RETURNING hits
""")


def allow_photo_request(scope, *, limit, window_seconds=600, session=None, now=None):
    """Count atomically across workers; fail closed if the shared store fails."""
    session = session or db.session
    now = now or utcnow()
    bucket_key = sha256(scope.encode("utf-8")).hexdigest()
    try:
        hits = session.execute(_UPSERT, {
            "bucket_key": bucket_key,
            "now": now,
            "cutoff": now - timedelta(seconds=window_seconds),
            "max_hits": limit + 1,
        }).scalar_one()
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise CustomerPhotoRateLimitUnavailable("El límite compartido no está disponible.") from exc
    return hits <= limit

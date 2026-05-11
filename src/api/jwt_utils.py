from __future__ import annotations

from typing import Any

from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity


def create_user_access_token(user, *, expires_delta=None) -> str:
    additional_claims = {
        "email": user.email,
        "is_admin": bool(user.is_admin),
    }

    return create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims,
        expires_delta=expires_delta,
    )


def get_current_user_context() -> dict[str, Any] | None:
    identity = get_jwt_identity()
    if identity is None:
        return None

    claims = get_jwt() or {}

    if isinstance(identity, dict):
        return {
            "user_id": _normalize_user_id(identity.get("user_id")),
            "email": identity.get("email") or claims.get("email"),
            "is_admin": _normalize_is_admin(identity.get("is_admin", claims.get("is_admin", False))),
        }

    return {
        "user_id": _normalize_user_id(identity),
        "email": claims.get("email"),
        "is_admin": _normalize_is_admin(claims.get("is_admin", False)),
    }


def _normalize_user_id(value: Any) -> Any:
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def _normalize_is_admin(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return bool(value)

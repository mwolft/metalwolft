"""Verify Google Identity Services credentials before issuing a local session."""

import os

import jwt
from flask import current_app, has_app_context
from jwt import PyJWKClient


GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
_jwks = PyJWKClient(GOOGLE_CERTS_URL, cache_jwk_set=True, lifespan=3600, timeout=5)


class GoogleIdentityError(ValueError):
    pass


def verify_google_identity(credential):
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise GoogleIdentityError("El acceso con Google no está configurado.")
    if not isinstance(credential, str) or not credential or len(credential) > 8192:
        raise GoogleIdentityError("Credencial de Google inválida.")

    phase = "key_fetch"
    try:
        key = _jwks.get_signing_key_from_jwt(credential).key
        phase = "claims_validation"
        claims = jwt.decode(
            credential,
            key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=GOOGLE_ISSUERS,
            options={"require": ["iss", "aud", "exp", "iat", "sub", "email"]},
            leeway=30,
        )
    except (jwt.PyJWTError, ValueError, OSError) as exc:
        if has_app_context() and current_app.config.get("APP_ENV") == "development":
            current_app.logger.warning(
                "google_identity_verification_failed category=%s exception=%s",
                phase,
                type(exc).__name__,
            )
        raise GoogleIdentityError("No se pudo verificar la identidad de Google.") from exc

    subject = claims.get("sub")
    email = claims.get("email")
    if (
        not isinstance(subject, str) or not subject or len(subject) > 255
        or not isinstance(email, str) or not email.strip() or len(email) > 120
        or claims.get("email_verified") is not True
    ):
        raise GoogleIdentityError("La cuenta Google no tiene un correo verificado.")

    return {"sub": subject, "email": email.strip().lower()}

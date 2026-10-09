"""Token-scoped public API for private post-delivery photographs."""

from flask import Blueprint, current_app, jsonify, request

from api.customer_photo_service import (
    MAX_REQUEST_BYTES, CustomerPhotoError, PhotoRateLimiter, resolve_photo_request,
    submit_photos, utcnow,
)
from api.models import db
from api.private_object_storage import (
    PrivateObjectStorageConfigurationError, PrivateObjectStorageOperationError,
)


customer_photo_bp = Blueprint("customer_photo_bp", __name__)
_limiter = PhotoRateLimiter()


def _token():
    header = request.headers.get("Authorization", "")
    return header[7:] if header.startswith("Bearer ") else ""


@customer_photo_bp.after_request
def _private_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    return response


@customer_photo_bp.route("", methods=["GET"])
def photo_request_details():
    if not current_app.config.get("CUSTOMER_PHOTOS_ENABLED"):
        return jsonify({"error": "Solicitud no disponible."}), 404
    if not _limiter.allow(f"get:{request.remote_addr}"):
        return jsonify({"error": "Demasiados intentos."}), 429
    item = resolve_photo_request(_token())
    if not item:
        return jsonify({"error": "Enlace no válido o caducado."}), 404
    return jsonify({
        "mode": item.mode,
        "status": "received" if item.submitted_at else "open",
        "commercial_consent_active": bool(item.commercial_consent and not item.consent_revoked_at),
        "max_images": 3,
        "max_image_bytes": 5 * 1024 * 1024,
        "terms_version": item.terms_version,
        "terms_url": item.terms_url,
        "terms_text": item.terms_text,
        "consent_text": item.offered_consent_text,
    })


@customer_photo_bp.route("", methods=["POST"])
def upload_customer_photos():
    if not current_app.config.get("CUSTOMER_PHOTOS_ENABLED"):
        return jsonify({"error": "Solicitud no disponible."}), 404
    if not _limiter.allow(f"post:{request.remote_addr}", limit=5):
        return jsonify({"error": "Demasiados intentos."}), 429
    if request.content_length is None or request.content_length > MAX_REQUEST_BYTES:
        return jsonify({"error": "El envío supera el tamaño permitido."}), 413
    try:
        submit_photos(
            token=_token(), files=request.files.getlist("photos"),
            commercial_consent=request.form.get("commercial_consent"),
            app=current_app,
            evidence={"channel": "public_photo_form"},
        )
    except CustomerPhotoError as exc:
        return jsonify({"error": str(exc)}), 400
    except (PrivateObjectStorageConfigurationError, PrivateObjectStorageOperationError):
        current_app.logger.exception("Private photo storage unavailable")
        return jsonify({"error": "No se han podido guardar las fotografías."}), 503
    return jsonify({"message": "Hemos recibido tus fotografías. Gracias por compartirlas."}), 201


@customer_photo_bp.route("/consent/revoke", methods=["POST"])
def revoke_customer_photo_consent():
    if not current_app.config.get("CUSTOMER_PHOTOS_ENABLED"):
        return jsonify({"error": "Solicitud no disponible."}), 404
    if not _limiter.allow(f"revoke:{request.remote_addr}", limit=5):
        return jsonify({"error": "Demasiados intentos."}), 429
    item = resolve_photo_request(_token())
    if not item or not item.submitted_at:
        return jsonify({"error": "Solicitud no disponible."}), 404
    if item.commercial_consent and not item.consent_revoked_at:
        item.consent_revoked_at = utcnow()
        db.session.commit()
    return jsonify({"message": "Hemos registrado la retirada de tu autorización comercial."})

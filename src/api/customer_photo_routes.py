"""Token-scoped public API for private post-delivery photographs."""

from io import BytesIO

from flask import Blueprint, Request, current_app, jsonify, request

from api.customer_photo_service import (
    MAX_IMAGES, MAX_IMAGE_BYTES, MAX_TOTAL_IMAGE_BYTES, MAX_REQUEST_BYTES,
    CustomerPhotoError, resolve_photo_request,
    submit_photos,
)
from api.customer_photo_mail import PhotoMailRejected, PhotoMailUncertain
from api.customer_photo_rate_limit import (
    CustomerPhotoRateLimitUnavailable, allow_photo_request,
)


customer_photo_bp = Blueprint("customer_photo_bp", __name__)


class PhotoUploadRequest(Request):
    """Keep bounded customer-photo multipart files in memory, never OS temp files."""

    def _get_file_stream(self, total_content_length, content_type, filename=None, content_length=None):
        if self.method == "POST" and self.path.rstrip("/") == "/api/customer-photos":
            return BytesIO()
        return super()._get_file_stream(total_content_length, content_type, filename, content_length)


def _token():
    header = request.headers.get("Authorization", "")
    return header[7:] if header.startswith("Bearer ") else ""


def _within_limits(operation, item=None):
    if item is None:
        return allow_photo_request("public", limit=3000)
    if not allow_photo_request(f"request:{item.id}:{operation}", limit={
        "get": 30, "post": 5,
    }[operation]):
        return False
    return True


@customer_photo_bp.errorhandler(CustomerPhotoRateLimitUnavailable)
def _rate_limit_unavailable(_error):
    current_app.logger.error("Shared customer photo rate limit unavailable")
    return jsonify({"error": "El formulario no está disponible temporalmente."}), 503


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
    if not _within_limits("get"):
        return jsonify({"error": "Demasiados intentos."}), 429
    item = resolve_photo_request(_token())
    if not item:
        return jsonify({"error": "Enlace no válido o caducado."}), 404
    if not _within_limits("get", item):
        return jsonify({"error": "Demasiados intentos."}), 429
    if item.mode == "incentive" and current_app.config.get("APP_ENV") == "production":
        return jsonify({"error": "Solicitud no disponible."}), 404
    if item.is_simulation:
        from api.customer_photo_service import _simulation_allowed
        from api.order_confirmation_context import get_order_confirmation_recipient_email
        if not _simulation_allowed(current_app, get_order_confirmation_recipient_email(item.order)):
            return jsonify({"error": "Solicitud no disponible."}), 404
    return jsonify({
        "mode": item.mode,
        "is_simulation": item.is_simulation,
        "status": "received" if item.submitted_at else "pending_confirmation" if item.delivery_status in {"sending", "unknown"} else "open",
        "commercial_consent_active": bool(item.commercial_consent and not item.consent_revoked_at),
        "max_images": MAX_IMAGES,
        "max_image_bytes": MAX_IMAGE_BYTES,
        "max_total_bytes": MAX_TOTAL_IMAGE_BYTES,
        "terms_version": item.terms_version,
        "terms_url": item.terms_url,
        "terms_text": item.terms_text,
        "consent_text": item.offered_consent_text,
    })


@customer_photo_bp.route("", methods=["POST"])
def upload_customer_photos():
    if not current_app.config.get("CUSTOMER_PHOTOS_ENABLED"):
        return jsonify({"error": "Solicitud no disponible."}), 404
    if not _within_limits("post"):
        return jsonify({"error": "Demasiados intentos."}), 429
    if request.content_length is None or request.content_length > MAX_REQUEST_BYTES:
        return jsonify({"error": "El envío supera el tamaño permitido."}), 413
    item = resolve_photo_request(_token())
    if not item:
        return jsonify({"error": "Enlace no válido o caducado."}), 404
    if not _within_limits("post", item):
        return jsonify({"error": "Demasiados intentos."}), 429
    try:
        submit_photos(
            token=_token(), files=request.files.getlist("photos"),
            commercial_consent=request.form.get("commercial_consent"),
            app=current_app,
            evidence={"channel": "public_photo_form"},
        )
    except CustomerPhotoError as exc:
        return jsonify({"error": str(exc)}), 400
    except PhotoMailRejected as exc:
        return jsonify({"error": str(exc)}), 503
    except PhotoMailUncertain as exc:
        current_app.logger.warning("Customer photo mail acceptance uncertain")
        return jsonify({"error": str(exc)}), 409
    return jsonify({"message": "El servidor de correo ha aceptado tus fotografías. Gracias por compartirlas."}), 201

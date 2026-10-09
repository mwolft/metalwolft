"""Post-delivery photo requests. No payment or fiscal side effects live here."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import secrets
import re
import threading
import time
import warnings
from collections import defaultdict, deque
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from api.design_service import order_contains_design_service
from api.models import CustomerPhotoImage, CustomerPhotoRequest, db
from api.order_confirmation_context import get_order_confirmation_recipient_email
from api.private_object_storage import get_private_object_storage


MODES = {"none", "free", "incentive"}
MAX_IMAGES = 3
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_REQUEST_BYTES = 16 * 1024 * 1024
MAX_PIXELS = 20_000_000
ALLOWED_IMAGES = {"image/jpeg": ("JPEG", ".jpg"), "image/png": ("PNG", ".png"), "image/webp": ("WEBP", ".webp")}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class CustomerPhotoError(ValueError):
    pass


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def token_hash(token):
    return sha256(str(token).encode("utf-8")).hexdigest()


def _photo_form_url(app, token):
    base = str(app.config.get("FRONTEND_URL") or "").rstrip("/")
    if not base.startswith(("https://", "http://localhost:", "http://127.0.0.1:")):
        raise CustomerPhotoError("La URL pública del formulario no es segura.")
    return f"{base}/fotos-clientes#{token}"


def _enabled(app, name):
    return bool(app.config.get(name, False))


def _terms(app, mode):
    version = str(app.config.get("CUSTOMER_PHOTOS_TERMS_VERSION") or "").strip()
    consent = str(app.config.get("CUSTOMER_PHOTOS_CONSENT_TEXT") or "").strip()
    terms_text = str(app.config.get("CUSTOMER_PHOTOS_TERMS_TEXT") or "").strip()
    conditions_url = str(app.config.get("CUSTOMER_PHOTOS_TERMS_URL") or "").strip()
    if not version or not consent or not terms_text or (mode == "incentive" and not conditions_url):
        raise CustomerPhotoError("Faltan las condiciones y autorización aprobadas para fotografías.")
    if mode == "incentive" and not conditions_url.startswith("https://"):
        raise CustomerPhotoError("Las condiciones del incentivo necesitan una URL HTTPS.")
    return version, consent, terms_text, conditions_url


def _eligible(order, mode, app):
    if mode not in MODES or mode == "none":
        raise CustomerPhotoError("Selecciona una modalidad de fotografías válida.")
    if not _enabled(app, "CUSTOMER_PHOTOS_ENABLED"):
        raise CustomerPhotoError("La solicitud de fotografías no está habilitada.")
    if order_contains_design_service(order) or not order.order_details:
        raise CustomerPhotoError("Solo se pueden solicitar fotografías de pedidos físicos.")
    email = get_order_confirmation_recipient_email(order)
    if not email or not EMAIL_PATTERN.fullmatch(email):
        raise CustomerPhotoError("El pedido no tiene destinatario de email válido.")
    _terms(app, mode)
    if mode == "free":
        return
    if not _enabled(app, "CUSTOMER_PHOTOS_INCENTIVE_ENABLED"):
        raise CustomerPhotoError("El incentivo fotográfico no está habilitado.")
    if app.config.get("APP_ENV") == "production":
        raise CustomerPhotoError("El incentivo fotográfico está pendiente de aprobación para producción.")
    context = order.confirmed_order_context
    if not context or context.source != "web_checkout" or context.payment_status != "confirmed":
        raise CustomerPhotoError("El pedido no tiene pago web confirmado.")
    if context.currency != "EUR" or context.payment_amount < Decimal("20.00"):
        raise CustomerPhotoError("El importe o la moneda no permiten el incentivo.")
    identifiers = context.provider_identifiers or {}
    session = context.source_checkout_session
    if not session or session.order_id != order.id or session.status != "order_created":
        raise CustomerPhotoError("El checkout del pedido no está confirmado.")
    if context.payment_method == "stripe":
        valid_ref = identifiers.get("payment_intent_id") == context.payment_reference == session.payment_intent_id
    elif context.payment_method == "paypal":
        valid_ref = bool(session.provider_capture_id) and identifiers.get("provider_capture_id") == session.provider_capture_id
    else:
        valid_ref = False
    if not valid_ref:
        raise CustomerPhotoError("No consta una referencia reembolsable del proveedor.")
    # An offer is not a promise of a successful provider refund. Remaining balance
    # and external refunds must be reconciled before a future payment operation.


def create_photo_request(*, order, mode, app, email_options=None, session=None):
    """Stage one request in the caller's transaction; return the transient link."""
    session = session or db.session
    _eligible(order, mode, app)
    if session.query(CustomerPhotoRequest.id).filter_by(order_id=order.id).first():
        raise CustomerPhotoError("Este pedido ya tiene una solicitud de fotografías.")
    token = secrets.token_urlsafe(32)
    url = _photo_form_url(app, token)
    version, consent, terms_text, terms_url = _terms(app, mode)
    days = int(app.config.get("CUSTOMER_PHOTOS_TOKEN_DAYS", 30))
    if days < 1 or days > 365:
        raise CustomerPhotoError("La caducidad del enlace no es válida.")
    photo_request = CustomerPhotoRequest(
        order_id=order.id,
        mode=mode,
        offered_amount=Decimal("20.00") if mode == "incentive" else Decimal("0.00"),
        status="offered",
        token_hash=token_hash(token),
        token_expires_at=utcnow() + timedelta(days=days),
        terms_version=version,
        terms_text=terms_text,
        terms_url=terms_url or None,
        offered_consent_text=consent,
        email_options=dict(email_options or {}),
    )
    session.add(photo_request)
    return photo_request, url


def rotate_photo_link(photo_request, *, app):
    if photo_request.status != "offered" or photo_request.submitted_at or photo_request.token_revoked_at:
        raise CustomerPhotoError("Solo se puede reenviar una solicitud pendiente.")
    token = secrets.token_urlsafe(32)
    url = _photo_form_url(app, token)
    photo_request.token_hash = token_hash(token)
    photo_request.email_sent_at = None
    photo_request.email_failed_at = None
    return url


def resolve_photo_request(token, *, session=None, now=None):
    if not isinstance(token, str) or len(token) < 32 or len(token) > 128:
        return None
    session = session or db.session
    item = session.query(CustomerPhotoRequest).filter_by(token_hash=token_hash(token)).one_or_none()
    now = now or utcnow()
    if not item or item.status == "revoked" or item.token_revoked_at or item.token_expires_at <= now:
        return None
    return item


def validate_image(file):
    declared = str(getattr(file, "mimetype", "") or "").lower().strip()
    if declared not in ALLOWED_IMAGES:
        raise CustomerPhotoError("Solo se admiten fotografías JPEG, PNG o WebP.")
    content = file.stream.read(MAX_IMAGE_BYTES + 1)
    if not content or len(content) > MAX_IMAGE_BYTES:
        raise CustomerPhotoError("Cada fotografía debe ocupar 5 MB o menos.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(BytesIO(content))
            if image.format != ALLOWED_IMAGES[declared][0] or image.width * image.height > MAX_PIXELS:
                raise CustomerPhotoError("Una fotografía tiene formato o dimensiones no válidos.")
            image = ImageOps.exif_transpose(image)
            image.load()
            clean = BytesIO()
            fmt = ALLOWED_IMAGES[declared][0]
            image.save(clean, format=fmt)
            normalized = clean.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning) as exc:
        raise CustomerPhotoError("Una fotografía no es una imagen válida.") from exc
    if len(normalized) > MAX_IMAGE_BYTES:
        raise CustomerPhotoError("Una fotografía procesada supera 5 MB.")
    return declared, normalized, sha256(normalized).hexdigest(), ALLOWED_IMAGES[declared][1]


def submit_photos(*, token, files, commercial_consent, app, session=None, storage=None, evidence=None):
    """Upload before DB locking; delete uploaded objects on any DB failure."""
    session = session or db.session
    photo_request = resolve_photo_request(token, session=session)
    if not photo_request or photo_request.status != "offered":
        raise CustomerPhotoError("El enlace no está disponible para un nuevo envío.")
    if commercial_consent not in ("yes", "no"):
        raise CustomerPhotoError("Indica expresamente si autorizas el uso comercial.")
    files = [file for file in files if file and getattr(file, "filename", None)]
    if not 1 <= len(files) <= MAX_IMAGES:
        raise CustomerPhotoError("Selecciona entre una y tres fotografías.")
    validated = [validate_image(file) for file in files]
    hashes = [item[2] for item in validated]
    if len(set(hashes)) != len(hashes):
        raise CustomerPhotoError("No envíes la misma fotografía dos veces.")
    request_id = photo_request.id
    consent_text = photo_request.offered_consent_text
    session.rollback()  # End the validation read transaction before any R2 network call.
    private_storage = storage or get_private_object_storage(app)
    uploaded = []
    try:
        for mime, content, digest, extension in validated:
            now = utcnow()
            key = f"customer-photos/{now:%Y}/{now:%m}/{uuid4().hex}{extension}"
            uploaded.append((key, mime, len(content), digest))
            private_storage.put_object(storage_key=key, content=content, mime_type=mime)
        locked = (
            session.query(CustomerPhotoRequest)
            .filter_by(id=request_id)
            .with_for_update()
            .one()
        )
        if locked.status != "offered" or locked.submitted_at or locked.token_revoked_at or locked.token_expires_at <= utcnow():
            raise CustomerPhotoError("Esta solicitud ya se ha enviado o ha caducado.")
        for key, mime, size, digest in uploaded:
            session.add(CustomerPhotoImage(
                request_id=locked.id, storage_key=key, mime_type=mime,
                file_size=size, sha256=digest, review_status="pending",
            ))
        locked.status = "received"
        locked.submitted_at = utcnow()
        locked.commercial_consent = commercial_consent == "yes"
        locked.consent_text = consent_text
        locked.consent_version = locked.terms_version
        locked.consent_at = utcnow()
        locked.consent_evidence = evidence or {}
        session.commit()
        return locked
    except Exception:
        session.rollback()
        for key, _, _, _ in uploaded:
            try:
                private_storage.delete_object(storage_key=key)
            except Exception:
                app.logger.exception("Private photo upload cleanup failed")
        raise


def review_photo_request(*, request_id, decision, note, actor, session=None):
    session = session or db.session
    item = session.query(CustomerPhotoRequest).filter_by(id=request_id).with_for_update().one_or_none()
    if not item or item.status != "received" or not item.images:
        raise CustomerPhotoError("La solicitud no está pendiente de revisión.")
    if decision not in {"approve", "reject"}:
        raise CustomerPhotoError("Decisión de revisión no válida.")
    if decision == "reject" and not str(note or "").strip():
        raise CustomerPhotoError("Indica el motivo interno del rechazo.")
    item.status = ("refund_pending" if item.mode == "incentive" else "approved") if decision == "approve" else "rejected"
    item.reviewed_at = utcnow()
    item.reviewed_by = actor
    item.review_note = str(note or "").strip() or None
    for image in item.images:
        image.review_status = "approved" if decision == "approve" else "rejected"
    return item


class PhotoRateLimiter:
    """Per-process abuse throttle; deployment-wide limiting needs an external store."""

    def __init__(self):
        self.lock = threading.Lock()
        self.requests = defaultdict(deque)

    def allow(self, key, *, limit=10, window=600):
        now = time.monotonic()
        with self.lock:
            bucket = self.requests[key]
            while bucket and bucket[0] <= now - window:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True

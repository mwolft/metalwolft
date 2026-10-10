"""Post-delivery photo requests. No payment or fiscal side effects live here."""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import os
import secrets
import re
import warnings
from uuid import uuid4
from zoneinfo import ZoneInfo

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import text

from api.database_identity import parse_database_identity, validate_database_identity
from api.design_service import order_contains_design_service
from api.models import CustomerPhotoRequest, db
from api.order_confirmation_context import get_order_confirmation_recipient_email
from api.customer_photo_mail import (
    PhotoMailRejected, PhotoMailUncertain, build_photo_message,
    build_photo_confirmation_message, send_photo_message,
)


MODES = {"none", "free", "incentive"}
MAX_IMAGES = 5
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_PROCESSED_IMAGE_BYTES = 3 * 1024 * 1024
MAX_TOTAL_IMAGE_BYTES = 8 * 1024 * 1024
MAX_REQUEST_BYTES = 26 * 1024 * 1024
MAX_PIXELS = 20_000_000
ALLOWED_IMAGES = {"image/jpeg": ("JPEG", ".jpg"), "image/png": ("PNG", ".png"), "image/webp": ("WEBP", ".webp")}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MADRID = ZoneInfo("Europe/Madrid")


class CustomerPhotoError(ValueError):
    pass


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _madrid_date(moment):
    return moment.replace(tzinfo=timezone.utc).astimezone(MADRID).date()


def madrid_today():
    return _madrid_date(utcnow())


def _end_of_madrid_day(day):
    return datetime.combine(day + timedelta(days=1), time.min, MADRID).astimezone(timezone.utc).replace(tzinfo=None)


def review_deadline_on(photo_request):
    """Only a relay-accepted or manually reconciled receipt starts review time."""
    if photo_request.delivery_status != "accepted" or not photo_request.receipt_accredited_on:
        return None
    received_on = photo_request.receipt_accredited_on
    for note in photo_request.followup_notes:
        if note.kind == "correction_received" and note.received_on and note.received_on > received_on:
            received_on = note.received_on
    return received_on + timedelta(days=7)


def token_hash(token):
    return sha256(str(token).encode("utf-8")).hexdigest()


def _photo_form_url(app, token):
    base = str(app.config.get("FRONTEND_URL") or "").rstrip("/")
    if not base.startswith(("https://", "http://localhost:", "http://127.0.0.1:")):
        raise CustomerPhotoError("La URL pública del formulario no es segura.")
    return f"{base}/fotos-clientes#{token}"


def _enabled(app, name):
    return bool(app.config.get(name, False))


def _incentive_allowed(app):
    return app.config.get("APP_ENV") != "production" and _enabled(app, "CUSTOMER_PHOTOS_INCENTIVE_ENABLED")


def _verified_test_database(app):
    """Fail closed unless the effective connection matches the configured Neon child."""
    expected_host = str(app.config.get("CUSTOMER_PHOTOS_INCENTIVE_TEST_DB_HOST") or "").strip()
    if not expected_host or not expected_host.endswith(".neon.tech"):
        return False
    try:
        identity = parse_database_identity(db.engine.url.render_as_string(hide_password=False))
        validate_database_identity(
            identity,
            expected_host=os.getenv("DATABASE_EXPECTED_HOST"),
            expected_name=os.getenv("DATABASE_EXPECTED_NAME"),
            expected_user=os.getenv("DATABASE_EXPECTED_USER"),
        )
        if identity.host != expected_host:
            return False
        with db.engine.connect() as connection:
            database_name, username = connection.execute(text("SELECT current_database(), current_user")).one()
        return database_name == identity.database_name and username == identity.username
    except Exception:
        return False


def _simulation_allowed(app, email):
    if not isinstance(email, str):
        return False
    if not (
        app.config.get("APP_ENV") == "development"
        and _enabled(app, "CUSTOMER_PHOTOS_ENABLED")
        and _enabled(app, "CUSTOMER_PHOTOS_INCENTIVE_ENABLED")
        and _enabled(app, "CUSTOMER_PHOTOS_INCENTIVE_TEST_MODE")
    ):
        return False
    allowed = {
        value.strip().casefold()
        for value in str(app.config.get("CUSTOMER_PHOTOS_INCENTIVE_TEST_EMAILS") or "").split(",")
        if value.strip()
    }
    return email.strip().casefold() in allowed and _verified_test_database(app)


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


def has_active_commercial_license(photo_request):
    return bool(
        photo_request.commercial_consent is True
        and photo_request.consent_at
        and photo_request.consent_version
        and photo_request.consent_version == photo_request.terms_version
        and photo_request.consent_text
        and photo_request.consent_text == photo_request.offered_consent_text
        and not photo_request.consent_revoked_at
    )


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
        return False
    if not _incentive_allowed(app):
        raise CustomerPhotoError("El incentivo fotográfico está pendiente de aprobación para producción.")
    if _enabled(app, "CUSTOMER_PHOTOS_INCENTIVE_TEST_MODE"):
        if not _simulation_allowed(app, email):
            raise CustomerPhotoError("La simulación requiere una child verificada y un destinatario autorizado.")
        return True
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
        refs = (identifiers.get("payment_intent_id"), context.payment_reference, session.payment_intent_id)
        valid_ref = session.payment_provider == "stripe" and all(isinstance(ref, str) and ref.strip() for ref in refs) and len(set(refs)) == 1
    elif context.payment_method == "paypal":
        capture = identifiers.get("provider_capture_id")
        provider_order = identifiers.get("provider_order_id")
        valid_ref = (
            session.payment_provider == "paypal"
            and isinstance(capture, str) and bool(capture.strip())
            and capture == session.provider_capture_id
            and isinstance(provider_order, str) and bool(provider_order.strip())
            and provider_order == session.provider_order_id
            and capture == context.payment_reference
        )
    else:
        valid_ref = False
    if not valid_ref:
        raise CustomerPhotoError("No consta una referencia reembolsable del proveedor.")
    # An offer is not a promise of a successful provider refund. Remaining balance
    # and external refunds must be reconciled before a future payment operation.
    return False


def create_photo_request(*, order, mode, app, delivered_on=None, email_options=None, session=None):
    """Stage one request in the caller's transaction; return the transient link."""
    session = session or db.session
    is_simulation = _eligible(order, mode, app)
    today = _madrid_date(utcnow())
    if type(delivered_on) is not date:
        raise CustomerPhotoError("Indica expresamente la fecha real de entrega del pedido.")
    if delivered_on > today:
        raise CustomerPhotoError("La fecha real de entrega no puede ser futura.")
    participation_deadline = delivered_on + timedelta(days=30)
    if today > participation_deadline:
        raise CustomerPhotoError("Han transcurrido más de 30 días desde la entrega real.")
    if session.query(CustomerPhotoRequest.id).filter_by(order_id=order.id).first():
        raise CustomerPhotoError("Este pedido ya tiene una solicitud de fotografías.")
    token = secrets.token_urlsafe(32)
    url = _photo_form_url(app, token)
    version, consent, terms_text, terms_url = _terms(app, mode)
    photo_request = CustomerPhotoRequest(
        order_id=order.id,
        mode=mode,
        is_simulation=is_simulation,
        offered_amount=Decimal("20.00") if mode == "incentive" and not is_simulation else Decimal("0.00"),
        status="offered",
        token_hash=token_hash(token),
        token_expires_at=_end_of_madrid_day(participation_deadline),
        actual_delivery_on=delivered_on,
        participation_deadline_on=participation_deadline,
        terms_version=version,
        terms_text=terms_text,
        terms_url=terms_url or None,
        offered_consent_text=consent,
        email_options=dict(email_options or {}),
    )
    session.add(photo_request)
    return photo_request, url


def rotate_photo_link(photo_request, *, app):
    if photo_request.participation_deadline_on and _madrid_date(utcnow()) > photo_request.participation_deadline_on:
        raise CustomerPhotoError("El plazo de participación de 30 días ha terminado.")
    if photo_request.mode == "incentive" and not _incentive_allowed(app):
        raise CustomerPhotoError("El incentivo fotográfico está pendiente de aprobación para producción.")
    if photo_request.is_simulation and not _simulation_allowed(app, get_order_confirmation_recipient_email(photo_request.order)):
        raise CustomerPhotoError("La simulación ya no está autorizada en este entorno.")
    if (photo_request.status != "offered" or photo_request.submitted_at or photo_request.token_revoked_at
            or photo_request.delivery_status in {"sending", "unknown"}):
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
    if (not item or item.status == "revoked" or item.token_revoked_at or item.token_expires_at <= now
            or (item.participation_deadline_on and _madrid_date(now) > item.participation_deadline_on)):
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
            fmt = ALLOWED_IMAGES[declared][0]
            if fmt == "JPEG" and image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
            normalized = None
            for edge in (2400, 2000, 1600):
                candidate = image.copy()
                candidate.thumbnail((edge, edge), Image.Resampling.LANCZOS)
                for quality in ((88, 80, 72) if fmt != "PNG" else (None,)):
                    clean = BytesIO()
                    options = {"optimize": True} if fmt == "PNG" else {"quality": quality}
                    candidate.save(clean, format=fmt, **options)
                    if clean.tell() <= MAX_PROCESSED_IMAGE_BYTES:
                        normalized = clean.getvalue()
                        break
                if normalized is not None:
                    break
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise CustomerPhotoError("Una fotografía no es una imagen válida.") from exc
    if normalized is None:
        raise CustomerPhotoError("No hemos podido ajustar una fotografía al tamaño permitido sin perder demasiada calidad.")
    return declared, normalized, sha256(normalized).hexdigest(), ALLOWED_IMAGES[declared][1]


def submit_photos(*, token, front_photo, perspective_photo, additional_photos, commercial_consent, app, session=None, send_message=None, evidence=None):
    """Reserve a single attempt, send without a DB lock, then record relay acceptance."""
    session = session or db.session
    photo_request = resolve_photo_request(token, session=session)
    if not photo_request or photo_request.status != "offered" or photo_request.delivery_status in {"sending", "unknown"}:
        raise CustomerPhotoError("El enlace no está disponible para un nuevo envío.")
    if photo_request.mode == "incentive" and not _incentive_allowed(app):
        raise CustomerPhotoError("El incentivo fotográfico está pendiente de aprobación para producción.")
    if photo_request.is_simulation and not _simulation_allowed(app, get_order_confirmation_recipient_email(photo_request.order)):
        raise CustomerPhotoError("La simulación ya no está autorizada en este entorno.")
    if commercial_consent not in ("yes", "no"):
        raise CustomerPhotoError("Indica expresamente si autorizas el uso comercial.")
    if photo_request.mode == "incentive" and commercial_consent != "yes":
        raise CustomerPhotoError("Para participar en la promoción de 20 €, acepta expresamente la licencia de uso comercial.")
    if not front_photo or not getattr(front_photo, "filename", None):
        raise CustomerPhotoError("Selecciona una fotografía frontal de la reja.")
    if not perspective_photo or not getattr(perspective_photo, "filename", None):
        raise CustomerPhotoError("Selecciona una fotografía lateral o en perspectiva.")
    if any(not file or not getattr(file, "filename", None) for file in additional_photos):
        raise CustomerPhotoError("Selecciona archivos válidos para las fotografías adicionales.")
    if len(additional_photos) > MAX_IMAGES - 2:
        raise CustomerPhotoError("Puedes añadir un máximo de tres fotografías adicionales.")
    files = [front_photo, perspective_photo, *additional_photos]
    validated = [validate_image(file) for file in files]
    if sum(len(image[1]) for image in validated) > MAX_TOTAL_IMAGE_BYTES:
        raise CustomerPhotoError("El conjunto de fotografías supera 8 MB. Selecciona imágenes más pequeñas.")
    hashes = [item[2] for item in validated]
    if len(set(hashes)) != len(hashes):
        raise CustomerPhotoError("No envíes la misma fotografía dos veces.")
    request_id = photo_request.id
    order_reference = photo_request.order.locator
    recipient = get_order_confirmation_recipient_email(photo_request.order)
    session.rollback()
    attempt_id = uuid4().hex
    created_at = utcnow()
    message = build_photo_message(
        app=app, order_reference=order_reference, request_id=request_id,
        attempt_id=attempt_id, date=created_at, consent=commercial_consent == "yes", photos=validated,
        is_simulation=photo_request.is_simulation,
    )
    try:
        locked = session.query(CustomerPhotoRequest).filter_by(id=request_id).with_for_update().one()
        if (locked.token_hash != token_hash(token) or locked.status != "offered" or locked.submitted_at
                or locked.token_revoked_at or locked.token_expires_at <= utcnow()
                or (locked.participation_deadline_on and _madrid_date(utcnow()) > locked.participation_deadline_on)
                or locked.delivery_status in {"sending", "unknown"}
                or (locked.mode == "incentive" and not _incentive_allowed(app))
                or (locked.mode == "incentive" and commercial_consent != "yes")
                or (locked.is_simulation and not _simulation_allowed(app, recipient))):
            raise CustomerPhotoError("El enlace ya no está disponible.")
        locked.delivery_status = "sending"
        locked.delivery_attempt_id = attempt_id
        locked.delivery_started_at = created_at
        locked.delivery_message_id = message["Message-ID"]
        locked.photo_count = len(validated)
        locked.commercial_consent = commercial_consent == "yes"
        locked.consent_text = locked.offered_consent_text
        locked.consent_version = locked.terms_version
        locked.consent_at = created_at
        locked.consent_evidence = evidence or {}
        session.commit()
        try:
            (send_message or send_photo_message)(app=app, message=message)
        except PhotoMailRejected:
            _finish_delivery(session, request_id, attempt_id, "rejected")
            raise
        except Exception as exc:
            _finish_delivery(session, request_id, attempt_id, "unknown")
            raise PhotoMailUncertain("No podemos confirmar el envío. Contacta con MetalWolft antes de intentarlo de nuevo.") from exc
        try:
            result = _finish_delivery(session, request_id, attempt_id, "accepted")
        except Exception as exc:
            session.rollback()
            raise PhotoMailUncertain("El correo pudo haberse enviado, pero no se confirmó el registro. Contacta con MetalWolft.") from exc
        try:
            confirmation = build_photo_confirmation_message(
                app=app, recipient=recipient, order_reference=order_reference, request_id=request_id,
                is_simulation=result.is_simulation,
            )
            (send_message or send_photo_message)(app=app, message=confirmation)
        except Exception:
            app.logger.exception("Customer photo confirmation email failed request_id=%s", request_id)
        return result
    except Exception:
        session.rollback()
        raise


def _finish_delivery(session, request_id, attempt_id, outcome):
    item = session.query(CustomerPhotoRequest).filter_by(id=request_id).with_for_update().one()
    if item.delivery_attempt_id != attempt_id or item.delivery_status != "sending":
        raise PhotoMailUncertain("El estado del envío cambió; requiere conciliación manual.")
    item.delivery_status = outcome
    if outcome == "accepted":
        if item.status != "revoked":
            item.status = "received"
        item.submitted_at = utcnow()
        item.receipt_accredited_on = _madrid_date(item.submitted_at)
    elif outcome == "rejected":
        item.photo_count = None
        item.commercial_consent = None
        item.consent_text = None
        item.consent_version = None
        item.consent_at = None
        item.consent_evidence = None
    session.commit()
    return item


def review_photo_request(*, request_id, decision, note, actor, session=None, app=None):
    session = session or db.session
    item = session.query(CustomerPhotoRequest).filter_by(id=request_id).with_for_update().one_or_none()
    if not item or item.status != "received" or not item.mailbox_confirmed_at:
        raise CustomerPhotoError("La solicitud no está pendiente de revisión.")
    if decision not in {"approve", "reject"}:
        raise CustomerPhotoError("Decisión de revisión no válida.")
    if decision == "approve" and item.is_simulation and (app is None or app.config.get("APP_ENV") != "development"):
        raise CustomerPhotoError("Una simulación solo puede revisarse en desarrollo.")
    if decision == "approve" and item.mode == "incentive" and not item.is_simulation and (app is None or not _incentive_allowed(app)):
        raise CustomerPhotoError("El incentivo fotográfico está pendiente de aprobación para producción.")
    if decision == "approve" and item.mode == "incentive" and not has_active_commercial_license(item):
        raise CustomerPhotoError("No se puede aprobar el incentivo sin una licencia comercial vigente y vinculada a las condiciones ofrecidas.")
    if decision == "reject" and not str(note or "").strip():
        raise CustomerPhotoError("Indica el motivo interno del rechazo.")
    item.status = ("refund_pending" if item.mode == "incentive" and not item.is_simulation else "approved") if decision == "approve" else "rejected"
    item.reviewed_at = utcnow()
    item.reviewed_by = actor
    item.review_note = str(note or "").strip() or None
    return item


def stale_mail_attempts(*, session=None, now=None, min_age=timedelta(minutes=10)):
    """Report attempts needing manual mailbox reconciliation; never resend."""
    session = session or db.session
    cutoff = (now or utcnow()) - min_age
    return session.query(CustomerPhotoRequest).filter(
        CustomerPhotoRequest.delivery_status.in_(("sending", "unknown")),
        CustomerPhotoRequest.delivery_started_at <= cutoff,
    ).order_by(CustomerPhotoRequest.delivery_started_at).all()

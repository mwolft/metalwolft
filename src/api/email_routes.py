from collections import deque
from dataclasses import dataclass
from email.message import EmailMessage
import hashlib
import math
import os
import re
import smtplib
import ssl
import threading
import time

from flask import Blueprint, request, jsonify, current_app
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

from api.order_confirmation_context import get_order_confirmation_recipient_email
from api.transactional_email_renderer import (
    render_order_delivery_estimate_update_email,
    render_order_status_update_email,
)

email_bp = Blueprint('email_bp', __name__)
mail = Mail()

ORDER_PROGRESS_STATUSES = (
    ("pendiente", "Recibido"),
    ("fabricacion", "Fabricación"),
    ("pintura", "Pintura"),
    ("embalaje", "Embalaje"),
    ("enviado", "Enviado"),
    ("entregado", "Entregado"),
)


@dataclass(frozen=True)
class OrderUpdateEmailChange:
    """Describe one committed operational change without persisting notification state."""

    old_order_status: str | None
    new_order_status: str | None
    old_estimated_delivery_at: object
    new_estimated_delivery_at: object
    old_estimated_delivery_note: str | None
    new_estimated_delivery_note: str | None
    status_email_options: dict | None = None

    @property
    def status_changed(self):
        return self.old_order_status != self.new_order_status

    @property
    def delivery_changed(self):
        return (
            self.old_estimated_delivery_at != self.new_estimated_delivery_at
            or self.old_estimated_delivery_note != self.new_estimated_delivery_note
        )

CONTACT_MAX_REQUEST_BYTES = 16_384
CONTACT_RATE_LIMIT_REQUESTS = 5
CONTACT_RATE_LIMIT_WINDOW_SECONDS = 600
CONTACT_GLOBAL_RATE_LIMIT_REQUESTS = 60
CONTACT_SMTP_TIMEOUT_SECONDS = 10
CONTACT_RECIPIENT = "admin@metalwolft.com"
ISSUE_MAX_REQUEST_BYTES = 16 * 1024 * 1024
ISSUE_MAX_IMAGES = 3
ISSUE_MAX_IMAGE_BYTES = 5 * 1024 * 1024
ISSUE_RATE_LIMIT_REQUESTS = 5
ISSUE_ALLOWED_IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
ISSUE_TYPES = frozenset(
    {
        "Pintura o acabado",
        "Medidas o encaje",
        "Transporte o embalaje",
        "Otro",
    }
)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_PATTERN = re.compile(r"^[0-9+().\-\s]+$")


class ContactEmailDeliveryError(RuntimeError):
    """Raised when the configured SMTP service cannot deliver contact mail."""


class _ContactRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._client_requests = {}
        self._global_requests = deque()
        self._last_cleanup = 0

    @staticmethod
    def _prune(requests, cutoff):
        while requests and requests[0] <= cutoff:
            requests.popleft()

    def allow(self, client_key):
        now = time.monotonic()
        cutoff = now - CONTACT_RATE_LIMIT_WINDOW_SECONDS

        with self._lock:
            self._prune(self._global_requests, cutoff)
            if now - self._last_cleanup >= CONTACT_RATE_LIMIT_WINDOW_SECONDS:
                for existing_key, requests in list(self._client_requests.items()):
                    self._prune(requests, cutoff)
                    if not requests:
                        del self._client_requests[existing_key]
                self._last_cleanup = now

            client_requests = self._client_requests.setdefault(client_key, deque())
            self._prune(client_requests, cutoff)

            if len(self._global_requests) >= CONTACT_GLOBAL_RATE_LIMIT_REQUESTS:
                retry_after = math.ceil(
                    CONTACT_RATE_LIMIT_WINDOW_SECONDS
                    - (now - self._global_requests[0])
                )
                return False, max(1, retry_after)

            if len(client_requests) >= CONTACT_RATE_LIMIT_REQUESTS:
                retry_after = math.ceil(
                    CONTACT_RATE_LIMIT_WINDOW_SECONDS
                    - (now - client_requests[0])
                )
                return False, max(1, retry_after)

            client_requests.append(now)
            self._global_requests.append(now)
            return True, None

    def reset(self):
        with self._lock:
            self._client_requests.clear()
            self._global_requests.clear()
            self._last_cleanup = 0


_contact_rate_limiter = _ContactRateLimiter()
_issue_rate_limiter = _ContactRateLimiter()


def _contact_client_key():
    client_address = (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
        or request.remote_addr
        or "unknown"
    )
    return hashlib.sha256(client_address.encode("utf-8")).hexdigest()


def _normalize_contact_data(data):
    if not isinstance(data, dict):
        return None, "La solicitud no contiene datos válidos."

    field_rules = {
        "name": ("El nombre", 1, 80),
        "firstname": ("Los apellidos", 1, 120),
        "email": ("El email", 3, 254),
        "phone": ("El teléfono", 7, 25),
        "message": ("El mensaje", 10, 4_000),
    }
    normalized = {}

    for field, (label, minimum, maximum) in field_rules.items():
        value = data.get(field)
        if not isinstance(value, str):
            return None, f"{label} es obligatorio."

        value = value.strip()
        if field != "message":
            value = " ".join(value.split())

        if len(value) < minimum or len(value) > maximum:
            return None, f"{label} debe tener entre {minimum} y {maximum} caracteres."
        normalized[field] = value

    if not _EMAIL_PATTERN.fullmatch(normalized["email"]):
        return None, "El email no tiene un formato válido."

    phone = normalized["phone"]
    digit_count = sum(character.isdigit() for character in phone)
    if not _PHONE_PATTERN.fullmatch(phone) or not 7 <= digit_count <= 15:
        return None, "El teléfono no tiene un formato válido."

    return normalized, None


def _send_contact_email(contact_data):
    smtp_server = current_app.config.get("MAIL_SERVER")
    smtp_port = current_app.config.get("MAIL_PORT")
    sender = current_app.config.get("MAIL_DEFAULT_SENDER") or os.getenv(
        "MAIL_DEFAULT_SENDER"
    )

    if not smtp_server or not smtp_port or not sender:
        raise ContactEmailDeliveryError("SMTP is not configured")

    message = EmailMessage()
    message["Subject"] = "Mensaje desde la web"
    message["From"] = sender
    message["To"] = CONTACT_RECIPIENT
    message.set_content(
        "\n".join(
            [
                f"Nombre: {contact_data['name']} {contact_data['firstname']}",
                f"Teléfono: {contact_data['phone']}",
                f"Correo: {contact_data['email']}",
                f"Mensaje: {contact_data['message']}",
            ]
        )
    )

    try:
        use_ssl = bool(current_app.config.get("MAIL_USE_SSL"))
        use_tls = bool(current_app.config.get("MAIL_USE_TLS"))
        smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        smtp_options = {
            "host": smtp_server,
            "port": int(smtp_port),
            "timeout": CONTACT_SMTP_TIMEOUT_SECONDS,
        }
        if use_ssl:
            smtp_options["context"] = ssl.create_default_context()

        with smtp_class(**smtp_options) as smtp:
            if use_tls and not use_ssl:
                smtp.starttls(context=ssl.create_default_context())

            username = current_app.config.get("MAIL_USERNAME")
            password = current_app.config.get("MAIL_PASSWORD")
            if username:
                smtp.login(username, password or "")

            smtp.send_message(message)
    except (OSError, TimeoutError, smtplib.SMTPException) as error:
        raise ContactEmailDeliveryError("SMTP delivery failed") from error

def configure_mail(app):
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'tu_correo@example.com')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'tu_contraseña')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
    mail.init_app(app)

def send_email(subject, recipients, body, attachment_path=None, html=None):
    try:
        msg = Message(subject, recipients=recipients, body=body, html=html)
        if attachment_path:
            with open(attachment_path, 'rb') as f:
                msg.attach(filename=os.path.basename(attachment_path),
                           content_type='application/pdf',
                           data=f.read())
        mail.send(msg)
        return True
    except Exception as exc:
        current_app.logger.error(
            "Error enviando correo (tipo=%s).",
            type(exc).__name__,
        )
        return False


def get_admin_recipients():
    """
    Devuelve lista de correos de admin desde ADMIN_NOTIFICATION_EMAILS.
    Puede contener varios separados por comas.
    """
    raw = os.getenv('ADMIN_NOTIFICATION_EMAILS', '')
    emails = [e.strip() for e in raw.split(',') if e.strip()]
    return emails


@email_bp.route('/contact', methods=['POST'])
def contact():
    allowed, retry_after = _contact_rate_limiter.allow(_contact_client_key())
    if not allowed:
        response = jsonify({
            "error": "Has enviado demasiadas solicitudes. Inténtalo de nuevo más tarde."
        })
        response.status_code = 429
        response.headers["Retry-After"] = str(retry_after)
        return response

    if (
        request.content_length is not None
        and request.content_length > CONTACT_MAX_REQUEST_BYTES
    ):
        return jsonify({"error": "La solicitud es demasiado grande."}), 400

    try:
        data, validation_error = _normalize_contact_data(request.get_json(silent=True))
        if validation_error:
            return jsonify({"error": validation_error}), 400

        _send_contact_email(data)
        return jsonify({"message": "Mensaje enviado correctamente."}), 200
    except ContactEmailDeliveryError as error:
        current_app.logger.warning(
            "Contact email delivery unavailable (error_type=%s)",
            type(error.__cause__ or error).__name__,
        )
        return jsonify({"error": "El servicio de contacto no está disponible."}), 503
    except Exception as error:
        current_app.logger.error(
            "Unexpected contact endpoint failure (error_type=%s)",
            type(error).__name__,
        )
        return jsonify({"error": "Internal server error"}), 500
    

def send_order_update_email(*, order, change, logger, send_email_func=None):
    """Send the applicable post-commit operational update for one order."""
    if not change.status_changed and not change.delivery_changed:
        return False

    if send_email_func is None:
        send_email_func = send_email

    try:
        recipient_email = get_order_confirmation_recipient_email(order)
        if not recipient_email:
            logger.warning("Order update email skipped without recipient order_id=%s", order.id)
            return False

        order_reference = getattr(order, "locator", None) or "—"
        if change.status_changed:
            current_status = getattr(order, "order_status", None)
            status_index = next(
                (index for index, (code, _) in enumerate(ORDER_PROGRESS_STATUSES) if code == current_status),
                None,
            )
            if status_index is None:
                return False

            options = change.status_email_options or {}
            if current_status in {"enviado", "entregado"} and options.get("status") == current_status:
                if not options.get("send_email", True):
                    return False
                include_receipt_guide = bool(options.get("include_receipt_guide", True))
                include_installation_guide = bool(options.get("include_installation_guide", True))
                include_incident_form = bool(options.get("include_incident_form", True))
                include_maintenance_guide = bool(options.get("include_maintenance_guide", True))
            else:
                include_receipt_guide = False
                include_installation_guide = True
                include_incident_form = False
                include_maintenance_guide = True

            rendered_email = render_order_status_update_email(
                order_reference=order_reference,
                current_status=current_status,
                statuses=ORDER_PROGRESS_STATUSES,
                estimated_delivery_date=_format_estimated_delivery_date(order),
                estimated_delivery_note=getattr(order, "estimated_delivery_note", None),
                include_receipt_guide=include_receipt_guide,
                include_installation_guide=include_installation_guide,
                include_incident_form=include_incident_form,
                include_maintenance_guide=include_maintenance_guide,
            )
            sent = bool(send_email_func(
                subject=f"Actualización de tu pedido: {ORDER_PROGRESS_STATUSES[status_index][1]}",
                recipients=[recipient_email],
                body=rendered_email.text,
                html=rendered_email.html,
            ))
            if not sent:
                logger.error("Order status email delivery failed order_id=%s", order.id)
            return sent

        rendered_email = render_order_delivery_estimate_update_email(
            order_reference=order_reference,
            estimated_delivery_date=_format_estimated_delivery_date(order),
            estimated_delivery_note=getattr(order, "estimated_delivery_note", None),
        )
        sent = bool(send_email_func(
            subject="Actualización: entrega estimada de tu pedido",
            recipients=[recipient_email],
            body=rendered_email.text,
            html=rendered_email.html,
        ))
        if not sent:
            logger.error("Order delivery update email delivery failed order_id=%s", order.id)
        return sent
    except Exception as exc:
        logger.error(
            "Order update email failed order_id=%s error_type=%s",
            getattr(order, "id", None),
            type(exc).__name__,
        )
        return False


def _format_estimated_delivery_date(order):
    value = getattr(order, "estimated_delivery_at", None)
    return value.strftime("%d/%m/%Y") if value else None


def _normalize_issue_report_data(data):
    field_rules = {
        "name": ("El nombre", 1, 80),
        "email": ("El email", 3, 254),
        "order_number": ("El número de pedido", 1, 80),
    }
    normalized = {}

    for field, (label, minimum, maximum) in field_rules.items():
        value = data.get(field)
        if not isinstance(value, str):
            return None, f"{label} es obligatorio."

        value = " ".join(value.strip().split())
        if len(value) < minimum or len(value) > maximum:
            return None, f"{label} debe tener entre {minimum} y {maximum} caracteres."
        normalized[field] = value

    if not _EMAIL_PATTERN.fullmatch(normalized["email"]):
        return None, "El email no tiene un formato válido."

    issue_type = data.get("issue_type")
    if issue_type not in ISSUE_TYPES:
        return None, "Selecciona un tipo de incidencia válido."
    normalized["issue_type"] = issue_type

    message_text = data.get("message", "")
    if not isinstance(message_text, str):
        return None, "La descripción de la incidencia no es válida."
    message_text = message_text.strip()
    if len(message_text) > 4_000:
        return None, "La descripción no puede superar los 4000 caracteres."
    normalized["message"] = message_text

    return normalized, None


def _matches_issue_image_signature(content, content_type):
    signatures = {
        "image/jpeg": lambda value: value.startswith(b"\xff\xd8\xff"),
        "image/png": lambda value: value.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": lambda value: len(value) >= 12
        and value.startswith(b"RIFF")
        and value[8:12] == b"WEBP",
    }
    return signatures[content_type](content)


def _validate_issue_images(files):
    images = [file for file in files if file and file.filename]
    if len(images) > ISSUE_MAX_IMAGES:
        return None, f"Puedes adjuntar un máximo de {ISSUE_MAX_IMAGES} imágenes."

    attachments = []
    for position, image in enumerate(images, start=1):
        content_type = (image.mimetype or "").lower()
        if content_type not in ISSUE_ALLOWED_IMAGE_MIME_TYPES:
            return None, "Las imágenes deben estar en formato JPG, PNG o WebP."

        content = image.read(ISSUE_MAX_IMAGE_BYTES + 1)
        if not content or len(content) > ISSUE_MAX_IMAGE_BYTES:
            return None, "Cada imagen puede ocupar como máximo 5 MB."
        if not _matches_issue_image_signature(content, content_type):
            return None, "Una de las imágenes no tiene un formato válido."

        filename = secure_filename(image.filename) or f"incidencia-{position}.jpg"
        attachments.append((filename, content_type, content))

    return attachments, None


def _send_issue_report_email(issue_data, attachments):
    body = "\n".join(
        [
            "INCIDENCIA DE CLIENTE - METALWOLFT",
            "",
            f"Nombre completo: {issue_data['name']}",
            f"Correo electrónico: {issue_data['email']}",
            f"Número de pedido: {issue_data['order_number']}",
            f"Tipo de incidencia: {issue_data['issue_type']}",
            "",
            "Descripción del problema:",
            issue_data["message"] or "(sin descripción)",
            "",
            "Este mensaje se ha generado automáticamente desde el formulario de incidencias de MetalWolft.",
        ]
    )
    message = Message(
        subject=f"Incidencia de cliente #{issue_data['order_number']} - {issue_data['issue_type']}",
        sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
        recipients=[CONTACT_RECIPIENT],
        body=body,
    )

    for filename, content_type, content in attachments:
        message.attach(filename=filename, content_type=content_type, data=content)

    mail.send(message)


@email_bp.route('/report-issue', methods=['POST'])
def report_issue():
    allowed, retry_after = _issue_rate_limiter.allow(_contact_client_key())
    if not allowed:
        response = jsonify({"error": "Has enviado demasiadas solicitudes. Inténtalo de nuevo más tarde."})
        response.status_code = 429
        response.headers["Retry-After"] = str(retry_after)
        return response

    if (
        request.content_length is not None
        and request.content_length > ISSUE_MAX_REQUEST_BYTES
    ):
        return jsonify({"error": "La solicitud es demasiado grande."}), 400

    issue_data, validation_error = _normalize_issue_report_data(request.form)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    attachments, image_error = _validate_issue_images(request.files.getlist("images"))
    if image_error:
        return jsonify({"error": image_error}), 400

    try:
        _send_issue_report_email(issue_data, attachments)
        return jsonify({"message": "Incidencia enviada correctamente."}), 200
    except Exception as error:
        current_app.logger.error(
            "Issue report delivery failed (error_type=%s)", type(error).__name__
        )
        return jsonify({"error": "El servicio de incidencias no está disponible."}), 503

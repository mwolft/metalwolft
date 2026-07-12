from flask_mail import Mail, Message
from flask import current_app, jsonify, url_for

mail = Mail()

ANCHORAGE_INTERIOR_HOLES = "Sin obra: con agujeros interiores"
ANCHORAGE_FRONT_PLATES = "Sin obra: con pletinas"
ANCHORAGE_METAL_CLAWS = "Con obra: con garras metálicas"
ANCHORAGE_METAL_CLAWS_DISABLED_LABEL = "Con obra: con garras metálicas (no disponible)"
ANCHORAGE_LEGACY_FRONT_HOLES = "Sin obra: con agujeros frontales"
LEGACY_ANCHORAGE_RECONFIGURE_MESSAGE = (
    "Esta configuración de instalación ya no está disponible. "
    "Vuelve a configurar el producto."
)

CONFIGURATOR_ANCHORAGES = {
    ANCHORAGE_INTERIOR_HOLES: {
        "label": ANCHORAGE_INTERIOR_HOLES,
        "supplement": 0.0,
        "enabled": True,
    },
    ANCHORAGE_FRONT_PLATES: {
        "label": ANCHORAGE_FRONT_PLATES,
        "supplement": 24.95,
        "enabled": True,
    },
    ANCHORAGE_METAL_CLAWS: {
        "label": ANCHORAGE_METAL_CLAWS,
        "supplement": 39.95,
        "enabled": False,
    },
}

CONFIGURATOR_COLORS = {
    "satinado_blanco",
    "satinado_negro",
    "satinado_gris",
    "satinado_verde",
    "forja_negro",
    "forja_gris",
    "forja_marron",
    "forja_azul",
    "forja_verde",
    "forja_dorado",
}


def _normalize_anchorage_value(value):
    if value is None:
        return None

    normalized = str(value).strip()
    if normalized == ANCHORAGE_METAL_CLAWS_DISABLED_LABEL:
        return ANCHORAGE_METAL_CLAWS
    return normalized


def _normalize_color_value(value):
    if value is None:
        return None
    return str(value).strip()


def validate_configurator_options(anclaje, color):
    normalized_anclaje = _normalize_anchorage_value(anclaje)
    normalized_color = _normalize_color_value(color)

    if normalized_anclaje == ANCHORAGE_LEGACY_FRONT_HOLES:
        raise ValueError(LEGACY_ANCHORAGE_RECONFIGURE_MESSAGE)

    anchorage_rule = CONFIGURATOR_ANCHORAGES.get(normalized_anclaje)
    if not anchorage_rule:
        raise ValueError("Selecciona un tipo de instalación válido")

    if not anchorage_rule["enabled"]:
        raise ValueError("Esta opción de instalación no está disponible actualmente")

    if normalized_color not in CONFIGURATOR_COLORS:
        raise ValueError("Selecciona un color válido")

    return normalized_anclaje, normalized_color

class APIException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


def send_email(subject, recipients, body, attachment_path=None):
    try:
        # Crear el mensaje de correo
        message = Message(
            subject=subject,
            recipients=recipients,  # Lista de destinatarios
            body=body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']  # Correo configurado como remitente
        )

        # Adjuntar archivo 
        if attachment_path:
            with open(attachment_path, "rb") as attachment:
                message.attach(
                    filename=attachment_path.split("/")[-1],
                    content_type="application/pdf",
                    data=attachment.read()
                )

        current_app.logger.info(f"Enviando correo a {recipients} con asunto '{subject}'.")
        mail.send(message)
        current_app.logger.info(f"Correo enviado correctamente a {recipients}.")
        return True
    except Exception as e:
        current_app.logger.error(f"Error al enviar el correo: {e}")
        return False


def calcular_precio_reja(alto_cm, ancho_cm, precio_m2):
    if not all([alto_cm, ancho_cm, precio_m2]):
        raise ValueError("Faltan datos para calcular el precio")

    alto = float(alto_cm)
    ancho = float(ancho_cm)
    area = (alto * ancho) / 10000  # cm² → m²

    if alto < 30 or ancho < 30 or alto > 250 or ancho > 250 or alto + ancho > 400:
        raise ValueError("Dimensiones fuera de rango permitido")

    base_price = 95
    if area >= 0.9:
        multiplier = 1
    elif area >= 0.8:
        multiplier = 1.1
    elif area >= 0.7:
        multiplier = 1.15
    elif area >= 0.6:
        multiplier = 1.2
    elif area >= 0.5:
        multiplier = 1.3
    elif area >= 0.4:
        multiplier = 1.55
    elif area >= 0.3:
        multiplier = 1.9
    elif area >= 0.2:
        multiplier = 2.5
    else:
        multiplier = 3.0

    precio = area * precio_m2 * multiplier
    return round(max(precio, base_price), 2)


def build_configured_reja_quote(alto_cm, ancho_cm, precio_m2, anclaje, color):
    base_unit_price = calcular_precio_reja(alto_cm, ancho_cm, precio_m2)
    normalized_anclaje, normalized_color = validate_configurator_options(anclaje, color)
    anchorage_supplement = CONFIGURATOR_ANCHORAGES[normalized_anclaje]["supplement"]

    return {
        "unit_price": round(base_unit_price + anchorage_supplement, 2),
        "base_unit_price": base_unit_price,
        "anchorage_supplement": anchorage_supplement,
        "anclaje": normalized_anclaje,
        "color": normalized_color,
    }


def calcular_precio_reja_configurada(alto_cm, ancho_cm, precio_m2, anclaje, color):
    return build_configured_reja_quote(
        alto_cm=alto_cm,
        ancho_cm=ancho_cm,
        precio_m2=precio_m2,
        anclaje=anclaje,
        color=color,
    )["unit_price"]

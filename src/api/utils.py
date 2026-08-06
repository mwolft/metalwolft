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
        "name": "Agujeros interiores",
        "label": ANCHORAGE_INTERIOR_HOLES,
        "description": "Instalación sin obra mediante agujeros interiores.",
        "supplement": 0.0,
        "enabled": True,
    },
    ANCHORAGE_FRONT_PLATES: {
        "name": "Pletinas",
        "label": ANCHORAGE_FRONT_PLATES,
        "description": "Instalación sin obra mediante pletinas.",
        "supplement": 24.95,
        "enabled": True,
    },
    ANCHORAGE_METAL_CLAWS: {
        "name": "Garras metálicas",
        "label": ANCHORAGE_METAL_CLAWS,
        "description": "Instalación con obra mediante garras metálicas.",
        "supplement": 39.95,
        "enabled": False,
    },
}

CONFIGURATOR_COLORS = {
    "satinado_blanco": {
        "name": "Blanco",
        "label": "Blanco liso",
        "finish": "liso",
        "finish_label": "Satinado liso",
        "enabled": True,
    },
    "satinado_negro": {
        "name": "Negro",
        "label": "Negro liso",
        "finish": "liso",
        "finish_label": "Satinado liso",
        "enabled": True,
    },
    "satinado_gris": {
        "name": "Gris medio",
        "label": "Gris medio liso",
        "finish": "liso",
        "finish_label": "Satinado liso",
        "enabled": True,
    },
    "satinado_verde": {
        "name": "Verde carruajes",
        "label": "Verde carruajes liso",
        "finish": "liso",
        "finish_label": "Satinado liso",
        "enabled": True,
    },
    "forja_negro": {
        "name": "Negro",
        "label": "Negro forja",
        "finish": "forja",
        "finish_label": "Efecto forja",
        "enabled": True,
    },
    "forja_gris": {
        "name": "Gris acero",
        "label": "Gris acero forja",
        "finish": "forja",
        "finish_label": "Efecto forja",
        "enabled": True,
    },
    "forja_marron": {
        "name": "Marrón castaño",
        "label": "Marrón castaño forja",
        "finish": "forja",
        "finish_label": "Efecto forja",
        "enabled": True,
    },
    "forja_azul": {
        "name": "Azul",
        "label": "Azul forja",
        "finish": "forja",
        "finish_label": "Efecto forja",
        "enabled": True,
    },
    "forja_verde": {
        "name": "Verde bronce",
        "label": "Verde bronce forja",
        "finish": "forja",
        "finish_label": "Efecto forja",
        "enabled": True,
    },
    "forja_dorado": {
        "name": "Dorado",
        "label": "Dorado forja",
        "finish": "forja",
        "finish_label": "Efecto forja",
        "enabled": True,
    },
}

CONFIGURATOR_MIN_DIMENSION_CM = 30.0
CONFIGURATOR_MAX_DIMENSION_CM = 250.0
CONFIGURATOR_MAX_DIMENSION_SUM_CM = 400.0
DEFAULT_CONFIGURATOR_ANCHORAGE = ANCHORAGE_INTERIOR_HOLES
DEFAULT_CONFIGURATOR_COLOR = "satinado_blanco"
DEFAULT_CONFIGURATOR_SCREW_OPTION = "standard"
SCREW_OPTION_LONG_150 = "long_150"

CONFIGURATOR_SCREW_OPTIONS = {
    ANCHORAGE_INTERIOR_HOLES: {
        DEFAULT_CONFIGURATOR_SCREW_OPTION: {
            "label": "Estándar incluida",
            "description": "Incluida en el pedido",
            "length_mm": 80,
            "supplement": 0.0,
            "enabled": True,
        },
        SCREW_OPTION_LONG_150: {
            "label": "Tornillos largos",
            "description": "Para huecos que necesitan mayor profundidad de fijación",
            "length_mm": 150,
            "supplement": 8.95,
            "enabled": True,
        },
    },
    ANCHORAGE_FRONT_PLATES: {
        DEFAULT_CONFIGURATOR_SCREW_OPTION: {
            "label": "Estándar incluida",
            "description": "Incluida en el pedido",
            "length_mm": 70,
            "supplement": 0.0,
            "enabled": True,
        },
        SCREW_OPTION_LONG_150: {
            "label": "Tornillos largos",
            "description": "Para huecos que necesitan mayor profundidad de fijación",
            "length_mm": 150,
            "supplement": 8.95,
            "enabled": True,
        },
    },
}


def serialize_configurator_configuration(product_id):
    return {
        "schema_version": 2,
        "product_id": int(product_id),
        "dimensions": {
            "alto": {
                "min_cm": CONFIGURATOR_MIN_DIMENSION_CM,
                "max_cm": CONFIGURATOR_MAX_DIMENSION_CM,
            },
            "ancho": {
                "min_cm": CONFIGURATOR_MIN_DIMENSION_CM,
                "max_cm": CONFIGURATOR_MAX_DIMENSION_CM,
            },
            "max_sum_cm": CONFIGURATOR_MAX_DIMENSION_SUM_CM,
        },
        "anchorages": [
            {
                "value": value,
                "name": rule["name"],
                "label": rule["label"],
                "description": rule["description"],
                "supplement": rule["supplement"],
                "enabled": rule["enabled"],
            }
            for value, rule in CONFIGURATOR_ANCHORAGES.items()
        ],
        "colors": [
            {
                "value": value,
                "name": rule["name"],
                "label": rule["label"],
                "finish": rule["finish"],
                "finish_label": rule["finish_label"],
                "enabled": rule["enabled"],
            }
            for value, rule in CONFIGURATOR_COLORS.items()
        ],
        "screw_options": {
            anchorage: [
                {
                    "value": value,
                    "label": rule["label"],
                    "description": rule["description"],
                    "length_mm": rule["length_mm"],
                    "supplement": rule["supplement"],
                    "enabled": rule["enabled"],
                }
                for value, rule in options.items()
            ]
            for anchorage, options in CONFIGURATOR_SCREW_OPTIONS.items()
        },
        "defaults": {
            "anchorage": DEFAULT_CONFIGURATOR_ANCHORAGE,
            "color": DEFAULT_CONFIGURATOR_COLOR,
            "screw_option": DEFAULT_CONFIGURATOR_SCREW_OPTION,
        },
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


def _normalize_screw_option_value(value):
    if value is None:
        return DEFAULT_CONFIGURATOR_SCREW_OPTION
    if not isinstance(value, str):
        raise ValueError("Selecciona una opción de tornillería válida")
    return value.strip()


def validate_configurator_options(anclaje, color, screw_option=None):
    normalized_anclaje = _normalize_anchorage_value(anclaje)
    normalized_color = _normalize_color_value(color)
    normalized_screw_option = _normalize_screw_option_value(screw_option)

    if normalized_anclaje == ANCHORAGE_LEGACY_FRONT_HOLES:
        raise ValueError(LEGACY_ANCHORAGE_RECONFIGURE_MESSAGE)

    anchorage_rule = CONFIGURATOR_ANCHORAGES.get(normalized_anclaje)
    if not anchorage_rule:
        raise ValueError("Selecciona un tipo de instalación válido")

    if not anchorage_rule["enabled"]:
        raise ValueError("Esta opción de instalación no está disponible actualmente")

    color_rule = CONFIGURATOR_COLORS.get(normalized_color)
    if not color_rule:
        raise ValueError("Selecciona un color válido")

    if not color_rule["enabled"]:
        raise ValueError("Este color no está disponible actualmente")

    screw_options = CONFIGURATOR_SCREW_OPTIONS.get(normalized_anclaje)
    screw_rule = screw_options.get(normalized_screw_option) if screw_options else None
    if not screw_rule:
        raise ValueError("Selecciona una opción de tornillería válida para esta instalación")

    if not screw_rule["enabled"]:
        raise ValueError("Esta opción de tornillería no está disponible actualmente")

    return normalized_anclaje, normalized_color, normalized_screw_option, screw_rule


def resolve_screw_configuration(anclaje, screw_option=None):
    normalized_anclaje = _normalize_anchorage_value(anclaje)
    normalized_screw_option = _normalize_screw_option_value(screw_option)
    screw_options = CONFIGURATOR_SCREW_OPTIONS.get(normalized_anclaje)
    screw_rule = screw_options.get(normalized_screw_option) if screw_options else None
    if not screw_rule or not screw_rule["enabled"]:
        return None
    return {
        "screw_option": normalized_screw_option,
        "screw_length_mm": screw_rule["length_mm"],
        "screw_supplement": screw_rule["supplement"],
    }


def format_screw_configuration(screw_length_mm, screw_supplement=0.0):
    if screw_length_mm is None:
        return None

    try:
        normalized_length = int(screw_length_mm)
        normalized_supplement = float(screw_supplement or 0.0)
    except (TypeError, ValueError):
        return None

    if normalized_supplement > 0:
        supplement = f"{normalized_supplement:.2f}".replace(".", ",")
        return f"{normalized_length} mm (+{supplement} €)"
    return f"{normalized_length} mm incluidos"


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

    if (
        alto < CONFIGURATOR_MIN_DIMENSION_CM
        or ancho < CONFIGURATOR_MIN_DIMENSION_CM
        or alto > CONFIGURATOR_MAX_DIMENSION_CM
        or ancho > CONFIGURATOR_MAX_DIMENSION_CM
        or alto + ancho > CONFIGURATOR_MAX_DIMENSION_SUM_CM
    ):
        raise ValueError("Dimensiones fuera de rango permitido")

    price_per_m2 = float(precio_m2)
    price_by_area = area * price_per_m2
    # Every grille is charged as at least one square metre at its own current rate.
    return round(max(price_by_area, price_per_m2), 2)


def build_configured_reja_quote(
    alto_cm,
    ancho_cm,
    precio_m2,
    anclaje,
    color,
    screw_option=None,
):
    base_unit_price = calcular_precio_reja(alto_cm, ancho_cm, precio_m2)
    (
        normalized_anclaje,
        normalized_color,
        normalized_screw_option,
        screw_rule,
    ) = validate_configurator_options(anclaje, color, screw_option)
    anchorage_supplement = CONFIGURATOR_ANCHORAGES[normalized_anclaje]["supplement"]
    screw_supplement = screw_rule["supplement"]

    return {
        "unit_price": round(base_unit_price + anchorage_supplement + screw_supplement, 2),
        "base_unit_price": base_unit_price,
        "anchorage_supplement": anchorage_supplement,
        "screw_supplement": screw_supplement,
        "anclaje": normalized_anclaje,
        "color": normalized_color,
        "screw_option": normalized_screw_option,
        "screw_length_mm": screw_rule["length_mm"],
    }


def calcular_precio_reja_configurada(
    alto_cm,
    ancho_cm,
    precio_m2,
    anclaje,
    color,
    screw_option=None,
):
    return build_configured_reja_quote(
        alto_cm=alto_cm,
        ancho_cm=ancho_cm,
        precio_m2=precio_m2,
        anclaje=anclaje,
        color=color,
        screw_option=screw_option,
    )["unit_price"]

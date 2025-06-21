from flask_mail import Mail, Message
from flask import current_app, jsonify, url_for

mail = Mail()

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


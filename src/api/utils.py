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


def generate_sitemap(app):
    links = ['/admin/']
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            if "/admin/" not in url:
                links.append(url)
    links_html = "".join(["<li><a href='" + link + "' target='_blank'>" + link + "</a></li>" for link in links])
    return """
        <div style="text-align: center;">
            <img style="max-height: 80px" src='https://storage.googleapis.com/breathecode/boilerplates/rigo-baby.jpeg' />
            <h1>Rigo welcomes you to your API!!</h1>
            <p>API HOST: <script>document.write('<input style="padding: 5px; width: 300px" type="text" value="'+window.location.href+'" />');</script></p>
            <p>Start working on your project by following the <a href="https://start.4geeksacademy.com/starters/full-stack" target="_blank">Quick Start</a></p>
            <p>Remember to specify a real endpoint path like: </p>
            <ul style="text-align: left;">
                """ + links_html + """
            </ul>
        </div>"""


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


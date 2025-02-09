from flask import Blueprint, request, jsonify, current_app
from flask_mail import Mail, Message
import os

email_bp = Blueprint('email_bp', __name__)

# Instancia global de Mail
mail = Mail()

# Configuración de Flask-Mail
def configure_mail(app):
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'tu_correo@example.com')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'tu_contraseña')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
    mail.init_app(app)

@email_bp.route('/contact', methods=['POST'])
def contact():
    try:
        data = request.get_json()

        # Validación de datos
        if not data or not all(key in data for key in ('name', 'firstname', 'phone', 'email', 'message')):
            return jsonify({"error": "Faltan datos obligatorios."}), 400

        # Preparar el correo
        message = Message(
            subject="Nuevo mensaje de contacto",
            sender=os.getenv('MAIL_DEFAULT_SENDER'),
            recipients=['admin@metalwolft.com'],
            body=(
                f"Nombre: {data['name']} {data['firstname']}\n"
                f"Teléfono: {data['phone']}\n"
                f"Correo: {data['email']}\n"
                f"Mensaje: {data['message']}"
            )
        )

        # Enviar el correo
        mail.send(message)
        return jsonify({"message": "Mensaje enviado correctamente."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

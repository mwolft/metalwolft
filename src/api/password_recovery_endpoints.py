from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, decode_token
from datetime import timedelta
from api.models import db, Users
from api.utils import send_email 
from api.credential_security import replace_password_if_version, token_credential_version, valid_new_password

auth_bp = Blueprint('auth_bp', __name__)


# Endpoint para recuperar contraseña
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({"error": "Correo electrónico requerido."}), 400

        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({"message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña."}), 200

        # Generar un token de recuperación
        reset_token = create_access_token(
            identity=email,
            additional_claims={"purpose": "password_reset", "credential_version": user.credential_version},
            expires_delta=timedelta(minutes=15),
        )

        # Crear el enlace de recuperación
        reset_link = f"{current_app.config['FRONTEND_URL']}/reset-password?token={reset_token}"

        # Enviar el correo
        subject = "Restablecer tu contraseña"
        body = f"Hola {user.firstname},\n\nHaz clic en el siguiente enlace para restablecer tu contraseña:\n{reset_link}\n\nEste enlace es válido por 15 minutos."
        send_email(subject, [email], body)

        return jsonify({"message": "Correo de recuperación enviado."}), 200

    except Exception as e:
        current_app.logger.exception("Error en forgot-password")
        return jsonify({"error": "Internal server error"}), 500

# Endpoint para restablecer contraseña
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password')

        if not token or not new_password:
            return jsonify({"error": "Token y nueva contraseña requeridos."}), 400
        if not valid_new_password(new_password):
            return jsonify({"error": "La contraseña debe tener entre 8 y 72 bytes UTF-8."}), 400

        # Verificar el token
        try:
            decoded_token = decode_token(token)
            if decoded_token.get("purpose") != "password_reset":
                return jsonify({"error": "Token inválido o expirado."}), 400
            email = decoded_token['sub']
            version = token_credential_version(decoded_token)
            if not isinstance(email, str) or version is None:
                return jsonify({"error": "Token inválido o expirado."}), 400
        except Exception:
            return jsonify({"error": "Token inválido o expirado."}), 400

        # Verificar que el usuario existe
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "Usuario no encontrado."}), 404
        if user.credential_version != version:
            return jsonify({"error": "Token inválido o expirado."}), 400

        if not replace_password_if_version(user, new_password, version):
            return jsonify({"error": "Token inválido o expirado."}), 400

        response = jsonify({"message": "Contraseña actualizada correctamente."})
        response.headers["Cache-Control"] = "no-store"
        return response, 200

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Error en reset-password")
        return jsonify({"error": "Internal server error"}), 500

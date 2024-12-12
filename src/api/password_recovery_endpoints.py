from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, decode_token
from datetime import timedelta
from api.models import db, Users
from api.utils import send_email 
import bcrypt

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/test-email', methods=['GET'])
def test_email():
    try:
        success = send_email(
            subject="Correo de prueba",
            recipients=["test@example.com"],
            body="Este es un correo de prueba enviado desde Flask-Mail."
        )
        if success:
            return jsonify({"message": "Correo enviado con éxito."}), 200
        else:
            return jsonify({"error": "No se pudo enviar el correo."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        reset_token = create_access_token(identity=email, expires_delta=timedelta(minutes=15))

        # Crear el enlace de recuperación
        reset_link = f"{current_app.config['FRONTEND_URL']}/reset-password?token={reset_token}"

        # Enviar el correo
        subject = "Restablecer tu contraseña"
        body = f"Hola {user.firstname},\n\nHaz clic en el siguiente enlace para restablecer tu contraseña:\n{reset_link}\n\nEste enlace es válido por 15 minutos."
        send_email(subject, [email], body)

        return jsonify({"message": "Correo de recuperación enviado."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para restablecer contraseña
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password')

        if not token or not new_password:
            return jsonify({"error": "Token y nueva contraseña requeridos."}), 400

        # Verificar el token
        try:
            decoded_token = decode_token(token)
            email = decoded_token['sub']
        except Exception:
            return jsonify({"error": "Token inválido o expirado."}), 400

        # Verificar que el usuario existe
        user = Users.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "Usuario no encontrado."}), 404

        # Actualizar la contraseña
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.password = hashed_password.decode('utf-8')
        db.session.commit()

        return jsonify({"message": "Contraseña actualizada correctamente."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

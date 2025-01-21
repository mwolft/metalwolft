from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from api.models import Users

def admin_required(fn):
    def wrapper(*args, **kwargs):
        try:
            # Verificar JWT
            verify_jwt_in_request()
            user_id = get_jwt_identity()

            # Validar si el usuario es administrador
            user = Users.query.get(user_id)
            if not user or not user.is_admin:
                return jsonify({"error": "Access denied. Admins only."}), 403

            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": str(e)}), 403

    wrapper.__name__ = fn.__name__
    return wrapper

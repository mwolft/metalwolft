from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request
from api.jwt_utils import get_current_user_context as get_jwt_identity

def admin_required(fn):
    def wrapper(*args, **kwargs):
        try:
            # Verificar JWT
            verify_jwt_in_request()
            current_user = get_jwt_identity()

            # Validar si el usuario es administrador
            if not current_user or not current_user.get("is_admin"):
                return jsonify({"error": "Access denied. Admins only."}), 403

            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": str(e)}), 403

    wrapper.__name__ = fn.__name__
    return wrapper

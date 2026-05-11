from flask import Blueprint, request, jsonify
from api.models import Users
from api.jwt_utils import create_user_access_token
from werkzeug.security import check_password_hash
from datetime import timedelta

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = Users.query.filter_by(email=email).first()

    if not user or not user.is_admin:
        return jsonify({"error": "Unauthorized. Admin access only."}), 403

    if not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials."}), 401

    access_token = create_user_access_token(user, expires_delta=timedelta(hours=24))
    return jsonify({"token": access_token}), 200

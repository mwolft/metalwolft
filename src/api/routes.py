"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from api.models import db, Users, Orders, OrderDetails
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
import json
import os
import requests

api = Blueprint('api', __name__)

@api.route('/hello', methods=['GET'])
def handle_hello():
    response_body = {}
    response_body['message'] = "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    return response_body, 200


@api.route("/login", methods=["POST"])
def login():
    response_body = {}
    data = request.json
    email = data.get("email", None)
    password = data.get("password", None)
    user = db.session.execute(db.select(Users).where(Users.email == email, Users.password == password)).scalar()
    if not user:
        response_body['message'] = 'Authorization denied'
        return response_body, 401
    access_token = create_access_token(identity={'email': user.email, 
                                                 'user_id': user.id,
                                                 "rol": user.rol})
    response_body['results'] = user.serialize()
    response_body['message'] = 'Bienvenido'
    response_body['access_token'] = access_token
    return response_body, 201


@api.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    response_body = {}
    current_user = get_jwt_identity()  
    if current_user:
        response_body['message'] = f'Access granted {current_user["email"]}'
        response_body['results'] = current_user
        return response_body, 200
    response_body['message'] = f'Access denied'
    response_body['results'] = {}
    return response_body, 403


@api.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required!"}), 400

    # Verifica si el usuario ya existe
    existing_user = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
    if existing_user:
        return jsonify({"message": "User already exists!"}), 409

    new_user = Users(
        email=email,
        password=password,
        rol='user',  # Asigna un rol predeterminado
        is_active=True  # Si tienes un campo 'is_active'
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User created successfully!"}), 201


@api.route('/users', methods=['GET'])
def handle_users():
    response_body = {}
    if request.method == 'GET':
        rows = db.session.execute(db.select(Users)).scalars()
        results = []
        for row in rows:
            results.append(row.serialize())
        response_body['results'] = results
        response_body['message'] = "Lista de usuarios"
        return response_body, 200


@api.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()  
def handle_user(user_id):
    response_body = {}
    current_user = get_jwt_identity()  
    if current_user['user_id'] != user_id:
        return jsonify({"message": "No autorizado para modificar este perfil"}), 403

    if request.method == 'GET':
        row = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not row:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        response_body['results'] = row.serialize()
        response_body['message'] = f'Datos del usuario {user_id} obtenidos correctamente'
        return response_body, 200

    if request.method == 'PUT':
        data = request.get_json()
        user = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not user:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        
        user.email = data.get('email', user.email)
        user.firstname = data.get('firstname', user.firstname)
        user.lastname = data.get('lastname', user.lastname)
        user.shipping_address = data.get('shipping_address', user.shipping_address)
        user.shipping_city = data.get('shipping_city', user.shipping_city)
        user.shipping_postal_code = data.get('shipping_postal_code', user.shipping_postal_code)
        user.billing_address = data.get('billing_address', user.billing_address)
        user.billing_city = data.get('billing_city', user.billing_city)
        user.billing_postal_code = data.get('billing_postal_code', user.billing_postal_code)
        user.CIF = data.get('CIF', user.CIF)
        
        db.session.commit()  
        response_body['results'] = user.serialize()
        response_body['message'] = f'Usuario {user_id} actualizado exitosamente'
        return response_body, 200

    if request.method == 'DELETE':
        user = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not user:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        db.session.delete(user)
        db.session.commit()
        response_body['message'] = f'Usuario {user_id} eliminado correctamente'
        return response_body, 200


@api.route('/orders', methods=['GET', 'POST'])
@jwt_required()
def handle_orders():
    response_body = {}
    current_user = get_jwt_identity()['user_id']
    
    if request.method == 'GET':
        orders = db.session.execute(db.select(Orders).where(Orders.user_id == current_user)).scalars()
        results = [order.serialize() for order in orders]
        response_body['results'] = results
        return response_body, 200
    
    if request.method == 'POST':
        data = request.get_json()
        new_order = Orders(user_id=current_user, total_amount=data['total_amount'])
        db.session.add(new_order)
        db.session.commit()
        response_body['message'] = 'Order created successfully.'
        response_body['order'] = new_order.serialize()
        return response_body, 201


@api.route('/orders/<int:order_id>', methods=['GET', 'DELETE'])
@jwt_required()
def handle_order(order_id):
    response_body = {}
    current_user = get_jwt_identity()['user_id']
    
    order = db.session.execute(db.select(Orders).where(Orders.id == order_id, Orders.user_id == current_user)).scalar()
    if not order:
        return jsonify({"message": "Order not found or not authorized"}), 404

    if request.method == 'GET':
        response_body['results'] = order.serialize()
        return response_body, 200

    if request.method == 'DELETE':
        db.session.delete(order)
        db.session.commit()
        response_body['message'] = 'Order deleted successfully.'
        return response_body, 200


@api.route('/orderdetails/<int:order_id>', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
def handle_order_details(order_id):
    response_body = {}
    current_user = get_jwt_identity()['user_id']
    
    # Verificar si el pedido pertenece al usuario
    order = db.session.execute(db.select(Orders).where(Orders.id == order_id, Orders.user_id == current_user)).scalar()
    if not order:
        return jsonify({"message": "Order not found or not authorized"}), 404

    if request.method == 'GET':
        # Obtener detalles del pedido
        order_details = db.session.execute(db.select(OrderDetails).where(OrderDetails.order_id == order_id)).scalars()
        results = [detail.serialize() for detail in order_details]
        response_body['results'] = results
        return response_body, 200

    if request.method == 'POST':
        # Agregar un detalle al pedido
        data = request.get_json()
        new_detail = OrderDetails(
            order_id=order_id,
            product_id=data['product_id'],  # Asegúrate de que el producto existe
            quantity=data['quantity'],
            price=data['price']
        )
        
        db.session.add(new_detail)
        db.session.commit()
        response_body['message'] = 'Order detail added successfully.'
        response_body['order_detail'] = new_detail.serialize()
        return response_body, 201

    if request.method == 'DELETE':
        # Eliminar un detalle del pedido
        detail_id = request.args.get('detail_id', type=int)
        detail = db.session.execute(db.select(OrderDetails).where(OrderDetails.id == detail_id, OrderDetails.order_id == order_id)).scalar()
        
        if not detail:
            return jsonify({"message": "Order detail not found"}), 404
        
        db.session.delete(detail)
        db.session.commit()
        response_body['message'] = 'Order detail deleted successfully.'
        return response_body, 200

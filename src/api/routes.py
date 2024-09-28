from flask import Flask, request, jsonify, url_for, Blueprint
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from api.models import db, Users, Products, Orders, OrderDetails 
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
                                                 "is_admin": user.is_admin})
    response_body['results'] = user.serialize()
    response_body['message'] = 'Bienvenido'
    response_body['access_token'] = access_token
    return response_body, 201

@api.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    shipping_address = data.get('shipping_address')
    shipping_city = data.get('shipping_city')
    shipping_postal_code = data.get('shipping_postal_code')
    billing_address = data.get('billing_address')
    billing_city = data.get('billing_city')
    billing_postal_code = data.get('billing_postal_code')
    CIF = data.get('CIF')

    if not email or not password:
        return jsonify({"message": "Email and password are required!"}), 400

    new_user = Users(
        email=email,
        password=password,
        firstname=firstname,
        lastname=lastname,
        is_admin=False,  # Asigna is_admin como False por defecto
        shipping_address=shipping_address,
        shipping_city=shipping_city,
        shipping_postal_code=shipping_postal_code,
        billing_address=billing_address,
        billing_city=billing_city,
        billing_postal_code=billing_postal_code,
        CIF=CIF
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.serialize()), 201

@api.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    users = Users.query.all()
    return jsonify([user.serialize() for user in users]), 200

@api.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    data = request.json
    new_user = Users(
        email=data.get('email'),
        password=data.get('password'),
        firstname=data.get('firstname'),
        lastname=data.get('lastname'),
        is_admin=data.get('is_admin', False)
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.serialize()), 201

@api.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify(user.serialize()), 200

@api.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found!"}), 404

    data = request.json
    user.firstname = data.get('firstname', user.firstname)
    user.lastname = data.get('lastname', user.lastname)
    user.email = data.get('email', user.email)
    user.is_admin = data.get('is_admin', user.is_admin)

    db.session.commit()
    return jsonify(user.serialize()), 200

@api.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found!"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted!"}), 200

@api.route('/products', methods=['POST'])
@jwt_required()
def add_product():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    data = request.get_json()
    new_product = Products(
        nombre=data['nombre'],
        descripcion=data['descripcion'],
        precio=data['precio'],
        categoria_id=data['categoria_id'],
        imagen=data.get('imagen', None),
        stock=data['stock'],
        alto=data['alto'],
        ancho=data['ancho'],
        anclaje=data['anclaje'],
        color=data['color']
    )
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"message": "Product created successfully.", "product": new_product.serialize()}), 201

# Mantén las rutas existentes para pedidos y detalles de pedidos, como en tu archivo original
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
    

@api.route('/orderdetails', methods=['POST'])
@jwt_required()
def add_order_detail():
    data = request.get_json()
    new_order_detail = OrderDetails(
        order_id=data['order_id'],
        product_id=data['product_id'],
        quantity=data['quantity'],
        alto=data['alto'],
        ancho=data['ancho'],
        anclaje=data['anclaje'],
        color=data['color']
    )
    db.session.add(new_order_detail)
    db.session.commit()

    return jsonify({"message": "Order detail added successfully.", "order_detail": new_order_detail.serialize()}), 201


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

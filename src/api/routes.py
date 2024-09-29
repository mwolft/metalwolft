from flask import Flask, request, jsonify, Blueprint
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from api.models import db, Users, Products, Orders, OrderDetails
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Definir el blueprint
api = Blueprint('api', __name__)
CORS(api, resources={r"/*": {"origins": "*"}})  # Aplicar CORS al blueprint

@api.route('/hello', methods=['GET'])
def handle_hello():
    return jsonify({"message": "Hello! I'm a message from the backend"}), 200

@api.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    user = db.session.execute(db.select(Users).where(Users.email == email, Users.password == password)).scalar()
    if not user:
        return jsonify({'message': 'Authorization denied'}), 401

    access_token = create_access_token(identity={'email': user.email, 'user_id': user.id, 'is_admin': user.is_admin})
    response = {
        'results': user.serialize(),
        'message': 'Bienvenido',
        'access_token': access_token
    }
    return jsonify(response), 201

@api.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required!"}), 400

    new_user = Users(
        email=data.get('email'),
        password=data.get('password'),
        firstname=data.get('firstname'),
        lastname=data.get('lastname'),
        is_admin=False,
        shipping_address=data.get('shipping_address'),
        shipping_city=data.get('shipping_city'),
        shipping_postal_code=data.get('shipping_postal_code'),
        billing_address=data.get('billing_address'),
        billing_city=data.get('billing_city'),
        billing_postal_code=data.get('billing_postal_code'),
        CIF=data.get('CIF')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.serialize()), 201

# Obtener todos los usuarios (GET)
@api.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    users = Users.query.all()
    total_count = len(users)

    response = jsonify([user.serialize() for user in users])
    response.headers['X-Total-Count'] = total_count
    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200

# Crear un usuario (POST)
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

# Obtener un usuario específico (GET)
@api.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    user = Users.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    response = jsonify(user.serialize())
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200

# Actualizar un usuario específico (PUT)
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
    response = jsonify(user.serialize())
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200

# Eliminar un usuario específico (DELETE)
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
    response = jsonify({"message": "User deleted!"})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200

# Obtener todos los productos (GET)
@api.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    products = Products.query.all()
    total_count = len(products)

    response = jsonify([product.serialize() for product in products])
    response.headers['X-Total-Count'] = total_count
    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200

# Crear un producto (POST)
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

    response = jsonify({"message": "Product created successfully.", "product": new_product.serialize()})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 201

# Obtener, actualizar o eliminar un producto específico
@api.route('/products/<int:product_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def handle_product(product_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    product = Products.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    if request.method == 'GET':
        response = jsonify(product.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200

    if request.method == 'PUT':
        data = request.json
        product.nombre = data.get('nombre', product.nombre)
        product.descripcion = data.get('descripcion', product.descripcion)
        product.precio = data.get('precio', product.precio)
        product.categoria_id = data.get('categoria_id', product.categoria_id)
        product.imagen = data.get('imagen', product.imagen)
        product.stock = data.get('stock', product.stock)
        product.alto = data.get('alto', product.alto)
        product.ancho = data.get('ancho', product.ancho)
        product.anclaje = data.get('anclaje', product.anclaje)
        product.color = data.get('color', product.color)

        db.session.commit()
        response = jsonify(product.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200

    if request.method == 'DELETE':
        db.session.delete(product)
        db.session.commit()
        response = jsonify({"message": "Product deleted successfully."})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200

# Obtener todos los pedidos (GET)
@api.route('/orders', methods=['GET', 'POST'])
@jwt_required()
def handle_orders():
    current_user = get_jwt_identity()
    
    if request.method == 'GET':
        orders = db.session.execute(db.select(Orders).where(Orders.user_id == current_user['user_id'])).scalars()
        results = [order.serialize() for order in orders]
        total_count = len(results)

        response = jsonify(results)
        response.headers['X-Total-Count'] = total_count
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200
    
    if request.method == 'POST':
        data = request.get_json()
        new_order = Orders(user_id=current_user['user_id'], total_amount=data['total_amount'])
        db.session.add(new_order)
        db.session.commit()

        response = jsonify({
            'message': 'Order created successfully.',
            'order': new_order.serialize()
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 201

# Obtener, actualizar o eliminar un pedido específico
@api.route('/orders/<int:order_id>', methods=['GET', 'DELETE'])
@jwt_required()
def handle_order(order_id):
    current_user = get_jwt_identity()

    order = db.session.execute(db.select(Orders).where(Orders.id == order_id, Orders.user_id == current_user['user_id'])).scalar()
    if not order:
        return jsonify({"message": "Order not found or not authorized"}), 404

    if request.method == 'GET':
        response = jsonify(order.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200

    if request.method == 'DELETE':
        db.session.delete(order)
        db.session.commit()
        response = jsonify({"message": "Order deleted successfully."})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200

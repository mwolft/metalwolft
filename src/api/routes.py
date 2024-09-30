from flask import Flask, request, jsonify, Blueprint
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from api.models import db, Users, Products, ProductImages, Categories, Orders, OrderDetails, Favorites
from sqlalchemy.exc import SQLAlchemyError


api = Blueprint('api', __name__)
CORS(api, resources={r"/*": {"origins": "*"}})  


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

    response = jsonify(user.serialize())
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200


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


@api.route('/categories', methods=['GET'])
def get_categories():
    categories = Categories.query.all()
    total_count = len(categories)

    response = jsonify([category.serialize() for category in categories])
    response.headers['X-Total-Count'] = total_count
    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
    return response, 200


# Rutas para manejar productos
@api.route('/products', methods=['GET', 'POST'])
@jwt_required()
def handle_products():
    current_user = get_jwt_identity()

    if request.method == 'GET':
        # Obtener todos los productos
        products = Products.query.all()
        total_count = len(products)
        response = jsonify([product.serialize_with_images() for product in products])
        response.headers['X-Total-Count'] = str(total_count)
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count, Authorization'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200

    elif request.method == 'POST':
        # Solo los administradores pueden crear productos
        if not current_user.get("is_admin"):
            return jsonify({"message": "Access forbidden: Admins only"}), 403

        data = request.json
        try:
            # Crear el nuevo producto
            new_product = Products(
                nombre=data.get('nombre'),
                descripcion=data.get('descripcion'),
                precio=data.get('precio'),
                categoria_id=data.get('categoria_id'),
                imagen=data.get('imagen')
            )
            db.session.add(new_product)
            db.session.flush()  # Para obtener el ID del producto antes de confirmar

            # Agregar imágenes adicionales si se proporcionan
            images_urls = data.get('images', [])
            for image_url in images_urls:
                new_image = ProductImages(product_id=new_product.id, image_url=image_url)
                db.session.add(new_image)

            db.session.commit()
            response = jsonify(new_product.serialize_with_images())
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 201

        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred while creating the product.", "error": str(e)}), 500

# Rutas para manejar un producto específico
@api.route('/products/<int:product_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def handle_product(product_id):
    current_user = get_jwt_identity()
    product = Products.query.get(product_id)

    if not product:
        return jsonify({"message": "Product not found"}), 404

    if request.method == 'GET':
        response = jsonify(product.serialize_with_images())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200

    elif request.method == 'PUT':
        # Solo los administradores pueden actualizar productos
        if not current_user.get("is_admin"):
            return jsonify({"message": "Access forbidden: Admins only"}), 403

        data = request.json
        try:
            # Actualizar los detalles del producto
            product.nombre = data.get('nombre', product.nombre)
            product.descripcion = data.get('descripcion', product.descripcion)
            product.precio = data.get('precio', product.precio)
            product.categoria_id = data.get('categoria_id', product.categoria_id)
            product.imagen = data.get('imagen', product.imagen)

            # Actualizar las imágenes adicionales si se proporcionan
            if 'images' in data:
                images_urls = data.get('images', [])
                # Borrar imágenes anteriores
                ProductImages.query.filter_by(product_id=product_id).delete()
                # Añadir nuevas imágenes
                for image_url in images_urls:
                    new_image = ProductImages(product_id=product_id, image_url=image_url)
                    db.session.add(new_image)

            db.session.commit()
            response = jsonify(product.serialize_with_images())
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 200

        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred while updating the product.", "error": str(e)}), 500

    elif request.method == 'DELETE':
        # Solo los administradores pueden eliminar productos
        if not current_user.get("is_admin"):
            return jsonify({"message": "Access forbidden: Admins only"}), 403

        try:
            db.session.delete(product)
            db.session.commit()
            response = jsonify({"message": "Product deleted successfully."})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 200

        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred while deleting the product.", "error": str(e)}), 500

# Ruta para agregar imágenes adicionales a un producto específico
@api.route('/products/<int:product_id>/images', methods=['POST'])
@jwt_required()
def add_product_images(product_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    product = Products.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    data = request.get_json()
    image_urls = data.get('images', [])
    if not isinstance(image_urls, list) or not all(isinstance(url, str) for url in image_urls):
        return jsonify({"message": "Invalid images format. Expected a list of URLs."}), 400

    try:
        for image_url in image_urls:
            new_image = ProductImages(product_id=product_id, image_url=image_url)
            db.session.add(new_image)

        db.session.commit()
        response = jsonify({"message": "Images added successfully.", "product": product.serialize_with_images()})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while adding images.", "error": str(e)}), 500


@api.route('/product_images', methods=['GET'])
@jwt_required()
def get_product_images():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    # Obtener todas las imágenes de productos
    product_images = ProductImages.query.all()
    total_count = len(product_images)

    # Preparar la respuesta con las imágenes serializadas
    response = jsonify([image.serialize() for image in product_images])
    response.headers['X-Total-Count'] = total_count
    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count, Authorization'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200


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


@api.route('/orderdetails', methods=['POST'])
@jwt_required()
def add_order_detail():
    data = request.get_json()
    new_order_detail = OrderDetails(
        order_id=data['order_id'],
        product_id=data['product_id'],
        quantity=data['quantity'],
        alto=data.get('alto'),  # Opcional
        ancho=data.get('ancho'),  # Opcional
        anclaje=data.get('anclaje'),  # Opcional
        color=data.get('color')  # Opcional
    )
    db.session.add(new_order_detail)
    db.session.commit()

    return jsonify({"message": "Order detail added successfully.", "order_detail": new_order_detail.serialize()}), 201

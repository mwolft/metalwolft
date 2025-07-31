from flask import request, jsonify, Blueprint, send_file, send_from_directory, current_app, redirect, abort, Response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from api.models import db, Users, Products, ProductImages, Categories, Subcategories, Orders, OrderDetails, Favorites, Cart, Posts, Comments, Invoices
from api.utils import send_email, calcular_precio_reja
from sqlalchemy.exc import SQLAlchemyError
import bcrypt
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph, Frame
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from sqlalchemy import func
from flask_mail import Message
from dotenv import load_dotenv
from api.exceptions import APIException
from api.utils import mail
from sqlalchemy.exc import IntegrityError
import logging


logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

load_dotenv()



redirect_map = {
    "/rejas/rejas-para-ventanas-pittsburgh": "/rejas-para-ventanas",
    "/rejas/rejas-para-ventanas-livingston": "/rejas-para-ventanas",
    "/rejas/rejas-para-ventanas-delhi": "/rejas-para-ventanas",
    "/rejas/rejas-para-ventanas-lancaster": "/rejas-para-ventanas",
    "/puertas-correderas/puerta-corredera-perth": "/puertas-correderas-metalicas",
    "/puertas-correderas/puerta-corredera-adelaida": "/puertas-correderas-metalicas",
    "/puertas-correderas/puerta-corredera-canberra": "/puertas-correderas-metalicas",
    "/puertas-correderas-interiores": "/puertas-correderas-metalicas",
    "/puertas-correderas-exteriores": "/puertas-correderas-metalicas",
    "/puertas-peatonales": "/puertas-peatonales-metalicas",
    "/vallados-metalicos-exteriores": "/vallados-metalicos",
    "/vallados-metalicos/vallado-metalico-geelong": "/vallados-metalicos",
    "/vallados-metalicos": "/vallados-metalicos",
    "/preguntas-frecuentes": "/faq",
}

gone_list = [
    "/blog/instalation-rejas-para-ventanas",
    "/index.php",
    "/blog/medir_hueco_rejas_para_ventanas.php",
    "/blog/medir-hueco-rejas-para-ventanas.php",
    "/blog/instalation-rejas-para-ventanas.php",
    "/rejas-para-ventanas.php",
    "/blog/blog-metal-wolft.php",
    "/",
    "/vallados-metalicos",
    "/puertas-correderas/puerta-corredera-adelaida",
    "/puertas-correderas/puerta-corredera-canberra",
    "/rejas/rejas-para-ventanas-delhi",
    "/rejas/rejas-para-ventanas-lancaster",
    "/puertas-peatonales",
    "/preguntas-frecuentes",
    "/vallados-metalicos/vallado-metalico-geelong",
]


@api.before_request
def handle_legacy_urls():
    if request.path in redirect_map:
        return redirect(redirect_map[request.path], code=301)
    if request.path in gone_list:
        return "Página obsoleta", 410


@api.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    try:
        import stripe 
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY') 

        data = request.get_json()

        import uuid  

        idempotency_key = data.get('idempotency_key')
        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())

        payment_intent_id = data.get('payment_intent_id')

        if payment_intent_id:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent['status'] == 'succeeded':
                return jsonify({"message": "El pago ya ha sido completado.", "paymentIntent": intent}), 200

        intent = stripe.PaymentIntent.create(
            amount=data['amount'], 
            currency='eur',
            payment_method=data['payment_method_id'],
            confirm=True,
            return_url=os.getenv('STRIPE_RETURN_URL'),
            idempotency_key=idempotency_key
        )

        return jsonify({
            'clientSecret': intent['client_secret'],
            'paymentIntent': intent
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 403


@api.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    try:
        comments = Comments.query.filter_by(post_id=post_id).all()
        if not comments:
            response = jsonify([])
        else:
            response = jsonify([comment.serialize() for comment in comments])
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except Exception as e:
        return jsonify({"message": "Error al obtener los comentarios", "error": str(e)}), 500


@api.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    try:
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({"message": "Autenticación requerida"}), 401

        user_id = current_user['user_id']  # Extraer el user_id del token

        data = request.get_json()
        if not data or not data.get("content"):
            return jsonify({"msg": "El contenido es requerido"}), 422

        new_comment = Comments(
            content=data["content"],
            post_id=post_id,
            user_id=user_id  
        )
        db.session.add(new_comment)
        db.session.commit()
        response = jsonify(new_comment.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error al agregar el comentario", "error": str(e)}), 500


@api.route('/posts', methods=['GET'])
@jwt_required(optional=True)
def get_posts():
    try:
        posts = Posts.query.all()
        total_count = len(posts)

        response = jsonify([post.serialize() for post in posts])
        response.headers['X-Total-Count'] = total_count
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count, Authorization'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200
    except Exception as e:
        return jsonify({"message": "Error al obtener los posts", "error": str(e)}), 500


@api.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required(optional=True)
def get_post(post_id):
    try:
        post = Posts.query.get(post_id)
        if post:
            response = jsonify(post.serialize())
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 200
        return jsonify({"message": "Post no encontrado"}), 404
    except Exception as e:
        return jsonify({"message": "Error al obtener el post", "error": str(e)}), 500


@api.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    try:
        current_user = get_jwt_identity()
        if not current_user.get("is_admin"):
            return jsonify({"message": "Acceso prohibido: Solo administradores"}), 403

        data = request.json
        new_post = Posts(
            title=data.get('title'),
            content=data.get('content'),
            author_id=current_user.get('id'),
            image_url=data.get('image_url')
        )
        db.session.add(new_post)
        db.session.commit()
        response = jsonify(new_post.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "Error al crear el post", "error": str(e)}), 500


@api.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    try:
        current_user = get_jwt_identity()
        if not current_user.get("is_admin"):
            return jsonify({"message": "Acceso prohibido: Solo administradores"}), 403

        post = Posts.query.get(post_id)
        if not post:
            return jsonify({"message": "Post no encontrado"}), 404

        data = request.json
        post.title = data.get('title', post.title)
        post.content = data.get('content', post.content)
        post.image_url = data.get('image_url', post.image_url)
        post.updated_at = datetime.utcnow()

        db.session.commit()
        response = jsonify(post.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "Error al actualizar el post", "error": str(e)}), 500


@api.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    try:
        current_user = get_jwt_identity()
        if not current_user.get("is_admin"):
            return jsonify({"message": "Acceso prohibido: Solo administradores"}), 403

        post = Posts.query.get(post_id)
        if not post:
            return jsonify({"message": "Post no encontrado"}), 404

        db.session.delete(post)
        db.session.commit()
        response = jsonify({"message": "Post eliminado"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "Error al eliminar el post", "error": str(e)}), 500


@api.route("/login", methods=["OPTIONS", "POST"])
def login():
    if request.method == "OPTIONS":
        # Manejar el preflight de CORS
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200

    # Lógica de inicio de sesión
    data = request.json
    email = data.get("email", None)
    password = data.get("password", None)
    user = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        response_body = {'message': 'Correo o contraseña incorrectos'}
        response = jsonify(response_body)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 401

    # Crear el token JWT con los datos del usuario
    access_token = create_access_token(identity={
        'user_id': user.id,
        'email': user.email,
        'is_admin': user.is_admin
    })

    response_body = {
        'results': user.serialize(),
        'message': 'Bienvenido',
        'access_token': access_token
    }
    response = jsonify(response_body)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, 200  


@api.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    response_body = {}
    current_user = get_jwt_identity()
    if current_user and current_user["rol"] == "admin":
        response_body['message'] = f'Access granted {current_user["email"]}'
        response_body['results'] = current_user
        return response_body, 200

    response_body['message'] = f'Acceso denegado'
    response_body['results'] = {}
    return response_body, 403


@api.route("/signup", methods=["OPTIONS", "POST"])
def signup():
    if request.method == "OPTIONS":
        # Manejar el preflight de CORS
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200

    # Lógica de registro de usuario
    data = request.json
    email = data.get("email", None)
    password = data.get("password", None)
    rol = data.get("rol", "user")
    # Verificar si el usuario ya existe
    existing_user = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
    if existing_user:
        response_body = {'message': 'Ya existe un usuario registrado con este correo'}
        response = jsonify(response_body)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 409
    # Encriptar la contraseña
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # Crear nuevo usuario
    user = Users()
    user.email = email
    user.password = hashed_password.decode('utf-8')
    user.is_admin = True if rol == "admin" else False
    # Guardar en la base de datos
    db.session.add(user)
    db.session.commit()
    # Crear el token JWT
    access_token = create_access_token(identity={
        'user_id': user.id,
        'email': user.email,
        'is_admin': user.is_admin
    })
    response_body = {
        'results': user.serialize(),
        'message': 'Usuario registrado',
        'access_token': access_token
    }
    response = jsonify(response_body)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, 201


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

    # Permitir que el usuario actualice su propio perfil o que el administrador actualice cualquier perfil
    if current_user["id"] != user_id and not current_user.get("is_admin"):
        response = jsonify({"message": "Access forbidden: Only admins or the user themselves can update the profile"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 403

    user = Users.query.get(user_id)
    if not user:
        response = jsonify({"message": "User not found!"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 404
    data = request.json
    user.firstname = data.get('firstname', user.firstname)
    user.lastname = data.get('lastname', user.lastname)
    user.email = data.get('email', user.email)
    # Solo un administrador puede cambiar el rol de administrador
    if current_user.get("is_admin"):
        user.is_admin = data.get('is_admin', user.is_admin)
    try:
        db.session.commit()
        response = jsonify(user.serialize())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'PUT, OPTIONS'
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
        return response, 200
    except Exception as e:
        db.session.rollback()
        response = jsonify({"message": "An error occurred", "error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@api.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        response = jsonify({"message": "Access forbidden: Admins only"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 403
    user = Users.query.get(user_id)
    if not user:
        response = jsonify({"message": "User not found!"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 404
    db.session.delete(user)
    db.session.commit()
    response = jsonify({"message": "User deleted!"})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200


@api.route('/categories', methods=['GET'])
def get_all_categories():
    try:
        categories = Categories.query.all()
        response_data = []
        for category in categories:
            product_count = Products.query.filter(Products.categoria_id == category.id).count()
            subcategories = Subcategories.query.filter_by(categoria_id=category.id).all()
            subcategories_data = []
            for subcat in subcategories:
                subcat_product_count = Products.query.filter(Products.subcategoria_id == subcat.id).count()
                subcategories_data.append({
                    **subcat.serialize(),
                    "product_count": subcat_product_count
                })
            response_data.append({
                **category.serialize(),
                "product_count": product_count,
                "subcategories": subcategories_data
            })
        response = jsonify(response_data)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        response = jsonify({"message": "Error retrieving categories", "error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@api.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        response = jsonify({"message": "Acceso prohibido: Solo administradores"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 403

    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    parent_id = data.get('parent_id')

    if not nombre:
        response = jsonify({"message": "El nombre de la categoría es obligatorio"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 400

    new_category = Categories(nombre=nombre, descripcion=descripcion, parent_id=parent_id)
    db.session.add(new_category)
    db.session.commit()

    response = jsonify(new_category.serialize())
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Expose-Headers'] = 'Authorization'
    return response, 201


@api.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        response = jsonify({"message": "Acceso prohibido: Solo administradores"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 403

    category = Categories.query.get(category_id)
    if not category:
        response = jsonify({"message": "Categoría no encontrada"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 404

    data = request.get_json()
    category.nombre = data.get('nombre', category.nombre)
    category.descripcion = data.get('descripcion', category.descripcion)
    category.parent_id = data.get('parent_id', category.parent_id)

    db.session.commit()

    response = jsonify(category.serialize())
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Expose-Headers'] = 'Authorization'
    return response, 200


@api.route('/categories/<int:category_id>/subcategories', methods=['GET'])
def get_subcategories(category_id):
    try:
        subcategories = Categories.query.filter_by(parent_id=category_id).all()
        print("Subcategories fetched from database:", subcategories)
        response = jsonify([subcategory.serialize() for subcategory in subcategories])
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        response = jsonify({"message": "Error retrieving subcategories", "error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 500


@api.route("/category/<string:slug>/products", methods=["GET"])
def get_products_by_category(slug):
    category = Categories.query.filter_by(slug=slug).first()
    if not category:
        return jsonify({"message": "Categoría no encontrada"}), 404

    products = Products.query.filter_by(categoria_id=category.id).all()
    return jsonify([p.serialize() for p in products]), 200


@api.route('/products', methods=['GET'])
def get_products():
    category_id = request.args.get('category_id', type=int)
    subcategory_id = request.args.get('subcategory_id', type=int)
    try:
        query = Products.query
        if subcategory_id:
            query = query.filter(Products.subcategoria_id == subcategory_id)
        elif category_id:
            subcategory_ids = [sub.id for sub in Subcategories.query.filter_by(categoria_id=category_id).all()]
            ids_to_filter = [category_id] + subcategory_ids
            query = query.filter(
                (Products.categoria_id == category_id) |
                (Products.subcategoria_id.in_(subcategory_ids))
            )

        total_count = query.count()
        
        products = query.all()
        response = jsonify([product.serialize_with_images() for product in products])
        
        response.headers['X-Total-Count'] = total_count
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count, Authorization'
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        return response, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        response = jsonify({"message": "Error retrieving products", "error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500


@api.route('/products', methods=['POST'])
def create_product():
    data = request.form  
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    precio = data.get('precio')
    imagen = data.get('imagen')
    categoria_id = data.get('categoria_id')
    subcategoria_id = data.get('subcategoria_id')
    subcategoria = Subcategories.query.get(subcategoria_id)
    if not subcategoria:
        return jsonify({"message": "La subcategoría especificada no existe"}), 400
    categoria_id = subcategoria.categoria_id
    new_product = Products(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        imagen=imagen,
        categoria_id=categoria_id,
        subcategoria_id=subcategoria_id
    )
    try:
        db.session.add(new_product)
        db.session.commit()
        return jsonify(new_product.serialize_with_images()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "Error al crear el producto", "error": str(e)}), 500


@api.route('/<string:category_slug>/<string:product_slug>', methods=['GET'])
def get_product_by_category_and_slug(category_slug, product_slug):
    try:
        category = Categories.query.filter_by(slug=category_slug).first()
        if not category:
            return jsonify({"message": "Category not found"}), 404
        product = Products.query.filter_by(slug=product_slug, categoria_id=category.id).first()

        if not product:
            return jsonify({"message": "Product not found in this category"}), 404
        response = jsonify(product.serialize_with_images())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    except Exception as e:
        logger.error(f"Error al obtener el producto por categoría y slug: {str(e)}")
    return jsonify({"message": "Error fetching product", "error": str(e)}), 500


@api.route('/products/<int:product_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_product(product_id):
    product = Products.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    if request.method == 'GET':
        response = jsonify(product.serialize_with_images())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 200
    current_user = get_jwt_identity()
    if request.method == 'PUT':
        if not current_user or not current_user.get("is_admin"):
            return jsonify({"message": "Access forbidden: Admins only"}), 403
        data = request.json
        try:
            product.nombre = data.get('nombre', product.nombre)
            product.descripcion = data.get('descripcion', product.descripcion)
            product.precio = data.get('precio', product.precio)
            product.categoria_id = data.get('categoria_id', product.categoria_id)
            product.imagen = data.get('imagen', product.imagen)
            if 'images' in data:
                images_urls = data.get('images', [])
                ProductImages.query.filter_by(product_id=product_id).delete()
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
        if not current_user or not current_user.get("is_admin"):
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
    product_images = ProductImages.query.all()
    total_count = len(product_images)
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
        try:
            # Si el usuario es administrador, devolver todas las órdenes
            if current_user.get("is_admin"):
                orders = db.session.execute(db.select(Orders)).scalars()
            else:
                # Si no, devolver solo las órdenes del usuario autenticado
                orders = db.session.execute(
                    db.select(Orders).where(Orders.user_id == current_user['user_id'])
                ).scalars()
            
            results = [order.serialize() for order in orders]
            total_count = len(results)
            
            # Crear respuesta con encabezados requeridos por React Admin
            response = jsonify(results)
            response.headers['X-Total-Count'] = str(total_count)
            response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 200
        except Exception as e:
            logger.error(f"Error al obtener las órdenes: {str(e)}")
            return jsonify({"message": "Error fetching orders", "error": str(e)}), 500 

    if request.method == 'POST':
        data = request.get_json()
        logger.info(f"Datos recibidos para crear la orden: {data}")
        try:
            # Crear la orden inicialmente sin total_amount definitivo
            new_order = Orders(
                user_id=current_user['user_id'],
                total_amount=0,  # Temporalmente 0, lo recalcularemos
                locator=Orders.generate_locator(),
                order_status="pendiente"
            )
            db.session.add(new_order)
            db.session.flush()  # Nos da el id de la orden

            # Crear los detalles de la orden y calcular subtotal
            order_details = data.get('products', [])
            subtotal = 0
            for detail in order_details:
                existing_detail = OrderDetails.query.filter_by(
                    order_id=new_order.id,
                    product_id=detail['producto_id'],
                    alto=detail.get('alto'),
                    ancho=detail.get('ancho'),
                    anclaje=detail.get('anclaje'),
                    color=detail.get('color')
                ).first()

                if existing_detail:
                    logger.info(f"Detalle ya existente: {existing_detail.serialize()}")
                    continue 

                # Obtener producto y calcular precio exacto según dimensiones
                prod = Products.query.get(detail['producto_id'])
                if not prod:
                    raise ValueError(f"Producto con ID {detail['producto_id']} no encontrado")

                precio_recalculado = calcular_precio_reja(
                    alto_cm=detail.get('alto'),
                    ancho_cm=detail.get('ancho'),
                    precio_m2=prod.precio_rebajado or prod.precio
                )

                new_detail = OrderDetails(
                    order_id=new_order.id,
                    product_id=detail['producto_id'],
                    quantity=detail['quantity'],
                    alto=detail.get('alto'),
                    ancho=detail.get('ancho'),
                    anclaje=detail.get('anclaje'),
                    color=detail.get('color'),
                    precio_total=precio_recalculado,
                    firstname=data.get('firstname'),
                    lastname=data.get('lastname'),
                    shipping_address=data.get('shipping_address'),
                    shipping_city=data.get('shipping_city'),
                    shipping_postal_code=data.get('shipping_postal_code'),
                    billing_address=data.get('billing_address'),
                    billing_city=data.get('billing_city'),
                    billing_postal_code=data.get('billing_postal_code'),
                    CIF=data.get('CIF'),
                    shipping_type=detail.get('shipping_type'),
                    shipping_cost=detail.get('shipping_cost')
                )

                db.session.add(new_detail)
                subtotal += precio_recalculado


            # Usar el coste de envío más alto entre los productos recibidos
            shipping_cost = max(
                float(detail.get('shipping_cost', 0)) for detail in order_details
            )

            # Total final de la orden
            total_final = subtotal + shipping_cost
            new_order.shipping_cost = shipping_cost
            new_order.total_amount = total_final

            db.session.commit()

            # Generar la factura
            try:
                invoice_number = Invoices.generate_next_invoice_number()
                pdf_filename = f"invoice_{invoice_number}.pdf"
                file_path = os.path.join(current_app.config['INVOICE_FOLDER'], pdf_filename)
                pdf_path = f"/api/download-invoice/{pdf_filename}"
                os.makedirs(current_app.config['INVOICE_FOLDER'], exist_ok=True)

                pdf_buffer = BytesIO()
                pdf = canvas.Canvas(pdf_buffer, pagesize=A4)

                # Agregar logo
                image_url = "https://res.cloudinary.com/dewanllxn/image/upload/v1740167674/logo_uxlqof.png"
                pdf.drawImage(image_url, 300, 750, width=250, height=64)

                # Información de la factura
                pdf.setTitle(f"Factura_{invoice_number}")
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, 800, f"Factura No: {invoice_number}")

                pdf.setFont("Helvetica", 10)
                fecha_emision = datetime.now().strftime("%d/%m/%Y")
                pdf.drawString(50, 780, f"Fecha: {fecha_emision}")

                # Información del proveedor
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(400, 700, "PROVEEDOR")
                pdf.setFont("Helvetica", 10)
                pdf.drawString(400, 680, "Sergio Arias Fernández")
                pdf.drawString(400, 665, "05703874N")
                pdf.drawString(400, 650, "Francisco Fernández Ordoñez 32")
                pdf.drawString(400, 635, "13170 Miguelturra")
                pdf.drawString(400, 620, "634112604")

                # Información del cliente
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, 700, "CLIENTE")
                pdf.setFont("Helvetica", 10)
                pdf.drawString(50, 680, f"{data.get('firstname')} {data.get('lastname')}")
                pdf.drawString(50, 665, f"{data.get('billing_address')}, {data.get('billing_city')} ({data.get('billing_postal_code')})")
                pdf.drawString(50, 650, f"{data.get('CIF')}")
                pdf.drawString(50, 635, f"{data.get('phone', 'No proporcionado')}")

                # Dirección de envío
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, 580, "Dirección de Envío")
                pdf.setFont("Helvetica", 10)

                # Verificar si la dirección de envío es igual a la de facturación o está vacía
                if not data.get('shipping_address') or data.get('shipping_address') == data.get('billing_address'):
                    pdf.drawString(50, 560, "La misma que la de facturación")
                else:
                    pdf.drawString(50, 560, f"{data.get('shipping_address')}, {data.get('shipping_city')} ({data.get('shipping_postal_code')})")

                # Detalles del pedido
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, 510, "Detalles del Pedido")
                pdf.setFont("Helvetica", 10)
                data_table = [["Producto", "Alto", "Ancho", "Anclaje", "Color", "Precio"]]
                for detail in order_details:
                    prod = Products.query.get(detail['producto_id'])
                    row = [
                        prod.nombre if prod else "Producto desconocido",
                        f"{detail['alto']} cm",
                        f"{detail['ancho']} cm",
                        detail['anclaje'],
                        detail['color'],
                        f"{float(detail['precio_total']):.2f} €"
                    ]
                    data_table.append(row)


                # Crear la tabla
                table = Table(data_table, colWidths=[4*cm, 2*cm, 2*cm, 5*cm, 2*cm, 2*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.Color(1, 0.196, 0.302)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                y_position = 480
                table.wrapOn(pdf, 50, y_position)
                table_height = table._height
                table.drawOn(pdf, 50, y_position - table_height)

                totals_y_position = y_position - table_height - 30
                if (totals_y_position < 50):
                    pdf.showPage()
                    totals_y_position = 750

                # Totales
                total = new_order.total_amount
                base_total = total / 1.21
                iva_calculado = total - base_total
                base_envio = new_order.shipping_cost / 1.21
                base_productos = base_total - base_envio

                # DEBUG - Verifica valores reales antes de escribir el PDF
                print("🧾 DEBUG FACTURA")
                print("Subtotal productos:", subtotal)
                print("Coste de envío:", shipping_cost)
                print("Total final (con envío):", total)
                print("Base imponible total:", base_total)
                print("Base envío:", base_envio)
                print("Base productos:", base_productos)
                print("IVA calculado:", iva_calculado)


                pdf.setFont("Helvetica", 10)
                pdf.drawString(50, totals_y_position, f"Base Imponible: {base_total:.2f} €")
                pdf.drawString(50, totals_y_position - 15, f"Envío (base): {base_envio:.2f} €")
                pdf.drawString(50, totals_y_position - 30, f"IVA (21%): {iva_calculado:.2f} €")

                # Indicar tipo de envío si aplica
                if new_order.shipping_cost == 49:
                    pdf.drawString(50, totals_y_position - 45, "Tipo de envío aplicado: Tarifa A - 49 €")
                elif shipping_cost == 99:
                    pdf.drawString(50, totals_y_position - 45, "Tipo de envío aplicado: Tarifa B - 99 €")
                elif shipping_cost == 17:
                    pdf.drawString(50, totals_y_position - 45, "Tipo de envío estándar - 17 €")
                elif shipping_cost == 0:
                    pdf.drawString(50, totals_y_position - 45, "Envío gratuito")

                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50, totals_y_position - 65, f"Total: {total:.2f} €")

                # Guardar el PDF
                pdf.save()
                pdf_buffer.seek(0)
                with open(file_path, "wb") as f:
                    f.write(pdf_buffer.getvalue())

                # Guardar la factura
                new_invoice = Invoices(
                    invoice_number=invoice_number,
                    order_id=new_order.id,
                    pdf_path=pdf_path,
                    client_name=f"{data.get('firstname')} {data.get('lastname')}",
                    client_address=data.get('billing_address'),
                    client_cif=data.get('CIF'),
                    client_phone=data.get('phone'),
                    amount=new_order.total_amount,
                    order_details=[detail.serialize() for detail in new_order.order_details]
                )
                db.session.add(new_invoice)
                new_order.invoice_number = invoice_number
                db.session.commit()

                # Enviar el correo con la factura
                email_sent = send_email(
                    subject=f"Factura de tu pedido #{invoice_number}",
                    recipients=[current_user['email'], current_app.config['MAIL_USERNAME']], # <--- current_app.config aquí
                    body=f"Hola {data.get('firstname')} {data.get('lastname')},\n\nAdjuntamos la factura {invoice_number} de tu compra.\n\nGracias por tu confianza.",
                    attachment_path=file_path
                )

                if not email_sent:
                    logger.error(f"Error al enviar el correo con la factura {invoice_number}.")
                else:
                    logger.info(f"Correo enviado correctamente con la factura {invoice_number}.")

                # Crear la respuesta con encabezados CORS
                response = jsonify({
                    "data": new_order.serialize(),
                    "message": "Order, details, and invoice created successfully."
                })
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
                return response, 201

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error al generar la factura: {str(e)}")
                return jsonify({"message": "An error occurred while generating the invoice.", "error": str(e)}), 500

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error al crear la orden: {str(e)}")
            return jsonify({"message": "An error occurred while creating the order.", "error": str(e)}), 500


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
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
        return response, 200
    if request.method == 'DELETE':
        try:
            db.session.delete(order)
            db.session.commit()
            response = jsonify({"message": "Order deleted successfully."})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
            return response, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"message": "An error occurred while deleting the order.", "error": str(e)}), 500


@api.route('/orderdetails', methods=['POST'])
@jwt_required()
def add_order_details():
    data = request.get_json()  # Recibe una lista de detalles
    current_user = get_jwt_identity()
    try:
        added_details = []
        for detail in data:
            # Verifica si el detalle ya existe
            existing_detail = OrderDetails.query.filter_by(
                order_id=detail['order_id'],
                product_id=detail['product_id'],
                alto=detail.get('alto'),
                ancho=detail.get('ancho'),
                anclaje=detail.get('anclaje'),
                color=detail.get('color')
            ).first()
            if existing_detail:
                continue  # Saltar si ya existe

            prod = Products.query.get(detail['producto_id'])

            precio_recalculado = calcular_precio_reja(
                alto_cm=detail.get('alto'),
                ancho_cm=detail.get('ancho'),
                precio_m2=prod.precio_rebajado or prod.precio
            )

            new_detail = OrderDetails(
                order_id=detail['order_id'],
                product_id=detail['product_id'],
                quantity=detail['quantity'],
                alto=detail.get('alto'),
                ancho=detail.get('ancho'),
                anclaje=detail.get('anclaje'),
                color=detail.get('color'),
                precio_total=precio_recalculado,
                firstname=detail.get('firstname'),
                lastname=detail.get('lastname'),
                shipping_address=detail.get('shipping_address'),
                shipping_city=detail.get('shipping_city'),
                shipping_postal_code=detail.get('shipping_postal_code'),
                billing_address=detail.get('billing_address'),
                billing_city=detail.get('billing_city'),
                billing_postal_code=detail.get('billing_postal_code'),
                CIF=detail.get('CIF'),
                shipping_type=detail.get('shipping_type'),
                shipping_cost=detail.get('shipping_cost')
            )
            db.session.add(new_detail)
            added_details.append(new_detail)
        db.session.commit()
        return jsonify([detail.serialize() for detail in added_details]), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while adding order details.", "error": str(e)}), 500


@api.route('/orderdetails', methods=['GET'])
@jwt_required()
def get_order_details():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403
    # Obtener todos los detalles de pedidos
    order_details = db.session.execute(db.select(OrderDetails)).scalars()
    results = [detail.serialize() for detail in order_details]
    total_count = len(results)
    response = jsonify(results)
    response.headers['X-Total-Count'] = str(total_count)
    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200

# crear una factura sin una orden asociada
@api.route('/manual-invoice', methods=['POST'])
@jwt_required()
def create_manual_invoice():
    try:
        # Verificar que el usuario sea administrador
        current_user = get_jwt_identity()
        if not current_user.get("is_admin"):
            return jsonify({"message": "Unauthorized"}), 403

        # Recibir los datos del formulario
        data = request.get_json()
        client_name = data.get("client_name")
        client_address = data.get("client_address")
        client_cif = data.get("client_cif")
        order_details = data.get("order_details", [])

        # Validar los datos requeridos
        if not client_name or not client_address or not order_details:
            return jsonify({"message": "Missing required fields"}), 400

        # Calcular el monto total de los productos
        amount = sum(
            detail.get("quantity", 1) * detail.get("price", 0.0)
            for detail in order_details
        )

        # Generar número de factura único
        invoice_number = Invoices.generate_next_invoice_number()

        # Crear el archivo PDF
        pdf_filename = f"invoice_{invoice_number}.pdf"
        file_path = os.path.join(current_app.config['INVOICE_FOLDER'], pdf_filename)
        pdf_path = f"/api/download-invoice/{pdf_filename}"
        os.makedirs(current_app.config['INVOICE_FOLDER'], exist_ok=True)

        pdf_buffer = BytesIO()
        pdf = canvas.Canvas(pdf_buffer, pagesize=A4)

        # Encabezado: Logo e información del proveedor
        image_url = "https://res.cloudinary.com/dewanllxn/image/upload/v1740167674/logo_uxlqof.png"
        pdf.drawImage(image_url, 300, 750, width=250, height=64)
        pdf.setTitle(f"Factura_{invoice_number}")
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 800, f"Factura No: {invoice_number}")
        pdf.setFont("Helvetica", 10)
        fecha_emision = datetime.now().strftime("%d/%m/%Y")
        pdf.drawString(50, 780, f"Fecha: {fecha_emision}")

        # Información del proveedor
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(400, 700, "PROVEEDOR")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(400, 680, "Sergio Arias Fernández")
        pdf.drawString(400, 665, "DNI 05703874N")
        pdf.drawString(400, 650, "Francisco Fernández Ordoñez 32")
        pdf.drawString(400, 635, "13170 Miguelturra")

        # Información del cliente
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 700, "Cliente")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 680, client_name)
        pdf.drawString(50, 665, client_address)
        pdf.drawString(50, 650, f"CIF: {client_cif}")
        pdf.drawString(50, 635, f"{data.get('phone', 'No proporcionado')}")

        # Detalles del pedido (Tabla)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 580, "Detalles del Pedido")
        pdf.setFont("Helvetica", 10)
        data_table = [["Producto", "Cantidad", "Precio Unitario", "Total"]]
        for detail in order_details:
            row = [
                detail.get("product", "Producto desconocido"),
                detail.get("quantity", 1),
                f"{detail.get('price', 0.0):.2f} €",
                f"{detail.get('quantity', 1) * detail.get('price', 0.0):.2f} €"
            ]
            data_table.append(row)

        # Crear la tabla
        table = Table(data_table, colWidths=[6*cm, 3*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(1, 0.196, 0.302)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        # Renderizar la tabla y calcular su altura
        y_position = 540  # Posición inicial de la tabla
        table.wrapOn(pdf, 50, y_position)
        table_height = table._height
        table.drawOn(pdf, 50, y_position - table_height)

        # Totales debajo de la tabla
        totals_y_position = y_position - table_height - 30
        if totals_y_position < 50:  # Mover a nueva página si no hay espacio
            pdf.showPage()
            totals_y_position = 750

        iva = amount - (amount / 1.21)
        base_imponible = amount - iva

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, totals_y_position, f"Base Imponible: {base_imponible:.2f} €")
        pdf.drawString(50, totals_y_position - 20, f"IVA (21%): {iva:.2f} €")
        pdf.drawString(50, totals_y_position - 40, f"Total: {amount:.2f} €")

        # Guardar el archivo PDF
        pdf.save()
        pdf_buffer.seek(0)
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.getvalue())

        # Registrar la factura en la base de datos
        new_invoice = Invoices(
            invoice_number=invoice_number,
            pdf_path=pdf_path,
            client_name=client_name,
            client_address=client_address,
            client_cif=client_cif,
            client_phone=data.get("phone"),
            amount=amount,
            order_details=order_details
        )
        db.session.add(new_invoice)
        db.session.commit()

        return jsonify({"data": new_invoice.serialize()}), 201

    except Exception as e:
        current_app.logger.error(f"Error al crear la factura manual: {str(e)}")
        return jsonify({"message": "An error occurred while creating the manual invoice.", "error": str(e)}), 500

# Descarga un archivo PDF de factura generado previamente
@api.route('/download-invoice/<filename>', methods=['GET'])
def download_invoice(filename):
    try:
        file_path = os.path.join(current_app.config['INVOICE_FOLDER'], filename)
        current_app.logger.info(f"Buscando archivo en: {file_path}")

        if not os.path.exists(file_path):
            return jsonify({"message": "No se encontró el archivo PDF para esta factura."}), 404

        return send_file(file_path, as_attachment=True, download_name=filename, mimetype='application/pdf')
    except Exception as e:
        current_app.logger.error(f"Error al descargar la factura: {str(e)}")
        return jsonify({"message": "An error occurred while downloading the invoice.", "error": str(e)}), 500

# Recupera todas las facturas con paginación
@api.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    try:
        # Parámetros de paginación
        start = int(request.args.get('_start', 0))
        end = int(request.args.get('_end', 10))

        # Obtener el número total de facturas
        total_count = Invoices.query.count()

        # Obtener las facturas dentro del rango solicitado
        invoices = Invoices.query.order_by(Invoices.id).slice(start, end).all()

        # Crear la respuesta con los encabezados necesarios
        response = jsonify([invoice.serialize() for invoice in invoices])
        response.headers['X-Total-Count'] = total_count
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'

        return response, 200
    except Exception as e:
        return jsonify({"message": "Error retrieving invoices", "error": str(e)}), 500

# Recupera una factura específica por su ID
@api.route('/invoices/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice_by_id(invoice_id):
    try:
        # Obtener la factura por ID
        invoice = Invoices.query.get(invoice_id)
        if not invoice:
            return jsonify({"message": "Invoice not found"}), 404

        # Crear la respuesta
        response = jsonify(invoice.serialize())
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'

        return response, 200
    except Exception as e:
        return jsonify({"message": "Error retrieving invoice", "error": str(e)}), 500


@api.route('/favorites', methods=['OPTIONS', 'GET', 'POST'])
@jwt_required(optional=True)  
def handle_favorites():
    if request.method == "OPTIONS":
        # Manejar el preflight de CORS
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        return response, 200
    current_user = get_jwt_identity()
    if request.method == 'GET':
        # Obtener todos los favoritos del usuario actual
        if not current_user:
            return jsonify({"message": "Debe estar autenticado para acceder a los favoritos"}), 401
        favorites = db.session.execute(db.select(Favorites).where(Favorites.usuario_id == current_user['user_id'])).scalars()
        products = [Products.query.get(fav.producto_id).serialize() for fav in favorites]
        response = jsonify(products)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200
    if request.method == 'POST':
        if not current_user:
            return jsonify({"message": "Debe estar autenticado para añadir a favoritos"}), 401
        data = request.get_json()
        product_id = data.get('product_id')
        # Verificar si el producto ya está en favoritos
        existing_favorite = db.session.execute(db.select(Favorites).where(Favorites.usuario_id == current_user['user_id'], Favorites.producto_id == product_id)).scalar()
        if existing_favorite:
            return jsonify({"message": "Producto ya está en favoritos"}), 409
        # Crear nuevo favorito
        new_favorite = Favorites(usuario_id=current_user['user_id'], producto_id=product_id)
        db.session.add(new_favorite)
        db.session.commit()
        response = jsonify({"message": "Producto añadido a favoritos"})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 201


@api.route('/favorites/<int:product_id>', methods=['OPTIONS', 'DELETE'])
@jwt_required(optional=True)
def remove_favorite(product_id):
    if request.method == "OPTIONS":
        # Manejar el preflight de CORS
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "DELETE, OPTIONS")
        return response, 200
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"message": "Debe estar autenticado para eliminar de favoritos"}), 401
    favorite = db.session.execute(db.select(Favorites).where(Favorites.usuario_id == current_user['user_id'], Favorites.producto_id == product_id)).scalar()
    if not favorite:
        return jsonify({"message": "Producto no encontrado en favoritos"}), 404
    db.session.delete(favorite)
    db.session.commit()
    response = jsonify({"message": "Producto eliminado de favoritos"})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200


@api.route('/cart', methods=['OPTIONS', 'GET', 'POST'])
@jwt_required()
def handle_cart():
    if request.method == "OPTIONS":
        # Manejar el preflight de CORS
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        return response, 200
    current_user = get_jwt_identity()
    if request.method == 'GET':
        # Obtener los productos en el carrito del usuario actual
        try:
            cart_items = Cart.query.filter_by(usuario_id=current_user['user_id']).all()
            products = [item.serialize() for item in cart_items]  # Ahora devuelve la información completa del producto

            response = jsonify(products)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 200
        except Exception as e:
            response = jsonify({"message": str(e)})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 500
    if request.method == 'POST':
        data = request.get_json()
        product_id = data.get('product_id')
        if not product_id:
            response = jsonify({"message": "Product ID is required"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 400
        try:
            new_cart_item = Cart(
                usuario_id=current_user['user_id'],
                producto_id=product_id,
                alto=data.get('alto'),
                ancho=data.get('ancho'),
                anclaje=data.get('anclaje'),
                color=data.get('color'),
                precio_total=data.get('precio_total')  # Guardar el precio total calculado
            )
            db.session.add(new_cart_item)
            db.session.commit()
            response = jsonify({"message": "Producto añadido al carrito"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            response = jsonify({"message": f"Database error: {str(e)}"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 500
        except Exception as e:
            db.session.rollback()
            response = jsonify({"message": f"Unexpected error: {str(e)}"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'Authorization'
            return response, 500


@api.route('/cart/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(product_id):
    current_user = get_jwt_identity()
    try:
        data = request.get_json()  # Obtener las especificaciones del producto
        cart_item = Cart.query.filter_by(
            usuario_id=current_user['user_id'],
            producto_id=product_id,
            alto=data.get('alto'),
            ancho=data.get('ancho'),
            anclaje=data.get('anclaje'),
            color=data.get('color')
        ).first()
        if not cart_item:
            return jsonify({"message": "Producto no encontrado en el carrito con esas especificaciones"}), 404
        db.session.delete(cart_item)
        db.session.commit()
        # Obtener el carrito actualizado
        updated_cart_items = Cart.query.filter_by(usuario_id=current_user['user_id']).all()
        updated_cart = [item.serialize() for item in updated_cart_items]
        return jsonify({"message": "Producto eliminado del carrito", "updated_cart": updated_cart}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500


@api.route('/cart/clear', methods=['POST'])
@jwt_required()
def clear_cart():
    current_user = get_jwt_identity()
    try:
        Cart.query.filter_by(usuario_id=current_user['user_id']).delete()
        db.session.commit()
        return jsonify({"message": "Carrito vaciado con éxito"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error al vaciar el carrito: {str(e)}"}), 500

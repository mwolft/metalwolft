from flask import Flask, request, jsonify, Blueprint, send_file
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from api.utils import generate_sitemap, APIException
from api.models import db, Users, Products, ProductImages, Categories, Orders, OrderDetails, Favorites, Cart, OrderDetails, Posts, Comments
from sqlalchemy.exc import SQLAlchemyError
import bcrypt
import stripe
from dotenv import load_dotenv
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from datetime import datetime

api = Blueprint('api', __name__)

load_dotenv()

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


@api.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    try:
        data = request.get_json()
        # Verificar si ya existe un Payment Intent
        payment_intent_id = data.get('payment_intent_id')
        if payment_intent_id:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            # Si el Payment Intent ya está completado, devolver el mensaje correspondiente
            if intent['status'] == 'succeeded':
                return jsonify({"message": "El pago ya ha sido completado.", "paymentIntent": intent}), 200
        # Crear un nuevo PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=data['amount'], 
            currency='eur',
            payment_method=data['payment_method_id'],  # ID del método de pago creado en el frontend
            confirm=True,  # Confirmar inmediatamente
            return_url=os.getenv('STRIPE_RETURN_URL')  
        )
        return jsonify({
            'clientSecret': intent['client_secret'],
            'paymentIntent': intent
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 403


@api.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    comments = Comments.query.filter_by(post_id=post_id).all()
    if not comments:
        return jsonify([]), 200
    return jsonify([comment.serialize() for comment in comments]), 200


@api.route('/posts', methods=['GET'])
@jwt_required(optional=True)
def get_posts():
    posts = Posts.query.all()
    total_count = len(posts)

    response = jsonify([post.serialize() for post in posts])
    response.headers['X-Total-Count'] = total_count
    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 200


@api.route('/posts/<int:post_id>', methods=['GET'])
@jwt_required(optional=True)
def get_post(post_id):
    post = Posts.query.get(post_id)
    if post:
        return jsonify(post.serialize()), 200
    return jsonify({"message": "Post not found"}), 404


@api.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    data = request.json
    new_post = Posts(
        title=data.get('title'),
        content=data.get('content'),
        author_id=current_user.get('id'),
        image_url=data.get('image_url')
    )
    db.session.add(new_post)
    db.session.commit()
    return jsonify(new_post.serialize()), 201


@api.route('/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    post = Posts.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found"}), 404

    data = request.json
    post.title = data.get('title', post.title)
    post.content = data.get('content', post.content)
    post.image_url = data.get('image_url', post.image_url)
    post.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify(post.serialize()), 200


@api.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    current_user = get_jwt_identity()
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403

    post = Posts.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found"}), 404

    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted"}), 200


@api.route('/generate-invoice', methods=['POST'])
@jwt_required()
def generate_invoice():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        if not order_id:
            return jsonify({"message": "Order ID is required"}), 400
        
        # Obtener el usuario actual
        current_user = get_jwt_identity()
        user_id = current_user['user_id']

        # Obtener la orden y validar si existe
        order = Orders.query.get(order_id)
        if not order:
            return jsonify({"message": "Order not found"}), 404
        
        # Validar que el usuario que solicita la factura sea el propietario de la orden o un administrador
        if order.user_id != user_id and not current_user.get("is_admin"):
            return jsonify({"message": "You do not have permission to access this invoice"}), 403
        
        # Obtener el usuario asociado a la orden
        user = Users.query.get(order.user_id)

        # Crear un buffer para el PDF
        pdf_buffer = BytesIO()
        pdf = canvas.Canvas(pdf_buffer, pagesize=A4)

        # Añadir la imagen en la parte superior derecha
        image_url = "https://www.metalwolft.com/assets/images/herrero-soldador-en-ciudad-real.jpg"
        pdf.drawImage(image_url, 300, 750, width=250, height=64)  # Ajustar posición y tamaño según necesidad

        # Configurar márgenes estrechos y título
        pdf.setTitle(f"Factura_{order.invoice_number}")
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 800, "Factura")

        # Datos de la empresa en la parte superior derecha debajo de la imagen
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(400, 700, "Información del Proveedor")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(400, 680, "Sergio Arias Fernández")
        pdf.drawString(400, 660, "DNI 05703874N")
        pdf.drawString(400, 640, "Francisco Fernández Ordoñez 32")
        pdf.drawString(400, 620, "13170 Miguelturra")

        # Información general
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 770, f"Factura No: {order.invoice_number}")
        pdf.drawString(50, 750, f"Fecha: {order.order_date.strftime('%d/%m/%Y')}")

        # Información del cliente
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 700, "Información del Cliente")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 680, f"{user.firstname} {user.lastname}")
        pdf.drawString(50, 660, f"{user.billing_address}, {user.billing_city} ({user.billing_postal_code})")
        pdf.drawString(50, 640, f"{user.CIF}")

        # Información del envío
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 580, "Dirección de envío")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 560, f"{user.shipping_address}, {user.shipping_city} ({user.shipping_postal_code})")

        # Detalles del pedido
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 510, "Detalles del Pedido")
        pdf.setFont("Helvetica", 10)

        # Crear datos para la tabla de productos
        data = [["Producto", "Alto", "Ancho", "Anclaje", "Color", "Precio"]]
        for detail in order.order_details:
            product = detail.product
            row = [
                product.nombre,
                f"{detail.alto}",
                f"{detail.ancho}",
                detail.anclaje,
                detail.color,
                f"{detail.precio_total:.2f} €"
            ]
            data.append(row)

        # Crear la tabla de productos
        table = Table(data, colWidths=[6*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(1, 0.196, 0.302)),  # #ff324d
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.941, 0.941, 0.941)),  # #f0f0f0
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        # Obtener el ancho total de la página menos márgenes
        page_width = A4[0] - 100

        # Posicionar la tabla de productos en el PDF alineada a la derecha
        y_position = 490
        table.wrapOn(pdf, 50, y_position)
        table_height = table._height
        table.drawOn(pdf, page_width - table._width, y_position - table_height)

        # Calcular valores para la tabla de totales
        total = order.total_amount
        iva = total - (total / 1.21)
        base_imponible = total - iva
        envio = 0.00  # Envío fijo a 0 euros

        # Crear datos para la tabla de totales
        totals_data = [
            ["Envío", "Base Imponible", "IVA (21%)", "Total"],
            [f"{envio:.2f} €", f"{base_imponible:.2f} €", f"{iva:.2f} €", f"{total:.2f} €"]
        ]

        # Crear la tabla de totales
        totals_table = Table(totals_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Negrita solo para la primera fila
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),  # Fuente normal para las filas restantes
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.941, 0.941, 0.941)),  # Mismo fondo para todas las filas
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),  # Color del texto en negro para toda la tabla
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        # Posicionar la tabla de totales alineada a la derecha, debajo de la tabla de productos
        totals_y_position = y_position - table_height - 20
        totals_table.wrapOn(pdf, 50, totals_y_position)
        totals_table_height = totals_table._height
        totals_table.drawOn(pdf, page_width - totals_table._width, totals_y_position - totals_table_height)

        # Finalizar el PDF
        pdf.save()

        # Devolver el PDF generado como respuesta
        pdf_buffer.seek(0)
        return send_file(pdf_buffer, as_attachment=True, download_name=f"invoice_{order.invoice_number}.pdf", mimetype='application/pdf')
    except Exception as e:
        # Devolver un mensaje de error detallado en el caso de que ocurra un problema
        return jsonify({"message": "An error occurred while generating the invoice.", "error": str(e)}), 500


@api.route('/hello', methods=['GET'])
def handle_hello():
    return jsonify({"message": "Hello! I'm a message from the backend"}), 200


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
        'email': user.email,
        'user_id': user.id,
        'is_admin': user.is_admin
    })
    response_body = {
        'results': user.serialize(),
        'message': 'Bienvenido',
        'access_token': access_token
    }
    response = jsonify(response_body)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, 201


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
        'email': user.email,
        'user_id': user.id,
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
def get_categories():
    categories = Categories.query.all()
    total_count = len(categories)

    response = jsonify([category.serialize() for category in categories])
    response.headers['X-Total-Count'] = total_count
    response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
    return response, 200


@api.route('/products', methods=['GET', 'POST'])
def handle_products():
    current_user = get_jwt_identity() if request.method == 'POST' else None
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
        if not current_user or not current_user.get("is_admin"):
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
    # Para los métodos PUT y DELETE requerimos autenticación
    current_user = get_jwt_identity()
    if request.method == 'PUT':
        # Solo los administradores pueden actualizar productos
        if not current_user or not current_user.get("is_admin"):
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
    # Solo los administradores pueden agregar imágenes
    if not current_user.get("is_admin"):
        return jsonify({"message": "Access forbidden: Admins only"}), 403
    # Obtener el producto por ID
    product = Products.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    # Obtener las URLs de las imágenes desde la solicitud
    data = request.get_json()
    image_urls = data.get('images', [])
    # Verificar que las URLs sean una lista de cadenas de texto válidas
    if not isinstance(image_urls, list) or not all(isinstance(url, str) for url in image_urls):
        return jsonify({"message": "Invalid images format. Expected a list of URLs."}), 400
    try:
        # Añadir cada imagen a la base de datos
        for image_url in image_urls:
            new_image = ProductImages(product_id=product_id, image_url=image_url)
            db.session.add(new_image)
        # Confirmar los cambios en la base de datos
        db.session.commit()
        # Devolver el producto con las nuevas imágenes
        response = jsonify({"message": "Images added successfully.", "product": product.serialize_with_images()})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Authorization'
        return response, 201
    except SQLAlchemyError as e:
        # Manejar errores y revertir la transacción si ocurre un problema
        db.session.rollback()
        return jsonify({"message": "An error occurred while adding images.", "error": str(e)}), 500


@api.route('/products/<int:product_id>', methods=['GET'])
def get_product_with_images(product_id):
    product = Products.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    return jsonify(product.serialize_with_images()), 200


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
        # Obtener todas las órdenes del usuario actual
        orders = db.session.execute(db.select(Orders).where(Orders.user_id == current_user['user_id'])).scalars()
        results = [order.serialize() for order in orders]
        total_count = len(results)
        response = jsonify(results)
        response.headers['X-Total-Count'] = str(total_count)
        response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200
    if request.method == 'POST':
        # Crear nueva orden
        data = request.get_json()
        try:
            new_order = Orders(
                user_id=current_user['user_id'],
                total_amount=data['total_amount'],
                invoice_number=Orders.generate_invoice_number(),
                locator=Orders.generate_locator()
            )
            db.session.add(new_order)
            db.session.commit()
            response = jsonify({
                'message': 'Order created successfully.',
                'order': new_order.serialize()
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Expose-Headers'] = 'X-Total-Count'
            return response, 201
        except SQLAlchemyError as e:
            db.session.rollback()
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
def add_order_detail():
    data = request.get_json()
    current_user = get_jwt_identity()  # Obtiene el usuario actual a través del JWT
    try:
        # Crear un nuevo detalle de pedido
        new_order_detail = OrderDetails(
            order_id=data['order_id'],
            product_id=data['product_id'],
            quantity=data['quantity'],
            alto=data.get('alto'),
            ancho=data.get('ancho'),
            anclaje=data.get('anclaje'),
            color=data.get('color'),
            precio_total=data['precio_total'],
            firstname=data.get('firstname'),
            lastname=data.get('lastname'),
            shipping_address=data.get('shipping_address'),
            shipping_city=data.get('shipping_city'),
            shipping_postal_code=data.get('shipping_postal_code'),
            billing_address=data.get('billing_address'),
            billing_city=data.get('billing_city'),
            billing_postal_code=data.get('billing_postal_code'),
            CIF=data.get('CIF')
        )
        db.session.add(new_order_detail)
        # Actualizar los datos del usuario si son diferentes o están vacíos
        user = Users.query.filter_by(id=current_user['user_id']).first()
        if user:
            user.firstname = data.get('firstname') or user.firstname
            user.lastname = data.get('lastname') or user.lastname
            user.shipping_address = data.get('shipping_address') or user.shipping_address
            user.shipping_city = data.get('shipping_city') or user.shipping_city
            user.shipping_postal_code = data.get('shipping_postal_code') or user.shipping_postal_code
            user.billing_address = data.get('billing_address') or user.billing_address
            user.billing_city = data.get('billing_city') or user.billing_city
            user.billing_postal_code = data.get('billing_postal_code') or user.billing_postal_code
            user.CIF = data.get('CIF') or user.CIF
        db.session.commit()
        response = jsonify({
            "message": "Order detail added successfully.",
            "order_detail": new_order_detail.serialize(),
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while adding the order detail.", "error": str(e)}), 500


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
            # Verificar si ya existe un producto con las mismas especificaciones en el carrito
            existing_item = Cart.query.filter_by(
                usuario_id=current_user['user_id'],
                producto_id=product_id,
                alto=data.get('alto'),
                ancho=data.get('ancho'),
                anclaje=data.get('anclaje'),
                color=data.get('color')
            ).first()
            if existing_item:
                response = jsonify({"message": "Producto ya está en el carrito con las mismas especificaciones"})
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Expose-Headers'] = 'Authorization'
                return response, 409
            # Añadir el producto al carrito con los detalles personalizados
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

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
import random
import string
from datetime import datetime

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    firstname = db.Column(db.String(100), nullable=True)
    lastname = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # Nuevo campo para indicar si el usuario es administrador
    shipping_address = db.Column(db.String(200), nullable=True)
    shipping_city = db.Column(db.String(100), nullable=True)
    shipping_postal_code = db.Column(db.String(20), nullable=True)
    billing_address = db.Column(db.String(200), nullable=True)
    billing_city = db.Column(db.String(100), nullable=True)
    billing_postal_code = db.Column(db.String(20), nullable=True)
    CIF = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f'<User {self.id}: {self.firstname} {self.lastname}>'

    def serialize(self):
        return {
            "id": self.id,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "is_active": self.is_active,
            "email": self.email,
            "is_admin": self.is_admin,  # Incluir el campo en la serialización
            "shipping_address": self.shipping_address,
            "shipping_city": self.shipping_city,
            "shipping_postal_code": self.shipping_postal_code,
            "billing_address": self.billing_address,
            "billing_city": self.billing_city,
            "billing_postal_code": self.billing_postal_code,
            "CIF": self.CIF,
        }


class Posts(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_url = db.Column(db.String(300), nullable=True)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relación con el modelo de Users
    author = db.relationship('Users', backref='posts', lazy=True)

    def __repr__(self):
        return f'<Post {self.id}: {self.title}>'

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author_id": self.author_id,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con el modelo de Posts
    post = db.relationship('Posts', backref='comments', lazy=True)

    # Relación con el modelo de Users
    user = db.relationship('Users', backref='comments', lazy=True)

    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id} by User {self.user_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "content": self.content,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
        }


class Products(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    imagen = db.Column(db.String(200), nullable=True)
    images = db.relationship('ProductImages', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.id}: {self.nombre}>'

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio": self.precio,
            "categoria_id": self.categoria_id,
            "imagen": self.imagen,
        }

    def serialize_with_images(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio": self.precio,
            "categoria_id": self.categoria_id,
            "imagen": self.imagen,
            "images": [image.serialize() for image in self.images]
        }


class ProductImages(db.Model):
    __tablename__ = "product_images"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<ProductImage {self.id}: {self.image_url}>'

    def serialize(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "image_url": self.image_url,
        }


class Categories(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    products = db.relationship('Products', backref='categoria', lazy=True)

    def __repr__(self):
        return f'<Category {self.id}: {self.nombre}>'

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion
        }


class Orders(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    total_amount = db.Column(db.Float, nullable=False)
    invoice_number = db.Column(db.String(50), nullable=False, unique=True)  # Número de factura
    locator = db.Column(db.String(10), nullable=False, unique=True)  # Localizador único

    user = db.relationship('Users', backref='orders', lazy=True)
    order_details = db.relationship('OrderDetails', backref='order', lazy=True)  # Relación con OrderDetails

    def __repr__(self):
        return f'<Order {self.id} by User {self.user_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "order_date": self.order_date,
            "total_amount": self.total_amount,
            "invoice_number": self.invoice_number,
            "locator": self.locator,
            "order_details": [detail.serialize() for detail in self.order_details]  # Serializar detalles del pedido
        }

    @staticmethod
    def generate_invoice_number():
        from datetime import datetime
        now = datetime.now()
        return f"{now.strftime('%b').upper()}-{now.year}-{random.randint(1, 999):03}"

    @staticmethod
    def generate_locator():
        letters = ''.join(random.choices(string.ascii_uppercase, k=2))
        numbers = ''.join(random.choices(string.digits, k=4))
        return f"{letters}{numbers}"


class OrderDetails(db.Model):
    __tablename__ = "order_details"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    alto = db.Column(db.Float, nullable=True)  
    ancho = db.Column(db.Float, nullable=True)  
    anclaje = db.Column(db.String(50), nullable=True)  
    color = db.Column(db.String(50), nullable=True) 
    precio_total = db.Column(db.Float, nullable=False)  

    # Campos de información de usuario y envío
    firstname = db.Column(db.String(100), nullable=True)
    lastname = db.Column(db.String(100), nullable=True)
    shipping_address = db.Column(db.String(200), nullable=True)
    shipping_city = db.Column(db.String(100), nullable=True)
    shipping_postal_code = db.Column(db.String(20), nullable=True)
    billing_address = db.Column(db.String(200), nullable=True)
    billing_city = db.Column(db.String(100), nullable=True)
    billing_postal_code = db.Column(db.String(20), nullable=True)
    CIF = db.Column(db.String(20), nullable=True)

    product = db.relationship('Products', backref='order_details', lazy=True)  

    def __repr__(self):
        return f'<OrderDetail {self.id}: Order {self.order_id} - Product {self.product_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "alto": self.alto,
            "ancho": self.ancho,
            "anclaje": self.anclaje,
            "color": self.color,
            "precio_total": self.precio_total,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "shipping_address": self.shipping_address,
            "shipping_city": self.shipping_city,
            "shipping_postal_code": self.shipping_postal_code,
            "billing_address": self.billing_address,
            "billing_city": self.billing_city,
            "billing_postal_code": self.billing_postal_code,
            "CIF": self.CIF
        }


class Favorites(db.Model):
    __tablename__ = "favorites"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    def __repr__(self):
        return f'<Favorite {self.id}: User {self.usuario_id}, Product {self.producto_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "producto_id": self.producto_id
        }


class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    alto = db.Column(db.Float, nullable=True)  
    ancho = db.Column(db.Float, nullable=True)  
    anclaje = db.Column(db.String(50), nullable=True)  
    color = db.Column(db.String(50), nullable=True)  
    precio_total = db.Column(db.Float, nullable=False)  

    product = db.relationship('Products', backref='cart_items', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "producto_id": self.producto_id,
            "nombre": self.product.nombre,  # Añadir el nombre del producto
            "descripcion": self.product.descripcion,  # Añadir la descripción
            "imagen": self.product.imagen,  # Añadir la imagen del producto
            "alto": self.alto,
            "ancho": self.ancho,
            "anclaje": self.anclaje,
            "color": self.color,
            "precio_total": self.precio_total
        }

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum


db = SQLAlchemy()


from flask_sqlalchemy import SQLAlchemy

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



class Products(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    imagen = db.Column(db.String(200), nullable=True)
    stock = db.Column(db.Integer, nullable=False, default=0)
    
    alto = db.Column(db.Float, nullable=False)  # Tamaño - Alto
    ancho = db.Column(db.Float, nullable=False)  # Tamaño - Ancho
    anclaje = db.Column(db.Enum('pared', 'suelo', 'mixto', name='anclaje_enum'), nullable=False)  # Tipo de anclaje
    color = db.Column(db.String(50), nullable=False)  # Color

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
            "stock": self.stock,
            "alto": self.alto,
            "ancho": self.ancho,
            "anclaje": self.anclaje,
            "color": self.color,
        }


class Categories(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)

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

    user = db.relationship('Users', backref='orders', lazy=True)

    def __repr__(self):
        return f'<Order {self.id} by User {self.user_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "order_date": self.order_date,
            "total_amount": self.total_amount,
        }


class OrderDetails(db.Model):
    __tablename__ = "order_details"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    alto = db.Column(db.Float, nullable=False)
    ancho = db.Column(db.Float, nullable=False)
    anclaje = db.Column(db.Enum('pared', 'suelo', 'mixto', name='anclaje_enum'), nullable=False)
    color = db.Column(db.String(50), nullable=False)

    order = db.relationship('Orders', backref='order_details', lazy=True)
    product = db.relationship('Products', backref='order_details', lazy=True)

    def __repr__(self):
        return f'<OrderDetail {self.id} for Order {self.order_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "alto": self.alto,
            "ancho": self.ancho,
            "anclaje": self.anclaje,
            "color": self.color
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

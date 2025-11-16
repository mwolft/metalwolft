from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, event
import random
import string
from datetime import datetime
from flask import current_app
from slugify import slugify

db = SQLAlchemy()

class DeliveryEstimateConfig(db.Model):
    __tablename__ = 'delivery_estimate_config'
    id = db.Column(db.Integer, primary_key=True)
    delivery_days = db.Column(db.Integer, nullable=False, default=15) 
    range_days = db.Column(db.Integer, nullable=False, default=7)   
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        from datetime import date, timedelta
        today = date.today()
        start_date = today + timedelta(days=self.delivery_days)
        end_date = start_date + timedelta(days=self.range_days)
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "is_active": self.is_active
        }


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    firstname = db.Column(db.String(100), nullable=True)
    lastname = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False) 
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
            "is_admin": self.is_admin,  
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
    slug = db.Column(db.String(100), unique=True, nullable=False)  

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
            "slug": self.slug
        }

    def generate_slug(self):
        self.slug = slugify(self.title)


class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    post = db.relationship('Posts', backref='comments', lazy=True)

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
    sort_order = db.Column(db.Integer, default=0)   
    slug = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    descripcion_seo = db.Column(db.Text, nullable=True)
    titulo_seo = db.Column(db.String(180), nullable=True)
    h1_seo = db.Column(db.String(180), nullable=True)
    es_mas_vendido = db.Column(db.Boolean, default=False)
    es_nuevo_diseno = db.Column(db.Boolean, default=False)
    precio = db.Column(db.Float, nullable=False)
    precio_rebajado = db.Column(db.Float, nullable=True)
    porcentaje_rebaja = db.Column(db.Integer, nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    subcategoria_id = db.Column(db.Integer, db.ForeignKey('subcategories.id'), nullable=True)
    imagen = db.Column(db.String(200), nullable=True)
    has_abatible = db.Column(db.Boolean, default=False)
    has_door_model = db.Column(db.Boolean, default=False)
    images = db.relationship('ProductImages', backref='product', lazy=True)
    categoria = db.relationship('Categories', backref='products', lazy=True)
    subcategoria = db.relationship('Subcategories', backref='products', lazy=True)

    def __repr__(self):
        return f'<Product {self.id}: {self.nombre}>'


    def generate_slug(self):
        from slugify import slugify
        self.slug = slugify(self.nombre)


    def serialize(self):
        rebajado = self.precio_rebajado if self.precio_rebajado else None
        porcentaje = (
            round(100 - (rebajado / self.precio * 100), 2)
            if rebajado
            else None
        )
        return {
            "id": self.id,
            "slug": self.slug,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "descripcion_seo": self.descripcion_seo,
            "titulo_seo": self.titulo_seo,
            "h1_seo": self.h1_seo,
            "precio": int(self.precio) if self.precio == int(self.precio) else self.precio,
            "precio_rebajado": int(rebajado) if rebajado and rebajado == int(rebajado) else rebajado,
            "porcentaje_rebaja": porcentaje,
            "categoria_id": self.categoria_id,
            "category_slug": self.categoria.slug, 
            "subcategoria_id": self.subcategoria_id,
            "imagen": self.imagen,
            "has_abatible": self.has_abatible,
            "has_door_model": self.has_door_model,
            "es_mas_vendido": self.es_mas_vendido,
            "es_nuevo_diseno": self.es_nuevo_diseno,
        }

    def serialize_with_images(self):
        return {
            **self.serialize(),
            "images": [image.serialize() for image in self.images],
            "categoria_nombre": self.categoria.nombre,
            "subcategoria_nombre": self.subcategoria.nombre if self.subcategoria else None,
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
    sort_order = db.Column(db.Integer, default=0) 
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)  

    children = db.relationship('Categories', backref=db.backref('parent', remote_side=[id]), lazy=True)

    def __repr__(self):
        return f'<Category {self.id}: {self.nombre}>'

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "parent_id": self.parent_id,
            "image_url": self.image_url,
            "slug": self.slug
        }

    def generate_slug(self):
        self.slug = slugify(self.nombre)


class Subcategories(db.Model):
    __tablename__ = "subcategories"
    id = db.Column(db.Integer, primary_key=True)
    sort_order = db.Column(db.Integer, default=0)   
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    categoria = db.relationship('Categories', backref='subcategories', lazy=True)  
    def __repr__(self):
        return f'<Subcategory {self.id}: {self.nombre}>'
    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "categoria_id": self.categoria_id
        }


class Orders(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    total_amount = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, nullable=True, default=0.0)
    discount_code = db.Column(db.String(50), nullable=True)        
    discount_value = db.Column(db.Float, nullable=True, default=0.0) 
    order_status = db.Column(db.String(50), nullable=False, default="pendiente")
    invoice_number = db.Column(db.String(50), nullable=True, unique=True)
    locator = db.Column(db.String(10), nullable=False, unique=True)
    estimated_delivery_at = db.Column(db.Date, nullable=True)             
    estimated_delivery_note = db.Column(db.String(255), nullable=True)     

    user = db.relationship('Users', backref='orders', lazy=True)
    order_details = db.relationship('OrderDetails', backref='order', lazy=True)

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
            "order_status": self.order_status,
            "estimated_delivery_at": self.estimated_delivery_at.isoformat() if self.estimated_delivery_at else None,
            "estimated_delivery_note": self.estimated_delivery_note,
            "order_details": [detail.serialize() for detail in self.order_details]
        }

        
    @staticmethod
    def generate_next_invoice_number():
        from datetime import datetime
        now = datetime.now()
        prefix = f"{now.strftime('%b').upper()}-{now.year}-"

        for attempt in range(3):
            try:
                # Consultar el número más alto de ambas tablas
                last_number_query = db.session.execute(
                    f"""
                    SELECT MAX(CAST(SUBSTRING(invoice_number, '([0-9]+)$') AS INTEGER)) AS last_number
                    FROM (
                        SELECT invoice_number FROM invoices WHERE invoice_number LIKE '{prefix}%'
                        UNION ALL
                        SELECT invoice_number FROM orders WHERE invoice_number LIKE '{prefix}%'
                    ) AS combined;
                    """
                ).scalar()

                next_number = (last_number_query or 0) + 1
                invoice_number = f"{prefix}{next_number:03}"
                
                # Agregar logs detallados para validar la existencia del número generado
                existing_invoice = db.session.query(Invoices).filter_by(invoice_number=invoice_number).first()
                existing_order = db.session.query(Orders).filter_by(invoice_number=invoice_number).first()
                
                if existing_invoice or existing_order:
                    current_app.logger.warning(
                        f"Intento {attempt + 1}: Número de factura duplicado detectado: {invoice_number}. "
                        f"En Invoices: {bool(existing_invoice)}, En Orders: {bool(existing_order)}"
                    )
                    continue  # Intentar nuevamente con el siguiente número
                
                # Si el número no existe en ninguna tabla, retornarlo
                current_app.logger.info(f"Número de factura generado exitosamente: {invoice_number}")
                return invoice_number

            except Exception as e:
                current_app.logger.error(f"Error durante la generación del número de factura: {str(e)}")

        raise Exception("Failed to generate a unique invoice number after 3 attempts")


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
    firstname = db.Column(db.String(100), nullable=True)
    lastname = db.Column(db.String(100), nullable=True)
    shipping_address = db.Column(db.String(200), nullable=True)
    shipping_city = db.Column(db.String(100), nullable=True)
    shipping_postal_code = db.Column(db.String(20), nullable=True)
    billing_address = db.Column(db.String(200), nullable=True)
    billing_city = db.Column(db.String(100), nullable=True)
    billing_postal_code = db.Column(db.String(20), nullable=True)
    shipping_type = db.Column(db.String(10), nullable=True)
    shipping_cost = db.Column(db.Float, nullable=True)
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
            "CIF": self.CIF,
            "shipping_type": self.shipping_type,
            "shipping_cost": self.shipping_cost
        }


class Invoices(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False, unique=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    pdf_path = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    client_name = db.Column(db.String(255), nullable=False)
    client_address = db.Column(db.String(255), nullable=False)
    client_cif = db.Column(db.String(50), nullable=True)
    client_phone = db.Column(db.String(50), nullable=True)
    order_details = db.Column(db.JSON, nullable=False)
    order = db.relationship('Orders', backref='invoice', lazy=True)

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

    @staticmethod
    def generate_next_invoice_number():
        from datetime import datetime
        now = datetime.now()
        prefix = f"{now.strftime('%b').upper()}-{now.year}-"
        last_invoice = db.session.query(Invoices.invoice_number).filter(
            Invoices.invoice_number.like(f"{prefix}%")
        ).order_by(Invoices.invoice_number.desc()).first()

        if last_invoice:
            # Extraer el último número secuencial
            last_number = int(last_invoice[0].split("-")[-1])
            next_number = last_number + 1
        else:
            next_number = 1 

        return f"{prefix}{next_number:03}"  

    def serialize(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "order_id": self.order_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "pdf_path": self.pdf_path,
            "amount": self.amount,
            "client_name": self.client_name,
            "client_address": self.client_address,
            "client_cif": self.client_cif,
            "client_phone": self.client_phone,
            "order_details": self.order_details,
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
    quantity = db.Column(db.Integer, nullable=False, default=1)  
    added_at = db.Column(db.DateTime, nullable=False)
    user = db.relationship('Users', backref='cart_items', lazy=True)
    product = db.relationship('Products', backref='cart_items', lazy=True)

    def serialize(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "producto_id": self.producto_id,
            "nombre": self.product.nombre,
            "descripcion": self.product.descripcion,
            "imagen": self.product.imagen,
            "slug": self.product.slug,
            "category_slug": self.product.categoria.slug if self.product.categoria else None,
            "alto": self.alto,
            "ancho": self.ancho,
            "anclaje": self.anclaje,
            "color": self.color,
            "precio_total": self.precio_total,
            "quantity": self.quantity,
            "added_at": self.added_at
        }


@event.listens_for(Products, 'before_insert')
@event.listens_for(Products, 'before_update')
def generate_product_slug(mapper, connection, target):
    if not target.nombre:
        return

    base = slugify(target.nombre)
    slug = base
    i = 1

    products_table = Products.__table__
    while connection.execute(
        products_table.select()
            .where(products_table.c.slug == slug)
            .where(products_table.c.id != (target.id or 0))
    ).first():
        i += 1
        slug = f"{base}-{i}"

    target.slug = slug
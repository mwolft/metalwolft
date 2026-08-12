from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, event, text
import random
import string
import uuid
from datetime import datetime
from flask import current_app
from slugify import slugify

db = SQLAlchemy()


def _serialize_screw_configuration(anclaje, screw_option, screw_length_mm, screw_supplement):
    from api.utils import DEFAULT_CONFIGURATOR_SCREW_OPTION, resolve_screw_configuration

    normalized_option = screw_option or DEFAULT_CONFIGURATOR_SCREW_OPTION
    normalized_length = screw_length_mm
    normalized_supplement = screw_supplement
    if normalized_length is None:
        legacy_configuration = resolve_screw_configuration(anclaje, normalized_option)
        if legacy_configuration:
            normalized_option = legacy_configuration["screw_option"]
            normalized_length = legacy_configuration["screw_length_mm"]
            if normalized_supplement is None:
                normalized_supplement = legacy_configuration["screw_supplement"]

    return {
        "screw_option": normalized_option,
        "screw_length_mm": normalized_length,
        "screw_supplement": float(normalized_supplement or 0.0),
    }

class DeliveryEstimateConfig(db.Model):
    __tablename__ = 'delivery_estimate_config'
    id = db.Column(db.Integer, primary_key=True)
    delivery_days = db.Column(db.Integer, nullable=False, default=15) 
    range_days = db.Column(db.Integer, nullable=False, default=7)   
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        from api.delivery_estimate_service import build_delivery_estimate

        return build_delivery_estimate(self)


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    firstname = db.Column(db.String(100), nullable=True)
    lastname = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
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
            "phone": self.phone,
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
    __table_args__ = (
        db.CheckConstraint(
            "published OR NOT available_for_sale",
            name="ck_products_published_available_for_sale",
        ),
        db.CheckConstraint(
            "opening_type IN ('fixed', 'hinged')",
            name="ck_products_opening_type",
        ),
    )

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
    published = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.true(),
    )
    available_for_sale = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.true(),
    )
    precio = db.Column(db.Float, nullable=False)
    precio_rebajado = db.Column(db.Float, nullable=True)
    porcentaje_rebaja = db.Column(db.Integer, nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    subcategoria_id = db.Column(db.Integer, db.ForeignKey('subcategories.id'), nullable=True)
    imagen = db.Column(db.String(200), nullable=True)
    opening_type = db.Column(
        db.String(16),
        nullable=False,
        default="fixed",
        server_default="fixed",
    )
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
            "opening_type": self.opening_type,
            "has_abatible": self.has_abatible,
            "has_door_model": self.has_door_model,
            "es_mas_vendido": self.es_mas_vendido,
            "es_nuevo_diseno": self.es_nuevo_diseno,
            "available_for_sale": self.available_for_sale,
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
        from flask import current_app

        now = datetime.now()
        month_str = now.strftime('%b').upper()   # NOV
        year_str = now.strftime('%Y')            # 2025

        # Nuevo prefijo compacto: NOV2025
        prefix = f"{month_str}{year_str}"

        for attempt in range(3):
            try:
                # Buscar el mayor correlativo del mes/año actual
                last_number_query = db.session.execute(
                    f"""
                    SELECT MAX(CAST(SUBSTRING(invoice_number, '([0-9]{{3}})$') AS INTEGER)) AS last_number
                    FROM (
                        SELECT invoice_number FROM invoices WHERE invoice_number LIKE '{prefix}%'
                        UNION ALL
                        SELECT invoice_number FROM orders WHERE invoice_number LIKE '{prefix}%'
                    ) AS combined;
                    """
                ).scalar()

                next_number = (last_number_query or 0) + 1

                # Formato final: NOV2025002
                invoice_number = f"{prefix}{next_number:03d}"

                # Verificación de colisiones (extra seguridad)
                exists_invoice = db.session.query(Invoices).filter_by(invoice_number=invoice_number).first()
                exists_order = db.session.query(Orders).filter_by(invoice_number=invoice_number).first()

                if exists_invoice or exists_order:
                    current_app.logger.warning(
                        f"Intento {attempt + 1}: Número de factura duplicado detectado: {invoice_number}"
                    )
                    continue

                current_app.logger.info(f"Número de factura generado: {invoice_number}")
                return invoice_number

            except Exception as e:
                current_app.logger.error(f"Error generando número de factura: {str(e)}")

        raise Exception("Failed to generate a unique invoice number after 3 attempts")


    @staticmethod
    def generate_locator():
        letters = ''.join(random.choices(string.ascii_uppercase, k=2))
        numbers = ''.join(random.choices(string.digits, k=4))
        return f"{letters}{numbers}"


class CheckoutSessions(db.Model):
    __tablename__ = "checkout_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, unique=True)
    payment_intent_id = db.Column(db.String(255), nullable=True, unique=True, index=True)
    payment_provider = db.Column(db.String(50), nullable=False, default="stripe")
    provider_order_id = db.Column(db.String(255), nullable=True, index=True)
    provider_capture_id = db.Column(db.String(255), nullable=True, index=True)
    provider_status = db.Column(db.String(100), nullable=True)
    public_checkout_token = db.Column(db.String(64), nullable=False, unique=True, index=True)
    idempotency_key = db.Column(db.String(255), nullable=True, index=True)
    status = db.Column(db.String(50), nullable=False, default="pending_payment")
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    shipping_cost = db.Column(db.Float, nullable=False, default=0.0)
    discount_code = db.Column(db.String(50), nullable=True)
    discount_percent = db.Column(db.Float, nullable=False, default=0.0)
    discount_amount = db.Column(db.Float, nullable=False, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    quote_snapshot = db.Column(db.JSON, nullable=False)
    customer_snapshot = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    user = db.relationship('Users', backref='checkout_sessions', lazy=True)
    order = db.relationship('Orders', backref=db.backref('checkout_session', uselist=False), lazy=True)

    @staticmethod
    def generate_public_checkout_token():
        return uuid.uuid4().hex

    def __repr__(self):
        provider_ref = self.payment_intent_id or self.provider_order_id or self.public_checkout_token
        return f'<CheckoutSession {self.id}: {self.payment_provider} {provider_ref}>'

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "order_id": self.order_id,
            "payment_intent_id": self.payment_intent_id,
            "payment_provider": self.payment_provider,
            "provider_order_id": self.provider_order_id,
            "provider_capture_id": self.provider_capture_id,
            "provider_status": self.provider_status,
            "public_checkout_token": self.public_checkout_token,
            "idempotency_key": self.idempotency_key,
            "status": self.status,
            "subtotal": self.subtotal,
            "shipping_cost": self.shipping_cost,
            "discount_code": self.discount_code,
            "discount_percent": self.discount_percent,
            "discount_amount": self.discount_amount,
            "total_amount": self.total_amount,
            "quote_snapshot": self.quote_snapshot,
            "customer_snapshot": self.customer_snapshot,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


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
    screw_option = db.Column(db.String(20), nullable=False, default="standard")
    screw_length_mm = db.Column(db.Integer, nullable=True)
    screw_supplement = db.Column(db.Float, nullable=False, default=0.0)
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
        screw_configuration = _serialize_screw_configuration(
            self.anclaje,
            self.screw_option,
            self.screw_length_mm,
            self.screw_supplement,
        )
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "alto": self.alto,
            "ancho": self.ancho,
            "anclaje": self.anclaje,
            "color": self.color,
            **screw_configuration,
            "precio_total": self.precio_total,
            "locator": self.order.locator if self.order else None,
            "invoice_number": self.order.invoice_number if self.order else None,
            "estimated_delivery_at": self.order.estimated_delivery_at.isoformat() if self.order and self.order.estimated_delivery_at else None,
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
    __table_args__ = (
        db.Index(
            "uq_invoices_one_ordinary_per_order",
            "order_id",
            unique=True,
            postgresql_where=text("invoice_type = 'ordinary' AND order_id IS NOT NULL"),
        ),
        db.Index(
            "ix_invoices_original_invoice_id",
            "original_invoice_id",
            unique=False,
        ),
        db.CheckConstraint(
            "("
            "invoice_type IS NULL AND original_invoice_id IS NULL AND "
            "rectification_type IS NULL AND rectification_reason IS NULL"
            ") OR ("
            "invoice_type = 'ordinary' AND original_invoice_id IS NULL AND "
            "rectification_type IS NULL AND rectification_reason IS NULL"
            ") OR ("
            "invoice_type = 'corrective' AND original_invoice_id IS NOT NULL AND "
            "original_invoice_id != id AND rectification_type IS NOT NULL AND "
            "rectification_reason IS NOT NULL"
            ")",
            name="ck_invoices_rectification_consistency",
        ),
        db.CheckConstraint(
            "invoice_type IS NULL OR invoice_type IN ('ordinary', 'corrective')",
            name="ck_invoices_invoice_type_valid",
        ),
        db.CheckConstraint(
            "rectification_type IS NULL OR rectification_type IN ('differences', 'substitution')",
            name="ck_invoices_rectification_type_valid",
        ),
        db.CheckConstraint(
            "rectification_reason IS NULL OR rectification_reason IN ("
            "'invoice_error', 'return', 'price_error', 'shipping_error', 'other')",
            name="ck_invoices_rectification_reason_valid",
        ),
        db.CheckConstraint(
            "rectification_aeat_type IS NULL OR rectification_aeat_type IN "
            "('R1', 'R2', 'R3', 'R4', 'R5')",
            name="ck_invoices_rectification_aeat_type_valid",
        ),
        db.CheckConstraint(
            "rectification_aeat_type IS NULL OR invoice_type = 'corrective'",
            name="ck_invoices_rectification_aeat_type_corrective_only",
        ),
        db.CheckConstraint(
            "original_invoice_id IS NULL OR original_invoice_id != id",
            name="ck_invoices_original_invoice_not_self",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False, unique=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    invoice_type = db.Column(db.String(20), nullable=True)
    original_invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    rectification_type = db.Column(db.String(30), nullable=True)
    rectification_reason = db.Column(db.String(50), nullable=True)
    rectification_aeat_type = db.Column(db.String(2), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    pdf_path = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Float, nullable=False)

    client_name = db.Column(db.String(255), nullable=False)
    client_address = db.Column(db.String(255), nullable=False)
    client_cif = db.Column(db.String(50), nullable=True)
    client_phone = db.Column(db.String(50), nullable=True)
    order_details = db.Column(db.JSON, nullable=False)
    invoice_snapshot = db.Column(db.JSON, nullable=True)
    invoice_snapshot_schema_version = db.Column(db.Integer, nullable=True)
    invoice_snapshot_hash = db.Column(db.String(64), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)
    issuance_source = db.Column(db.String(50), nullable=True)
    issued_by = db.Column(db.String(255), nullable=True)
    email_status = db.Column(db.String(20), nullable=True)
    email_sent_at = db.Column(db.DateTime, nullable=True)
    email_last_error = db.Column(db.Text, nullable=True)
    email_attempts = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    order = db.relationship('Orders', backref='invoice', lazy=True)
    original_invoice = db.relationship(
        'Invoices',
        remote_side=[id],
        foreign_keys=[original_invoice_id],
        backref=db.backref('corrective_invoices', lazy=True),
        lazy=True,
    )

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

    def serialize_summary(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "order_id": self.order_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": self.amount,
        }

    def serialize_admin(self):
        sale_accounting_entry = next(
            (
                entry for entry in (self.accounting_entries or [])
                if entry.entry_type == "sale"
            ),
            None,
        )

        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "order_id": self.order_id,
            "invoice_type": self.invoice_type,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "pdf_path": self.pdf_path,
            "pdf_available": bool(self.pdf_path),
            "amount": self.amount,
            "client_name": self.client_name,
            "client_address": self.client_address,
            "client_cif": self.client_cif,
            "client_phone": self.client_phone,
            "order_details": self.order_details,
            "invoice_snapshot_schema_version": self.invoice_snapshot_schema_version,
            "email_status": self.email_status,
            "email_sent_at": self.email_sent_at.isoformat() if self.email_sent_at else None,
            "email_attempts": self.email_attempts,
            "accounting_entry_id": sale_accounting_entry.id if sale_accounting_entry else None,
            "accounting_entry_status": sale_accounting_entry.status if sale_accounting_entry else None,
        }

    def serialize(self):
        return self.serialize_admin()


class InvoiceFiscalSubmission(db.Model):
    __tablename__ = "invoice_fiscal_submissions"
    __table_args__ = (
        db.UniqueConstraint(
            "invoice_id",
            "provider",
            "attempt_number",
            name="uq_invoice_fiscal_submissions_invoice_provider_attempt",
        ),
        db.Index(
            "ix_invoice_fiscal_submissions_invoice_id",
            "invoice_id",
            unique=False,
        ),
    )

    PROVIDER_VERIFACTU = "verifactu"

    STATUS_PENDING = "PENDING"
    STATUS_SENT = "SENT"
    STATUS_ACCEPTED = "ACCEPTED"
    STATUS_REJECTED = "REJECTED"
    STATUS_FAILED = "FAILED"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    provider = db.Column(db.String(30), nullable=False, default=PROVIDER_VERIFACTU)
    status = db.Column(db.String(30), nullable=False, default=STATUS_PENDING)
    attempt_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )
    submitted_at = db.Column(db.DateTime, nullable=True)
    response_at = db.Column(db.DateTime, nullable=True)
    request_payload = db.Column(db.JSON, nullable=True)
    response_payload = db.Column(db.JSON, nullable=True)
    response_code = db.Column(db.String(100), nullable=True)
    response_message = db.Column(db.Text, nullable=True)
    verification_csv = db.Column(db.String(255), nullable=True)
    verification_url = db.Column(db.String(500), nullable=True)
    external_reference = db.Column(db.String(255), nullable=True)
    error_type = db.Column(db.String(100), nullable=True)
    error_detail = db.Column(db.Text, nullable=True)

    invoice = db.relationship(
        'Invoices',
        backref=db.backref('fiscal_submissions', lazy=True),
        lazy=True,
    )

    def __repr__(self):
        return (
            f'<InvoiceFiscalSubmission invoice={self.invoice_id} '
            f'provider={self.provider} attempt={self.attempt_number} '
            f'status={self.status}>'
        )


class VeriFactuRecord(db.Model):
    __tablename__ = "verifactu_records"
    __table_args__ = (
        db.UniqueConstraint(
            "invoice_id",
            "record_type",
            name="uq_verifactu_records_invoice_record_type",
        ),
        db.UniqueConstraint(
            "fingerprint",
            name="uq_verifactu_records_fingerprint",
        ),
        db.UniqueConstraint(
            "chain_key",
            "chain_sequence",
            name="uq_verifactu_records_chain_sequence",
        ),
        db.Index(
            "ix_verifactu_records_invoice_id",
            "invoice_id",
            unique=False,
        ),
        db.Index(
            "ix_verifactu_records_chain_key_sequence",
            "chain_key",
            "chain_sequence",
            unique=False,
        ),
        db.Index(
            "ix_verifactu_records_previous_record_id",
            "previous_record_id",
            unique=True,
        ),
        db.CheckConstraint(
            "previous_record_id IS NULL OR previous_record_id != id",
            name="ck_verifactu_records_previous_not_self",
        ),
        db.CheckConstraint(
            "chain_sequence IS NULL OR chain_sequence >= 1",
            name="ck_verifactu_records_chain_sequence_positive",
        ),
        db.CheckConstraint(
            "status != 'READY' OR (chain_key IS NOT NULL AND chain_sequence IS NOT NULL AND fingerprint IS NOT NULL)",
            name="ck_verifactu_records_ready_chain_complete",
        ),
        db.CheckConstraint(
            "is_first_record IS NULL OR "
            "(is_first_record = true AND previous_record_id IS NULL AND chain_sequence = 1) OR "
            "(is_first_record = false AND previous_record_id IS NOT NULL AND chain_sequence > 1)",
            name="ck_verifactu_records_first_previous_coherent",
        ),
    )

    PROVIDER_VERIFACTU = "verifactu"
    MODE_VERIFACTU = "VERI*FACTU"

    RECORD_TYPE_ALTA = "alta"
    RECORD_TYPE_ANULACION = "anulacion"

    STATUS_BUILT = "BUILT"
    STATUS_READY = "READY"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    provider = db.Column(db.String(30), nullable=False, default=PROVIDER_VERIFACTU)
    mode = db.Column(db.String(30), nullable=False, default=MODE_VERIFACTU)
    record_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), nullable=False, default=STATUS_BUILT)
    schema_version = db.Column(db.Integer, nullable=False)
    invoice_number = db.Column(db.String(50), nullable=False)
    invoice_issued_at = db.Column(db.DateTime, nullable=False)
    invoice_snapshot_hash = db.Column(db.String(64), nullable=False)
    record_payload = db.Column(db.JSON, nullable=False)
    record_payload_hash = db.Column(db.String(64), nullable=False)
    official_payload = db.Column(db.JSON, nullable=True)
    official_payload_schema_version = db.Column(db.Integer, nullable=True)
    chain_key = db.Column(db.String(300), nullable=True)
    chain_sequence = db.Column(db.Integer, nullable=True)
    fingerprint = db.Column(db.String(128), nullable=True)
    fingerprint_algorithm = db.Column(db.String(100), nullable=True)
    fingerprint_status = db.Column(db.String(30), nullable=False, default="NOT_CALCULATED")
    fingerprint_input = db.Column(db.Text, nullable=True)
    fingerprint_calculated_at = db.Column(db.DateTime, nullable=True)
    previous_record_id = db.Column(db.Integer, db.ForeignKey('verifactu_records.id'), nullable=True)
    previous_fingerprint = db.Column(db.String(128), nullable=True)
    is_first_record = db.Column(db.Boolean, nullable=True)
    system_id = db.Column(db.String(100), nullable=False)
    software_name = db.Column(db.String(120), nullable=False)
    software_version = db.Column(db.String(50), nullable=False)
    installation_id = db.Column(db.String(100), nullable=True)
    producer_name = db.Column(db.String(120), nullable=True)
    producer_tax_id = db.Column(db.String(50), nullable=True)
    generation_timestamp = db.Column(db.DateTime, nullable=True)
    generation_timezone = db.Column(db.String(50), nullable=True)
    ready_at = db.Column(db.DateTime, nullable=True)
    issuer_tax_id = db.Column(db.String(50), nullable=False)
    recipient_tax_id = db.Column(db.String(50), nullable=True)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    invoice = db.relationship(
        'Invoices',
        backref=db.backref('verifactu_records', lazy=True),
        lazy=True,
    )
    previous_record = db.relationship(
        'VeriFactuRecord',
        remote_side=[id],
        lazy=True,
    )

    def __repr__(self):
        return (
            f'<VeriFactuRecord invoice={self.invoice_id} '
            f'type={self.record_type} status={self.status}>'
        )


class VeriFactuChainState(db.Model):
    __tablename__ = "verifactu_chain_states"
    __table_args__ = (
        db.UniqueConstraint(
            "chain_key",
            name="uq_verifactu_chain_states_chain_key",
        ),
        db.Index(
            "ix_verifactu_chain_states_chain_key",
            "chain_key",
            unique=False,
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    chain_key = db.Column(db.String(300), nullable=False)
    issuer_tax_id = db.Column(db.String(50), nullable=False)
    provider = db.Column(db.String(30), nullable=False, default=VeriFactuRecord.PROVIDER_VERIFACTU)
    mode = db.Column(db.String(30), nullable=False, default=VeriFactuRecord.MODE_VERIFACTU)
    system_id = db.Column(db.String(100), nullable=False)
    installation_id = db.Column(db.String(100), nullable=False)
    producer_tax_id = db.Column(db.String(50), nullable=False)
    last_record_id = db.Column(db.Integer, db.ForeignKey('verifactu_records.id'), nullable=True)
    last_fingerprint = db.Column(db.String(128), nullable=True)
    next_sequence = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    last_record = db.relationship(
        'VeriFactuRecord',
        foreign_keys=[last_record_id],
        lazy=True,
    )

    def __repr__(self):
        return (
            f'<VeriFactuChainState chain={self.chain_key} '
            f'next={self.next_sequence}>'
        )


class AccountingEntry(db.Model):
    __tablename__ = "accounting_entries"
    __table_args__ = (
        db.UniqueConstraint(
            "invoice_id",
            "entry_type",
            name="uq_accounting_entries_invoice_entry_type",
        ),
        db.Index(
            "ix_accounting_entries_invoice_id",
            "invoice_id",
            unique=False,
        ),
    )

    ENTRY_TYPE_SALE = "sale"

    STATUS_PENDING = "pending"
    STATUS_RECORDED = "recorded"
    STATUS_FAILED = "failed"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    entry_type = db.Column(db.String(30), nullable=False, default=ENTRY_TYPE_SALE)
    status = db.Column(db.String(30), nullable=False, default=STATUS_PENDING)
    invoice_number = db.Column(db.String(50), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    customer_name = db.Column(db.String(255), nullable=False)
    customer_tax_id = db.Column(db.String(50), nullable=True)
    taxable_base = db.Column(db.Numeric(12, 2), nullable=False)
    vat_amount = db.Column(db.Numeric(12, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    payment_provider = db.Column(db.String(30), nullable=True)
    order_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )
    recorded_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    invoice = db.relationship(
        'Invoices',
        backref=db.backref('accounting_entries', lazy=True),
        lazy=True,
    )

    def __repr__(self):
        return (
            f'<AccountingEntry invoice={self.invoice_id} '
            f'type={self.entry_type} status={self.status}>'
        )


class SupplierInvoice(db.Model):
    """A supplier document registered independently from sales invoices."""

    __tablename__ = "supplier_invoices"
    __table_args__ = (
        db.Index(
            "ix_supplier_invoices_supplier_tax_id_invoice_number",
            "supplier_tax_id",
            "supplier_invoice_number",
            unique=False,
        ),
        db.CheckConstraint(
            "status IN ('draft', 'needs_review', 'registered', 'cancelled')",
            name="ck_supplier_invoices_status_valid",
        ),
        db.CheckConstraint(
            "currency = 'EUR'",
            name="ck_supplier_invoices_currency_eur",
        ),
        db.CheckConstraint(
            "supplier_country_code = 'ES'",
            name="ck_supplier_invoices_country_es",
        ),
        db.CheckConstraint(
            "supplier_tax_id_type = 'NIF'",
            name="ck_supplier_invoices_tax_id_type_nif",
        ),
        db.CheckConstraint(
            "fiscal_invoice_type = 'F1'",
            name="ck_supplier_invoices_fiscal_type_f1",
        ),
        db.CheckConstraint(
            "tax_treatment = 'domestic_standard'",
            name="ck_supplier_invoices_tax_treatment_domestic_standard",
        ),
        db.CheckConstraint(
            "reception_number IS NULL OR reception_number >= 1",
            name="ck_supplier_invoices_reception_number_positive",
        ),
        db.CheckConstraint(
            "status != 'registered' OR ("
            "reception_number IS NOT NULL AND registered_at IS NOT NULL AND "
            "fiscal_snapshot IS NOT NULL AND snapshot_schema_version IN (1, 2) AND "
            "snapshot_hash IS NOT NULL"
            ")",
            name="ck_supplier_invoices_registered_snapshot_complete",
        ),
        db.CheckConstraint(
            "aeat_expense_concept_code IS NULL OR "
            "aeat_expense_concept_code IN ('G01', 'G03', 'G22', 'G24')",
            name="ck_supplier_invoices_aeat_expense_concept_code_valid",
        ),
        db.CheckConstraint(
            "expense_deductible_amount IS NULL OR expense_deductible_amount >= 0",
            name="ck_supplier_invoices_expense_deductible_amount_nonnegative",
        ),
    )

    STATUS_DRAFT = "draft"
    STATUS_NEEDS_REVIEW = "needs_review"
    STATUS_REGISTERED = "registered"
    STATUS_CANCELLED = "cancelled"

    id = db.Column(db.Integer, primary_key=True)
    supplier_legal_name = db.Column(db.String(255), nullable=True)
    supplier_tax_id = db.Column(db.String(50), nullable=True)
    supplier_country_code = db.Column(db.String(2), nullable=False, default="ES", server_default="ES")
    supplier_tax_id_type = db.Column(db.String(20), nullable=False, default="NIF", server_default="NIF")
    supplier_invoice_number = db.Column(db.String(100), nullable=True)
    reception_number = db.Column(db.Integer, nullable=True, unique=True)
    issue_date = db.Column(db.Date, nullable=True)
    operation_date = db.Column(db.Date, nullable=True)
    received_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    registered_at = db.Column(db.DateTime, nullable=True)
    registered_by = db.Column(db.String(255), nullable=True)
    concept = db.Column(db.Text, nullable=True)
    currency = db.Column(db.String(3), nullable=False, default="EUR", server_default="EUR")
    total_amount = db.Column(db.Numeric(12, 2), nullable=True)

    fiscal_invoice_type = db.Column(db.String(10), nullable=False, default="F1", server_default="F1")
    tax_treatment = db.Column(
        db.String(40),
        nullable=False,
        default="domestic_standard",
        server_default="domestic_standard",
    )
    special_regime_key = db.Column(db.String(20), nullable=True)
    aeat_expense_concept_code = db.Column(db.String(3), nullable=True)
    expense_deductible_amount = db.Column(db.Numeric(12, 2), nullable=True)
    status = db.Column(db.String(30), nullable=False, default=STATUS_DRAFT, server_default=STATUS_DRAFT)
    source = db.Column(db.String(30), nullable=False, default="manual", server_default="manual")
    fiscal_snapshot = db.Column(db.JSON, nullable=True)
    snapshot_schema_version = db.Column(db.Integer, nullable=True)
    snapshot_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )
    documents = db.relationship(
        "SupplierInvoiceDocument",
        back_populates="supplier_invoice",
        lazy=True,
    )

    def __repr__(self):
        return f"<SupplierInvoice id={self.id} reception={self.reception_number} status={self.status}>"


class SupplierInvoiceTaxBreakdown(db.Model):
    __tablename__ = "supplier_invoice_tax_breakdowns"
    __table_args__ = (
        db.UniqueConstraint(
            "supplier_invoice_id",
            "position",
            name="uq_supplier_invoice_tax_breakdowns_position",
        ),
        db.CheckConstraint("position >= 1", name="ck_supplier_invoice_tax_breakdowns_position_positive"),
        db.CheckConstraint("tax_base >= 0", name="ck_supplier_invoice_tax_breakdowns_tax_base_nonnegative"),
        db.CheckConstraint("tax_rate >= 0", name="ck_supplier_invoice_tax_breakdowns_tax_rate_nonnegative"),
        db.CheckConstraint("tax_amount >= 0", name="ck_supplier_invoice_tax_breakdowns_tax_amount_nonnegative"),
        db.CheckConstraint(
            "deductible_tax_amount >= 0 AND deductible_tax_amount <= tax_amount",
            name="ck_supplier_invoice_tax_breakdowns_deductible_valid",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    supplier_invoice_id = db.Column(db.Integer, db.ForeignKey("supplier_invoices.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    tax_base = db.Column(db.Numeric(12, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=False)
    deductible_tax_amount = db.Column(db.Numeric(12, 2), nullable=False)
    supplier_invoice = db.relationship(
        "SupplierInvoice",
        backref=db.backref("tax_breakdowns", lazy=True),
        lazy=True,
    )

    def __repr__(self):
        return f"<SupplierInvoiceTaxBreakdown invoice={self.supplier_invoice_id} position={self.position}>"


class SupplierInvoiceDocument(db.Model):
    """Private source document uploaded for a supplier invoice draft."""

    __tablename__ = "supplier_invoice_documents"
    __table_args__ = (
        db.Index(
            "ix_supplier_invoice_documents_sha256",
            "sha256",
            unique=False,
        ),
        db.Index(
            "ix_supplier_invoice_documents_supplier_invoice_id",
            "supplier_invoice_id",
            unique=False,
        ),
        db.CheckConstraint(
            "storage_provider IN ('r2')",
            name="ck_supplier_invoice_documents_storage_provider_valid",
        ),
        db.CheckConstraint(
            "file_size > 0",
            name="ck_supplier_invoice_documents_file_size_positive",
        ),
        db.CheckConstraint(
            "processing_status IN ('uploaded', 'extracting', 'extracted', 'needs_review', 'failed', 'applied', 'deleting', 'delete_failed')",
            name="ck_supplier_invoice_documents_processing_status_valid",
        ),
        db.CheckConstraint(
            "sha256 <> ''",
            name="ck_supplier_invoice_documents_sha256_present",
        ),
        db.CheckConstraint(
            "storage_key <> ''",
            name="ck_supplier_invoice_documents_storage_key_present",
        ),
    )

    STATUS_UPLOADED = "uploaded"
    STATUS_EXTRACTING = "extracting"
    STATUS_EXTRACTED = "extracted"
    STATUS_NEEDS_REVIEW = "needs_review"
    STATUS_FAILED = "failed"
    STATUS_APPLIED = "applied"
    STATUS_DELETING = "deleting"
    STATUS_DELETE_FAILED = "delete_failed"

    id = db.Column(db.Integer, primary_key=True)
    supplier_invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_invoices.id", ondelete="RESTRICT"),
        nullable=True,
    )
    storage_provider = db.Column(db.String(20), nullable=False)
    storage_key = db.Column(db.String(255), nullable=False, unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    sha256 = db.Column(db.String(64), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    uploaded_by = db.Column(db.String(255), nullable=True)
    processing_status = db.Column(
        db.String(30),
        nullable=False,
        default=STATUS_UPLOADED,
        server_default=STATUS_UPLOADED,
    )
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )
    supplier_invoice = db.relationship(
        "SupplierInvoice",
        back_populates="documents",
        lazy=True,
    )
    extractions = db.relationship(
        "SupplierInvoiceExtraction",
        back_populates="supplier_invoice_document",
        lazy=True,
    )

    def __repr__(self):
        return f"<SupplierInvoiceDocument id={self.id} invoice={self.supplier_invoice_id}>"


class SupplierInvoiceExtraction(db.Model):
    """A non-fiscal, reviewable proposal extracted from a private source document."""

    __tablename__ = "supplier_invoice_extractions"
    __table_args__ = (
        db.Index(
            "ix_supplier_invoice_extractions_document_id",
            "supplier_invoice_document_id",
            unique=False,
        ),
        db.CheckConstraint(
            "status IN ('extracting', 'extracted', 'needs_review', 'failed', 'applied')",
            name="ck_supplier_invoice_extractions_status_valid",
        ),
        db.CheckConstraint(
            "status NOT IN ('extracted', 'needs_review', 'applied') OR ("
            "extraction_payload IS NOT NULL AND payload_hash IS NOT NULL AND completed_at IS NOT NULL"
            ")",
            name="ck_supplier_invoice_extractions_completed_payload_present",
        ),
        db.CheckConstraint(
            "status != 'failed' OR completed_at IS NOT NULL",
            name="ck_supplier_invoice_extractions_failed_completed",
        ),
    )

    STATUS_EXTRACTING = "extracting"
    STATUS_EXTRACTED = "extracted"
    STATUS_NEEDS_REVIEW = "needs_review"
    STATUS_FAILED = "failed"
    STATUS_APPLIED = "applied"

    id = db.Column(db.Integer, primary_key=True)
    supplier_invoice_document_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_invoice_documents.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider = db.Column(db.String(50), nullable=False)
    extractor_version = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), nullable=False, default=STATUS_EXTRACTING)
    payload_schema_version = db.Column(db.Integer, nullable=False, default=1)
    extraction_payload = db.Column(db.JSON, nullable=True)
    payload_hash = db.Column(db.String(64), nullable=True)
    started_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    completed_at = db.Column(db.DateTime, nullable=True)
    error_code = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    supplier_invoice_document = db.relationship(
        "SupplierInvoiceDocument",
        back_populates="extractions",
        lazy=True,
    )

    def __repr__(self):
        return (
            f"<SupplierInvoiceExtraction id={self.id} "
            f"document={self.supplier_invoice_document_id} status={self.status}>"
        )


class SupplierInvoiceReceptionSequence(db.Model):
    """Singleton row locked while assigning internal receipt numbers."""

    __tablename__ = "supplier_invoice_reception_sequences"
    __table_args__ = (
        db.CheckConstraint("last_number >= 0", name="ck_supplier_invoice_reception_sequences_last_number_nonnegative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    last_number = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )


class InvoiceSequence(db.Model):
    __tablename__ = "invoice_sequences"
    __table_args__ = (
        db.UniqueConstraint(
            "series",
            "fiscal_year",
            name="uq_invoice_sequences_series_fiscal_year",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    series = db.Column(db.String(10), nullable=False)
    fiscal_year = db.Column(db.Integer, nullable=False)
    # last_number = ultimo numero fiscal confirmado dentro de una transaccion.
    # El siguiente numero fiscal sera last_number + 1.
    last_number = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    def __repr__(self):
        return f'<InvoiceSequence {self.series}-{self.fiscal_year}: {self.last_number}>'


class Favorites(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    # 🔗 Relaciones
    usuario = db.relationship('Users', backref='favorites')
    producto = db.relationship('Products')

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
    screw_option = db.Column(db.String(20), nullable=False, default="standard")
    screw_length_mm = db.Column(db.Integer, nullable=True)
    screw_supplement = db.Column(db.Float, nullable=False, default=0.0)
    precio_total = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)  
    added_at = db.Column(db.DateTime, nullable=False)
    user = db.relationship('Users', backref='cart_items', lazy=True)
    product = db.relationship('Products', backref='cart_items', lazy=True)

    def serialize(self):
        screw_configuration = _serialize_screw_configuration(
            self.anclaje,
            self.screw_option,
            self.screw_length_mm,
            self.screw_supplement,
        )
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
            **screw_configuration,
            "precio_total": self.precio_total,
            "quantity": self.quantity,
            "added_at": self.added_at,
            "available_for_sale": self.product.available_for_sale,
        }


@event.listens_for(Products, 'before_insert')
@event.listens_for(Products, 'before_update')
def validate_product_lifecycle(mapper, connection, target):
    published = True if target.published is None else target.published
    available_for_sale = (
        True if target.available_for_sale is None else target.available_for_sale
    )
    if not published and available_for_sale:
        raise ValueError(
            "A product cannot be available for sale when it is not published."
        )


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

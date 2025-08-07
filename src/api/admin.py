import os
from flask import request, Response
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from wtforms.fields import SelectField, StringField
from .models import (
    db, Users, Products, ProductImages,
    Categories, Subcategories, Cart,
    Orders, OrderDetails, Favorites,
    Posts, Comments, Invoices, DeliveryEstimateConfig
)
from api.email_routes import send_order_status_email

# Credenciales desde ENV
ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PW   = os.getenv('ADMIN_PW')

# Vista principal protegida
class SecureAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        auth = request.authorization or {}
        if auth.get('username') != ADMIN_USER or auth.get('password') != ADMIN_PW:
            return Response(
                'Login required', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )
        return super().index()

# ModelView seguro
class SecureModelView(ModelView):
    def is_accessible(self):
        auth = request.authorization or {}
        return auth.get('username') == ADMIN_USER and auth.get('password') == ADMIN_PW

    def inaccessible_callback(self, name, **kwargs):
        return Response(
            'Login required', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'}
        )

# Vistas personalizadas
class ProductAdminView(SecureModelView):
    form_extra_fields = {
        'categoria_id': SelectField('Categoría', choices=[])
    }
    def on_form_prefill(self, form, id):
        form.categoria_id.choices = [(c.id, c.nombre) for c in Categories.query.all()]
    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.categoria_id.choices = [(c.id, c.nombre) for c in Categories.query.all()]
        return form
    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        form.categoria_id.choices = [(c.id, c.nombre) for c in Categories.query.all()]
        return form

class OrderAdminView(SecureModelView):
    form_columns = ['user_id', 'total_amount', 'order_date', 'invoice_number', 'locator', 'order_status']
    column_list =  ['id', 'user_id', 'total_amount', 'order_date', 'invoice_number', 'locator', 'order_status']
    column_editable_list = ['total_amount', 'order_status']

    form_extra_fields = {
        'invoice_number': StringField('Número de Factura', render_kw={'readonly': True}),
        'locator': StringField('Localizador', render_kw={'readonly': True}),
        'order_status': SelectField(
            'Estado del Pedido',
            choices=[
                ('pendiente', 'Pendiente'),
                ('fabricacion', 'En fabricación'),
                ('pintura', 'En pintura'),
                ('embalaje', 'En embalaje'),
                ('enviado', 'Enviado'),
                ('entregado', 'Entregado')
            ]
        )
    }

    def create_form(self, obj=None):
        form = super().create_form(obj)
        if not form.invoice_number.data:
            form.invoice_number.data = Orders.generate_next_invoice_number()
        if not form.locator.data:
            form.locator.data = Orders.generate_locator()
        return form

    def on_model_change(self, form, model, is_created):
        if not is_created:
            original = Orders.query.get(model.id)
            if original.order_status != model.order_status:
                send_order_status_email(
                    user_email=model.user.email,
                    order_status=model.order_status,
                    locator=model.locator
                )


class CartAdminView(SecureModelView):
    column_list = ('usuario_email', 'product_display', 'alto', 'ancho', 'anclaje', 'color', 'quantity', 'precio_total', 'added_at')

    column_labels = {
        'usuario_email': 'Usuario (Email)',
        'product_display': 'Producto',
        'alto': 'Alto',
        'ancho': 'Ancho',
        'anclaje': 'Anclaje',
        'color': 'Color',
        'quantity': 'Ud.',
        'precio_total': 'Precio Total',
        'added_at': 'Añadido el'
    }

    form_columns = ['usuario_id', 'producto_id', 'alto', 'ancho', 'anclaje', 'color', 'quantity', 'precio_total', 'added_at']
    column_formatters = {
        'usuario_email': lambda v, c, m, p: m.user.email if m.user else 'Sin usuario',
        'precio_total': lambda v, c, m, p: f"{(m.precio_total * m.quantity):.2f} €" if m.precio_total and m.quantity else '0.00 €',
        'product_display': lambda v, c, m, p: m.product.nombre if m.product else f'ID {m.producto_id}',
        'added_at': lambda v, c, m, p: m.added_at.strftime("%d/%m/%Y %H:%M") if m.added_at else ''
    }

    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()
        if 'usuario_email' not in columns:
            columns.append('usuario_email')
        if 'product_display' not in columns:
            columns.append('product_display')
        return columns

    column_default_sort = ('added_at', True)

class OrderDetailsAdminView(SecureModelView):
    column_list = [
        'order_id', 'locator', 'cliente', 'product_name',
        'quantity', 'alto', 'ancho', 'anclaje', 'color',
        'precio_total'
    ]

    column_labels = {
        'order_id': 'Pedido ID',
        'locator': 'Localizador',
        'cliente': 'Cliente',
        'product_name': 'Producto',
        'quantity': 'Ud.',
        'alto': 'Alto',
        'ancho': 'Ancho',
        'anclaje': 'Anclaje',
        'color': 'Color',
        'precio_total': 'Precio Total'
    }

    column_formatters = {
        'locator': lambda v, c, m, p: m.order.locator if m.order else '',
        'cliente': lambda v, c, m, p: f"{m.order.user.email}" if m.order and m.order.user else '',
        'product_name': lambda v, c, m, p: m.product.nombre if m.product else '',
        'precio_total': lambda v, c, m, p: f"{m.precio_total * m.quantity:.2f} €" if m.precio_total and m.quantity else '0.00 €'
    }

    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()
        if 'locator' not in columns:
            columns.append('locator')
        if 'cliente' not in columns:
            columns.append('cliente')
        if 'product_name' not in columns:
            columns.append('product_name')
        return columns

    column_default_sort = ('order_id', True)


class InvoiceAdminView(SecureModelView):
    form_columns = ['invoice_number','client_name','client_address','client_cif','amount','order_id','created_at']
    column_list    = ['id','invoice_number','client_name','amount','created_at','order_id']
    column_editable_list = ['client_name','client_address','client_cif','amount']
    form_extra_fields = {
        'invoice_number': StringField('Número de Factura', render_kw={'readonly': True})
    }
    def create_form(self, obj=None):
        form = super().create_form(obj)
        if not form.invoice_number.data:
            form.invoice_number.data = Invoices.generate_next_invoice_number()
        return form

def setup_admin(app):
    # Secret key y tema
    app.secret_key = os.getenv('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'sandstone'

    # Monta Flask-Admin en /admin
    admin = Admin(
        app,
        name='MetalWolft.com',
        index_view=SecureAdminIndexView(),
        template_mode='bootstrap3',
        url='/admin'
    )

    # Registra vistas
    admin.add_view(SecureModelView(Users, db.session))
    admin.add_view(SecureModelView(Categories, db.session))
    admin.add_view(SecureModelView(Subcategories, db.session))
    admin.add_view(ProductAdminView(Products, db.session))
    admin.add_view(SecureModelView(ProductImages, db.session))
    admin.add_view(CartAdminView(Cart, db.session))
    admin.add_view(OrderAdminView(Orders, db.session))
    admin.add_view(OrderDetailsAdminView(OrderDetails, db.session))
    admin.add_view(SecureModelView(Favorites, db.session))
    admin.add_view(SecureModelView(Posts, db.session))
    admin.add_view(SecureModelView(Comments, db.session))
    admin.add_view(InvoiceAdminView(Invoices, db.session))
    admin.add_view(ModelView(DeliveryEstimateConfig, db.session))

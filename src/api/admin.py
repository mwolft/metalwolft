import os
from flask import request, Response
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from wtforms.fields import SelectField, StringField
from .models import (
    db, Users, Products, ProductImages,
    Categories, Subcategories, Cart,
    Orders, OrderDetails, Favorites,
    Posts, Comments, Invoices
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
    admin.add_view(SecureModelView(Cart, db.session))
    admin.add_view(OrderAdminView(Orders, db.session))
    admin.add_view(SecureModelView(OrderDetails, db.session))
    admin.add_view(SecureModelView(Favorites, db.session))
    admin.add_view(SecureModelView(Posts, db.session))
    admin.add_view(SecureModelView(Comments, db.session))
    admin.add_view(InvoiceAdminView(Invoices, db.session))

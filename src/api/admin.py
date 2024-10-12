import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms.fields import SelectField, StringField
from .models import db, Users, Products, ProductImages, Categories, Cart, Orders, OrderDetails, Favorites


class ProductAdminView(ModelView):
    # Modificar el formulario para seleccionar la categoría
    form_extra_fields = {
        'categoria_id': SelectField('Categoría', choices=[])
    }

    def on_form_prefill(self, form, id):
        form.categoria_id.choices = [(c.id, c.nombre) for c in Categories.query.all()]

    def create_form(self, obj=None):
        form = super(ProductAdminView, self).create_form(obj)
        form.categoria_id.choices = [(c.id, c.nombre) for c in Categories.query.all()]
        return form

    def edit_form(self, obj=None):
        form = super(ProductAdminView, self).edit_form(obj)
        form.categoria_id.choices = [(c.id, c.nombre) for c in Categories.query.all()]
        return form


class OrderAdminView(ModelView):
    # Mostrar los campos de factura y localizador como de solo lectura
    form_columns = ['user_id', 'total_amount', 'order_date', 'invoice_number', 'locator']
    column_list = ['id', 'user_id', 'total_amount', 'order_date', 'invoice_number', 'locator']
    column_editable_list = ['total_amount']
    form_extra_fields = {
        'invoice_number': StringField('Número de Factura', render_kw={'readonly': True}),
        'locator': StringField('Localizador', render_kw={'readonly': True})
    }

    def create_form(self, obj=None):
        form = super(OrderAdminView, self).create_form(obj)
        if not form.invoice_number.data:
            form.invoice_number.data = Orders.generate_invoice_number()
        if not form.locator.data:
            form.locator.data = Orders.generate_locator()
        return form


def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'sandstone'
    admin = Admin(app, name='MetalWolft.com', template_mode='bootstrap3')

    # Agregar vistas personalizadas para los modelos
    admin.add_view(ModelView(Users, db.session))
    admin.add_view(ModelView(Categories, db.session))
    admin.add_view(ProductAdminView(Products, db.session))
    admin.add_view(ModelView(ProductImages, db.session))
    admin.add_view(ModelView(Cart, db.session))
    admin.add_view(OrderAdminView(Orders, db.session))  # Vista personalizada para Orders
    admin.add_view(ModelView(OrderDetails, db.session))
    admin.add_view(ModelView(Favorites, db.session))

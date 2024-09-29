import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms.fields import SelectField
from .models import db, Users, Products, Categories, Orders, OrderDetails


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


def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'darkly'  # Dark theme, for light theme use 'cerulean'
    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')
    
    # Agregar vistas personalizadas para los modelos
    admin.add_view(ModelView(Users, db.session))
    admin.add_view(ModelView(Categories, db.session))
    admin.add_view(ProductAdminView(Products, db.session))
    admin.add_view(ModelView(Orders, db.session))
    admin.add_view(ModelView(OrderDetails, db.session))

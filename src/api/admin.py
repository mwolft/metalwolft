import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from .models import db, Users, Orders, OrderDetails


def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'darkly'  # Dark theme, for light theme use 'cerulean'
    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')
    admin.add_view(ModelView(Users, db.session)) 
    admin.add_view(ModelView(Orders, db.session)) 
    admin.add_view(ModelView(OrderDetails, db.session)) 
    
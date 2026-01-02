import os
from flask import request, Response, current_app
from flask_admin import Admin, AdminIndexView, expose
from markupsafe import Markup
from flask_admin.contrib.sqla import ModelView
from wtforms.fields import SelectField, StringField, DateField, TextAreaField
from .models import (
    db, Users, Products, ProductImages,
    Categories, Subcategories, Cart,
    Orders, OrderDetails, Favorites,
    Posts, Comments, Invoices, DeliveryEstimateConfig
)
from api.email_routes import send_order_status_email
from datetime import timedelta
from sqlalchemy import inspect 


# Credenciales desde ENV
ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PW   = os.getenv('ADMIN_PW')


# ========================== VISTA PRINCIPAL PROTEGIDA (ÚNICA) ==========================
class SecureAdminIndexView(AdminIndexView):

    def is_accessible(self):
        auth = request.authorization or {}
        return (
            auth.get('username') == ADMIN_USER and
            auth.get('password') == ADMIN_PW
        )

    def inaccessible_callback(self, name, **kwargs):
        return Response(
            'Login required',
            401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'}
        )

    @expose('/')
    def index(self=None, **kwargs):
        self = self or kwargs.get('cls')


        from datetime import datetime, timezone, timedelta
        from sqlalchemy import func, extract

        products_count = db.session.scalar(
            db.select(func.count(Products.id))
        ) or 0

        invoices_count = db.session.scalar(
            db.select(func.count(Invoices.id))
        ) or 0

        users_count = db.session.scalar(
            db.select(func.count(Users.id))
        ) or 0

        orders_count = db.session.scalar(
            db.select(func.count(Orders.id))
        ) or 0

        avg_ticket = db.session.scalar(
            db.select(func.avg(Orders.total_amount))
            .where(Orders.total_amount.isnot(None))
        ) or 0

        now = datetime.now(timezone.utc)
        current_year = 2025

        hace_30 = now - timedelta(days=30)
        hace_60 = now - timedelta(days=60)

        ingresos_30d = db.session.scalar(
            db.select(func.sum(Orders.total_amount))
            .where(Orders.order_date.isnot(None))
            .where(Orders.order_date >= hace_30)
            .where(Orders.order_date <= now)
        ) or 0

        ingresos_previos_30d = db.session.scalar(
            db.select(func.sum(Orders.total_amount))
            .where(Orders.order_date.isnot(None))
            .where(Orders.order_date >= hace_60)
            .where(Orders.order_date < hace_30)
        ) or 0

        if ingresos_previos_30d > 0:
            variacion_porcentual = (
                (ingresos_30d - ingresos_previos_30d) / ingresos_previos_30d
            ) * 100
            variacion_label = f"{variacion_porcentual:.2f}%"
            variacion_up = variacion_porcentual >= 0
            variacion_es_nueva = False
        else:
            if ingresos_30d > 0:
                variacion_porcentual = None
                variacion_label = "nuevo"
                variacion_up = True
                variacion_es_nueva = True
            else:
                variacion_porcentual = 0.0
                variacion_label = "0.00%"
                variacion_up = False
                variacion_es_nueva = False

        rows = db.session.execute(
            db.select(
                extract('month', Orders.order_date).label('month'),
                func.sum(Orders.total_amount).label('total')
            )
            .where(Orders.order_date.isnot(None))
            .where(extract('year', Orders.order_date) == current_year)
            .group_by('month')
            .order_by('month')
        ).all()

        monthly_sales = {m: 0 for m in range(1, 13)}
        for r in rows:
            monthly_sales[int(r.month)] = float(r.total or 0)

        monthly_sales_current = [monthly_sales[m] for m in range(1, 13)]

        rows_users = db.session.execute(
            db.select(
                extract('month', Users.created_at).label('month'),
                func.count(Users.id).label('total')
            )
            .where(Users.created_at.isnot(None))
            .where(extract('year', Users.created_at) == current_year)
            .group_by('month')
            .order_by('month')
        ).all()

        monthly_users = {m: 0 for m in range(1, 13)}
        for r in rows_users:
            monthly_users[int(r.month)] = int(r.total or 0)

        users_monthly_values = [monthly_users[m] for m in range(1, 13)]


        monthly_sales_labels = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]

        recent_orders = db.session.execute(
            db.select(Orders).order_by(Orders.id.desc()).limit(10)
        ).scalars().all()

        recent_invoices = db.session.execute(
            db.select(Invoices).order_by(Invoices.id.desc()).limit(10)
        ).scalars().all()

        def tz_es(dt):
            if not dt:
                return ""
            return (dt + timedelta(hours=2)).strftime("%d/%m %H:%M")

        return self.render(
            'admin/dashboard.html',
            admin_view=self,
            metrics={
                'products_count': products_count,
                'orders_count': orders_count,
                'invoices_count': invoices_count,
                'users_count': users_count,
                'avg_ticket': avg_ticket,
                'ingresos_30d': ingresos_30d,
                'variacion_porcentual': variacion_porcentual,
                'variacion_label': variacion_label,
                'variacion_up': variacion_up,
                'variacion_es_nueva': variacion_es_nueva,
            },
            recent_orders=recent_orders,
            recent_invoices=recent_invoices,
            monthly_sales_labels=monthly_sales_labels,
            monthly_sales_values=monthly_sales_current,
            users_monthly_values=users_monthly_values,
            current_year=current_year,
            tz_es=tz_es
        )


# ========================== BASE SEGURA PARA MODELOS ==========================
class SecureModelView(ModelView):
    def is_accessible(self):
        auth = request.authorization or {}
        return auth.get('username') == ADMIN_USER and auth.get('password') == ADMIN_PW

    def inaccessible_callback(self, name, **kwargs):
        return Response('Login required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


# ========================== SAFE MODEL VIEW (CON PAPELERA Y MASIVO) ==========================
class SafeModelView(SecureModelView):
    """
    Igual que SecureModelView pero con icono de borrar por fila
    y borrado masivo habilitado.
    """
    can_delete = True
    action_disallowed_list = []   # asegura que 'delete' esté permitido


# ========================== VISTAS ==========================
class UsersAdminView(SafeModelView):
    column_default_sort = ('id', True)  # DESC
    column_sortable_list = ('id', 'email')
    column_searchable_list = ('email',)
    column_list = (
        'id',
        'email',
        'firstname',
        'lastname',
        'is_active',
        'is_admin',
        'shipping_address',
        'shipping_city',
        'shipping_postal_code',
        'billing_address',
        'billing_city',
        'billing_postal_code',
        'CIF',
    )
    form_excluded_columns = ('password', 'orders', 'favorites', 'cart')

    column_formatters = {
        'email': lambda v, c, m, p: Markup(f'<a href="mailto:{m.email}">{m.email}</a>') if m.email else ''
    }


class ProductAdminView(SafeModelView):
    column_sortable_list = ('id', 'sort_order', 'nombre', 'precio', 'precio_rebajado', 'categoria_id')  # 👈 AÑADIDO

    column_searchable_list = ('nombre',)
    column_filters = ('categoria_id',)
    page_size = 50
    can_set_page_size = True

    form_columns = [
        'nombre',
        'slug',
        'sort_order',        
        'categoria_id',
        'subcategoria',
        'descripcion',
        'descripcion_seo',
        'titulo_seo',
        'h1_seo',
        'precio',
        'precio_rebajado',
        'porcentaje_rebaja',
        'has_abatible',
        'has_door_model',
        'es_mas_vendido',
        'es_nuevo_diseno',
        'imagen'
    ]

    PRIORITY_CATEGORY_NAMES = ['rejas', 'rejas para ventanas']

    def _priority_category_ids(self):
        q = Categories.query.with_entities(Categories.id, Categories.nombre)
        ids = []
        for cid, nombre in q:
            nom = (nombre or '').lower()
            if any(token in nom for token in self.PRIORITY_CATEGORY_NAMES):
                ids.append(cid)
        return ids

    def get_query(self):
        """
        Orden final:
        1. sort_order ASC (orden manual)
        2. prioridad categorías
        3. categoria_id ASC
        4. nombre ASC
        5. id ASC
        """
        from sqlalchemy import case
        ids = self._priority_category_ids() or [-1]
        priority = case((Products.categoria_id.in_(ids), 0), else_=1)

        return (
            super().get_query()
            .order_by(
                Products.sort_order.asc(),   
                priority.asc(),
                Products.categoria_id.asc(),
                Products.nombre.asc(),
                Products.id.asc()
            )
        )

    def get_count_query(self):
        return super().get_count_query()

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

    column_formatters = {
        'descripcion': lambda v, c, m, p: (m.descripcion[:30] + '…') if m.descripcion and len(m.descripcion) > 30 else (m.descripcion or ''),
        'descripcion_seo': lambda v, c, m, p: (m.descripcion_seo[:30] + '…') if m.descripcion_seo and len(m.descripcion_seo) > 30 else (m.descripcion_seo or ''),
        'titulo_seo': lambda v, c, m, p: (m.titulo_seo[:30] + '…') if m.titulo_seo and len(m.titulo_seo) > 30 else (m.titulo_seo or ''),
        'h1_seo': lambda v, c, m, p: (m.h1_seo[:30] + '…') if m.h1_seo and len(m.h1_seo) > 30 else (m.h1_seo or ''),
    }


class OrderAdminView(SafeModelView):
    form_columns = [
        'user_id',
        'total_amount',
        'discount_code',
        'discount_value',
        'order_date',
        'invoice_number',
        'locator',
        'order_status',
        'estimated_delivery_at',
        'estimated_delivery_note',
    ]

    # Columnas visibles en la tabla
    column_list = [
        'id',
        'user_id',
        'total_amount',
        'discount_code',
        'discount_value',
        'order_date',
        'invoice_number',
        'locator',
        'order_status',
        'estimated_delivery_at',
        'estimated_delivery_note',
    ]

    column_editable_list = ['total_amount', 'order_status']
    column_searchable_list = ['invoice_number', 'locator', 'discount_code']
    column_filters = [
        'order_status',
        'order_date',
        'estimated_delivery_at',
        'discount_code',
    ]

    column_labels = {
        'discount_code': 'Código',
        'discount_value': 'Importe',
        'total_amount': 'Total (€)',
        'order_date': 'Fecha pedido',
        'invoice_number': 'Factura',
        'locator': 'Localizador',
        'order_status': 'Estado',
        'estimated_delivery_at': 'Entrega estimada',
        'estimated_delivery_note': 'Nota entrega',
    }

    column_formatters = {
        'total_amount': lambda v, c, m, p: f"{(m.total_amount or 0):.2f}€",
        'discount_value': lambda v, c, m, p: f"-{m.discount_value:.2f}€" if m.discount_value else "—",
        'discount_code': lambda v, c, m, p: m.discount_code or "—",
        'order_date': lambda v, c, m, p: (
            (m.order_date + timedelta(hours=2)).strftime("%d/%m/%Y %H:%M") if m.order_date else ''
        ),
        'estimated_delivery_at': lambda v, c, m, p: (
            m.estimated_delivery_at.strftime("%d/%m/%Y") if m.estimated_delivery_at else '—'
        ),
    }

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
        ),

        'estimated_delivery_at': DateField(
            'Fecha estimada de entrega',
            format='%Y-%m-%d',
            render_kw={'placeholder': 'YYYY-MM-DD'}
        ),
        'estimated_delivery_note': TextAreaField(
            'Nota (opcional)',
            render_kw={'rows': 2, 'maxlength': 255, 'placeholder': 'p.ej. Retraso por pintura'}
        ),
    }

    def create_form(self, obj=None):
        form = super().create_form(obj)
        if not form.invoice_number.data:
            form.invoice_number.data = Orders.generate_next_invoice_number()
        if not form.locator.data:
            form.locator.data = Orders.generate_locator()
        return form


    # Hook para evitar errores al borrar por FK: eliminar detalles primero
    def on_model_delete(self, model):
        self.session.query(OrderDetails).filter_by(order_id=model.id).delete(synchronize_session=False)

    column_default_sort = ('order_date', True)



class CartAdminView(SafeModelView):
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
        'precio_total': lambda v, c, m, p: f"{(m.precio_total * m.quantity):.2f}€" if m.precio_total and m.quantity else '0.00 €',
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


class OrderDetailsAdminView(SafeModelView):
    column_list = [
        'order_id', 'locator', 'cliente', 'product_name',
        'quantity', 'alto', 'ancho', 'anclaje', 'color',
        'precio_total', 'shipping_cost', 'total_con_envio'
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
        'precio_total': 'Precio Total',
        'shipping_cost': 'Coste Envío',
        'total_con_envio': 'Total con Envío'
    }

    column_formatters = {
        'locator': lambda v, c, m, p: m.order.locator if m.order else '',
        'cliente': lambda v, c, m, p: f"{m.order.user.email}" if m.order and m.order.user else '',
        'product_name': lambda v, c, m, p: m.product.nombre if m.product else '',
        'precio_total': lambda v, c, m, p: f"{m.precio_total * m.quantity:.2f} €" if m.precio_total and m.quantity else '0.00 €',
        'shipping_cost': lambda v, c, m, p: f"{m.shipping_cost:.2f} €" if m.shipping_cost else "0.00 €",
        'total_con_envio': lambda v, c, m, p: f"{(m.precio_total * m.quantity + (m.shipping_cost or 0)):.2f} €"
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


class FavoritesAdminView(SafeModelView):
    column_list = ('id', 'usuario_email', 'producto_nombre')

    column_labels = {
        'usuario_email': 'Usuario',
        'producto_nombre': 'Producto'
    }

    column_formatters = {
        'usuario_email': lambda v, c, m, p: m.usuario.email if m.usuario else '—',
        'producto_nombre': lambda v, c, m, p: m.producto.nombre if m.producto else f'ID {m.producto_id}',
    }

    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()
        if 'usuario_email' not in columns:
            columns.append('usuario_email')
        if 'producto_nombre' not in columns:
            columns.append('producto_nombre')
        return columns

    can_create = False
    can_edit = False


class InvoiceAdminView(SafeModelView):
    form_columns = ['invoice_number','client_name','client_address','client_cif','amount','order_id','created_at']
    column_list    = ['id','invoice_number','client_name','amount','created_at','order_id']
    column_editable_list = ['client_name','client_address','client_cif','amount']
    form_extra_fields = {
        'invoice_number': StringField('Número de Factura', render_kw={'readonly': True})
    }

    column_formatters = {
        'amount': lambda v, c, m, p: f"{m.amount:.2f}€" if m.amount is not None else "0.00€",
        'created_at': lambda v, c, m, p: (
            (m.created_at + timedelta(hours=2)).strftime("%d/%m %H:%M") if m.created_at else ''
        )
    }

    column_default_sort = ('created_at', True)

    def create_form(self, obj=None):
        form = super().create_form(obj)
        if not form.invoice_number.data:
            form.invoice_number.data = Invoices.generate_next_invoice_number()
        return form


# ========================== SETUP ADMIN ==========================
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
    admin.add_view(UsersAdminView(Users, db.session))
    admin.add_view(SafeModelView(Categories, db.session))
    admin.add_view(SafeModelView(Subcategories, db.session))
    admin.add_view(ProductAdminView(Products, db.session))
    admin.add_view(SafeModelView(ProductImages, db.session))
    admin.add_view(CartAdminView(Cart, db.session))
    admin.add_view(OrderAdminView(Orders, db.session))
    admin.add_view(OrderDetailsAdminView(OrderDetails, db.session))
    admin.add_view(FavoritesAdminView(Favorites, db.session, name="Favoritos"))
    admin.add_view(SafeModelView(Posts, db.session))
    admin.add_view(SafeModelView(Comments, db.session))
    admin.add_view(InvoiceAdminView(Invoices, db.session))
    admin.add_view(SafeModelView(DeliveryEstimateConfig, db.session))

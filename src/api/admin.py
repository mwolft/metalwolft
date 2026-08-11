import hmac
import os
import secrets
from collections.abc import Mapping
from io import BytesIO

from flask import request, Response, current_app, send_file, flash, redirect, session
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.actions import action
from markupsafe import Markup
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.form import InlineModelConverter, InlineModelFormList
from flask_admin.form import RenderTemplateWidget
from wtforms import validators
from wtforms.fields import SelectField, StringField, DateField, TextAreaField
from .models import (
    db, Users, Products, ProductImages,
    Categories, Subcategories, Cart,
    Orders, OrderDetails, Favorites,
    Posts, Comments, Invoices, VeriFactuRecord, DeliveryEstimateConfig,
    AccountingEntry, SupplierInvoice, SupplierInvoiceDocument, SupplierInvoiceTaxBreakdown,
)
from api.accounting_excel_service import (
    AccountingExcelExportError,
    export_sales_accounting_entries,
)
from api.aeat_sales_ledger_service import (
    AeatSalesLedgerError,
    export_aeat_sales_ledger,
)
from api.flask_mail_invoice_adapter import FlaskMailInvoiceAdapter, FlaskMailInvoiceAdapterError
from api.email_routes import send_order_status_email
from api.invoice_accounting_service import (
    AccountingEntryIntegrityError,
    AccountingEntryUnsupportedSchema,
    AccountingEntryValidationError,
    create_accounting_entry,
)
from api.supplier_invoice_registration_service import (
    SupplierInvoiceDuplicateError,
    SupplierInvoiceRegistrationError,
    SupplierInvoiceRegistrationValidationError,
    find_possible_supplier_invoice_duplicates,
    register_supplier_invoice,
)
from api.supplier_invoice_document_service import (
    SupplierInvoiceDocumentError,
    SupplierInvoiceDocumentImmutabilityError,
    SupplierInvoiceDocumentPersistenceError,
    SupplierInvoiceDocumentValidationError,
    upload_supplier_invoice_document,
)
from api.supplier_invoice_document_storage import (
    SupplierInvoiceDocumentStorageConfigurationError,
    SupplierInvoiceDocumentStorageOperationError,
    get_supplier_invoice_document_storage,
)
from api.invoice_pdf_download_service import (
    InvoicePdfDownloadFileMissing,
    InvoicePdfDownloadInvalidPath,
    InvoicePdfDownloadUnavailable,
    resolve_invoice_pdf_download,
)
from api.invoice_pdf_service import (
    InvoicePdfIntegrityError,
    InvoicePdfSnapshotMissing,
    InvoicePdfUnsupportedSchema,
    InvoicePdfWriteError,
    generate_invoice_pdf,
)
from api.invoice_email_service import (
    EMAIL_STATUS_FAILED,
    EMAIL_STATUS_SENT,
    InvoiceEmailIntegrityError,
    InvoiceEmailPdfMissing,
    InvoiceEmailRecipientMissing,
    InvoiceEmailSendError,
    InvoiceEmailSnapshotMissing,
    InvoiceEmailUnsupportedSchema,
    send_invoice_email as send_invoice_email_v2,
)
from api.utils import mail
from api.cart_reminder_service import (
    CartReminderDeliveryError,
    CartReminderIneligibleError,
    get_cart_reminder_eligibility,
    send_manual_cart_reminder,
)
from api.invoice_admin_helpers import (
    build_invoice_issuer_from_config,
    invoice_admin_actor_from_basic_auth,
    select_checkout_session_for_invoice,
)
from api.invoice_issue_service import (
    CORRECTIVE_INVOICE_TYPE,
    ORDINARY_INVOICE_TYPE,
    InvoiceIssueError,
    InvoiceNumberError,
    issue_invoice_for_order,
    issue_total_rectification_for_invoice,
)
from api.invoice_snapshot_builder import (
    SUPPORTED_TOTAL_RECTIFICATION_AEAT_TYPES,
    RECTIFICATION_REASON_TEXTS,
    InvoiceSnapshotValidationError,
)
from api.verifactu_record_service import (
    VeriFactuRecordConcurrencyError,
    VeriFactuRecordIntegrityError,
    VeriFactuRecordUnsupportedSchema,
    VeriFactuRecordValidationError,
    create_verifactu_registration_record,
    prepare_verifactu_record_for_submission,
    verifactu_system_identity_from_config,
)
from datetime import timedelta
from sqlalchemy import inspect 
from sqlalchemy.exc import IntegrityError


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
        current_year = now.year
        selected_year = int(request.args.get("year", current_year))
        

        inicio_mes_actual = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if inicio_mes_actual.month == 1:
            inicio_mes_anterior = inicio_mes_actual.replace(year=inicio_mes_actual.year - 1, month=12)
        else:
            inicio_mes_anterior = inicio_mes_actual.replace(month=inicio_mes_actual.month - 1)

        fin_mes_anterior = inicio_mes_actual


        ingresos_mes_actual = db.session.scalar(
            db.select(func.sum(Orders.total_amount))
            .where(Orders.order_date.isnot(None))
            .where(Orders.order_date >= inicio_mes_actual)
            .where(Orders.order_date <= now)
        ) or 0


        # ===== KPI PUNTO MUERTO =====
        fixed_costs_monthly = 496.70
        target_salary_monthly = 1200
        average_margin_percent = 0.509
        break_even_override = 3300  # usa None si no quieres forzar

        if break_even_override:
            break_even = break_even_override
        else:
            break_even = (fixed_costs_monthly + target_salary_monthly) / average_margin_percent

        coverage_ratio = ingresos_mes_actual / break_even if break_even else 0
        difference = ingresos_mes_actual - break_even


        if coverage_ratio < 0.7:
            status = "FRENAR"
        elif coverage_ratio < 1.0:
            status = "MANTENER"
        else:
            status = "APRETAR"

        break_even_kpi = {
            "revenue_current_month": round(ingresos_mes_actual, 2),
            "break_even_monthly": round(break_even, 2),
            "coverage_ratio": round(coverage_ratio, 2),
            "status": status,
            "difference": round(difference, 2)
        }

        ingresos_mes_anterior = db.session.scalar(
            db.select(func.sum(Orders.total_amount))
            .where(Orders.order_date.isnot(None))
            .where(Orders.order_date >= inicio_mes_anterior)
            .where(Orders.order_date < fin_mes_anterior)
        ) or 0


        if ingresos_mes_anterior > 0:
            variacion_porcentual = (
                (ingresos_mes_actual - ingresos_mes_anterior) / ingresos_mes_anterior
            ) * 100
            variacion_label = f"{variacion_porcentual:.2f}%"
            variacion_up = variacion_porcentual >= 0
            variacion_es_nueva = False
        else:
            if ingresos_mes_actual > 0:
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
            .where(extract('year', Orders.order_date) == selected_year)
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
            .where(extract('year', Users.created_at) == selected_year)
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
                'ingresos_mes_actual': ingresos_mes_actual,
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
            selected_year=selected_year,
            tz_es=tz_es,
            break_even_kpi=break_even_kpi,
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
def _format_cart_reminder(view, context, model, name):
    user = getattr(model, 'user', None)
    if not user:
        return Markup('<span class="text-muted">No elegible</span>')

    eligibility = get_cart_reminder_eligibility(db_session=view.session, user=user)
    if not eligibility.eligible or not eligibility.cart_items or eligibility.cart_items[0].id != model.id:
        return Markup('<span class="text-muted">No elegible</span>')

    action_url = view.get_url(".send_cart_reminder", cart_id=model.id)
    confirmation = "Se enviara un recordatorio manual con el carrito guardado. Continuar?"
    return Markup(
        '<form method="post" action="{action_url}" style="margin:0;" '
        'onsubmit="return confirm(\'{confirmation}\');">'
        '<button type="submit" class="btn btn-primary btn-sm">Enviar recordatorio</button>'
        "</form>"
    ).format(action_url=action_url, confirmation=confirmation)


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
        'email': lambda v, c, m, p: Markup(f'<a href="mailto:{m.email}">{m.email}</a>') if m.email else '',
    }


class ProductAdminView(SafeModelView):
    column_sortable_list = ('id', 'sort_order', 'nombre', 'precio', 'precio_rebajado', 'categoria_id')  # 👈 AÑADIDO

    column_searchable_list = ('nombre',)
    column_filters = ('categoria_id', 'published', 'available_for_sale')
    column_labels = {
        'published': 'Publicado',
        'available_for_sale': 'Disponible para venta',
        'opening_type': 'Tipo de apertura',
    }
    form_args = {
        'published': {
            'label': 'Publicado',
            'description': 'Determina si la ficha pública existe y puede aparecer en el sitemap.',
            'default': True,
        },
        'available_for_sale': {
            'label': 'Disponible para venta',
            'description': 'Determina si puede aparecer en catálogos y aceptar nuevos pedidos.',
            'default': True,
        },
    }
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
        'opening_type',
        'has_abatible',
        'has_door_model',
        'es_mas_vendido',
        'es_nuevo_diseno',
        'published',
        'available_for_sale',
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
        'categoria_id': SelectField('Categoría', choices=[]),
        'opening_type': SelectField(
            'Tipo de apertura',
            choices=[
                ('fixed', 'Fija'),
                ('hinged', 'Abatible'),
            ],
        ),
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

    def on_model_change(self, form, model, is_created):
        if not model.published and model.available_for_sale:
            model.available_for_sale = False
            flash(
                'Al despublicar el producto también se ha desactivado su disponibilidad para venta.',
                'warning',
            )

        return super().on_model_change(form, model, is_created)

    def handle_view_exception(self, exc):
        if isinstance(exc, IntegrityError) and (
            'ck_products_published_available_for_sale'
            in str(getattr(exc, 'orig', ''))
        ):
            current_app.logger.warning(
                'Product lifecycle constraint rejected an administrative update.',
                exc_info=True,
            )
            flash(
                'Un producto no publicado no puede estar disponible para la venta.',
                'error',
            )
            return True

        return super().handle_view_exception(exc)

    column_formatters = {
        'descripcion': lambda v, c, m, p: (m.descripcion[:30] + '…') if m.descripcion and len(m.descripcion) > 30 else (m.descripcion or ''),
        'descripcion_seo': lambda v, c, m, p: (m.descripcion_seo[:30] + '…') if m.descripcion_seo and len(m.descripcion_seo) > 30 else (m.descripcion_seo or ''),
        'titulo_seo': lambda v, c, m, p: (m.titulo_seo[:30] + '…') if m.titulo_seo and len(m.titulo_seo) > 30 else (m.titulo_seo or ''),
        'h1_seo': lambda v, c, m, p: (m.h1_seo[:30] + '…') if m.h1_seo and len(m.h1_seo) > 30 else (m.h1_seo or ''),
    }


def _find_order_ordinary_invoice(view, order):
    return (
        view.session.query(Invoices)
        .filter(
            Invoices.order_id == order.id,
            Invoices.invoice_type == ORDINARY_INVOICE_TYPE,
        )
        .order_by(Invoices.id.asc())
        .first()
    )


def _format_order_invoice_detail(view, context, model, name):
    invoice = _find_order_ordinary_invoice(view, model)
    if invoice:
        return Markup("<span>Factura emitida: {}</span>").format(invoice.invoice_number)

    legacy_invoice_number = getattr(model, name, None)
    legacy_notice = (
        Markup('<div class="text-muted">Número legacy en pedido: {}</div>').format(legacy_invoice_number)
        if legacy_invoice_number
        else Markup('<div class="text-muted">Sin factura fiscal emitida.</div>')
    )
    action_url = view.get_url(".issue_invoice", order_id=model.id)
    confirmation = "Se asignará un número fiscal y la factura emitida será inmutable. ¿Continuar?"

    return Markup(
        '<div class="order-invoice-admin-action">'
        "{legacy_notice}"
        '<form method="post" action="{action_url}" style="margin-top: 8px;" '
        'onsubmit="return confirm(\'{confirmation}\');">'
        '<button type="submit" class="btn btn-success btn-sm">Emitir factura</button>'
        "</form>"
        "</div>"
    ).format(
        legacy_notice=legacy_notice,
        action_url=action_url,
        confirmation=confirmation,
    )


def _admin_issue_invoice_success_message(result):
    if result.created:
        return f"Factura {result.invoice_number} emitida correctamente."
    return f"El pedido ya tenía emitida la factura {result.invoice_number}."


class OrderAdminView(SafeModelView):
    can_view_details = True

    form_columns = [
        'user_id',
        'total_amount',
        'discount_code',
        'discount_value',
        'order_date',
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
    column_details_list = column_list

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
    column_formatters_detail = {
        **column_formatters,
        'invoice_number': _format_order_invoice_detail,
    }

    form_extra_fields = {
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
        if not form.locator.data:
            form.locator.data = Orders.generate_locator()
        return form

    @expose('/issue-invoice/<int:order_id>', methods=['POST'])
    def issue_invoice(self, order_id):
        order = self.session.get(Orders, order_id)
        if not order:
            flash('Pedido no encontrado.', 'error')
            return redirect(self.get_url(".index_view"))

        redirect_url = self.get_url(".details_view", id=order.id)
        request_data = request.get_json(silent=True) if request.is_json else None
        if request.args or request.form or (
            request_data is not None and (not isinstance(request_data, dict) or request_data)
        ):
            flash('Esta acción no acepta datos fiscales desde el navegador.', 'error')
            return redirect(redirect_url)

        checkout_session, invoiceability_error = select_checkout_session_for_invoice(order)
        if invoiceability_error:
            flash(invoiceability_error, 'error')
            return redirect(redirect_url)

        try:
            result = issue_invoice_for_order(
                db_session=self.session,
                checkout_session=checkout_session,
                issuer=build_invoice_issuer_from_config(),
                order=order,
                source="manual",
                actor=invoice_admin_actor_from_basic_auth(request.authorization),
            )
            flash(_admin_issue_invoice_success_message(result), 'success' if result.created else 'info')
        except InvoiceIssueError:
            current_app.logger.warning(
                "Flask Admin invoice issue requested for missing order_id=%s",
                order_id,
            )
            flash('Pedido no encontrado.', 'error')
        except InvoiceSnapshotValidationError as exc:
            current_app.logger.exception(
                "Invalid Flask Admin invoice issue request for order_id=%s",
                order_id,
            )
            if getattr(exc, "field", "") == "issuer":
                flash('La configuración fiscal del emisor no está completa.', 'error')
            else:
                flash('No se puede emitir la factura para este pedido.', 'error')
        except InvoiceNumberError:
            current_app.logger.exception(
                "Flask Admin invoice number allocation failed for order_id=%s",
                order_id,
            )
            flash('No se ha podido reservar un número de factura.', 'error')
        except IntegrityError:
            current_app.logger.exception(
                "Flask Admin ordinary invoice conflict for order_id=%s",
                order_id,
            )
            flash('Ya existe una factura ordinaria para este pedido.', 'error')
        except Exception:
            current_app.logger.exception(
                "Unexpected Flask Admin invoice issue error for order_id=%s",
                order_id,
            )
            flash('No se ha podido emitir la factura.', 'error')

        return redirect(redirect_url)


    # Hook para evitar errores al borrar por FK: eliminar detalles primero
    def on_model_delete(self, model):
        self.session.query(OrderDetails).filter_by(order_id=model.id).delete(synchronize_session=False)

    column_default_sort = ('order_date', True)



class CartAdminView(SafeModelView):
    column_list = ('usuario_email', 'product_display', 'alto', 'ancho', 'anclaje', 'color', 'quantity', 'precio_total', 'added_at', 'cart_reminder')

    column_labels = {
        'usuario_email': 'Usuario (Email)',
        'product_display': 'Producto',
        'alto': 'Alto',
        'ancho': 'Ancho',
        'anclaje': 'Anclaje',
        'color': 'Color',
        'quantity': 'Ud.',
        'precio_total': 'Precio Total',
        'added_at': 'Añadido el',
        'cart_reminder': 'Recordatorio'
    }

    form_columns = ['usuario_id', 'producto_id', 'alto', 'ancho', 'anclaje', 'color', 'quantity', 'precio_total', 'added_at']
    column_formatters = {
        'usuario_email': lambda v, c, m, p: m.user.email if m.user else 'Sin usuario',
        'precio_total': lambda v, c, m, p: f"{(m.precio_total * m.quantity):.2f}€" if m.precio_total and m.quantity else '0.00 €',
        'product_display': lambda v, c, m, p: m.product.nombre if m.product else f'ID {m.producto_id}',
        'added_at': lambda v, c, m, p: m.added_at.strftime("%d/%m/%Y %H:%M") if m.added_at else '',
        'cart_reminder': _format_cart_reminder,
    }

    def scaffold_list_columns(self):
        columns = super().scaffold_list_columns()
        if 'usuario_email' not in columns:
            columns.append('usuario_email')
        if 'product_display' not in columns:
            columns.append('product_display')
        return columns

    column_default_sort = ('added_at', True)

    @expose('/send-cart-reminder/<int:cart_id>', methods=['POST'])
    def send_cart_reminder(self, cart_id):
        cart_item = self.session.get(Cart, cart_id)
        if not cart_item or not cart_item.user:
            flash('Carrito no encontrado.', 'error')
            return redirect(self.get_url('.index_view'))

        try:
            frontend_base_url = (
                current_app.config.get('FRONTEND_URL') or 'https://www.metalwolft.com'
            ).rstrip('/')
            send_manual_cart_reminder(
                db_session=self.session,
                user=cart_item.user,
                cart_url=f'{frontend_base_url}/cart',
                logger=current_app.logger,
            )
            flash('Recordatorio de carrito enviado correctamente.', 'success')
        except CartReminderIneligibleError as exc:
            current_app.logger.info('Cart reminder rejected user_id=%s', cart_item.usuario_id)
            flash(str(exc), 'warning')
        except CartReminderDeliveryError:
            current_app.logger.error('Cart reminder delivery failed user_id=%s', cart_item.usuario_id)
            flash('No se pudo enviar el recordatorio del carrito.', 'error')
        except Exception:
            current_app.logger.exception('Unexpected cart reminder error user_id=%s', cart_item.usuario_id)
            flash('No se pudo enviar el recordatorio del carrito.', 'error')

        return redirect(self.get_url('.index_view'))


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


def _format_admin_invoice_nullable(value):
    return value if value not in (None, "") else "—"


def _format_admin_invoice_value(view, context, model, name):
    return _format_admin_invoice_nullable(getattr(model, name, None))


def _format_admin_invoice_amount(view, context, model, name):
    value = getattr(model, name, None)
    if value is None:
        return "—"
    try:
        return f"{value:.2f}€"
    except (TypeError, ValueError):
        return str(value)


def _format_admin_invoice_datetime(view, context, model, name):
    value = getattr(model, name, None)
    if not value:
        return "—"
    if hasattr(value, "strftime"):
        return (value + timedelta(hours=2)).strftime("%d/%m/%Y %H:%M")
    return str(value)


def _format_admin_invoice_pdf_available(view, context, model, name):
    if not getattr(model, name, None):
        return "—"
    download_url = view.get_url(".download_pdf", invoice_id=model.id)
    return Markup('<a href="{}">Descargar PDF</a>').format(download_url)


def _format_admin_invoice_pdf_detail(view, context, model, name):
    has_pdf = bool(getattr(model, name, None))
    status = _format_admin_invoice_pdf_available(view, context, model, name) if has_pdf else Markup("PDF pendiente")
    action_url = view.get_url(".generate_pdf", invoice_id=model.id)
    button_label = "Regenerar PDF" if has_pdf else "Generar PDF"
    confirm_attr = (
        Markup(' onsubmit="return confirm(\'¿Seguro que quieres regenerar el PDF existente?\');"')
        if has_pdf
        else Markup("")
    )

    return Markup(
        '<div class="invoice-pdf-admin-action">'
        '<div>{status}</div>'
        '<form method="post" action="{action_url}" style="margin-top: 8px;"{confirm_attr}>'
        '<button type="submit" class="btn btn-warning btn-sm">{button_label}</button>'
        '</form>'
        '</div>'
    ).format(
        status=status,
        action_url=action_url,
        confirm_attr=confirm_attr,
        button_label=button_label,
    )


def _admin_invoice_pdf_success_message(*, regenerate, previous_pdf_path, result):
    if not regenerate and previous_pdf_path == result.pdf_path:
        return "El PDF ya estaba generado."
    if regenerate:
        return "PDF regenerado correctamente."
    return "PDF generado correctamente."


def _find_invoice_sale_accounting_entry(view, invoice):
    for entry in (getattr(invoice, "accounting_entries", None) or []):
        if entry.entry_type == AccountingEntry.ENTRY_TYPE_SALE:
            return entry

    invoice_id = getattr(invoice, "id", None)
    if not invoice_id:
        return None

    return (
        view.session.query(AccountingEntry)
        .filter_by(invoice_id=invoice_id, entry_type=AccountingEntry.ENTRY_TYPE_SALE)
        .one_or_none()
    )


def _format_admin_invoice_accounting_status(view, context, model, name):
    entry = _find_invoice_sale_accounting_entry(view, model)
    if not entry:
        return "Sin registrar"
    return _format_admin_accounting_status_label(entry.status)


def _format_admin_accounting_status_label(status):
    labels = {
        AccountingEntry.STATUS_PENDING: "Registrada",
        AccountingEntry.STATUS_RECORDED: "Contabilizada",
        AccountingEntry.STATUS_FAILED: "Con error",
    }
    return labels.get(status, _format_admin_invoice_nullable(status))


def _format_admin_invoice_accounting_detail(view, context, model, name):
    entry = _find_invoice_sale_accounting_entry(view, model)
    export_url = view.get_url(".export_accounting")
    aeat_export_url = view.get_url(".export_aeat_accounting")

    if entry:
        return Markup(
            '<div class="invoice-accounting-admin-action">'
            '<div>{status}</div>'
            '<div style="margin-top: 8px;">'
            '<a class="btn btn-default btn-sm" href="{export_url}">Exportar Excel de ingresos</a>'
            ' <a class="btn btn-default btn-sm" href="{aeat_export_url}">Exportar libro AEAT de ingresos</a>'
            '</div>'
            '</div>'
        ).format(
            status=_format_admin_accounting_status_label(entry.status),
            export_url=export_url,
            aeat_export_url=aeat_export_url,
        )

    if not getattr(model, "invoice_number", None) or not getattr(model, "issued_at", None):
        return Markup("Factura no emitida")

    action_url = view.get_url(".record_accounting", invoice_id=model.id)
    return Markup(
        '<div class="invoice-accounting-admin-action">'
        '<div>Sin registrar</div>'
        '<form method="post" action="{action_url}" style="margin-top: 8px;">'
        '<button type="submit" class="btn btn-primary btn-sm">Registrar contabilidad</button>'
        '</form>'
        '<div style="margin-top: 8px;">'
        '<a class="btn btn-default btn-sm" href="{export_url}">Exportar Excel de ingresos</a>'
        ' <a class="btn btn-default btn-sm" href="{aeat_export_url}">Exportar libro AEAT de ingresos</a>'
        '</div>'
        '</div>'
    ).format(action_url=action_url, export_url=export_url, aeat_export_url=aeat_export_url)


def _format_admin_invoice_email_detail(view, context, model, name):
    status = getattr(model, name, None)
    if not getattr(model, "invoice_number", None) or not getattr(model, "issued_at", None):
        return Markup("Factura no emitida")

    action_url = view.get_url(".send_invoice_email", invoice_id=model.id)
    button_label = "Reenviar factura" if status == EMAIL_STATUS_SENT else "Enviar factura"
    confirm_attr = (
        ' onsubmit="return confirm(\'La factura ya consta como enviada. ¿Quieres reenviarla?\')"'
        if status == EMAIL_STATUS_SENT
        else ""
    )

    return Markup(
        '<div class="invoice-email-admin-action">'
        '<div>{status}</div>'
        '<form method="post" action="{action_url}" style="margin-top: 8px;"{confirm_attr}>'
        '<button type="submit" class="btn btn-primary btn-sm">{button_label}</button>'
        '</form>'
        '</div>'
    ).format(
        status=_format_admin_invoice_nullable(status),
        action_url=action_url,
        confirm_attr=Markup(confirm_attr),
        button_label=button_label,
    )


def _persist_admin_invoice_email_failure(session, invoice_id, attempts_before):
    failed_invoice = session.get(Invoices, invoice_id)
    if not failed_invoice:
        return

    failed_invoice.email_status = EMAIL_STATUS_FAILED
    failed_invoice.email_attempts = int(attempts_before or 0) + 1
    failed_invoice.email_last_error = "No se pudo enviar el email de factura."
    session.commit()


def _find_invoice_verifactu_registration_record(view, invoice):
    for record in (getattr(invoice, "verifactu_records", None) or []):
        if record.record_type == VeriFactuRecord.RECORD_TYPE_ALTA:
            return record

    invoice_id = getattr(invoice, "id", None)
    if not invoice_id:
        return None

    return (
        view.session.query(VeriFactuRecord)
        .filter_by(invoice_id=invoice_id, record_type=VeriFactuRecord.RECORD_TYPE_ALTA)
        .one_or_none()
    )


def _format_admin_verifactu_record_link(view, record):
    record_url = view.get_url("verifacturecord.details_view", id=record.id)
    return Markup('<a href="{url}">Ver registro #{record_id}</a>').format(
        url=record_url,
        record_id=record.id,
    )


def _format_admin_invoice_verifactu_detail(view, context, model, name):
    record = _find_invoice_verifactu_registration_record(view, model)

    if record:
        record_link = _format_admin_verifactu_record_link(view, record)
        if record.status == VeriFactuRecord.STATUS_READY:
            fingerprint = getattr(record, "fingerprint", None)
            fingerprint_label = f"{fingerprint[:12]}..." if fingerprint else "—"
            return Markup(
                '<div class="invoice-verifactu-admin-action">'
                '<div>Preparado</div>'
                '<div>Secuencia: {sequence}</div>'
                '<div>Huella: {fingerprint}</div>'
                '<div style="margin-top: 8px;">{record_link}</div>'
                '</div>'
            ).format(
                sequence=_format_admin_invoice_nullable(record.chain_sequence),
                fingerprint=fingerprint_label,
                record_link=record_link,
            )

        return Markup(
            '<div class="invoice-verifactu-admin-action">'
            '<div>Generado</div>'
            '<div>ID registro: {record_id}</div>'
            '<div style="margin-top: 8px;">{record_link}</div>'
            '</div>'
        ).format(record_id=record.id, record_link=record_link)

    if not getattr(model, "invoice_number", None) or not getattr(model, "issued_at", None):
        return Markup("Factura no emitida")

    action_url = view.get_url(".generate_verifactu_record", invoice_id=model.id)
    return Markup(
        '<div class="invoice-verifactu-admin-action">'
        '<div>No generado</div>'
        '<form method="post" action="{action_url}" style="margin-top: 8px;">'
        '<button type="submit" class="btn btn-primary btn-sm">GENERAR REGISTRO VERIFACTU</button>'
        '</form>'
        '</div>'
    ).format(action_url=action_url)


def _admin_invoice_accounting_success_message(*, already_existed):
    if already_existed:
        return "La factura ya tenía registro contable."
    return "Registro contable creado correctamente."


def _admin_accounting_export_folder():
    configured_folder = current_app.config.get("ACCOUNTING_EXPORT_FOLDER") or os.getenv("ACCOUNTING_EXPORT_FOLDER")
    if configured_folder:
        return configured_folder

    instance_path = getattr(current_app, "instance_path", None)
    if instance_path:
        return os.path.join(instance_path, "accounting_exports")

    return os.path.join(os.getcwd(), ".tmp_accounting_exports")


def _find_invoice_corrective_invoice(view, invoice):
    invoice_id = getattr(invoice, "id", None)
    if not invoice_id:
        return None

    return (
        view.session.query(Invoices)
        .filter(
            Invoices.original_invoice_id == invoice_id,
            Invoices.invoice_type == CORRECTIVE_INVOICE_TYPE,
        )
        .order_by(Invoices.id.asc())
        .first()
    )


def _invoice_supports_total_rectification(invoice):
    snapshot = getattr(invoice, "invoice_snapshot", None)
    return (
        getattr(invoice, "invoice_type", None) == ORDINARY_INVOICE_TYPE
        and bool(getattr(invoice, "invoice_number", None))
        and getattr(invoice, "issued_at", None) is not None
        and isinstance(snapshot, Mapping)
        and snapshot.get("schema_version") == 2
    )


def _is_matching_admin_total_rectification(invoice, reason, aeat_type):
    snapshot = getattr(invoice, "invoice_snapshot", None)
    operation = snapshot.get("operation") if isinstance(snapshot, Mapping) else None
    rectification = operation.get("rectification") if isinstance(operation, Mapping) else None
    return (
        getattr(invoice, "rectification_type", None) == 'differences'
        and getattr(invoice, "rectification_reason", None) == reason
        and getattr(invoice, "rectification_aeat_type", None) == aeat_type
        and isinstance(rectification, Mapping)
        and rectification.get("rectification_scope") == 'total'
        and rectification.get("aeat_type") == aeat_type
    )


def _format_admin_invoice_type_detail(view, context, model, name):
    invoice_type = _format_admin_invoice_value(view, context, model, name)
    if getattr(model, "invoice_type", None) == CORRECTIVE_INVOICE_TYPE:
        original = getattr(model, "original_invoice", None)
        aeat_type = getattr(model, "rectification_aeat_type", None) or "Sin clasificación AEAT"
        if original and getattr(original, "id", None):
            original_url = view.get_url(".details_view", id=original.id)
            return Markup(
                '<div>{invoice_type}</div><div style="margin-top: 8px;">'
                '<a href="{original_url}">Ver factura original {original_number}</a>'
                '<div style="margin-top: 4px;">Tipo fiscal AEAT: {aeat_type}</div>'
                '</div>'
            ).format(
                invoice_type=invoice_type,
                original_url=original_url,
                original_number=_format_admin_invoice_nullable(original.invoice_number),
                aeat_type=aeat_type,
            )
        return invoice_type

    corrective = _find_invoice_corrective_invoice(view, model)
    if corrective:
        corrective_url = view.get_url(".details_view", id=corrective.id)
        return Markup(
            '<div>{invoice_type}</div><div style="margin-top: 8px;">'
            '<a href="{corrective_url}">Ver rectificativa {corrective_number}</a>'
            '</div>'
        ).format(
            invoice_type=invoice_type,
            corrective_url=corrective_url,
            corrective_number=_format_admin_invoice_nullable(corrective.invoice_number),
        )

    if not _invoice_supports_total_rectification(model):
        return invoice_type

    confirmation_url = view.get_url(".issue_total_rectification", invoice_id=model.id)
    return Markup(
        '<div>{invoice_type}</div><div style="margin-top: 8px;">'
        '<a class="btn btn-danger btn-sm" href="{confirmation_url}">'
        'EMITIR RECTIFICATIVA TOTAL</a></div>'
    ).format(invoice_type=invoice_type, confirmation_url=confirmation_url)


def _admin_total_rectification_success_message(result):
    if result.created:
        return f"Factura rectificativa {result.invoice_number} emitida correctamente."
    return f"Ya existe la factura rectificativa {result.invoice_number}."


def _format_supplier_invoice_registration(view, context, model, name):
    if model.status == SupplierInvoice.STATUS_REGISTERED:
        return Markup("<span class='label label-success'>Registrada</span>")
    if model.status == SupplierInvoice.STATUS_CANCELLED:
        return Markup("<span class='label label-default'>Cancelada</span>")

    action_url = view.get_url(".confirm_register", supplier_invoice_id=model.id)
    return Markup(
        '<a class="btn btn-primary btn-sm" href="{action_url}">CONFIRMAR Y REGISTRAR</a>'
    ).format(action_url=action_url)


def _format_supplier_invoice_hash(view, context, model, name):
    snapshot_hash = getattr(model, name, None)
    if not snapshot_hash:
        return "—"
    return f"{snapshot_hash[:12]}…"


SUPPLIER_DOCUMENT_UPLOAD_CSRF_SESSION_KEY = "supplier_document_upload_csrf"


def _issue_supplier_document_upload_csrf_token():
    token = session.get(SUPPLIER_DOCUMENT_UPLOAD_CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[SUPPLIER_DOCUMENT_UPLOAD_CSRF_SESSION_KEY] = token
    return token


def _valid_supplier_document_upload_csrf_token(token):
    expected_token = session.get(SUPPLIER_DOCUMENT_UPLOAD_CSRF_SESSION_KEY)
    return bool(
        expected_token
        and token
        and hmac.compare_digest(str(expected_token), str(token))
    )


def _format_supplier_invoice_documents(view, context, model, name):
    documents = list(getattr(model, "documents", []) or [])
    upload_url = view.get_url(".upload_document", supplier_invoice_id=model.id)
    if not documents:
        if model.status == SupplierInvoice.STATUS_REGISTERED:
            return Markup("<span class='text-muted'>Sin documentos adjuntos</span>")
        return Markup(
            '<a class="btn btn-default btn-sm" href="{upload_url}">SUBIR DOCUMENTO</a>'
        ).format(upload_url=upload_url)

    items = []
    for document in documents:
        download_url = view.get_url(".download_document", document_id=document.id)
        items.append(
            '<li>{filename} <span class="text-muted">({mime}, {size} bytes, {hash}…)</span> '
            '<a class="btn btn-default btn-xs" href="{download_url}">DESCARGAR</a></li>'.format(
                filename=document.original_filename,
                mime=document.mime_type,
                size=document.file_size,
                hash=document.sha256[:12],
                download_url=download_url,
            )
        )
    upload_action = ""
    if model.status != SupplierInvoice.STATUS_REGISTERED:
        upload_action = (
            '<p><a class="btn btn-default btn-sm" href="{upload_url}">SUBIR DOCUMENTO</a></p>'.format(
                upload_url=upload_url,
            )
        )
    return Markup("<ul>{items}</ul>{upload_action}").format(
        items=Markup("".join(items)),
        upload_action=Markup(upload_action),
    )


def _supplier_document_redirect_url(view, document):
    if document.supplier_invoice_id:
        return view.get_url(".details_view", id=document.supplier_invoice_id)
    return view.get_url(".index_view")


def _cleanup_supplier_document_after_commit_failure(storage_key):
    try:
        get_supplier_invoice_document_storage(current_app).delete_document(storage_key=storage_key)
    except Exception:
        current_app.logger.error("Supplier document cleanup after database failure was unsuccessful")


class SupplierInvoiceTaxBreakdownInlineFieldList(InlineModelFormList):
    widget = RenderTemplateWidget("admin/supplier_invoice_tax_breakdowns_inline.html")


class SupplierInvoiceInlineModelConverter(InlineModelConverter):
    inline_field_list_type = SupplierInvoiceTaxBreakdownInlineFieldList


def _supplier_invoice_registration_error_message(error):
    message = str(error)
    known_messages = {
        "Debe existir al menos un desglose de IVA.": message,
        "El total no coincide con la suma de las bases y cuotas de IVA.": message,
        "La cuota deducible no puede superar la cuota soportada.": message,
    }
    return known_messages.get(message, "No se ha podido registrar la factura recibida. Revisa sus datos fiscales.")


class SupplierInvoiceAdminView(SafeModelView):
    can_view_details = True
    column_default_sort = ("created_at", True)
    inline_models = (SupplierInvoiceTaxBreakdown,)
    inline_model_form_converter = SupplierInvoiceInlineModelConverter
    extra_js = ["/static/admin/supplier_invoice_tax_breakdowns.js"]
    column_list = [
        "id",
        "reception_number",
        "supplier_legal_name",
        "supplier_tax_id",
        "supplier_invoice_number",
        "issue_date",
        "total_amount",
        "status",
        "registration_action",
    ]
    column_details_list = [
        "id",
        "reception_number",
        "supplier_legal_name",
        "supplier_tax_id",
        "supplier_country_code",
        "supplier_tax_id_type",
        "supplier_invoice_number",
        "issue_date",
        "operation_date",
        "received_at",
        "registered_at",
        "registered_by",
        "concept",
        "currency",
        "total_amount",
        "fiscal_invoice_type",
        "tax_treatment",
        "special_regime_key",
        "status",
        "source",
        "documents",
        "tax_breakdowns",
        "snapshot_schema_version",
        "snapshot_hash",
        "registration_action",
    ]
    column_searchable_list = [
        "supplier_legal_name",
        "supplier_tax_id",
        "supplier_invoice_number",
    ]
    column_filters = ["status", "issue_date", "registered_at", "created_at"]
    column_sortable_list = [
        "id",
        "reception_number",
        "supplier_legal_name",
        "supplier_invoice_number",
        "issue_date",
        "total_amount",
        "status",
        "created_at",
    ]
    column_labels = {
        "reception_number": "N.º recepción",
        "supplier_legal_name": "Proveedor",
        "supplier_tax_id": "NIF/CIF proveedor",
        "supplier_country_code": "País proveedor",
        "supplier_tax_id_type": "Tipo identificador",
        "supplier_invoice_number": "N.º factura proveedor",
        "issue_date": "Fecha expedición",
        "operation_date": "Fecha operación",
        "received_at": "Recibida",
        "registered_at": "Registrada",
        "registered_by": "Registrada por",
        "concept": "Concepto",
        "total_amount": "Total",
        "fiscal_invoice_type": "Tipo fiscal",
        "tax_treatment": "Tratamiento fiscal",
        "special_regime_key": "Régimen especial",
        "documents": "Documentos",
        "tax_breakdowns": "Desgloses IVA",
        "snapshot_schema_version": "Versión snapshot",
        "snapshot_hash": "Hash snapshot",
        "registration_action": "Registro",
    }
    column_formatters = {
        "registration_action": _format_supplier_invoice_registration,
        "snapshot_hash": _format_supplier_invoice_hash,
        "documents": _format_supplier_invoice_documents,
    }
    column_formatters_detail = column_formatters
    form_columns = [
        "supplier_legal_name",
        "supplier_tax_id",
        "supplier_country_code",
        "supplier_tax_id_type",
        "supplier_invoice_number",
        "issue_date",
        "operation_date",
        "concept",
        "currency",
        "total_amount",
        "fiscal_invoice_type",
        "tax_treatment",
        "special_regime_key",
        "status",
        "source",
    ]
    form_excluded_columns = [
        "reception_number",
        "received_at",
        "registered_at",
        "registered_by",
        "fiscal_snapshot",
        "snapshot_schema_version",
        "snapshot_hash",
    ]
    form_overrides = {
        "issue_date": DateField,
        "operation_date": DateField,
        "status": SelectField,
    }
    form_args = {
        "issue_date": {
            "format": "%Y-%m-%d",
            "validators": [validators.InputRequired()],
            "render_kw": {
                "placeholder": "YYYY-MM-DD",
            },
        },
        "operation_date": {
            "format": "%Y-%m-%d",
            "validators": [validators.Optional()],
            "render_kw": {
                "placeholder": "YYYY-MM-DD",
            },
        },
        "status": {
            "choices": [
                (SupplierInvoice.STATUS_DRAFT, "Borrador"),
                (SupplierInvoice.STATUS_NEEDS_REVIEW, "Revisar"),
                (SupplierInvoice.STATUS_CANCELLED, "Cancelada"),
            ]
        }
    }

    @expose("/edit/", methods=("GET", "POST"))
    def edit_view(self):
        supplier_invoice = self.get_one(request.args.get("id"))
        if supplier_invoice and supplier_invoice.status == SupplierInvoice.STATUS_REGISTERED:
            flash("Una factura recibida registrada no puede editarse.", "error")
            return redirect(self.get_url(".details_view", id=supplier_invoice.id))
        return super().edit_view()

    def on_model_change(self, form, model, is_created):
        if model.status == SupplierInvoice.STATUS_REGISTERED:
            raise ValueError("Las facturas recibidas solo se registran mediante la acción de confirmación.")
        if is_created and model.status != SupplierInvoice.STATUS_DRAFT:
            raise ValueError("Una factura recibida nueva debe crearse como borrador.")

    def delete_model(self, model):
        if model.status == SupplierInvoice.STATUS_REGISTERED:
            flash("Una factura recibida registrada no puede borrarse.", "error")
            return False
        return super().delete_model(model)

    @expose("/upload-document/", methods=["GET", "POST"])
    def upload_document(self):
        supplier_invoice_id = request.values.get("supplier_invoice_id", type=int)
        supplier_invoice = (
            self.session.get(SupplierInvoice, supplier_invoice_id)
            if supplier_invoice_id
            else None
        )
        if supplier_invoice_id and not supplier_invoice:
            flash("Factura recibida no encontrada.", "error")
            return redirect(self.get_url(".index_view"))
        if supplier_invoice and supplier_invoice.status == SupplierInvoice.STATUS_REGISTERED:
            flash("No se pueden añadir documentos a una factura recibida registrada.", "error")
            return redirect(self.get_url(".details_view", id=supplier_invoice.id))

        if request.method == "GET":
            return self.render(
                "admin/supplier_invoice_document_upload.html",
                supplier_invoice=supplier_invoice,
                csrf_token=_issue_supplier_document_upload_csrf_token(),
                action_url=self.get_url(
                    ".upload_document",
                    supplier_invoice_id=supplier_invoice.id if supplier_invoice else None,
                ),
                cancel_url=(
                    self.get_url(".details_view", id=supplier_invoice.id)
                    if supplier_invoice
                    else self.get_url(".index_view")
                ),
            )

        if not _valid_supplier_document_upload_csrf_token(request.form.get("csrf_token")):
            flash("La sesión del formulario ha caducado. Vuelve a intentarlo.", "error")
            return redirect(request.url)

        actor = request.authorization.username if request.authorization else None
        result = None
        try:
            result = upload_supplier_invoice_document(
                request.files.get("document"),
                supplier_invoice=supplier_invoice,
                actor=actor,
                db_session=self.session,
            )
            self.session.commit()
        except SupplierInvoiceDocumentValidationError as error:
            self.session.rollback()
            flash(str(error), "error")
            return redirect(request.url)
        except SupplierInvoiceDocumentImmutabilityError as error:
            self.session.rollback()
            flash(str(error), "error")
            return redirect(request.url)
        except SupplierInvoiceDocumentPersistenceError:
            self.session.rollback()
            current_app.logger.warning("Supplier document metadata persistence failed")
            flash("No se ha podido guardar la referencia del documento.", "error")
            return redirect(request.url)
        except SupplierInvoiceDocumentStorageConfigurationError:
            self.session.rollback()
            current_app.logger.warning("Supplier document storage configuration is missing")
            flash("El almacenamiento privado de documentos no está configurado.", "error")
            return redirect(request.url)
        except (SupplierInvoiceDocumentStorageOperationError, SupplierInvoiceDocumentError):
            self.session.rollback()
            current_app.logger.warning("Supplier document upload failed")
            flash("No se ha podido subir el documento privado.", "error")
            return redirect(request.url)
        except Exception:
            self.session.rollback()
            if result:
                _cleanup_supplier_document_after_commit_failure(result.document.storage_key)
            current_app.logger.exception("Unexpected supplier document upload failure")
            flash("No se ha podido subir el documento privado.", "error")
            return redirect(request.url)

        if result.duplicate_count:
            flash(
                "Se ha detectado un documento con el mismo hash. Revisa si es un duplicado antes de registrarlo.",
                "warning",
            )
        else:
            flash("Documento privado subido correctamente.", "success")
        if supplier_invoice:
            return redirect(self.get_url(".details_view", id=supplier_invoice.id))
        return redirect(self.get_url(".index_view"))

    @expose("/download-document/<int:document_id>", methods=["GET"])
    def download_document(self, document_id):
        document = self.session.get(SupplierInvoiceDocument, document_id)
        if not document:
            flash("Documento recibido no encontrado.", "error")
            return redirect(self.get_url(".index_view"))
        try:
            storage = get_supplier_invoice_document_storage(current_app)
            content = storage.get_document(storage_key=document.storage_key)
        except SupplierInvoiceDocumentStorageConfigurationError:
            current_app.logger.warning("Supplier document storage configuration is missing")
            flash("El almacenamiento privado de documentos no está configurado.", "error")
            return redirect(_supplier_document_redirect_url(self, document))
        except SupplierInvoiceDocumentStorageOperationError:
            current_app.logger.warning("Supplier document download failed document_id=%s", document.id)
            flash("No se ha podido descargar el documento privado.", "error")
            return redirect(_supplier_document_redirect_url(self, document))

        response = send_file(
            BytesIO(content),
            mimetype=document.mime_type,
            as_attachment=True,
            download_name=document.original_filename,
            max_age=0,
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @expose("/confirm-register/<int:supplier_invoice_id>", methods=["GET", "POST"])
    def confirm_register(self, supplier_invoice_id):
        supplier_invoice = self.session.get(SupplierInvoice, supplier_invoice_id)
        if not supplier_invoice:
            flash("Factura recibida no encontrada.", "error")
            return redirect(self.get_url(".index_view"))
        if supplier_invoice.status == SupplierInvoice.STATUS_REGISTERED:
            flash("La factura recibida ya está registrada.", "info")
            return redirect(self.get_url(".details_view", id=supplier_invoice.id))
        if supplier_invoice.status not in (
            SupplierInvoice.STATUS_DRAFT,
            SupplierInvoice.STATUS_NEEDS_REVIEW,
        ):
            flash("Esta factura recibida no puede registrarse desde su estado actual.", "error")
            return redirect(self.get_url(".details_view", id=supplier_invoice.id))

        duplicates = find_possible_supplier_invoice_duplicates(
            supplier_invoice,
            db_session=self.session,
        )
        if request.method == "GET":
            return self.render(
                "admin/supplier_invoice_register_confirm.html",
                supplier_invoice=supplier_invoice,
                duplicate_count=len(duplicates),
                action_url=self.get_url(".confirm_register", supplier_invoice_id=supplier_invoice.id),
                cancel_url=self.get_url(".details_view", id=supplier_invoice.id),
            )

        allow_duplicate = request.form.get("allow_duplicate") == "1"
        actor = request.authorization.username if request.authorization else None
        try:
            result = register_supplier_invoice(
                supplier_invoice,
                db_session=self.session,
                actor=actor,
                allow_duplicate=allow_duplicate,
            )
            self.session.commit()
            message = (
                f"Factura recibida registrada con número de recepción {result.invoice.reception_number}."
                if result.registered
                else "La factura recibida ya estaba registrada."
            )
            flash(message, "success" if result.registered else "info")
        except SupplierInvoiceDuplicateError:
            self.session.rollback()
            flash("Existe una posible factura duplicada. Marca la confirmación explícita para continuar.", "error")
            return redirect(self.get_url(".confirm_register", supplier_invoice_id=supplier_invoice.id))
        except SupplierInvoiceRegistrationValidationError as error:
            self.session.rollback()
            current_app.logger.warning(
                "Supplier invoice registration rejected invoice_id=%s",
                supplier_invoice_id,
            )
            flash(_supplier_invoice_registration_error_message(error), "error")
            return redirect(self.get_url(".details_view", id=supplier_invoice.id))
        except SupplierInvoiceRegistrationError:
            self.session.rollback()
            current_app.logger.warning(
                "Supplier invoice registration failed invoice_id=%s",
                supplier_invoice_id,
                exc_info=True,
            )
            flash("No se ha podido registrar la factura recibida. Revisa sus datos fiscales.", "error")
            return redirect(self.get_url(".details_view", id=supplier_invoice.id))
        except Exception:
            self.session.rollback()
            current_app.logger.exception(
                "Unexpected supplier invoice registration failure invoice_id=%s",
                supplier_invoice_id,
            )
            flash("No se ha podido registrar la factura recibida.", "error")
            return redirect(self.get_url(".details_view", id=supplier_invoice.id))

        return redirect(self.get_url(".details_view", id=supplier_invoice.id))


class InvoiceAdminView(SafeModelView):
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True

    column_list = [
        'id',
        'invoice_number',
        'invoice_type',
        'order_id',
        'client_name',
        'client_cif',
        'amount',
        'created_at',
        'issued_at',
        'pdf_path',
        'accounting_entries',
        'email_status',
        'invoice_snapshot_schema_version',
    ]
    column_details_list = [
        'id',
        'invoice_number',
        'invoice_type',
        'order_id',
        'client_name',
        'client_address',
        'client_cif',
        'amount',
        'created_at',
        'issued_at',
        'pdf_path',
        'accounting_entries',
        'email_status',
        'verifactu_records',
        'invoice_snapshot_schema_version',
    ]
    column_searchable_list = [
        'invoice_number',
        'client_name',
        'client_cif',
    ]
    column_filters = [
        'invoice_type',
        'email_status',
        'created_at',
        'issued_at',
        'invoice_snapshot_schema_version',
    ]
    column_sortable_list = [
        'id',
        'invoice_number',
        'invoice_type',
        'order_id',
        'client_name',
        'client_cif',
        'amount',
        'created_at',
        'issued_at',
        'email_status',
        'invoice_snapshot_schema_version',
    ]
    column_labels = {
        'id': 'ID',
        'invoice_number': 'N.º factura',
        'invoice_type': 'Tipo',
        'rectification_aeat_type': 'Tipo fiscal AEAT',
        'order_id': 'Pedido',
        'client_name': 'Cliente',
        'client_cif': 'NIF/CIF',
        'amount': 'Total',
        'created_at': 'Creada',
        'issued_at': 'Emitida',
        'pdf_path': 'PDF',
        'accounting_entries': 'Contabilidad',
        'email_status': 'Email',
        'verifactu_records': 'VeriFactu',
        'invoice_snapshot_schema_version': 'Versión snapshot',
    }
    column_formatters = {
        'invoice_number': _format_admin_invoice_value,
        'order_id': _format_admin_invoice_value,
        'client_name': _format_admin_invoice_value,
        'client_cif': _format_admin_invoice_value,
        'amount': _format_admin_invoice_amount,
        'created_at': _format_admin_invoice_datetime,
        'issued_at': _format_admin_invoice_datetime,
        'invoice_type': _format_admin_invoice_value,
        'rectification_aeat_type': _format_admin_invoice_value,
        'pdf_path': _format_admin_invoice_pdf_available,
        'accounting_entries': _format_admin_invoice_accounting_status,
        'email_status': _format_admin_invoice_value,
        'invoice_snapshot_schema_version': _format_admin_invoice_value,
    }
    column_formatters_detail = {
        **column_formatters,
        'invoice_type': _format_admin_invoice_type_detail,
        'pdf_path': _format_admin_invoice_pdf_detail,
        'accounting_entries': _format_admin_invoice_accounting_detail,
        'email_status': _format_admin_invoice_email_detail,
        'verifactu_records': _format_admin_invoice_verifactu_detail,
    }

    column_default_sort = ('created_at', True)

    @expose('/download-pdf/<int:invoice_id>')
    def download_pdf(self, invoice_id):
        invoice = self.session.get(Invoices, invoice_id)
        if not invoice:
            return Response('Factura no encontrada.', status=404)

        try:
            resolved_pdf = resolve_invoice_pdf_download(
                invoice,
                current_app.config.get("INVOICE_FOLDER"),
            )
            return send_file(
                resolved_pdf.file_path,
                as_attachment=True,
                download_name=resolved_pdf.download_name,
                mimetype='application/pdf',
            )
        except InvoicePdfDownloadUnavailable:
            return Response('PDF no disponible.', status=404)
        except InvoicePdfDownloadFileMissing:
            return Response('Archivo PDF no encontrado.', status=404)
        except InvoicePdfDownloadInvalidPath:
            return Response('Ruta de PDF no válida.', status=400)
        except Exception:
            current_app.logger.exception(
                "Unexpected Flask Admin invoice PDF download error for invoice %s",
                invoice_id,
            )
            return Response('No se ha podido descargar la factura.', status=500)

    @expose('/issue-total-rectification/<int:invoice_id>', methods=['GET', 'POST'])
    def issue_total_rectification(self, invoice_id):
        invoice = self.session.get(Invoices, invoice_id)
        if not invoice:
            flash('Factura no encontrada.', 'error')
            return redirect(self.get_url(".index_view"))

        if not _invoice_supports_total_rectification(invoice):
            flash('Esta factura no puede rectificarse desde administraci\u00f3n.', 'error')
            return redirect(self.get_url(".details_view", id=invoice.id))

        existing = _find_invoice_corrective_invoice(self, invoice)
        if request.method == 'GET':
            if existing is not None:
                flash(f'La factura ya tiene la rectificativa {existing.invoice_number}.', 'info')
                return redirect(self.get_url(".details_view", id=existing.id))
            return self.render(
                'admin/invoice_rectification_confirm.html',
                invoice=invoice,
                reason_choices=sorted(RECTIFICATION_REASON_TEXTS.items()),
                aeat_type_choices=sorted(SUPPORTED_TOTAL_RECTIFICATION_AEAT_TYPES),
                action_url=self.get_url(".issue_total_rectification", invoice_id=invoice.id),
                cancel_url=self.get_url(".details_view", id=invoice.id),
            )

        if request.form.get('rectification_scope') not in (None, '', 'total'):
            flash('La rectificaci\u00f3n parcial todav\u00eda no est\u00e1 soportada.', 'error')
            return redirect(self.get_url(".issue_total_rectification", invoice_id=invoice.id))

        reason = (request.form.get('rectification_reason') or '').strip()
        if reason not in RECTIFICATION_REASON_TEXTS:
            flash('Selecciona un motivo v\u00e1lido para la rectificaci\u00f3n.', 'error')
            return redirect(self.get_url(".issue_total_rectification", invoice_id=invoice.id))

        aeat_type = (request.form.get('rectification_aeat_type') or '').strip()
        if aeat_type not in SUPPORTED_TOTAL_RECTIFICATION_AEAT_TYPES:
            flash('Selecciona un tipo fiscal AEAT válido para la rectificación.', 'error')
            return redirect(self.get_url(".issue_total_rectification", invoice_id=invoice.id))

        if existing is not None:
            if _is_matching_admin_total_rectification(existing, reason, aeat_type):
                flash(f'La factura ya tiene la rectificativa {existing.invoice_number}.', 'info')
                return redirect(self.get_url(".details_view", id=existing.id))
            flash('La factura ya tiene una rectificativa incompatible.', 'error')
            return redirect(self.get_url(".details_view", id=invoice.id))

        try:
            result = issue_total_rectification_for_invoice(
                db_session=self.session,
                original_invoice_id=invoice.id,
                rectification_type='differences',
                rectification_reason=reason,
                rectification_aeat_type=aeat_type,
                rectification_scope='total',
                source='manual',
                actor=invoice_admin_actor_from_basic_auth(request.authorization),
            )
            flash(
                _admin_total_rectification_success_message(result),
                'success' if result.created else 'info',
            )
            return redirect(self.get_url(".details_view", id=result.invoice.id))
        except (InvoiceIssueError, InvoiceSnapshotValidationError, InvoiceNumberError, IntegrityError):
            self.session.rollback()
            current_app.logger.warning(
                "Invalid Flask Admin total rectification request for invoice %s",
                invoice_id,
                exc_info=True,
            )
            flash('No se ha podido emitir la rectificativa total para esta factura.', 'error')
        except Exception:
            self.session.rollback()
            current_app.logger.exception(
                "Unexpected Flask Admin total rectification error for invoice %s",
                invoice_id,
            )
            flash('No se ha podido emitir la rectificativa total.', 'error')

        return redirect(self.get_url(".details_view", id=invoice.id))

    @expose('/generate-pdf/<int:invoice_id>', methods=['POST'])
    def generate_pdf(self, invoice_id):
        invoice = self.session.get(Invoices, invoice_id)
        if not invoice:
            flash('Factura no encontrada.', 'error')
            return redirect(self.get_url(".index_view"))

        regenerate = bool(invoice.pdf_path)
        previous_pdf_path = invoice.pdf_path

        try:
            result = generate_invoice_pdf(
                invoice,
                regenerate=regenerate,
            )
            self.session.commit()
            flash(
                _admin_invoice_pdf_success_message(
                    regenerate=regenerate,
                    previous_pdf_path=previous_pdf_path,
                    result=result,
                ),
                'success',
            )
        except InvoicePdfSnapshotMissing:
            self.session.rollback()
            if not getattr(invoice, "invoice_number", None):
                flash('La factura todavía no está emitida.', 'error')
            else:
                flash('La factura no dispone de un snapshot fiscal válido.', 'error')
        except InvoicePdfIntegrityError:
            self.session.rollback()
            flash('No se puede generar el PDF porque la integridad fiscal no es válida.', 'error')
        except InvoicePdfUnsupportedSchema:
            self.session.rollback()
            flash('La versión del snapshot fiscal no está soportada.', 'error')
        except InvoicePdfWriteError as exc:
            self.session.rollback()
            if "sobrescribir" in str(exc).lower():
                flash('No se puede sobrescribir un PDF que no está asociado a esta factura.', 'error')
            else:
                flash('No se pudo generar el PDF.', 'error')
        except Exception:
            self.session.rollback()
            current_app.logger.exception(
                "Unexpected Flask Admin invoice PDF generation error for invoice %s",
                invoice_id,
            )
            flash('No se pudo generar el PDF.', 'error')

        return redirect(self.get_url(".details_view", id=invoice.id))

    @expose('/send-email/<int:invoice_id>', methods=['POST'])
    def send_invoice_email(self, invoice_id):
        invoice = self.session.get(Invoices, invoice_id)
        if not invoice:
            flash('Factura no encontrada.', 'error')
            return redirect(self.get_url(".index_view"))

        if request.args or request.form or (request.get_json(silent=True) or {}):
            flash('Esta acción no acepta datos de email desde el navegador.', 'error')
            return redirect(self.get_url(".details_view", id=invoice.id))

        if not invoice.invoice_number or not invoice.issued_at:
            flash('La factura debe estar emitida antes de enviarse por email.', 'error')
            return redirect(self.get_url(".details_view", id=invoice.id))

        if not invoice.pdf_path:
            flash('No existe PDF.', 'error')
            return redirect(self.get_url(".details_view", id=invoice.id))

        attempts_before = int(invoice.email_attempts or 0)

        try:
            adapter = FlaskMailInvoiceAdapter(mail)
            send_invoice_email_v2(
                invoice,
                mailer=adapter,
                invoice_folder=current_app.config.get("INVOICE_FOLDER"),
                allow_resend=True,
            )
            self.session.commit()
            flash('Factura enviada correctamente.', 'success')
        except InvoiceEmailRecipientMissing:
            self.session.rollback()
            flash('No existe email del cliente.', 'error')
        except InvoiceEmailPdfMissing:
            self.session.rollback()
            flash('No existe PDF.', 'error')
        except (InvoiceEmailSendError, FlaskMailInvoiceAdapterError):
            self.session.rollback()
            current_app.logger.exception(
                "Flask Admin invoice email SMTP error for invoice %s",
                invoice_id,
            )
            try:
                _persist_admin_invoice_email_failure(self.session, invoice_id, attempts_before)
            except Exception:
                self.session.rollback()
                current_app.logger.exception(
                    "Could not persist Flask Admin invoice email failure for invoice %s",
                    invoice_id,
                )
            flash('Error SMTP.', 'error')
        except InvoiceEmailSnapshotMissing:
            self.session.rollback()
            flash('La factura no contiene los datos necesarios para enviar el email.', 'error')
        except InvoiceEmailUnsupportedSchema:
            self.session.rollback()
            flash('La versión del snapshot fiscal no está soportada para email.', 'error')
        except InvoiceEmailIntegrityError:
            self.session.rollback()
            flash('No se puede enviar el email porque la integridad fiscal no coincide.', 'error')
        except Exception:
            self.session.rollback()
            current_app.logger.exception(
                "Unexpected Flask Admin invoice email error for invoice %s",
                invoice_id,
            )
            flash('No se ha podido enviar la factura por email.', 'error')

        return redirect(self.get_url(".details_view", id=invoice.id))

    @expose('/record-accounting/<int:invoice_id>', methods=['POST'])
    def record_accounting(self, invoice_id):
        invoice = self.session.get(Invoices, invoice_id)
        if not invoice:
            flash('Factura no encontrada.', 'error')
            return redirect(self.get_url(".index_view"))

        if request.args or request.form or (request.get_json(silent=True) or {}):
            flash('Esta acción no acepta datos contables desde el navegador.', 'error')
            return redirect(self.get_url(".details_view", id=invoice.id))

        try:
            existing_entry = _find_invoice_sale_accounting_entry(self, invoice)
            create_accounting_entry(invoice, db_session=self.session)
            self.session.commit()
            flash(
                _admin_invoice_accounting_success_message(
                    already_existed=existing_entry is not None,
                ),
                'success',
            )
        except AccountingEntryValidationError:
            self.session.rollback()
            current_app.logger.warning(
                "Invalid Flask Admin accounting entry request for invoice %s",
                invoice_id,
            )
            flash('La factura no contiene los datos necesarios para registrar contabilidad.', 'error')
        except AccountingEntryUnsupportedSchema:
            self.session.rollback()
            current_app.logger.warning(
                "Unsupported Flask Admin accounting snapshot schema for invoice %s",
                invoice_id,
            )
            flash('La versión del snapshot fiscal no es compatible con contabilidad.', 'error')
        except AccountingEntryIntegrityError:
            self.session.rollback()
            current_app.logger.warning(
                "Flask Admin accounting snapshot hash mismatch for invoice %s",
                invoice_id,
            )
            flash('No se puede registrar contabilidad porque la integridad fiscal no coincide.', 'error')
        except IntegrityError:
            self.session.rollback()
            current_app.logger.exception(
                "Flask Admin accounting entry conflict for invoice %s",
                invoice_id,
            )
            flash('Ya existe un registro contable para esta factura.', 'error')
        except Exception:
            self.session.rollback()
            current_app.logger.exception(
                "Unexpected Flask Admin accounting entry error for invoice %s",
                invoice_id,
            )
            flash('No se ha podido registrar contabilidad.', 'error')

        return redirect(self.get_url(".details_view", id=invoice.id))

    @expose('/generate-verifactu-record/<int:invoice_id>', methods=['POST'])
    def generate_verifactu_record(self, invoice_id):
        invoice = self.session.get(Invoices, invoice_id)
        if not invoice:
            flash('Factura no encontrada.', 'error')
            return redirect(self.get_url(".index_view"))

        if request.args or request.form or (request.get_json(silent=True) or {}):
            flash('Esta acción no acepta datos VeriFactu desde el navegador.', 'error')
            return redirect(self.get_url(".details_view", id=invoice.id))

        try:
            result = create_verifactu_registration_record(
                invoice,
                db_session=self.session,
                system_id=current_app.config.get("VERIFACTU_SYSTEM_ID"),
                software_name=current_app.config.get("VERIFACTU_SYSTEM_NAME"),
                software_version=current_app.config.get("VERIFACTU_SYSTEM_VERSION"),
            )
            self.session.commit()
            if result.created:
                flash('Registro VeriFactu generado correctamente.', 'success')
            else:
                flash('La factura ya tiene un registro VeriFactu generado.', 'success')
        except VeriFactuRecordUnsupportedSchema:
            self.session.rollback()
            flash('La versión del snapshot fiscal no está soportada para VeriFactu.', 'error')
        except VeriFactuRecordIntegrityError:
            self.session.rollback()
            flash('No se puede generar VeriFactu porque la integridad fiscal no coincide.', 'error')
        except VeriFactuRecordValidationError as exc:
            self.session.rollback()
            current_app.logger.warning("Invalid Flask Admin VeriFactu record request for invoice %s: %s", invoice_id, exc)
            flash(f'No se puede generar el registro VeriFactu: {exc}', 'error')
        except IntegrityError:
            self.session.rollback()
            current_app.logger.exception("Flask Admin VeriFactu record conflict for invoice %s", invoice_id)
            flash('La factura ya tiene un registro VeriFactu o se está creando en otra operación.', 'error')
        except Exception:
            self.session.rollback()
            current_app.logger.exception("Unexpected Flask Admin VeriFactu record generation error for invoice %s", invoice_id)
            flash('No se ha podido generar el registro VeriFactu.', 'error')

        return redirect(self.get_url(".details_view", id=invoice.id))

    @expose('/export-accounting')
    def export_accounting(self):
        entries = (
            self.session.query(AccountingEntry)
            .filter_by(entry_type=AccountingEntry.ENTRY_TYPE_SALE)
            .order_by(
                AccountingEntry.invoice_date.asc(),
                AccountingEntry.invoice_number.asc(),
                AccountingEntry.id.asc(),
            )
            .all()
        )

        if not entries:
            flash('No hay registros contables de ingresos para exportar.', 'error')
            return redirect(self.get_url(".index_view"))

        output_path = os.path.join(_admin_accounting_export_folder(), "ingresos_completo.xlsx")

        try:
            result = export_sales_accounting_entries(entries, output_path=output_path, overwrite=True)
            return send_file(
                result.output_path,
                as_attachment=True,
                download_name=result.filename,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except AccountingExcelExportError:
            current_app.logger.exception("Flask Admin accounting sales export failed")
            flash('No se ha podido generar la exportación de ingresos.', 'error')
        except Exception:
            current_app.logger.exception("Unexpected Flask Admin accounting sales export error")
            flash('No se ha podido generar la exportación de ingresos.', 'error')

        return redirect(self.get_url(".index_view"))

    @expose('/export-aeat-accounting')
    def export_aeat_accounting(self):
        entries = (
            self.session.query(AccountingEntry)
            .filter_by(entry_type=AccountingEntry.ENTRY_TYPE_SALE)
            .order_by(
                AccountingEntry.invoice_date.asc(),
                AccountingEntry.invoice_number.asc(),
                AccountingEntry.id.asc(),
            )
            .all()
        )

        if not entries:
            flash('No hay registros contables de ingresos para exportar al libro AEAT.', 'error')
            return redirect(self.get_url(".index_view"))

        output_path = os.path.join(_admin_accounting_export_folder(), "aeat_expedidas_ingresos.xlsx")

        try:
            result = export_aeat_sales_ledger(entries, output_path=output_path, overwrite=True)
            return send_file(
                result.output_path,
                as_attachment=True,
                download_name=result.filename,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except AeatSalesLedgerError as exc:
            current_app.logger.exception("Flask Admin AEAT sales ledger export failed")
            flash(f'No se puede generar el libro AEAT: {exc}', 'error')
        except Exception:
            current_app.logger.exception("Unexpected Flask Admin AEAT sales ledger export error")
            flash('No se ha podido generar el libro AEAT de ingresos.', 'error')

        return redirect(self.get_url(".index_view"))


class VeriFactuRecordAdminView(SafeModelView):
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True

    column_list = [
        'id',
        'invoice_id',
        'record_type',
        'status',
        'invoice_number',
        'invoice_snapshot_hash',
        'record_payload_hash',
        'fingerprint_status',
        'fingerprint',
        'chain_sequence',
        'previous_record_id',
        'system_id',
        'software_name',
        'software_version',
        'ready_at',
        'created_at',
    ]
    column_details_list = [
        'id',
        'invoice_id',
        'provider',
        'mode',
        'record_type',
        'status',
        'schema_version',
        'invoice_number',
        'invoice_issued_at',
        'invoice_snapshot_hash',
        'record_payload_hash',
        'official_payload_schema_version',
        'chain_key',
        'chain_sequence',
        'fingerprint',
        'fingerprint_algorithm',
        'fingerprint_status',
        'fingerprint_input',
        'fingerprint_calculated_at',
        'previous_record_id',
        'previous_fingerprint',
        'is_first_record',
        'system_id',
        'software_name',
        'software_version',
        'installation_id',
        'producer_name',
        'producer_tax_id',
        'generation_timestamp',
        'generation_timezone',
        'ready_at',
        'issuer_tax_id',
        'recipient_tax_id',
        'total_amount',
        'currency',
        'created_at',
        'updated_at',
    ]
    column_searchable_list = [
        'invoice_number',
        'issuer_tax_id',
        'recipient_tax_id',
        'system_id',
    ]
    column_filters = [
        'record_type',
        'status',
        'fingerprint_status',
        'chain_key',
        'software_name',
        'ready_at',
        'created_at',
    ]
    column_sortable_list = [
        'id',
        'invoice_id',
        'record_type',
        'status',
        'invoice_number',
        'chain_sequence',
        'ready_at',
        'created_at',
    ]
    column_labels = {
        'id': 'ID',
        'invoice_id': 'Factura',
        'provider': 'Proveedor',
        'mode': 'Modalidad',
        'record_type': 'Tipo registro',
        'status': 'Estado',
        'schema_version': 'Versión esquema',
        'invoice_number': 'N.º factura',
        'invoice_issued_at': 'Emitida',
        'invoice_snapshot_hash': 'Hash snapshot interno',
        'record_payload_hash': 'Hash registro interno',
        'fingerprint': 'Huella VeriFactu',
        'fingerprint_algorithm': 'Algoritmo huella',
        'fingerprint_status': 'Estado huella',
        'chain_key': 'Clave de cadena',
        'chain_sequence': 'Secuencia',
        'official_payload_schema_version': 'Version payload oficial',
        'fingerprint_input': 'Cadena de huella',
        'fingerprint_calculated_at': 'Huella calculada',
        'previous_record_id': 'Registro anterior',
        'previous_fingerprint': 'Huella anterior',
        'is_first_record': 'Primer registro',
        'installation_id': 'N. instalacion',
        'producer_name': 'Productor',
        'producer_tax_id': 'NIF productor',
        'generation_timestamp': 'Generado',
        'generation_timezone': 'Huso horario',
        'ready_at': 'Preparado',
        'system_id': 'Instalación',
        'software_name': 'Software',
        'software_version': 'Versión software',
        'issuer_tax_id': 'NIF emisor',
        'recipient_tax_id': 'NIF destinatario',
        'total_amount': 'Total',
        'currency': 'Moneda',
        'created_at': 'Creado',
        'updated_at': 'Actualizado',
    }
    column_formatters = {
        'invoice_issued_at': _format_admin_invoice_datetime,
        'fingerprint_calculated_at': _format_admin_invoice_datetime,
        'generation_timestamp': _format_admin_invoice_datetime,
        'ready_at': _format_admin_invoice_datetime,
        'created_at': _format_admin_invoice_datetime,
        'updated_at': _format_admin_invoice_datetime,
        'total_amount': _format_admin_invoice_amount,
        'fingerprint': _format_admin_invoice_value,
        'fingerprint_algorithm': _format_admin_invoice_value,
        'previous_fingerprint': _format_admin_invoice_value,
    }
    column_formatters_detail = column_formatters
    column_default_sort = ('created_at', True)

    @action(
        'prepare_verifactu_records',
        'Preparar VeriFactu',
        'Calcular huella y marcar READY para los registros seleccionados?',
    )
    def action_prepare_verifactu_records(self, ids):
        current_app.logger.info(
            "VeriFactu admin prepare action entered ids=%r ids_type=%s",
            ids,
            type(ids).__name__,
        )
        selected_ids = list(ids or [])
        current_app.logger.info(
            "VeriFactu admin prepare action normalized ids=%r",
            selected_ids,
        )
        if not selected_ids:
            flash('Selecciona al menos un registro VeriFactu.', 'warning')
            return redirect(self.get_url(".index_view"))

        prepared = 0
        already_ready = 0
        skipped = 0
        missing = 0

        try:
            system_identity = verifactu_system_identity_from_config(current_app.config)
            for record_id in selected_ids:
                current_app.logger.info(
                    "VeriFactu admin prepare action loading record_id=%r",
                    record_id,
                )
                try:
                    record_pk = int(record_id)
                except (TypeError, ValueError):
                    missing += 1
                    continue

                record = self.session.get(VeriFactuRecord, record_pk)
                current_app.logger.info(
                    "VeriFactu admin prepare action loaded record id=%s status=%s",
                    getattr(record, "id", None),
                    getattr(record, "status", None),
                )
                if record is None:
                    missing += 1
                    continue
                if record.status == VeriFactuRecord.STATUS_READY:
                    already_ready += 1
                    continue
                if record.status != VeriFactuRecord.STATUS_BUILT:
                    skipped += 1
                    continue
                current_app.logger.info(
                    "VeriFactu admin prepare action calling prepare service record_id=%s",
                    record.id,
                )
                result = prepare_verifactu_record_for_submission(
                    record,
                    db_session=self.session,
                    system_identity=system_identity,
                )
                current_app.logger.info(
                    "VeriFactu admin prepare action prepare service returned record_id=%s prepared=%s",
                    record.id,
                    getattr(result, "prepared", None),
                )
                if result.prepared:
                    prepared += 1
                else:
                    already_ready += 1
            current_app.logger.info(
                "VeriFactu admin prepare action committing prepared=%s already_ready=%s skipped=%s missing=%s",
                prepared,
                already_ready,
                skipped,
                missing,
            )
            self.session.commit()
            current_app.logger.info(
                "VeriFactu admin prepare action committed prepared=%s already_ready=%s skipped=%s missing=%s",
                prepared,
                already_ready,
                skipped,
                missing,
            )

            messages = [f'Registros VeriFactu preparados: {prepared}.']
            if already_ready:
                messages.append(f'Ya preparados: {already_ready}.')
            if skipped:
                messages.append(f'Omitidos por estado no preparable: {skipped}.')
            if missing:
                messages.append(f'No encontrados: {missing}.')
            flash(' '.join(messages), 'success' if prepared else 'warning')
        except (
            VeriFactuRecordValidationError,
            VeriFactuRecordIntegrityError,
            VeriFactuRecordConcurrencyError,
        ) as exc:
            self.session.rollback()
            current_app.logger.warning("VeriFactu admin preparation rejected: %s", exc, exc_info=True)
            flash(str(exc), 'error')
        except Exception:
            self.session.rollback()
            current_app.logger.exception("Unexpected VeriFactu admin preparation error")
            flash('No se han podido preparar los registros VeriFactu.', 'error')

        return redirect(self.get_url(".index_view"))

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
    admin.add_view(SupplierInvoiceAdminView(SupplierInvoice, db.session, name="Facturas recibidas"))
    admin.add_view(InvoiceAdminView(Invoices, db.session))
    admin.add_view(VeriFactuRecordAdminView(VeriFactuRecord, db.session, name="VeriFactu"))
    admin.add_view(SafeModelView(DeliveryEstimateConfig, db.session))

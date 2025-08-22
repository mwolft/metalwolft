from flask import Blueprint, request, jsonify, current_app
from flask_mail import Mail, Message
from sqlalchemy import event, inspect as sqla_inspect
from api.models import db, Orders
import os

email_bp = Blueprint('email_bp', __name__)
mail = Mail()

def configure_mail(app):
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'tu_correo@example.com')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'tu_contraseña')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
    mail.init_app(app)

def send_email(subject, recipients, body, attachment_path=None, html=None):
    try:
        msg = Message(subject, recipients=recipients, body=body, html=html)
        if attachment_path:
            with open(attachment_path, 'rb') as f:
                msg.attach(filename=os.path.basename(attachment_path),
                           content_type='application/pdf',
                           data=f.read())
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"❌ Error enviando correo: {str(e)}")
        return False

@email_bp.route('/contact', methods=['POST'])
def contact():
    try:
        data = request.get_json()

        # Validación de datos
        if not data or not all(key in data for key in ('name', 'firstname', 'phone', 'email', 'message')):
            return jsonify({"error": "Faltan datos obligatorios."}), 400

        # Preparar el correo
        message = Message(
            subject="Mensaje desde la web",
            sender=os.getenv('MAIL_DEFAULT_SENDER'),
            recipients=['admin@metalwolft.com'],
            body=(
                f"Nombre: {data['name']} {data['firstname']}\n"
                f"Teléfono: {data['phone']}\n"
                f"Correo: {data['email']}\n"
                f"Mensaje: {data['message']}"
            )
        )

        # Enviar el correo
        mail.send(message)
        return jsonify({"message": "Mensaje enviado correctamente."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@event.listens_for(Orders, 'after_update')
def enviar_correo_cambio_estado_o_entrega(mapper, connection, target: Orders):
    """
    Envía correo SOLO cuando:
    - Cambia el estado (order_status): email de progreso (incluye fecha estimada si existe).
    - Cambia la entrega estimada (estimated_delivery_at / estimated_delivery_note): email específico.
    """
    try:
        # Detecta cambios reales en este UPDATE
        insp = sqla_inspect(target)
        changed = {attr.key for attr in insp.attrs if attr.history.has_changes()}

        # Campos de entrega (solo si existen ya en el modelo)
        campos_entrega = set()
        if hasattr(target, 'estimated_delivery_at'):
            campos_entrega.add('estimated_delivery_at')
        if hasattr(target, 'estimated_delivery_note'):
            campos_entrega.add('estimated_delivery_note')

        cambio_estado = 'order_status' in changed
        cambio_entrega = len(changed.intersection(campos_entrega)) > 0

        # Si no cambió nada relevante, salimos
        if not cambio_estado and not cambio_entrega:
            return

        # Datos comunes
        try:
            email = target.user.email  # relación ya cargada normalmente
        except Exception:
            email = None

        locator = getattr(target, 'locator', None) or '—'
        estado_actual = getattr(target, 'order_status', None)

        # Estados en el mismo orden que usas en frontend/admin
        estados = [
            ('pendiente', 'Pendiente'),
            ('fabricacion', 'Fabricación'),
            ('pintura', 'Pintura'),
            ('embalaje', 'Embalaje'),
            ('enviado', 'Enviado'),
            ('entregado', 'Entregado'),
        ]

        # Helpers de entrega estimada
        def fmt_fecha_estimada():
            if hasattr(target, 'estimated_delivery_at') and target.estimated_delivery_at:
                return target.estimated_delivery_at.strftime("%d/%m/%Y")
            return None

        def bloque_entrega_html():
            fecha = fmt_fecha_estimada()
            nota = getattr(target, 'estimated_delivery_note', None) if hasattr(target, 'estimated_delivery_note') else None
            if not fecha and not nota:
                return ""
            extra = []
            if fecha:
                extra.append(f"<div>📅 <strong>Fecha estimada de entrega:</strong> {fecha}</div>")
            if nota:
                extra.append(f"<div>📝 <em>{nota}</em></div>")
            return f"""<div style="margin-top:12px;">{''.join(extra)}</div>"""

        # 1) Cambio de estado: email con barra de progreso + bloque de entrega si existe
        if cambio_estado and estado_actual and email:
            # si sigue en 'pendiente', opcionalmente puedes no enviar:
            # if estado_actual == 'pendiente': return

            indice_actual = next((i for i, (val, _) in enumerate(estados) if val == estado_actual), -1)
            if indice_actual == -1:
                return  # estado no reconocido

            circulos = ""
            etiquetas = ""
            for i, (valor, texto) in enumerate(estados):
                if i < indice_actual:
                    color = "#4CAF50"  # Completado
                    icono = "✔"
                elif i == indice_actual:
                    color = "#ff324d"  # Actual (tu color)
                    icono = str(i + 1)
                else:
                    color = "#ccc"     # Pendiente
                    icono = str(i + 1)

                circulos += f"""
                    <td>
                        <div style="margin: auto; background-color: {color}; color: white; width: 30px; height: 30px;
                                    border-radius: 50%; line-height: 30px; font-weight: bold;">
                            {icono}
                        </div>
                    </td>
                """
                etiquetas += f"""<td style="padding-top: 5px; font-size: 12px;">{texto}</td>"""

            html_body = f"""
            <p style="font-weight: bold; font-size: 18px; margin-bottom: 10px;">📦 Estado de su pedido</p>
            <p>Estimado cliente,</p>
            <p>Su pedido ha cambiado de estado y ahora se encuentra en la fase: <strong>{estados[indice_actual][1]}</strong>.</p>

            <table style="width: 100%; text-align: center; margin: 30px 0;">
              <tr>{circulos}</tr>
              <tr>{etiquetas}</tr>
            </table>

            <p style="margin-top: 10px;">📍 <strong>Localizador:</strong> {locator}</p>
            {bloque_entrega_html()}

            <p style="margin-top: 20px; font-size: 14px; color: #333;">
              Gracias por confiar en <span style="font-weight: bold; color: #000;">Metal Wolft</span>.<br>
              Si tienes cualquier duda, puedes responder directamente a este correo.
            </p>
            """

            send_email(
                subject=f"Actualización de tu pedido: {estados[indice_actual][1]}",
                recipients=[email],
                body="",
                html=html_body
            )

        # 2) Cambio de entrega estimada (fecha/nota) sin cambio de estado: email breve
        elif cambio_entrega and email:
            fecha = fmt_fecha_estimada()
            nota = getattr(target, 'estimated_delivery_note', None) if hasattr(target, 'estimated_delivery_note') else None

            partes = ["<p>Estimado cliente,</p>"]
            if fecha:
                partes.append(f"<p>Hemos actualizado la <strong>fecha estimada de entrega</strong> a: <strong>{fecha}</strong>.</p>")
            if nota:
                partes.append(f"<p>Nota: <em>{nota}</em></p>")
            partes.append(f"<p>📍 <strong>Localizador:</strong> {locator}</p>")
            partes.append("""
              <p style="margin-top: 20px; font-size: 14px; color: #333;">
                Gracias por confiar en <span style="font-weight: bold; color: #000;">Metal Wolft</span>.
              </p>
            """)
            html_body = "\n".join(partes)

            send_email(
                subject="Actualización: entrega estimada de tu pedido",
                recipients=[email],
                body="",
                html=html_body
            )

    except Exception as e:
        try:
            current_app.logger.error(f"❌ Error en listener after_update: {str(e)}")
        except Exception:
            pass


@email_bp.route('/test-change-order-status', methods=['POST'])
def test_change_order_status():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        new_status = data.get('order_status')

        if not order_id or not new_status:
            return jsonify({"error": "Faltan datos: 'order_id' y 'order_status' son obligatorios."}), 400

        order = Orders.query.get(order_id)
        if not order:
            return jsonify({"error": f"No se encontró el pedido con ID {order_id}."}), 404

        order.order_status = new_status
        db.session.commit()

        return jsonify({"message": f"Estado del pedido {order_id} actualizado a '{new_status}'."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
    
def send_order_status_email(user_email, order_status, locator):
    try:
        subject = f"Actualización de tu pedido ({locator})"
        body = f"Tu pedido con localizador {locator} ha cambiado de estado a: {order_status}."

        msg = Message(
            subject=subject,
            recipients=[user_email],
            body=body
        )

        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Error al enviar correo de estado del pedido: {str(e)}")
        return False


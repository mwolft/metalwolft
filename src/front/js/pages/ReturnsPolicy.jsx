import React from 'react';
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../component/Breadcrumb.jsx';

export const ReturnsPolicy = () => {
    return (
        <>
            <Breadcrumb />
            <div className="container py-5">
                <h1>Política de Devolución</h1>
                <p>En Metal Wolft, valoramos tu satisfacción y queremos ofrecerte productos de alta calidad. Si no estás satisfecho con tu compra, ofrecemos la posibilidad de devolver los artículos según nuestra política de devolución.</p>

                <h2>Plazo de Devolución</h2>
                <p>Dispones de siete (7) días hábiles desde la recepción del producto para solicitar una devolución. Pasado este plazo, no aceptaremos devoluciones.</p>

                <h2>Requisitos para la Devolución</h2>
                <ul>
                    <li><strong>Devolución por Error o Producto Dañado:</strong> Solo se aceptarán devoluciones en caso de error o si el artículo está dañado. Debes comunicarte con nosotros previamente por teléfono al +34 634112604 o al correo <a href="mailto:admin@metalwolft.com">admin@metalwolft.com</a>.</li>
                    <li><strong>Estado y Embalaje:</strong> El producto debe estar en el mismo estado que al ser entregado, con su embalaje original y en una caja adecuada para su protección.</li>
                    <li><strong>Incluir Factura:</strong> Adjunta una copia de la factura de compra dentro del paquete, indicando los artículos devueltos y el motivo de la devolución.</li>
                </ul>

                <h2>Costes de Envío</h2>
                <p>Si la devolución es por error o daño, cubriremos los gastos de envío de retorno. En otros casos, el cliente asumirá los costos de envío de devolución y los del producto de reemplazo si aplica.</p>

                <h2>Opciones de Devolución</h2>
                <ul>
                    <li><strong>Sustitución:</strong> Reemplazo del producto por uno igual o similar.</li>
                    <li><strong>Reembolso:</strong> Devolución del importe, preferiblemente a través del método de pago original.</li>
                    <li><strong>Cupón de Descuento:</strong> Emitimos un cupón de descuento por el importe correspondiente, que podrás usar en futuras compras.</li>
                </ul>

                <h2>Cancelación de Pedidos</h2>
                <p>Para cancelar un pedido, contáctanos antes de que se procese. Si ya has realizado el pago, procederemos a cancelar el pedido y reembolsar el importe si el pedido aún no ha sido fabricado.</p>

                <p>Si tienes alguna pregunta o necesitas ayuda con una devolución, contáctanos. Estamos aquí para ayudarte.</p>
            </div>
        </>
    );
};

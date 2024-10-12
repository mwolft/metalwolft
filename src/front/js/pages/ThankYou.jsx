import React, { useContext, useEffect, useState } from 'react';
import { Context } from "../store/appContext";

export const ThankYou = () => {
    const { store } = useContext(Context);
    const [orderSummary, setOrderSummary] = useState(null);

    useEffect(() => {
        // Si los datos ya están en el store, podemos usarlos directamente
        if (store.orders.length > 0) {
            const lastOrder = store.orders[store.orders.length - 1]; // Última orden guardada
            setOrderSummary(lastOrder);
        }
    }, [store.orders]);

    if (!orderSummary) {
        return <div>Cargando el resumen de tu compra...</div>;
    }

    return (
        <div style={{ marginTop: '100px' }}>
            <h1>Gracias por tu compra</h1>
            <p>Tu pago ha sido procesado exitosamente.</p>

            {/* Resumen de la orden */}
            <h2>Resumen de la orden</h2>
            <p><strong>Número de Factura:</strong> {orderSummary.invoice_number}</p>
            <p><strong>Localizador:</strong> {orderSummary.locator}</p>
            <p><strong>Total:</strong> {orderSummary.total_amount} €</p>

            {/* Detalles de los productos */}
            <h3>Detalles del pedido</h3>
            {store.orderDetails.length > 0 ? (
                store.orderDetails.map((detail, index) => (
                    <div key={index}>
                        {/* Validación adicional para evitar errores si product es undefined */}
                        {detail.product ? (
                            <>
                                <p><strong>Producto:</strong> {detail.product.nombre || 'Nombre no disponible'}</p>
                                <p><strong>Cantidad:</strong> {detail.quantity}</p>
                                <p><strong>Alto:</strong> {detail.alto}</p>
                                <p><strong>Ancho:</strong> {detail.ancho}</p>
                                <p><strong>Color:</strong> {detail.color}</p>
                                <p><strong>Precio total:</strong> {detail.precio_total} €</p>
                                <hr />
                            </>
                        ) : (
                            <p>Información del producto no disponible.</p>
                        )}
                    </div>
                ))
            ) : (
                <p>No hay detalles del pedido disponibles.</p>
            )}

            {/* Detalles de envío */}
            <h3>Dirección de Envío</h3>
            <p><strong>Nombre:</strong> {orderSummary.firstname} {orderSummary.lastname}</p>
            <p><strong>Dirección:</strong> {orderSummary.shipping_address}</p>
            <p><strong>Ciudad:</strong> {orderSummary.shipping_city}</p>
            <p><strong>Código Postal:</strong> {orderSummary.shipping_postal_code}</p>
        </div>
    );
};

import React, { useContext, useEffect, useState } from 'react';
import { Context } from "../store/appContext";
import { Button } from "react-bootstrap";
import { useNavigate } from 'react-router-dom';

export const ThankYou = () => {
    const { store } = useContext(Context);
    const [orderSummary, setOrderSummary] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        if (store.orders.length > 0) {
            const lastOrder = store.orders[store.orders.length - 1];
            setOrderSummary(lastOrder);
        }
    }, [store.orders]);

    if (!orderSummary) {
        return <div>Cargando el resumen de tu compra...</div>;
    }

    return (
        <div className="container" style={{ marginTop: '100px', marginBottom: '250px' }}>
            <div className="row">
                <div className="col-11 text-center">
                    <h1>Gracias por tu compra</h1>
                    <p>Tu pago ha sido procesado correctamente.</p>
                    <p>
                        <strong>Localizador:</strong> {orderSummary.locator}
                    </p>
                    <p>
                        Tu factura se ha enviado al correo: <strong>{store.user?.email}</strong>
                    </p>
                    <Button
                        className="btn btn-style-background-color"
                        onClick={() => navigate('/')}>
                        Volver al inicio
                    </Button>
                </div>
            </div>
        </div>
    );
};

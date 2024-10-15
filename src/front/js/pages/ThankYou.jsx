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
                <div className="col-11">
                    <h1 className='text-center'>Gracias por su compra</h1>
                    <p className='text-center'>Tu pago ha sido procesado correctamente</p>
                    <p className='mt-5'><strong>Número de Factura:</strong> {orderSummary.invoice_number}</p>
                    <p><strong>Localizador:</strong> {orderSummary.locator}</p>
                    <Button
                        className="btn btn-style-background-color btn-block my-5"
                        onClick={() => navigate('/')}>
                        Volver a inicio
                    </Button>
                </div>
            </div>
        </div>
    );
};

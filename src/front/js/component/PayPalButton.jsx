import React from 'react';
import { PayPalButtons } from "@paypal/react-paypal-js";

const PayPalButton = ({ amount, onSuccess }) => {
    return (
        <div style={{ minHeight: '200px', overflow: 'hidden', marginBottom: '20px' }}> {/* Ajusta según el tamaño necesario */}
            <PayPalButtons
                style={{ layout: 'vertical' }}
                createOrder={(data, actions) => {
                    return actions.order.create({
                        purchase_units: [{
                            amount: {
                                value: amount, // Monto total de la compra
                            },
                        }],
                    });
                }}
                onApprove={(data, actions) => {
                    return actions.order.capture().then((details) => {
                        onSuccess(details); // Llama la función onSuccess tras una compra exitosa
                    });
                }}
                onError={(err) => {
                    console.error("PayPal Checkout onError", err);
                }}
            />
        </div>
    );    
}

export default PayPalButton;

import React, { useEffect } from "react";

const PayPalButton = () => {
    useEffect(() => {
        // Cargar el script de PayPal dinámicamente si aún no está cargado
        const script = document.createElement('script');
        script.src = "https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID";
        script.addEventListener('load', () => {
            window.paypal.Buttons({
                createOrder: (data, actions) => {
                    return actions.order.create({
                        purchase_units: [{
                            amount: {
                                value: '10.00' // Ajusta el valor según el total
                            }
                        }]
                    });
                },
                onApprove: (data, actions) => {
                    return actions.order.capture().then(function (details) {
                        alert('Transacción completada por ' + details.payer.name.given_name);
                    });
                }
            }).render('#paypal-button-container');
        });
        document.body.appendChild(script);
    }, []);

    return <div id="paypal-button-container"></div>;
};

export default PayPalButton;

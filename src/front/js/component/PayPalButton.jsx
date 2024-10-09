import React, { useEffect } from "react";

const PayPalButton = () => {
    useEffect(() => {
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
    }, []);

    return <div id="paypal-button-container"></div>;
};

export default PayPalButton;

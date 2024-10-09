import React, { useContext } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Form } from "react-bootstrap";

// Cargar la clave pública de Stripe
const stripePromise = loadStripe('pk_test_51I1FgUDyMBNofWjFVmq85bCUIBbzjopkQw1VWtt7I9Gp0trmFwYH0O60Heuit0BOaaa2dEJvEMzaB90uGxjr5Cuw00hVfWhV4y');

const CheckoutForm = () => {
    const stripe = useStripe();
    const elements = useElements();
    const { store } = useContext(Context);  // Obtener el carrito y otros datos del estado global

    const handleSubmit = async (event) => {
        event.preventDefault();
    
        if (!stripe || !elements) {
            return;
        }
    
        const cardElement = elements.getElement(CardElement);
    
        const { error, paymentMethod } = await stripe.createPaymentMethod({
            type: 'card',
            card: cardElement,
        });
    
        if (error) {
            console.log('[Error]', error);
            return;
        }
    
        console.log('Método de pago creado:', paymentMethod);
    
        // Enviar el método de pago al backend para crear o verificar un Payment Intent
        const response = await fetch(`${process.env.BACKEND_URL}/api/create-payment-intent`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount: total * 100,  // Convertir a centavos
                payment_method_id: paymentMethod.id,
                payment_intent_id: store.paymentIntentId  // Si ya existe, incluir el PaymentIntent ID
            }),
        });
    
        const data = await response.json();
    
        if (data.paymentIntent && data.paymentIntent.status === 'succeeded') {
            console.log('El pago ya ha sido completado');
            window.location.href = "/thank-you";
            return;
        }
    
        // Confirmar el intento de pago con el clientSecret si es necesario
        const { error: confirmError } = await stripe.confirmCardPayment(data.clientSecret);
        if (confirmError) {
            console.log('[Error]', confirmError);
            return;
        }
    
        console.log('Pago exitoso');
        // Vaciar el carrito y redirigir a una página de agradecimiento
        actions.clearCart();  // Esta función debería vaciar el carrito
        window.location.href = "/thank-you";  // Redirigir al usuario a una página de confirmación o agradecimiento
    };    
    

    // Calcular el total del carrito
    const total = store.cart.reduce((acc, product) => acc + parseFloat(product.precio_total), 0);

    return (
        <Container className="mt-5">
            <Row>
                <Col md={6} className="mx-auto">
                    <h2 className="text-center my-4">Checkout</h2>
                    <p className="text-center">Total a pagar: {total.toFixed(2)} €</p>
                    <Form onSubmit={handleSubmit}>
                        <Form.Group controlId="card-element">
                            <Form.Label>Detalles de la tarjeta</Form.Label>
                            <CardElement />
                        </Form.Group>
                        <Button type="submit" disabled={!stripe} className="btn-style-background-color mt-4">
                            Pagar
                        </Button>
                    </Form>
                </Col>
            </Row>
        </Container>
    );
};

// Envolver CheckoutForm con Elements para Stripe
const CheckoutWrapper = () => {
    return (
        <Elements stripe={stripePromise}>
            <CheckoutForm />
        </Elements>
    );
};

export default CheckoutWrapper;

import React, { useContext, useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Form, Accordion } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import PayPalButton from './PayPalButton.jsx'; // Importar el botón de PayPal
import { PayPalScriptProvider } from "@paypal/react-paypal-js";

const stripePromise = loadStripe('pk_test_51I1FgUDyMBNofWjFVmq85bCUIBbzjopkQw1VWtt7I9Gp0trmFwYH0O60Heuit0BOaaa2dEJvEMzaB90uGxjr5Cuw00hVfWhV4y');

const CheckoutForm = () => {
    const stripe = useStripe();
    const elements = useElements();
    const { store, actions } = useContext(Context);
    const [paymentMethod, setPaymentMethod] = useState("stripe"); // Estado para seleccionar entre Stripe y PayPal
    const [differentBilling, setDifferentBilling] = useState(false);
    const [formData, setFormData] = useState({
        firstname: "",
        lastname: "",
        shipping_address: "",
        shipping_city: "",
        shipping_postal_code: "",
        billing_address: "",
        billing_city: "",
        billing_postal_code: "",
        CIF: ""
    });
    const navigate = useNavigate();
    // Manejar cambios en los campos del formulario
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    const handlePayPalSuccess = (details) => {
        console.log("Pago exitoso con PayPal:", details);
        // Guardar la orden y vaciar el carrito
        actions.saveOrder();
        actions.clearCart();
        navigate("/thank-you");
    };
    // Pago con Stripe
    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!stripe || !elements) return;

        const cardElement = elements.getElement(CardElement);
        const { error, paymentMethod } = await stripe.createPaymentMethod({
            type: 'card',
            card: cardElement,
        });
        if (error) {
            alert(`Error en el pago: ${error.message}`);
            return;
        }

        // Convertir el total a un número entero para evitar errores con Stripe
        const convertedAmount = Math.round(total * 100);

        // Enviar la solicitud de creación de Payment Intent a tu backend
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/create-payment-intent`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount: convertedAmount,
                payment_method_id: paymentMethod.id,
                payment_intent_id: store.paymentIntentId  // Si ya tienes un paymentIntent guardado
            }),
        });

        const data = await response.json();
        console.log("Response from create-payment-intent:", data);  // Para depuración

        if (!data || !data.clientSecret) {
            alert("Hubo un error en la creación del intento de pago.");
            return;
        }

        // Verificar si el PaymentIntent ya ha sido confirmado
        if (data.paymentIntent && data.paymentIntent.status === 'succeeded') {
            console.log("El PaymentIntent ya está completado.");

            console.log("Datos que se envían al backend:", {
                total_amount: total,
                products: store.cart,
                ...formData
            });
            
        // Guardar la orden en el backend
        const { ok, order, error } = await actions.saveOrder({
            total_amount: total,
            products: store.cart.map(product => ({
                producto_id: product.producto_id,
                quantity: product.quantity || 1, // Asignar 1 como predeterminado si no existe
                alto: product.alto,
                ancho: product.ancho,
                anclaje: product.anclaje,
                color: product.color,
                precio_total: product.precio_total
            })),
            ...formData
        });

        // Log para depuración
        console.log("Datos que se envían al backend:", {
            total_amount: total,
            products: store.cart.map(product => ({
                producto_id: product.producto_id,
                quantity: product.quantity || 1,
                alto: product.alto,
                ancho: product.ancho,
                anclaje: product.anclaje,
                color: product.color,
                precio_total: product.precio_total
            })),
            ...formData
        });
                        
            
            if (!ok) {
                console.error("Error al guardar la orden:", error);
                alert("No se pudo procesar tu pedido. Por favor, inténtalo nuevamente.");
                return;
            }
            
            // Enviar los datos de facturación y envío junto con los detalles de la orden
            const result = await actions.saveOrderDetails(order.id, formData);
            if (!result.ok) {
                console.error("Error al guardar los detalles de la orden.");
                alert("Error al guardar los detalles de la orden.");
                return;
            }
            

            // Limpiar el carrito en el frontend y backend
            actions.clearCart();
            localStorage.removeItem("cart");

            await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/cart/clear`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${localStorage.getItem("token")}`
                }
            });

            console.log("Carrito vaciado");
            navigate("/thank-you");
            return;
        }

        // Confirmar el pago con Stripe
        const { error: confirmError, paymentIntent: confirmedPaymentIntent } = await stripe.confirmCardPayment(data.clientSecret);

        if (confirmError) {
            alert(`Error en la confirmación del pago: ${confirmError.message}`);
            return;
        }

        if (confirmedPaymentIntent && confirmedPaymentIntent.status === 'succeeded') {
            console.log("Pago completado con éxito, creando la orden...");

            const { ok, order } = await actions.saveOrder();
            if (!ok) {
                alert("Error al guardar la orden.");
                return;
            }

            const result = await actions.saveOrderDetails(order.id, formData);
            if (!result.ok) {
                alert("Error al guardar los detalles de la orden.");
                return;
            }

            actions.clearCart();
            localStorage.removeItem("cart");

            await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/cart/clear`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${localStorage.getItem("token")}`
                }
            });

            console.log("Carrito vaciado");
            navigate("/thank-you");
        }
    };


    const handleCheckboxChange = (e) => {
        setDifferentBilling(e.target.checked);
        if (!e.target.checked) {
            setFormData({
                ...formData,
                billing_address: "",
                billing_city: "",
                billing_postal_code: ""
            });
        }
    };

    const total = store.cart.reduce((acc, product) => acc + parseFloat(product.precio_total), 0);

    return (
        <Container fluid="sm" className="mt-5">
            <div className="py-5 text-center">
                <h2>Formulario de proceso de pago</h2>
            </div>
            <Row>
                <Col md={4} className="order-md-2 mb-4">
                    <ul className="list-group mb-3">
                        {store.cart.map((product, index) => (
                            <li key={index} className="list-group-item d-flex justify-content-between lh-condensed">
                                <div className="d-flex align-items-start">
                                    <div>
                                        <img src={product.imagen} alt={product.nombre} className="img-thumbnail me-3" style={{ width: "80px", height: "80px" }} />
                                        <h6 className="my-0">{product.nombre}</h6>
                                        <small className="text-muted d-block mt-1 mx-1">Alto: {product.alto}cm | Ancho: {product.ancho}cm</small>
                                        <small className="text-muted d-block mx-1">Anclaje: {product.anclaje}</small>
                                        <small className="text-muted d-block mx-1">Color: {product.color}</small>
                                    </div>
                                </div>
                                <span className="text-muted">{product.precio_total} €</span>
                            </li>
                        ))}
                        <li className="list-group-item d-flex justify-content-between">
                            <span>Envío: </span>
                            <strong>0€</strong>
                        </li>
                        <li className="list-group-item d-flex justify-content-between">
                            <span>Total (EUR)</span>
                            <strong>{total.toFixed(2)} €</strong>
                        </li>
                        <div className="text-center">
                            <img
                                src="https://formalba.es/wp-content/uploads/2021/04/pagos-seguros-autorizado.png"
                                alt="Pago Seguro Autorizado"
                                style={{ maxWidth: '250px', height: 'auto' }}
                            />
                        </div>
                    </ul>
                </Col>
                <Col md={8} className="order-md-1">
                    <Form onSubmit={handleSubmit} className="needs-validation" noValidate>
                        <h4 className="mb-3">Dirección de facturación</h4>
                        <hr className='hr-cart' />
                        <div className="row">
                            <div className="col-md-6">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="firstname"
                                    placeholder="Nombre"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">El nombre es obligatorio.</div>
                            </div>

                            <div className="col-md-6">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="lastname"
                                    placeholder="Apellidos"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">El apellido es obligatorio.</div>
                            </div>
                        </div>
                        <div className="row">
                            <div className="col-md-8">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="billing_address"
                                    placeholder="Calle, número, portal..."
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">La dirección es obligatoria.</div>
                            </div>

                            <div className="col-md-4">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="billing_postal_code"
                                    placeholder="Código Postal"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">El código postal es obligatorio.</div>
                            </div>
                        </div>
                        <div className="row">
                            <div className="col-md-6">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="billing_city"
                                    placeholder="Ciudad"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">La ciudad es obligatoria.</div>
                            </div>

                            <div className="col-md-6 mb-3">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="CIF"
                                    placeholder="CIF o DNI"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">El CIF o DNI es obligatorio.</div>
                            </div>
                        </div>
                        <Form.Check type="checkbox" label="La dirección de envío es diferente a la de facturación"
                            id="differentBilling"
                            onChange={handleCheckboxChange} />

                        {differentBilling && (
                            <div className="my-3" style={{ marginTop: '50px' }}>
                                <h4 className="mb-3">Dirección de envío</h4>
                                <hr className='hr-cart' />
                                <Form.Group controlId="shipping_address">
                                    <Form.Label></Form.Label>
                                    <Form.Control name="shipping_address" placeholder="Calle, número, portal, piso..." onChange={handleInputChange} required />
                                </Form.Group>
                                <Form.Group controlId="shipping_city">
                                    <Form.Label></Form.Label>
                                    <Form.Control name="shipping_city" placeholder="Ciudad" onChange={handleInputChange} required />
                                </Form.Group>
                                <Form.Group controlId="shipping_postal_code">
                                    <Form.Label></Form.Label>
                                    <Form.Control name="shipping_postal_code" placeholder="Código Postal" onChange={handleInputChange} required />
                                </Form.Group>
                            </div>
                        )}
                        <h4 className="mb-3" style={{ marginTop: '50px' }}>Método de pago</h4>
                        <hr className='hr-cart' />
                        <Form.Check
                            type="radio"
                            label="Tarjeta de crédito"
                            name="paymentMethod"
                            id="paymentStripe"
                            checked={paymentMethod === "stripe"}
                            onChange={() => setPaymentMethod("stripe")}
                            className="mb-2" />
                        <Form.Check
                            type="radio"
                            label="PayPal"
                            name="paymentMethod"
                            id="paymentPayPal"
                            checked={paymentMethod === "paypal"}
                            onChange={() => setPaymentMethod("paypal")}
                            className="mb-4" />
                        {/* Mostrar el formulario de pago adecuado */}
                        {paymentMethod === "paypal" ? (
                            <PayPalButton amount={total} onSuccess={handlePayPalSuccess} />
                        ) : (
                            <div className="mt-4">
                                <div role="group" aria-labelledby="payment-method-label">
                                    <Form.Group controlId="card-element">
                                        <Form.Label id="payment-method-label">Detalles de la tarjeta</Form.Label>
                                        <div style={{ position: "relative" }}>
                                            <CardElement options={{ hidePostalCode: true }} />
                                        </div>
                                    </Form.Group>
                                </div>
                                <Button className="btn btn-style-background-color btn-block my-5" type="submit" disabled={!stripe}>
                                    Pagar
                                </Button>
                            </div>
                        )}
                    </Form>
                </Col>
            </Row>
        </Container>
    );
};
// Envolver CheckoutForm con Elements para Stripe y PayPalScriptProvider para PayPal
const CheckoutWrapper = () => {
    return (
        <PayPalScriptProvider options={{ "client-id": "Aaj17-VA823EmfsMZpQYMV6d9KwWwmFHLcuX8xZTKp19etDK6TpF6Idd2zjbdTMbfxZaEuNFTVinS6uO" }}>
            <Elements stripe={stripePromise}>
                <CheckoutForm />
            </Elements>
        </PayPalScriptProvider>
    );
};

export default CheckoutWrapper;

import React, { useContext, useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Form, Accordion } from "react-bootstrap";
import { useNavigate } from "react-router-dom";


const stripePromise = loadStripe('pk_test_51I1FgUDyMBNofWjFVmq85bCUIBbzjopkQw1VWtt7I9Gp0trmFwYH0O60Heuit0BOaaa2dEJvEMzaB90uGxjr5Cuw00hVfWhV4y');


const CheckoutForm = () => {
    const stripe = useStripe();
    const elements = useElements();
    const { store, actions } = useContext(Context);
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

        // Enviar la solicitud de creación de Payment Intent a tu backend
        const response = await fetch(`${process.env.BACKEND_URL}/api/create-payment-intent`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount: total * 100,  // Enviar el monto en centavos
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

            // Guardar la orden y detalles en el backend
            const { ok, order } = await actions.saveOrder();
            if (!ok) {
                alert("Error al guardar la orden.");
                return;
            }

            // Enviar los datos de facturación y envío junto con los detalles de la orden
            const result = await actions.saveOrderDetails(order.id, formData);
            if (!result.ok) {
                alert("Error al guardar los detalles de la orden.");
                return;
            }

            // Limpiar el carrito en el frontend y backend
            actions.clearCart();
            localStorage.removeItem("cart");

            await fetch(`${process.env.BACKEND_URL}/api/cart/clear`, {
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

        // Si el pago fue exitoso, proceder a guardar la orden en el backend
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

            // Limpiar el carrito del frontend
            actions.clearCart();
            localStorage.removeItem("cart");

            // Limpiar el carrito en el backend
            await fetch(`${process.env.BACKEND_URL}/api/cart/clear`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${localStorage.getItem("token")}`
                }
            });

            console.log("Carrito vaciado");
            navigate("/thank-you");  // Redirigir a la página de agradecimiento
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
                <h2>Checkout Form</h2>
                <p className="lead">Por favor, llena los campos para continuar con el pago.</p>
            </div>

            <Row>
                <Col md={4} className="order-md-2 mb-4">
                    <h4 className="d-flex justify-content-between align-items-center mb-3">
                        <span className="text-muted">Tu carrito</span>
                        <span className="badge badge-secondary badge-pill text-secondary">{store.cart.length}</span>
                    </h4>
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
                                <hr />
                            </li>
                        ))}
                        <li className="list-group-item d-flex justify-content-between">
                            <span>Total (EUR)</span>
                            <strong>{total.toFixed(2)} €</strong>
                        </li>
                    </ul>
                </Col>

                <Col md={8} className="order-md-1">
                    <h4 className="mb-3">Dirección de facturación</h4>
                    <Form onSubmit={handleSubmit} className="needs-validation" noValidate>
                        <div className="row">
                            <div className="col-md-6 mb-3">
                                <Form.Label>Nombre</Form.Label>
                                <Form.Control
                                    name="firstname"
                                    placeholder="Nombre"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">El nombre es obligatorio.</div>
                            </div>

                            <div className="col-md-6 mb-3">
                                <Form.Label>Apellido</Form.Label>
                                <Form.Control
                                    name="lastname"
                                    placeholder="Apellido"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">El apellido es obligatorio.</div>
                            </div>
                        </div>

                        <div className="row">
                            <div className="col-md-8 mb-3">
                                <Form.Label>Dirección de Envío</Form.Label>
                                <Form.Control
                                    name="shipping_address"
                                    placeholder="Calle y número"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">La dirección es obligatoria.</div>
                            </div>

                            <div className="col-md-4 mb-3">
                                <Form.Label>Código Postal</Form.Label>
                                <Form.Control
                                    name="shipping_postal_code"
                                    placeholder="Código Postal"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">El código postal es obligatorio.</div>
                            </div>
                        </div>

                        <div className="row">
                            <div className="col-md-6 mb-3">
                                <Form.Label>Ciudad</Form.Label>
                                <Form.Control
                                    name="shipping_city"
                                    placeholder="Ciudad"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">La ciudad es obligatoria.</div>
                            </div>

                            <div className="col-md-6 mb-3">
                                <Form.Label>CIF</Form.Label>
                                <Form.Control
                                    name="CIF"
                                    placeholder="CIF o DNI"
                                    onChange={handleInputChange}
                                    required
                                />
                                <div className="invalid-feedback">El CIF o DNI es obligatorio.</div>
                            </div>
                        </div>

                        <hr className="mb-4" />

                        <Form.Check
                            type="checkbox"
                            label="La dirección de envío es diferente a la de facturación"
                            id="differentBilling"
                            onChange={handleCheckboxChange}
                        />

                        {differentBilling && (
                            <Accordion className="my-3">
                                <Accordion.Item eventKey="0">
                                    <Accordion.Header>Dirección de facturación</Accordion.Header>
                                    <Accordion.Body>
                                        <Form.Group controlId="billingAddress">
                                            <Form.Label>Dirección de facturación</Form.Label>
                                            <Form.Control
                                                name="billing_address"
                                                placeholder="Calle y número"
                                                onChange={handleInputChange}
                                                required
                                            />
                                        </Form.Group>
                                        <Form.Group controlId="billingCity">
                                            <Form.Label>Ciudad</Form.Label>
                                            <Form.Control
                                                name="billing_city"
                                                placeholder="Ciudad"
                                                onChange={handleInputChange}
                                                required
                                            />
                                        </Form.Group>
                                        <Form.Group controlId="billingPostalCode">
                                            <Form.Label>Código Postal</Form.Label>
                                            <Form.Control
                                                name="billing_postal_code"
                                                placeholder="Código Postal"
                                                onChange={handleInputChange}
                                                required
                                            />
                                        </Form.Group>
                                    </Accordion.Body>
                                </Accordion.Item>
                            </Accordion>
                        )}

                        <hr className="mb-4" />
                        <h4 className="mb-3">Pago</h4>
                        <Form.Group controlId="card-element">
                            <Form.Label>Detalles de la tarjeta</Form.Label>
                            <CardElement />
                        </Form.Group>
                        <Button className="btn btn-primary btn-lg btn-block mt-4" type="submit" disabled={!stripe}>
                            Continuar al pago
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

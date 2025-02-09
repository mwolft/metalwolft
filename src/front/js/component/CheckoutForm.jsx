import React, { useContext, useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Form, Accordion } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

const stripePromise = loadStripe('pk_live_51I1FgUDyMBNofWjFzagO0jTrkfQBvlt5Pshx3hLJbDLCxahT7Cn5NF9oozvey5iiH6lZhP82p3TFFmrdHGh3CQW700GiDX1dtz');

const CheckoutForm = () => {
    const stripe = useStripe();
    const elements = useElements();
    const { store, actions } = useContext(Context);
    const [paymentMethod, setPaymentMethod] = useState("stripe");
    const [differentBilling, setDifferentBilling] = useState(false);
    const [errors, setErrors] = useState({});
    const [isProcessing, setIsProcessing] = useState(false);
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
    const total = store.cart.reduce((acc, product) => acc + parseFloat(product.precio_total), 0);
    // Manejar cambios en los campos del formulario
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    const handlePayPalSuccess = (details) => {
        // Guardar la orden y vaciar el carrito
        actions.saveOrder();
        actions.clearCart();
        navigate("/thank-you");
    };
    const validateForm = () => {
        const requiredFields = [
            "firstname",
            "lastname",
            "billing_address",
            "billing_city",
            "billing_postal_code",
            "CIF"
        ];

        if (differentBilling) {
            requiredFields.push(
                "shipping_address",
                "shipping_city",
                "shipping_postal_code"
            );
        }

        const newErrors = {};
        requiredFields.forEach((field) => {
            if (!formData[field]) {
                newErrors[field] = `Campo  obligatorio.`;
            }
        });

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    // Pago con Stripe
    const handleSubmit = async (event) => {
        event.preventDefault();

        if (!validateForm()) {
            console.error("El formulario no pasó la validación.");
            return;
        }

        if (!stripe || !elements) {
            console.error("Stripe o Elements no están cargados.");
            return;
        }

        setIsProcessing(true);
        console.log("Iniciando el proceso de pago...");

        try {
            // Obtén el elemento de la tarjeta y crea el PaymentMethod
            const cardElement = elements.getElement(CardElement);
            const { error, paymentMethod } = await stripe.createPaymentMethod({
                type: 'card',
                card: cardElement,
            });

            if (error) {
                console.error("Error al crear PaymentMethod:", error);
                alert(`Error en el pago: ${error.message}`);
                return;
            }

            console.log("PaymentMethod creado correctamente:", paymentMethod);

            // Convertir el total a un número entero (en la unidad mínima)
            const convertedAmount = Math.round(total * 100);

            // Solicitud al backend para crear el PaymentIntent
            console.log("Solicitando creación del PaymentIntent al backend...");
            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/create-payment-intent`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    amount: convertedAmount,
                    payment_method_id: paymentMethod.id,
                    payment_intent_id: store.paymentIntentId
                }),
            });

            if (!response.ok) {
                console.error("Error en la respuesta del backend al crear el PaymentIntent.", response.statusText);
                alert("Error al crear el PaymentIntent. Por favor, inténtalo nuevamente.");
                return;
            }

            const data = await response.json();
            console.log("Respuesta del backend:", data);

            if (!data || !data.clientSecret) {
                console.error("La respuesta no contiene clientSecret.");
                alert("Hubo un error en la creación del intento de pago.");
                return;
            }

            // Si el PaymentIntent ya fue confirmado
            if (data.paymentIntent && data.paymentIntent.status === 'succeeded') {
                console.log("El PaymentIntent ya se encuentra confirmado en el backend.");
                const orderData = {
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
                };
                console.log("orderData a enviar:", orderData);
                const { ok, order, error } = await actions.saveOrder(orderData);
                if (!ok) {
                    console.error("Error al guardar la orden:", error);
                    alert("No se pudo procesar tu pedido. Por favor, inténtalo nuevamente.");
                    return;
                }
                await handleOrderCompletion(order.id, formData);
                return;
            }

            // Confirmar el pago (esto ejecutará 3D Secure si es necesario)
            console.log("Confirmando el pago con stripe.confirmCardPayment...");
            const { error: confirmError, paymentIntent: confirmedPaymentIntent } = await stripe.confirmCardPayment(data.clientSecret);

            if (confirmError) {
                console.error("Error en la confirmación del pago:", confirmError);
                alert(`Error en la confirmación del pago: ${confirmError.message}`);
                return;
            }

            console.log("Respuesta de confirmCardPayment:", confirmedPaymentIntent);

            if (confirmedPaymentIntent && confirmedPaymentIntent.status === 'succeeded') {
                console.log("El pago fue confirmado exitosamente.");
                // Construir el objeto orderData de la misma forma que en la otra rama:
                const orderData = {
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
                };
                console.log("orderData a enviar:", orderData);
                const { ok, order, error } = await actions.saveOrder(orderData);
                if (!ok) {
                    console.error("Error al guardar la orden tras confirmación del pago:", error);
                    alert("Error al guardar la orden.");
                    return;
                }
                await handleOrderCompletion(order.id, formData);
            }
        } catch (err) {
            console.error("Error inesperado en el flujo de pago:", err);
            alert("Se produjo un error inesperado. Por favor, inténtalo nuevamente.");
        } finally {
            setIsProcessing(false);
            console.log("Proceso de pago finalizado. isProcessing reestablecido a false.");
        }
    };


    const handleCheckboxChange = (e) => {
        setDifferentBilling(e.target.checked);
        if (!e.target.checked) {
            setFormData({
                ...formData,
                shipping_address: "La misma que la de facturación",
                shipping_city: "",
                shipping_postal_code: ""
            });
        } else {
            setFormData({
                ...formData,
                shipping_address: "",
                shipping_city: "",
                shipping_postal_code: ""
            });
        }
    };


    const handleOrderCompletion = async (orderId, formData) => {
        const { ok, order, error } = await actions.saveOrderDetails(orderId, formData);
        if (!ok) {
            throw new Error("Error al guardar los detalles de la orden.");
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
        navigate("/thank-you");
    };


    return (
        <Container fluid="sm" className="mt-5">
            <div className="text-center">
                <h2 className='h2-categories' style={{ marginTop: '80px', marginBottom: '30px' }}>Formulario de pago</h2>
            </div>
            <Row>
                <Col md={4} className="order-md-2 mb-4">
                    <ul className="list-group mb-3">
                        <h6>Resumen:</h6>
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
                            <strong>GRATIS</strong>
                        </li>
                        <li className="list-group-item d-flex justify-content-between">
                            <span>Total (EUR)</span>
                            <strong>{total.toFixed(2)} €</strong>
                        </li>
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
                                    value={formData.firstname}
                                />
                                {errors.firstname && (
                                    <p className="text-danger">{errors.firstname}</p>
                                )}
                            </div>
                            <div className="col-md-6">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="lastname"
                                    placeholder="Apellidos"
                                    onChange={handleInputChange}
                                    value={formData.lastname}
                                />
                                {errors.lastname && (
                                    <p className="text-danger">{errors.lastname}</p>
                                )}
                            </div>
                        </div>
                        <div className="row">
                            <div className="col-md-8">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="billing_address"
                                    placeholder="Calle, número, portal..."
                                    onChange={handleInputChange}
                                    value={formData.billing_address}
                                />
                                {errors.billing_address && (
                                    <p className="text-danger">{errors.billing_address}</p>
                                )}
                            </div>
                            <div className="col-md-4">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="billing_postal_code"
                                    placeholder="Código Postal"
                                    onChange={handleInputChange}
                                    value={formData.billing_postal_code}
                                />
                                {errors.billing_postal_code && (
                                    <p className="text-danger">{errors.billing_postal_code}</p>
                                )}
                            </div>
                        </div>
                        <div className="row">
                            <div className="col-md-6">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="billing_city"
                                    placeholder="Ciudad"
                                    onChange={handleInputChange}
                                    value={formData.billing_city}
                                />
                                {errors.billing_city && (
                                    <p className="text-danger">{errors.billing_city}</p>
                                )}
                            </div>
                            <div className="col-md-6 mb-3">
                                <Form.Label></Form.Label>
                                <Form.Control
                                    name="CIF"
                                    placeholder="CIF o DNI"
                                    onChange={handleInputChange}
                                    value={formData.CIF}
                                />
                                {errors.CIF && (
                                    <p className="text-danger">{errors.CIF}</p>
                                )}
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
                                    <Form.Control
                                        name="shipping_address"
                                        placeholder="Calle, número, portal, piso..."
                                        onChange={handleInputChange}
                                        value={formData.shipping_address}
                                    />
                                    {errors.shipping_address && (
                                        <p className="text-danger">{errors.shipping_address}</p>
                                    )}
                                </Form.Group>
                                <Form.Group controlId="shipping_city">
                                    <Form.Label></Form.Label>
                                    <Form.Control
                                        name="shipping_city"
                                        placeholder="Ciudad"
                                        onChange={handleInputChange}
                                        value={formData.shipping_city}
                                    />
                                    {errors.shipping_city && (
                                        <p className="text-danger">{errors.shipping_city}</p>
                                    )}
                                </Form.Group>
                                <Form.Group controlId="shipping_postal_code">
                                    <Form.Label></Form.Label>
                                    <Form.Control
                                        name="shipping_postal_code"
                                        placeholder="Código Postal"
                                        onChange={handleInputChange}
                                        value={formData.shipping_postal_code}
                                    />
                                    {errors.shipping_postal_code && (
                                        <p className="text-danger">{errors.shipping_postal_code}</p>
                                    )}
                                </Form.Group>
                            </div>
                        )}
                        <h4 className="mb-3" style={{ marginTop: '50px' }}>Método de pago</h4>
                        <hr className='hr-cart' />
                        <div className="mt-4">
                            <div role="group" aria-labelledby="payment-method-label">
                                <Form.Group controlId="card-element">
                                    <Form.Label id="payment-method-label">Detalles de la tarjeta</Form.Label>
                                    <div style={{ position: "relative" }}>
                                        <CardElement options={{ hidePostalCode: true }} />
                                    </div>
                                </Form.Group>
                            </div>
                            <Button
                                className="btn btn-style-background-color btn-block my-5"
                                type="submit"
                                disabled={isProcessing || !stripe}
                            >
                                {isProcessing ? "Pagando..." : "Pagar"}
                            </Button>
                        </div>
                    </Form>
                    <div className="text-center">
                        <img
                            src="https://formalba.es/wp-content/uploads/2021/04/pagos-seguros-autorizado.png"
                            alt="Pago Seguro Autorizado"
                            style={{ maxWidth: '70%', height: 'auto', marginBottom: '30px' }}
                        />
                    </div>
                </Col>
            </Row>
        </Container>
    );
};
// Envolver CheckoutForm con Elements para Stripe y PayPalScriptProvider para PayPal
const CheckoutWrapper = () => {
    return (
        <Elements stripe={stripePromise}>
            <CheckoutForm />
        </Elements>
    );
};


export default CheckoutWrapper;

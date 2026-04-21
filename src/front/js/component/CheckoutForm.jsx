import React, { useContext, useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Form } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { calcularEnvio } from "../../utils/shippingCalculator";
import { Helmet } from "react-helmet-async";
import PayPalButton from "./PayPalButton";

const stripePromise = loadStripe('pk_live_51I1FgUDyMBNofWjFzagO0jTrkfQBvlt5Pshx3hLJbDLCxahT7Cn5NF9oozvey5iiH6lZhP82p3TFFmrdHGh3CQW700GiDX1dtz');

const CheckoutForm = () => {
    const stripe = useStripe();
    const elements = useElements();
    const { store, actions } = useContext(Context);
    const [differentBilling, setDifferentBilling] = useState(false);
    const [errors, setErrors] = useState({});
    const [isProcessing, setIsProcessing] = useState(false);
    const [paypalError, setPaypalError] = useState("");
    const [paypalCheckoutToken, setPaypalCheckoutToken] = useState(null);
    const [formData, setFormData] = useState({
        firstname: "",
        lastname: "",
        phone: "",
        shipping_address: "",
        shipping_city: "",
        shipping_postal_code: "",
        billing_address: "",
        billing_city: "",
        billing_postal_code: "",
        CIF: ""
    });
    const [acceptedPolicy, setAcceptedPolicy] = useState(false);
    const navigate = useNavigate();
    const backendUrl = process.env.REACT_APP_BACKEND_URL || "";
    const paypalClientId = process.env.REACT_APP_PAYPAL_CLIENT_ID || "";

    const { products, totalShipping: shippingCost, finalTotal } = calcularEnvio(store.cart);
    const discountPercent = store.discountPercent || 0;
    const totalWithDiscount = finalTotal * (1 - discountPercent / 100);

    const buildOrderProducts = (checkoutSummary) => {
        if (checkoutSummary?.lines?.length) {
            return checkoutSummary.lines.map((line) => ({
                producto_id: line.product_id,
                quantity: line.quantity || 1,
                alto: line.alto,
                ancho: line.ancho,
                anclaje: line.anclaje,
                color: line.color,
                precio_total: line.unit_price,
                shipping_type: line.shipping_type,
                shipping_cost: line.shipping_cost
            }));
        }

        return products.map((product) => ({
            producto_id: product.producto_id,
            quantity: product.quantity || 1,
            alto: product.alto,
            ancho: product.ancho,
            anclaje: product.anclaje,
            color: product.color,
            precio_total: product.precio_total,
            shipping_type: product.shipping_type,
            shipping_cost: product.shipping_cost
        }));
    };

    const buildAnalyticsItems = (checkoutSummary) => {
        if (checkoutSummary?.lines?.length) {
            return checkoutSummary.lines.map((line) => ({
                item_id: line.product_id,
                item_name: line.product_name,
                price: line.unit_price,
                quantity: line.quantity || 1
            }));
        }

        return products.map((product) => ({
            item_id: product.producto_id,
            item_name: product.nombre,
            price: product.precio_total,
            quantity: product.quantity || 1
        }));
    };

    const buildOrderData = (checkoutSummary, paymentIntentId = null) => ({
        payment_intent_id: paymentIntentId || store.paymentIntentId || null,
        total_amount: checkoutSummary?.total_amount ?? totalWithDiscount,
        shipping_cost: checkoutSummary?.shipping_cost ?? shippingCost,
        discount_code: checkoutSummary && Object.prototype.hasOwnProperty.call(checkoutSummary, "discount_code")
            ? checkoutSummary.discount_code
            : (store.discountCode || null),
        discount_percent: checkoutSummary?.discount_percent ?? (store.discountPercent || 0),
        products: buildOrderProducts(checkoutSummary),
        ...formData
    });

    const pushPurchaseEvent = (transactionId, checkoutSummary) => {
        window.dataLayer = window.dataLayer || [];
        window.dataLayer.push({
            event: "purchase",
            ecommerce: {
                transaction_id: transactionId,
                value: checkoutSummary?.total_amount ?? totalWithDiscount,
                currency: "EUR",
                shipping: checkoutSummary?.shipping_cost ?? shippingCost,
                coupon: checkoutSummary && Object.prototype.hasOwnProperty.call(checkoutSummary, "discount_code")
                    ? checkoutSummary.discount_code
                    : (store.discountCode || null),
                items: buildAnalyticsItems(checkoutSummary)
            }
        });
    };

    const persistPostPurchaseContext = (paymentIntentId, checkoutToken = null) => {
        if (paymentIntentId) {
            actions.setPaymentIntentId(paymentIntentId);
            sessionStorage.setItem("lastPaymentIntentId", paymentIntentId);
        }

        if (checkoutToken) {
            sessionStorage.setItem("lastCheckoutToken", checkoutToken);
        }
    };

    const buildThankYouUrl = (paymentIntentId, checkoutToken = null) => {
        const searchParams = new URLSearchParams();

        if (checkoutToken) {
            searchParams.set("checkout_token", checkoutToken);
        }

        if (paymentIntentId) {
            searchParams.set("payment_intent_id", paymentIntentId);
        }

        const queryString = searchParams.toString();
        return queryString ? `/thank-you?${queryString}` : "/thank-you";
    };

    const validateCheckoutBeforePayment = ({ showAlert = false } = {}) => {
        if (!acceptedPolicy) {
            const message = "Debes aceptar la Politica de Devoluciones y Garantias antes de continuar.";
            setPaypalError(message);
            if (showAlert) {
                alert(message);
            }
            return false;
        }

        const isValid = validateForm();
        if (!isValid) {
            const message = "Revisa los datos obligatorios antes de continuar con el pago.";
            setPaypalError(message);
            if (showAlert) {
                alert(message);
            }
            return false;
        }

        setPaypalError("");
        return true;
    };

    const colorLabels = {
        satinado_blanco: "Blanco liso",
        satinado_negro: "Negro liso",
        satinado_gris: "Gris medio liso",
        satinado_verde: "Verde carruajes liso",
        forja_negro: "Negro forja",
        forja_gris: "Gris acero forja",
        forja_marron: "MarrÃ³n castaÃ±o forja",
        forja_marron: "Marron castano forja",
        forja_azul: "Azul forja",
        forja_verde: "Verde bronce forja",
        forja_dorado: "Dorado forja",
        blanco: "Blanco",
        negro: "Negro",
        gris: "Gris",
        marron: "Marron",
        verde: "Verde"
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    const validateForm = () => {
        const requiredFields = [
            "firstname",
            "lastname",
            "phone",
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
                newErrors[field] = "Campo obligatorio.";
            }
        });

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleOrderCompletion = async (
        paymentIntentId,
        checkoutSummary,
        { attemptOrderFallback = true, checkoutToken = null } = {}
    ) => {
        persistPostPurchaseContext(paymentIntentId, checkoutToken);

        if (attemptOrderFallback) {
            const orderData = buildOrderData(checkoutSummary, paymentIntentId);
            const { ok, error } = await actions.saveOrder(orderData);
            if (!ok) {
                console.warn("No se pudo cerrar el pedido desde frontend; el webhook seguira siendo la via principal.", error);
            }
        }

        await actions.clearCart();
        navigate(buildThankYouUrl(paymentIntentId, checkoutToken));
    };

    const handlePayPalCheckoutContext = ({ checkoutToken }) => {
        if (checkoutToken) {
            setPaypalError("");
            setPaypalCheckoutToken(checkoutToken);
            persistPostPurchaseContext(null, checkoutToken);
        }
    };

    const handlePayPalSuccess = async ({ checkoutToken, captureId, checkoutSummary }) => {
        if (!checkoutToken) {
            const message = "No hemos podido identificar esta compra de PayPal. Revisa tu cuenta o intentalo de nuevo.";
            setPaypalError(message);
            return;
        }

        setPaypalError("");
        setPaypalCheckoutToken(checkoutToken || null);
        persistPostPurchaseContext(null, checkoutToken);
        pushPurchaseEvent(captureId || checkoutToken || "paypal", checkoutSummary);
        await actions.clearCart();
        navigate(buildThankYouUrl(null, checkoutToken));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();

        if (!validateCheckoutBeforePayment({ showAlert: true })) {
            return;
        }

        if (!stripe || !elements) {
            console.error("Stripe o Elements no estan cargados.");
            return;
        }

        setIsProcessing(true);

        try {
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

            const convertedAmount = Math.round(totalWithDiscount * 100);
            const idempotencyKey = store.idempotencyKey || (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2));
            actions.setIdempotencyKey(idempotencyKey);

            const token = localStorage.getItem("token");
            const response = await fetch(`${backendUrl}/api/create-payment-intent`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    amount: convertedAmount,
                    payment_method_id: paymentMethod.id,
                    payment_intent_id: store.paymentIntentId,
                    idempotency_key: idempotencyKey,
                    email: store.currentUser?.email || null,
                    discount_code: store.discountCode || null,
                    discount_percent: store.discountPercent || 0,
                    shipping_cost: shippingCost,
                    total_amount: totalWithDiscount,
                    customer_data: formData
                }),
            });

            const data = await response.json().catch(() => null);

            if (!response.ok) {
                console.error("Error en la respuesta del backend al crear el PaymentIntent.", response.statusText, data);
                alert("Error al crear el PaymentIntent. Por favor, intentalo nuevamente.");
                return;
            }

            const checkoutSummary = data?.checkout_summary || null;
            const checkoutToken = data?.public_checkout_token || null;

            if (data.paymentIntent?.id) {
                persistPostPurchaseContext(data.paymentIntent.id, checkoutToken);
            }

            if (!data?.clientSecret) {
                console.error("La respuesta no contiene clientSecret.");
                alert("Hubo un error en la creacion del intento de pago.");
                return;
            }

            if (data.paymentIntent?.status === "succeeded") {
                pushPurchaseEvent(data.paymentIntent.id, checkoutSummary);
                await handleOrderCompletion(data.paymentIntent.id, checkoutSummary, {
                    attemptOrderFallback: true,
                    checkoutToken
                });
                return;
            }

            const { error: confirmError, paymentIntent: confirmedPaymentIntent } = await stripe.confirmCardPayment(data.clientSecret);

            if (confirmError) {
                console.error("Error en la confirmacion del pago:", confirmError);
                alert(`Error en la confirmacion del pago: ${confirmError.message}`);
                return;
            }

            if (confirmedPaymentIntent?.status === 'succeeded') {
                pushPurchaseEvent(confirmedPaymentIntent.id, checkoutSummary);
                await handleOrderCompletion(confirmedPaymentIntent.id, checkoutSummary, {
                    attemptOrderFallback: true,
                    checkoutToken
                });
                return;
            }

            if (confirmedPaymentIntent?.status === 'processing') {
                await handleOrderCompletion(confirmedPaymentIntent.id, checkoutSummary, {
                    attemptOrderFallback: false,
                    checkoutToken
                });
                return;
            }

            alert("No hemos podido confirmar el estado final del pago. Revisa tu cuenta en unos instantes.");
        } catch (err) {
            console.error("Error inesperado en el flujo de pago:", err);
            alert("Se produjo un error inesperado. Por favor, inténtalo nuevamente.");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleCheckboxChange = (e) => {
        setDifferentBilling(e.target.checked);
        if (!e.target.checked) {
            setFormData({
                ...formData,
                shipping_address: "La misma que la de facturacion",
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

    return (
        <>
            <Helmet>
                <meta name="theme-color" content="#ff324d" />
                <meta name="msapplication-navbutton-color" content="#ff324d" />
                <meta name="apple-mobile-web-app-status-bar-style" content="#ff324d" />
            </Helmet>
            <Container fluid="sm" className="mt-5">
                <div className="text-center">
                    <h2 className='h2-categories' style={{ marginTop: '80px', marginBottom: '30px' }}>Formulario de pago</h2>
                </div>
                <Row>
                    <Col md={4} className="order-md-2 mb-4">
                        <ul className="list-group mb-3">
                            <h6>Resumen:</h6>
                            {products.map((product, index) => (
                                <li key={index} className="list-group-item d-flex justify-content-between lh-condensed">
                                    <div className="d-flex align-items-start">
                                        <div>
                                            <img src={product.imagen} alt={product.nombre} className="img-thumbnail me-3" style={{ width: "80px", height: "80px" }} />
                                            <h6 className="my-2">
                                                {product.nombre}
                                            </h6>
                                            <small className="text-muted d-block mt-1 mx-1">Alto: {product.alto}cm | Ancho: {product.ancho}cm</small>
                                            <small className="text-muted d-block mx-1">Anclaje: {product.anclaje}</small>
                                            <small className="text-muted d-block mx-1">
                                                Color: {colorLabels[product.color] ?? product.color}
                                            </small>
                                            {product.shipping_type !== 'normal' && (
                                                <>
                                                    <small className="text-danger d-block mx-1">
                                                        ðŸšš Este producto requiere enví­o especial ({product.shipping_cost.toFixed(2)}€)
                                                    </small>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                    <span style={{ color: "#6c757d", opacity: 1, fontSize: "0.875rem", textAlign: "right", display: "block" }}>
                                        {product.precio_total.toFixed(2)}EUR <br /> {product.quantity ?? 1} und<br /> {(product.precio_total * (product.quantity ?? 1)).toFixed(2)}EUR
                                    </span>
                                </li>
                            ))}
                            <li className="list-group-item d-flex justify-content-between">
                                <span>Envio:</span>
                                <strong>{shippingCost === 0 ? "GRATIS" : `${shippingCost.toFixed(2)} EUR`}</strong>
                            </li>
                            {discountPercent > 0 && (
                                <li className="list-group-item d-flex justify-content-between text-success">
                                    <span>Descuento ({discountPercent}%)</span>
                                    <strong>-{(finalTotal * discountPercent / 100).toFixed(2)}EUR</strong>
                                </li>
                            )}
                            <li className="list-group-item d-flex justify-content-between">
                                <span>Total (EUR)</span>
                                <strong>{totalWithDiscount.toFixed(2)}EUR</strong>
                            </li>
                        </ul>
                    </Col>
                    <Col md={8} className="order-md-1">
                        <Form onSubmit={handleSubmit} className="needs-validation" noValidate>
                            <h4 className="mb-3">Direccion de facturacion</h4>
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
                                <div className="col-md-12">
                                    <Form.Label></Form.Label>
                                    <Form.Control
                                        name="billing_address"
                                        placeholder="Calle, numero, portal..."
                                        onChange={handleInputChange}
                                        value={formData.billing_address}
                                    />
                                    {errors.billing_address && (
                                        <p className="text-danger">{errors.billing_address}</p>
                                    )}
                                </div>
                            </div>
                            <div className="row">
                                <div className="col-md-6">
                                    <Form.Label></Form.Label>
                                    <Form.Control
                                        name="billing_postal_code"
                                        placeholder="Codigo Postal"
                                        onChange={handleInputChange}
                                        value={formData.billing_postal_code}
                                    />
                                    {errors.billing_postal_code && (
                                        <p className="text-danger">{errors.billing_postal_code}</p>
                                    )}
                                </div>
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
                            </div>
                            <div className="row">
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
                                <div className="col-md-6 mb-3">
                                    <Form.Label></Form.Label>
                                    <Form.Control
                                        name="phone"
                                        placeholder="Telefono"
                                        onChange={handleInputChange}
                                        value={formData.phone}
                                    />
                                    {errors.phone && (
                                        <p className="text-danger">{errors.phone}</p>
                                    )}
                                </div>
                            </div>
                            <Form.Check
                                type="checkbox"
                                label="La direccion de envio es diferente a la de facturacion"
                                id="differentBilling"
                                onChange={handleCheckboxChange}
                            />

                            {differentBilling && (
                                <div className="my-3" style={{ marginTop: '50px' }}>
                                    <h4 className="mb-3">Direccion de envio</h4>
                                    <hr className='hr-cart' />
                                    <Form.Group controlId="shipping_address">
                                        <Form.Label></Form.Label>
                                        <Form.Control
                                            name="shipping_address"
                                            placeholder="Calle, numero, portal, piso..."
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
                                            placeholder="Codigo Postal"
                                            onChange={handleInputChange}
                                            value={formData.shipping_postal_code}
                                        />
                                        {errors.shipping_postal_code && (
                                            <p className="text-danger">{errors.shipping_postal_code}</p>
                                        )}
                                    </Form.Group>
                                </div>
                            )}
                            <h4 className="mb-3" style={{ marginTop: '50px' }}>Metodo de pago</h4>
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
                                <Form.Group className="mt-4">
                                    <Form.Check
                                        type="checkbox"
                                        id="accept-policy"
                                        label={
                                            <>
                                                Confirmo que he leido y acepto la{" "}
                                                <a
                                                    href="/politica-devolucion"
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    style={{ textDecoration: "underline" }}
                                                >
                                                    Politica de Devoluciones y Garantias
                                                </a>.
                                            </>
                                        }
                                        checked={acceptedPolicy}
                                        onChange={(e) => setAcceptedPolicy(e.target.checked)}
                                        required
                                    />
                                </Form.Group>

                                <Button
                                    className="btn btn-style-background-color btn-block my-4"
                                    type="submit"
                                    disabled={isProcessing || !stripe}
                                >
                                    {isProcessing ? "Pagando..." : "Pagar con tarjeta"}
                                </Button>

                                <div className="text-center my-3">
                                    <span className="text-muted">o paga con</span>
                                </div>

                                {paypalClientId ? (
                                    <>
                                        <PayPalButton
                                            clientId={paypalClientId}
                                            backendUrl={backendUrl}
                                            authToken={localStorage.getItem("token")}
                                            customerData={formData}
                                            checkoutToken={paypalCheckoutToken}
                                            disabled={isProcessing}
                                            discountCode={store.discountCode || null}
                                            discountPercent={store.discountPercent || 0}
                                            shippingCost={shippingCost}
                                            totalAmount={totalWithDiscount}
                                            onBeforeCreateOrder={() => validateCheckoutBeforePayment({ showAlert: false })}
                                            onProcessingChange={setIsProcessing}
                                            onCheckoutContext={handlePayPalCheckoutContext}
                                            onApproveSuccess={handlePayPalSuccess}
                                            onError={setPaypalError}
                                        />
                                        {paypalError && (
                                            <p className="text-danger mt-3 mb-0">{paypalError}</p>
                                        )}
                                    </>
                                ) : (
                                    <p className="text-muted small mb-0">PayPal no esta disponible en este entorno.</p>
                                )}
                            </div>
                        </Form>
                        <div className="text-center">
                            <img
                                src="https://kompozits.lv/app/uploads/2021/02/secure-600x123.png"
                                alt="Pago Seguro Autorizado"
                                style={{ maxWidth: '70%', height: 'auto', marginBottom: '30px' }}
                            />
                        </div>
                    </Col>
                </Row>
            </Container>
        </>
    );
};

const CheckoutWrapper = () => {
    return (
        <Elements stripe={stripePromise}>
            <CheckoutForm />
        </Elements>
    );
};

export default CheckoutWrapper;

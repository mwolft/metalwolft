import React, { useContext, useEffect, useRef, useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Form } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import { calcularEnvio } from "../../utils/shippingCalculator";
import { Helmet } from "react-helmet-async";
import PayPalButton from "./PayPalButton";

const stripePromise = loadStripe('pk_live_51I1FgUDyMBNofWjFzagO0jTrkfQBvlt5Pshx3hLJbDLCxahT7Cn5NF9oozvey5iiH6lZhP82p3TFFmrdHGh3CQW700GiDX1dtz');

const CHECKOUT_PROFILE_FIELDS = [
    "firstname",
    "lastname",
    "phone",
    "shipping_address",
    "shipping_city",
    "shipping_postal_code",
    "billing_address",
    "billing_city",
    "billing_postal_code",
    "CIF"
];

const EMPTY_CHECKOUT_FORM = {
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
};

const VALID_SPANISH_POSTAL_CODE_REGEX = /^\d{5}$/;
const RESTRICTED_SHIPPING_POSTAL_PREFIXES = ["07", "35", "38", "51", "52"];
const INVALID_POSTAL_CODE_MESSAGE = "Introduce un código postal válido.";
const PENINSULA_ONLY_SHIPPING_MESSAGE = "Actualmente solo realizamos envíos a la península. Para Baleares, Canarias, Ceuta o Melilla, consúltanos antes de comprar.";

const CheckoutForm = () => {
    const stripe = useStripe();
    const elements = useElements();
    const { store, actions } = useContext(Context);
    const [differentBilling, setDifferentBilling] = useState(false);
    const [errors, setErrors] = useState({});
    const [isProcessing, setIsProcessing] = useState(false);
    const [paypalError, setPaypalError] = useState("");
    const [paypalCheckoutToken, setPaypalCheckoutToken] = useState(null);
    const [formData, setFormData] = useState(EMPTY_CHECKOUT_FORM);
    const [showSavedDataNotice, setShowSavedDataNotice] = useState(false);
    const [acceptedPolicy, setAcceptedPolicy] = useState(false);
    const [touchedPostalFields, setTouchedPostalFields] = useState({
        billing_postal_code: false,
        shipping_postal_code: false
    });
    const hasAutofilledSavedDataRef = useRef(false);
    const hasUserEditedCheckoutRef = useRef(false);
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

        const validationResult = validateForm();
        if (!validationResult.isValid) {
            const message = validationResult.message || "Revisa los datos obligatorios antes de continuar con el pago.";
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
        forja_marron: "Marrón castaño forja",
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

    const getStoredCheckoutUser = () => {
        try {
            const rawUser = localStorage.getItem("user");
            if (!rawUser || rawUser === "undefined") {
                return null;
            }

            const parsedUser = JSON.parse(rawUser);
            return parsedUser && typeof parsedUser === "object" ? parsedUser : null;
        } catch (error) {
            console.warn("No se pudieron leer los datos guardados del usuario para el checkout.", error);
            return null;
        }
    };

    const normalizeSameAsBillingValue = (value) => {
        if (!value) return "";

        const normalized = String(value).trim().toLowerCase();

        if (
            normalized === "la misma que la de facturación" ||
            normalized === "la misma que la de facturacion" ||
            normalized === "misma dirección" ||
            normalized === "misma direccion" ||
            normalized === "igual que facturación" ||
            normalized === "igual que facturacion"
        ) {
            return "";
        }

        return value;
    };

    const normalizePostalCodeValue = (value) => String(value || "").trim();

    const getPostalCodeValidationMessage = (postalCode, { checkShippingRestriction = false } = {}) => {
        const normalizedPostalCode = normalizePostalCodeValue(postalCode);

        if (!normalizedPostalCode) {
            return "";
        }

        if (!VALID_SPANISH_POSTAL_CODE_REGEX.test(normalizedPostalCode)) {
            return INVALID_POSTAL_CODE_MESSAGE;
        }

        if (
            checkShippingRestriction &&
            RESTRICTED_SHIPPING_POSTAL_PREFIXES.includes(normalizedPostalCode.slice(0, 2))
        ) {
            return PENINSULA_ONLY_SHIPPING_MESSAGE;
        }

        return "";
    };

    const setFieldError = (fieldName, message) => {
        setErrors((prevErrors) => {
            const nextErrors = { ...prevErrors };

            if (message) {
                nextErrors[fieldName] = message;
            } else {
                delete nextErrors[fieldName];
            }

            return nextErrors;
        });
    };

    const getPostalCodeFieldValidationMessage = (
        fieldName,
        value,
        useDifferentShippingOverride = differentBilling
    ) => {
        const checkShippingRestriction = fieldName === "shipping_postal_code"
            ? true
            : !useDifferentShippingOverride;

        return getPostalCodeValidationMessage(value, { checkShippingRestriction });
    };

    const validatePostalCodeField = (
        fieldName,
        value,
        useDifferentShippingOverride = differentBilling
    ) => {
        const message = getPostalCodeFieldValidationMessage(
            fieldName,
            value,
            useDifferentShippingOverride
        );

        setFieldError(fieldName, message);
        return message;
    };

    const buildCheckoutPrefillData = (userData = {}) => ({
        firstname: userData.firstname || "",
        lastname: userData.lastname || "",
        phone: userData.phone || "",
        shipping_address: normalizeSameAsBillingValue(userData.shipping_address),
        shipping_city: normalizeSameAsBillingValue(userData.shipping_city),
        shipping_postal_code: normalizeSameAsBillingValue(userData.shipping_postal_code),
        billing_address: userData.billing_address || "",
        billing_city: userData.billing_city || "",
        billing_postal_code: userData.billing_postal_code || "",
        CIF: userData.CIF || userData.cif || userData.tax_id || ""
    });

    const shouldUseDifferentShipping = (prefillData) => {
        const shippingAddress = (prefillData.shipping_address || "").trim();
        const shippingCity = (prefillData.shipping_city || "").trim();
        const shippingPostalCode = (prefillData.shipping_postal_code || "").trim();

        if (!shippingAddress && !shippingCity && !shippingPostalCode) {
            return false;
        }

        return (
            shippingAddress !== (prefillData.billing_address || "").trim() ||
            shippingCity !== (prefillData.billing_city || "").trim() ||
            shippingPostalCode !== (prefillData.billing_postal_code || "").trim()
        );
    };

    useEffect(() => {
        if (!store.isLoged || hasAutofilledSavedDataRef.current || hasUserEditedCheckoutRef.current) {
            return;
        }

        const sourceUser = store.currentUser || getStoredCheckoutUser();
        if (!sourceUser) {
            return;
        }

        const prefillData = buildCheckoutPrefillData(sourceUser);
        const useDifferentShipping = shouldUseDifferentShipping(prefillData);
        const effectivePrefillData = useDifferentShipping
            ? prefillData
            : {
                ...prefillData,
                shipping_address: "",
                shipping_city: "",
                shipping_postal_code: ""
            };

        const hasAnyStoredValue = CHECKOUT_PROFILE_FIELDS.some((field) => effectivePrefillData[field]);
        const hasAnyMissingField = CHECKOUT_PROFILE_FIELDS.some(
            (field) => !formData[field] && effectivePrefillData[field]
        );

        if (!hasAnyStoredValue || !hasAnyMissingField) {
            return;
        }

        setFormData((prevData) => {
            const nextData = { ...prevData };

            CHECKOUT_PROFILE_FIELDS.forEach((field) => {
                if (!nextData[field] && effectivePrefillData[field]) {
                    nextData[field] = effectivePrefillData[field];
                }
            });

            return nextData;
        });

        setDifferentBilling(useDifferentShipping);
        setShowSavedDataNotice(true);
        hasAutofilledSavedDataRef.current = true;
    }, [formData, store.currentUser, store.isLoged]);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        hasUserEditedCheckoutRef.current = true;
        setFormData({
            ...formData,
            [name]: value
        });

        if (
            (name === "billing_postal_code" || name === "shipping_postal_code") &&
            (touchedPostalFields[name] || Boolean(errors[name]))
        ) {
            validatePostalCodeField(name, value);
        }
    };

    const handlePostalCodeBlur = (e) => {
        const { name, value } = e.target;
        setTouchedPostalFields((prevState) => ({
            ...prevState,
            [name]: true
        }));
        validatePostalCodeField(name, value);
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

        const billingPostalCodeError = getPostalCodeValidationMessage(formData.billing_postal_code, {
            checkShippingRestriction: !differentBilling
        });

        if (billingPostalCodeError) {
            newErrors.billing_postal_code = billingPostalCodeError;
        }

        if (differentBilling) {
            const shippingPostalCodeError = getPostalCodeValidationMessage(formData.shipping_postal_code, {
                checkShippingRestriction: true
            });

            if (shippingPostalCodeError) {
                newErrors.shipping_postal_code = shippingPostalCodeError;
            }
        }

        setErrors(newErrors);

        return {
            isValid: Object.keys(newErrors).length === 0,
            message: newErrors.shipping_postal_code || newErrors.billing_postal_code || null
        };
    };

    const hasBlockingPostalError = Boolean(
        errors.billing_postal_code ||
        (differentBilling && errors.shipping_postal_code)
    );

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
                console.error("Error en la confirmación del pago:", confirmError);
                alert(`Error en la confirmación del pago: ${confirmError.message}`);
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
        hasUserEditedCheckoutRef.current = true;
        const useDifferentShipping = e.target.checked;
        setDifferentBilling(useDifferentShipping);
        setFormData({
            ...formData,
            shipping_address: "",
            shipping_city: "",
            shipping_postal_code: ""
        });

        setTouchedPostalFields((prevState) => ({
            ...prevState,
            shipping_postal_code: false
        }));
        setFieldError("shipping_postal_code", "");

        if (touchedPostalFields.billing_postal_code || Boolean(errors.billing_postal_code)) {
            validatePostalCodeField(
                "billing_postal_code",
                formData.billing_postal_code,
                useDifferentShipping
            );
        }
    };


    const checkoutSectionCardStyle = {
        border: "1px solid #e9ecef",
        borderRadius: "16px",
        padding: "24px",
        backgroundColor: "#ffffff",
        boxShadow: "0 12px 30px rgba(15, 23, 42, 0.05)"
    };

    const checkoutSectionMutedCardStyle = {
        border: "1px solid #e9ecef",
        borderRadius: "14px",
        padding: "18px 20px",
        backgroundColor: "#f8f9fa"
    };

    const checkoutSectionTitleStyle = {
        fontSize: "1.15rem",
        fontWeight: 600,
        marginBottom: "4px"
    };

    const checkoutSectionSubtitleStyle = {
        color: "#6c757d",
        fontSize: "0.92rem",
        marginBottom: "0px"
    };

    const checkoutLabelStyle = {
        fontSize: "0.75rem",
        fontWeight: 600,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        color: "#6c757d",
        marginBottom: "8px"
    };

    const checkoutInputStyle = {
        border: "1px solid #d8dee4",
        borderRadius: "12px",
        padding: "14px 16px",
        backgroundColor: "#fbfcfd",
        minHeight: "52px"
    };

    const checkoutErrorStyle = {
        marginTop: "8px",
        marginBottom: "0px",
        fontSize: "0.9rem"
    };

    const paymentNoticeStyle = {
        border: "1px solid #e9ecef",
        borderRadius: "14px",
        padding: "18px 20px",
        backgroundColor: "#f8f9fa"
    };

    const savedDataNoticeStyle = {
        border: "1px solid #dbeafe",
        borderRadius: "14px",
        padding: "14px 16px",
        backgroundColor: "#eff6ff",
        color: "#1d4ed8"
    };

    const paymentMethodCardStyle = {
        border: "1px solid #e9ecef",
        borderRadius: "14px",
        padding: "20px 20px 0px 20px",
        backgroundColor: "#ffffff"
    };

    const cardElementWrapperStyle = {
        border: "1px solid #d8dee4",
        borderRadius: "12px",
        padding: "14px 16px",
        backgroundColor: "#fbfcfd",
        minHeight: "54px",
        display: "flex",
        alignItems: "center"
    };

    const paymentDividerLineStyle = {
        flex: 1,
        height: "1px",
        backgroundColor: "#e9ecef"
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
                                                <small className="text-danger d-block mx-1">
                                                    Este producto requiere envio especial ({product.shipping_cost.toFixed(2)}EUR)
                                                </small>
                                            )}
                                        </div>
                                    </div>
                                    <span style={{ color: "#6c757d", opacity: 1, fontSize: "0.875rem", textAlign: "right", display: "block" }}>
                                        {product.precio_total.toFixed(2)}EUR <br /> {product.quantity ?? 1} und<br /> {(product.precio_total * (product.quantity ?? 1)).toFixed(2)}EUR
                                    </span>
                                </li>
                            ))}
                            <li className="list-group-item d-flex justify-content-between">
                                <span>envío:</span>
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
                    <Col md={8} className="order-md-1 mb-5">
                        <Form onSubmit={handleSubmit} className="needs-validation" noValidate>
                            <div style={checkoutSectionCardStyle}>
                                <div className="mb-4">
                                    <h4 style={checkoutSectionTitleStyle}>Dirección de facturación</h4>
                                    <p style={checkoutSectionSubtitleStyle}>Datos para la factura y la confirmación del pedido.</p>
                                </div>

                                {showSavedDataNotice && (
                                    <div className="mb-4" style={savedDataNoticeStyle}>
                                        Hemos rellenado tus datos guardados. Puedes modificarlos antes de pagar.
                                    </div>
                                )}

                                <Row className="g-3">
                                    <Col md={6}>
                                        <Form.Group className="mb-0">
                                            <Form.Label style={checkoutLabelStyle}>Nombre</Form.Label>
                                            <Form.Control
                                                name="firstname"
                                                placeholder="Nombre"
                                                onChange={handleInputChange}
                                                value={formData.firstname}
                                                style={checkoutInputStyle}
                                            />
                                            {errors.firstname && (
                                                <p className="text-danger" style={checkoutErrorStyle}>{errors.firstname}</p>
                                            )}
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className="mb-0">
                                            <Form.Label style={checkoutLabelStyle}>Apellidos</Form.Label>
                                            <Form.Control
                                                name="lastname"
                                                placeholder="Apellidos"
                                                onChange={handleInputChange}
                                                value={formData.lastname}
                                                style={checkoutInputStyle}
                                            />
                                            {errors.lastname && (
                                                <p className="text-danger" style={checkoutErrorStyle}>{errors.lastname}</p>
                                            )}
                                        </Form.Group>
                                    </Col>
                                    <Col md={12}>
                                        <Form.Group className="mb-0">
                                            <Form.Label style={checkoutLabelStyle}>Dirección de facturación</Form.Label>
                                            <Form.Control
                                                name="billing_address"
                                                placeholder="Calle, número, portal..."
                                                onChange={handleInputChange}
                                                value={formData.billing_address}
                                                style={checkoutInputStyle}
                                            />
                                            {errors.billing_address && (
                                                <p className="text-danger" style={checkoutErrorStyle}>{errors.billing_address}</p>
                                            )}
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className="mb-0">
                                            <Form.Label style={checkoutLabelStyle}>Codigo Postal</Form.Label>
                                            <Form.Control
                                                name="billing_postal_code"
                                                placeholder="Codigo Postal"
                                                onChange={handleInputChange}
                                                onBlur={handlePostalCodeBlur}
                                                value={formData.billing_postal_code}
                                                style={checkoutInputStyle}
                                            />
                                            {errors.billing_postal_code && (
                                                <p className="text-danger" style={checkoutErrorStyle}>{errors.billing_postal_code}</p>
                                            )}
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className="mb-0">
                                            <Form.Label style={checkoutLabelStyle}>Ciudad</Form.Label>
                                            <Form.Control
                                                name="billing_city"
                                                placeholder="Ciudad"
                                                onChange={handleInputChange}
                                                value={formData.billing_city}
                                                style={checkoutInputStyle}
                                            />
                                            {errors.billing_city && (
                                                <p className="text-danger" style={checkoutErrorStyle}>{errors.billing_city}</p>
                                            )}
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className="mb-0">
                                            <Form.Label style={checkoutLabelStyle}>CIF o DNI</Form.Label>
                                            <Form.Control
                                                name="CIF"
                                                placeholder="CIF o DNI"
                                                onChange={handleInputChange}
                                                value={formData.CIF}
                                                style={checkoutInputStyle}
                                            />
                                            {errors.CIF && (
                                                <p className="text-danger" style={checkoutErrorStyle}>{errors.CIF}</p>
                                            )}
                                        </Form.Group>
                                    </Col>
                                    <Col md={6}>
                                        <Form.Group className="mb-0">
                                            <Form.Label style={checkoutLabelStyle}>Teléfono</Form.Label>
                                            <Form.Control
                                                name="phone"
                                                placeholder="Teléfono"
                                                onChange={handleInputChange}
                                                value={formData.phone}
                                                style={checkoutInputStyle}
                                            />
                                            {errors.phone && (
                                                <p className="text-danger" style={checkoutErrorStyle}>{errors.phone}</p>
                                            )}
                                        </Form.Group>
                                    </Col>
                                </Row>
                            </div>

                            <div className="mt-4" style={checkoutSectionMutedCardStyle}>
                                <div className="d-flex flex-column gap-2">
                                    <div>
                                        <h5 className="mb-1" style={{ fontSize: "1rem", fontWeight: 600 }}>Dirección de envío</h5>
                                        <p className="text-muted small mb-0">
                                            Indica si quieres recibir el pedido en una dirección distinta a la de facturación.
                                        </p>
                                    </div>
                                    <Form.Check
                                        type="checkbox"
                                        label="La dirección de envío es diferente a la de facturación"
                                        id="differentBilling"
                                        onChange={handleCheckboxChange}
                                        className="mb-0"
                                    />
                                </div>
                            </div>

                            {differentBilling && (
                                <div className="mt-4" style={checkoutSectionCardStyle}>
                                    <div className="mb-4">
                                        <h4 style={checkoutSectionTitleStyle}>Dirección de envío</h4>
                                        <p style={checkoutSectionSubtitleStyle}>Dirección donde recibiras el pedido.</p>
                                    </div>

                                    <Row className="g-3">
                                        <Col md={12}>
                                            <Form.Group className="mb-0" controlId="shipping_address">
                                                <Form.Label style={checkoutLabelStyle}>Dirección de envío</Form.Label>
                                                <Form.Control
                                                    name="shipping_address"
                                                    placeholder="Calle, número, portal, piso..."
                                                    onChange={handleInputChange}
                                                    value={formData.shipping_address}
                                                    style={checkoutInputStyle}
                                                />
                                                {errors.shipping_address && (
                                                    <p className="text-danger" style={checkoutErrorStyle}>{errors.shipping_address}</p>
                                                )}
                                            </Form.Group>
                                        </Col>
                                        <Col md={6}>
                                            <Form.Group className="mb-0" controlId="shipping_city">
                                                <Form.Label style={checkoutLabelStyle}>Ciudad</Form.Label>
                                                <Form.Control
                                                    name="shipping_city"
                                                    placeholder="Ciudad"
                                                    onChange={handleInputChange}
                                                    value={formData.shipping_city}
                                                    style={checkoutInputStyle}
                                                />
                                                {errors.shipping_city && (
                                                    <p className="text-danger" style={checkoutErrorStyle}>{errors.shipping_city}</p>
                                                )}
                                            </Form.Group>
                                        </Col>
                                        <Col md={6}>
                                            <Form.Group className="mb-0" controlId="shipping_postal_code">
                                                <Form.Label style={checkoutLabelStyle}>Codigo Postal</Form.Label>
                                                <Form.Control
                                                    name="shipping_postal_code"
                                                    placeholder="Codigo Postal"
                                                    onChange={handleInputChange}
                                                    onBlur={handlePostalCodeBlur}
                                                    value={formData.shipping_postal_code}
                                                    style={checkoutInputStyle}
                                                />
                                                {errors.shipping_postal_code && (
                                                    <p className="text-danger" style={checkoutErrorStyle}>{errors.shipping_postal_code}</p>
                                                )}
                                            </Form.Group>
                                        </Col>
                                    </Row>
                                </div>
                            )}

                            <h4 className="mb-3" style={{ marginTop: '50px' }}>Método de pago</h4>
                            <hr className='hr-cart' />
                            <div className="mt-4">
                                <div style={paymentNoticeStyle}>
                                    <div className="d-flex flex-column gap-2">
                                        <div>
                                            <h5 className="mb-1" style={{ fontSize: "1rem", fontWeight: 600 }}>Confirmación del pedido</h5>
                                            <p className="text-muted small mb-0">
                                                La aceptacion de la política es necesaria para completar cualquier metodo de pago.
                                            </p>
                                        </div>
                                        <Form.Group className="mb-0">
                                            <Form.Check
                                                type="checkbox"
                                                id="accept-policy"
                                                label={
                                                    <>
                                                        Confirmo que he leido y acepto la{" "}
                                                        <Link
                                                            to="/politica-devolucion"
                                                            style={{ textDecoration: "underline" }}
                                                        >
                                                            Política de Devoluciones y Garantías
                                                        </Link>.
                                                    </>
                                                }
                                                checked={acceptedPolicy}
                                                onChange={(e) => setAcceptedPolicy(e.target.checked)}
                                                required
                                            />
                                        </Form.Group>
                                    </div>
                                </div>

                                <div className="mt-4" style={paymentMethodCardStyle}>
                                    <div className="d-flex flex-column gap-2 mb-4">
                                        <div className="d-flex align-items-center justify-content-between gap-3 flex-wrap">
                                            <h5 className="mb-0" style={{ fontSize: "1.05rem", fontWeight: 600 }}>1. Tarjeta</h5>
                                            <span className="text-muted small">Pago seguro con Stripe</span>
                                        </div>
                                        <p className="text-muted small mb-0">
                                            Introduce los datos de tu tarjeta para completar el pago de forma segura.
                                        </p>
                                    </div>

                                    <div role="group" aria-labelledby="payment-method-label">
                                        <Form.Group controlId="card-element" className="mb-0">
                                            <Form.Label id="payment-method-label" className="small text-uppercase text-muted mb-2">
                                                Detalles de la tarjeta
                                            </Form.Label>
                                            <div style={cardElementWrapperStyle}>
                                                <div style={{ position: "relative", width: "100%" }}>
                                                    <CardElement options={{ hidePostalCode: true }} />
                                                </div>
                                            </div>
                                        </Form.Group>
                                    </div>

                                    <Button
                                        className="btn btn-style-background-color w-100 mt-4"
                                        type="submit"
                                        disabled={isProcessing || !stripe || hasBlockingPostalError}
                                    >
                                        {isProcessing ? "Pagando..." : "Pagar con tarjeta"}
                                    </Button>
                                    <div className="text-center">
                                        <img
                                            src="https://kompozits.lv/app/uploads/2021/02/secure-600x123.png"
                                            alt="Pago Seguro Autorizado"
                                            style={{ maxWidth: '30%', height: 'auto', marginBottom: '5px', marginTop: '5px' }}
                                        />
                                    </div>
                                </div>
                                <div className="d-flex align-items-center my-4" aria-hidden="true">
                                    <div style={paymentDividerLineStyle}></div>
                                    <span className="text-muted small px-3 text-uppercase" style={{ letterSpacing: "0.08em" }}>
                                        O bien
                                    </span>
                                    <div style={paymentDividerLineStyle}></div>
                                </div>

                                <div style={paymentMethodCardStyle}>
                                    <div className="d-flex flex-column gap-2 mb-4">
                                        <div className="d-flex align-items-center justify-content-between gap-3 flex-wrap">
                                            <h5 className="mb-0" style={{ fontSize: "1.05rem", fontWeight: 600 }}>2. PayPal</h5>
                                            <span className="text-muted small">Pago rápido y seguro</span>
                                        </div>
                                        <p className="text-muted small mb-0">
                                            Paga con tu cuenta PayPal o con tarjeta a traves de PayPal.
                                        </p>
                                    </div>

                                    {paypalClientId ? (
                                        <>
                                            <PayPalButton
                                                clientId={paypalClientId}
                                                backendUrl={backendUrl}
                                                authToken={localStorage.getItem("token")}
                                                customerData={formData}
                                                checkoutToken={paypalCheckoutToken}
                                                disabled={isProcessing || hasBlockingPostalError}
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
                            </div>
                        </Form>
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

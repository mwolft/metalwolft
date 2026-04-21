import React, { useContext, useEffect, useState } from 'react';
import { Context } from "../store/appContext";
import { Button } from "react-bootstrap";
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Helmet } from "react-helmet";

export const ThankYou = () => {
    const { store } = useContext(Context);
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [statusData, setStatusData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    const checkoutToken =
        searchParams.get("checkout_token") ||
        searchParams.get("public_checkout_token") ||
        sessionStorage.getItem("lastCheckoutToken") ||
        null;

    const paymentIntentId =
        searchParams.get("payment_intent_id") ||
        sessionStorage.getItem("lastPaymentIntentId") ||
        store.paymentIntentId ||
        null;

    const checkoutIdentifier = checkoutToken || paymentIntentId || null;

    useEffect(() => {
        if (checkoutToken) {
            sessionStorage.setItem("lastCheckoutToken", checkoutToken);
        }
    }, [checkoutToken]);

    useEffect(() => {
        if (paymentIntentId) {
            sessionStorage.setItem("lastPaymentIntentId", paymentIntentId);
        }
    }, [paymentIntentId]);

    useEffect(() => {
        let isCancelled = false;
        let pollTimeoutId = null;

        const fetchCheckoutStatus = async () => {
            if (!checkoutIdentifier) {
                setStatusData({
                    state: "not_found",
                    message: "No hemos encontrado información de esta compra."
                });
                setIsLoading(false);
                return;
            }

            try {
                const token = localStorage.getItem("token");
                const checkoutStatusQuery = checkoutToken
                    ? `checkout_token=${encodeURIComponent(checkoutToken)}`
                    : `payment_intent_id=${encodeURIComponent(paymentIntentId)}`;
                const response = await fetch(
                    `${process.env.REACT_APP_BACKEND_URL}/api/checkout/status?${checkoutStatusQuery}`,
                    {
                        headers: token ? { Authorization: `Bearer ${token}` } : {}
                    }
                );

                const data = await response.json().catch(() => null);
                if (isCancelled) return;

                if (response.status === 401 || response.status === 403) {
                    setStatusData({
                        state: "auth_required",
                        message: "Necesitamos que inicies sesion de nuevo para consultar el estado real de tu compra."
                    });
                    setIsLoading(false);
                    return;
                }

                if (!response.ok && !data) {
                    throw new Error("No se pudo comprobar el estado del pedido.");
                }

                const nextStatus = data || {
                    state: "not_found",
                    message: "No hemos podido recuperar el estado de tu compra."
                };

                setStatusData(nextStatus);
                setIsLoading(false);

                if (nextStatus.state === "processing") {
                    pollTimeoutId = window.setTimeout(fetchCheckoutStatus, 3000);
                }
            } catch (error) {
                if (isCancelled) return;

                setStatusData({
                    state: "not_found",
                    message: "No hemos podido comprobar el estado de tu compra."
                });
                setIsLoading(false);
            }
        };

        fetchCheckoutStatus();

        return () => {
            isCancelled = true;
            if (pollTimeoutId) {
                window.clearTimeout(pollTimeoutId);
            }
        };
    }, [checkoutIdentifier, checkoutToken, paymentIntentId]);

    const legacyOrderFallback = !checkoutIdentifier && store.orders?.length
        ? store.orders[store.orders.length - 1]
        : null;
    const orderSummary = statusData?.order || legacyOrderFallback || null;
    const customerEmail = statusData?.email || store.currentUser?.email || "";
    const currentState = legacyOrderFallback && !checkoutIdentifier
        ? "confirmed"
        : (statusData?.state || "loading");

    const renderContent = () => {
        if (isLoading) {
            return (
                <>
                    <h1>Estamos comprobando tu pedido</h1>
                    <p>Un momento, estamos consultando el estado real de tu compra.</p>
                </>
            );
        }

        if (currentState === "confirmed" && orderSummary) {
            return (
                <>
                    <h1>Gracias por tu compra</h1>
                    <p>Tu pedido ya ha quedado confirmado correctamente.</p>
                    <p>
                        <strong>Localizador:</strong> {orderSummary.locator}
                    </p>
                    {customerEmail && (
                        <p>
                            Tu factura se ha enviado al correo: <strong>{customerEmail}</strong>
                        </p>
                    )}
                </>
            );
        }

        if (currentState === "processing") {
            return (
                <>
                    <h1>Estamos confirmando tu pedido</h1>
                    <p>Hemos recibido tu pago y estamos cerrando la compra en este momento.</p>
                    <p>Esta página se actualizará automáticamente cuando el pedido quede confirmado.</p>
                </>
            );
        }

        if (currentState === "failed") {
            return (
                <>
                    <h1>No hemos podido confirmar tu pedido</h1>
                    <p>{statusData?.message || "El pago no se ha completado correctamente."}</p>
                    <p>Si crees que esto no es correcto, revisa tu cuenta o contacta con nosotros.</p>
                </>
            );
        }

        if (currentState === "auth_required") {
            return (
                <>
                    <h1>Necesitamos confirmar tu sesion</h1>
                    <p>{statusData?.message}</p>
                    <p>Cuando vuelvas a iniciar sesion podras consultar el estado real del pedido.</p>
                </>
            );
        }

        return (
            <>
                <h1>No hemos encontrado tu pedido</h1>
                <p>{statusData?.message || "No hemos podido localizar esta compra."}</p>
                <p>Si acabas de pagar, espera unos segundos y vuelve a intentarlo.</p>
            </>
        );
    };

    return (
        <>
            <Helmet>
                <meta name="robots" content="noindex, nofollow" />
                <meta name="theme-color" content="#ff324d" />
            </Helmet>
            <div className="container" style={{ marginTop: '100px', marginBottom: '250px' }}>
                <div className="row">
                    <div className="col-11 text-center">
                        {renderContent()}
                        <div className="d-flex justify-content-center gap-3 mt-4">
                            <Button
                                className="btn btn-style-background-color"
                                onClick={() => navigate('/')}>
                                Volver al inicio
                            </Button>
                            <Button
                                variant="outline-secondary"
                                onClick={() => navigate('/mi-cuenta')}>
                                Ir a mi cuenta
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

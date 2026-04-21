import React, { useEffect, useRef } from 'react';
import { PayPalButtons, PayPalScriptProvider } from "@paypal/react-paypal-js";

const PayPalButton = ({
    clientId,
    backendUrl,
    authToken,
    customerData,
    checkoutToken = null,
    disabled = false,
    discountCode = null,
    discountPercent = 0,
    shippingCost = 0,
    totalAmount = 0,
    onBeforeCreateOrder,
    onProcessingChange,
    onCheckoutContext,
    onApproveSuccess,
    onError
}) => {
    const checkoutTokenRef = useRef(checkoutToken || null);

    useEffect(() => {
        if (checkoutToken) {
            checkoutTokenRef.current = checkoutToken;
        }
    }, [checkoutToken]);

    if (!clientId) {
        return null;
    }

    const handleCreateOrder = async () => {
        const canContinue = await onBeforeCreateOrder?.();
        if (canContinue === false) {
            const validationError = new Error("Revisa los datos de facturación antes de continuar con PayPal.");
            onError?.(validationError.message);
            throw validationError;
        }

        if (!authToken) {
            const authError = new Error("Debes iniciar sesión para pagar con PayPal.");
            onError?.(authError.message);
            throw authError;
        }

        onProcessingChange?.(true);

        try {
            const response = await fetch(`${backendUrl}/api/paypal/create-order`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    checkout_token: checkoutTokenRef.current,
                    discount_code: discountCode,
                    discount_percent: discountPercent,
                    shipping_cost: shippingCost,
                    total_amount: totalAmount,
                    customer_data: customerData
                })
            });

            const data = await response.json().catch(() => null);

            if (!response.ok || !data?.provider_order_id) {
                throw new Error(data?.error || "No se pudo crear la orden de PayPal.");
            }

            checkoutTokenRef.current = data.public_checkout_token || checkoutTokenRef.current || null;
            onCheckoutContext?.({
                checkoutToken: checkoutTokenRef.current,
                providerOrderId: data.provider_order_id,
                checkoutSummary: data.checkout_summary || null
            });

            return data.provider_order_id;
        } catch (error) {
            onError?.(error.message || "No se pudo iniciar el pago con PayPal.");
            throw error;
        } finally {
            onProcessingChange?.(false);
        }
    };

    const handleApprove = async (data) => {
        if (!authToken) {
            const authError = new Error("Tu sesión ha caducado. Vuelve a iniciar sesión.");
            onError?.(authError.message);
            throw authError;
        }

        onProcessingChange?.(true);

        try {
            const response = await fetch(`${backendUrl}/api/paypal/capture-order`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    checkout_token: checkoutTokenRef.current,
                    provider_order_id: data.orderID,
                    customer_data: customerData
                })
            });

            const captureData = await response.json().catch(() => null);

            if (!response.ok) {
                throw new Error(captureData?.error || "No se pudo capturar el pago con PayPal.");
            }

            checkoutTokenRef.current = captureData?.public_checkout_token || checkoutTokenRef.current || null;

            await onApproveSuccess?.({
                checkoutToken: checkoutTokenRef.current,
                captureId: captureData?.provider_capture_id || null,
                providerOrderId: captureData?.provider_order_id || data.orderID,
                checkoutSummary: captureData?.checkout_summary || null
            });
        } catch (error) {
            onError?.(
                error.message ||
                "No se pudo confirmar el pago con PayPal. Si el cargo se hubiera autorizado, revisa el estado en tu cuenta o en la pagina de gracias."
            );
            throw error;
        } finally {
            onProcessingChange?.(false);
        }
    };

    return (
        <PayPalScriptProvider
            options={{
                "client-id": clientId,
                currency: "EUR",
                intent: "capture"
            }}
        >
            <div style={{ minHeight: "45px", overflow: "hidden" }}>
                <PayPalButtons
                    style={{ layout: "vertical", shape: "rect", label: "paypal" }}
                    disabled={disabled}
                    forceReRender={[clientId, disabled, checkoutTokenRef.current]}
                    createOrder={handleCreateOrder}
                    onApprove={handleApprove}
                    onCancel={() => onProcessingChange?.(false)}
                    onError={(error) => {
                        console.error("PayPal Checkout onError", error);
                        onProcessingChange?.(false);
                        onError?.("PayPal no ha podido iniciar o confirmar el pago. Puedes intentarlo de nuevo.");
                    }}
                />
            </div>
        </PayPalScriptProvider>
    );
};

export default PayPalButton;

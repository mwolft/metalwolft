"use client";

import { PayPalButtons, PayPalScriptProvider } from "@paypal/react-paypal-js";
import { useRef, useState, type ComponentProps } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth-client";
import {
  CheckoutClientError,
  capturePayPalOrder,
  createPayPalOrder,
  getCheckoutQuote,
  isCheckoutSessionError,
  type CheckoutQuote
} from "@/lib/checkout-client";
import { buildCustomerData, type CheckoutCustomerDetails } from "@/lib/checkout-details";

type PayPalPaymentFormProps = {
  clientId: string;
  customerDetails: CheckoutCustomerDetails;
  initialQuote: CheckoutQuote;
  onQuoteUpdated: (quote: CheckoutQuote) => void;
  onSessionExpired: () => void;
};

type Feedback = {
  type: "error" | "info" | "success";
  message: string;
};

type PayPalCreateOrderHandler = NonNullable<ComponentProps<typeof PayPalButtons>["createOrder"]>;
type PayPalApproveHandler = NonNullable<ComponentProps<typeof PayPalButtons>["onApprove"]>;
type PayPalApproveData = {
  orderID?: string;
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

function hasTotalChanged(left: CheckoutQuote, right: CheckoutQuote) {
  return Math.abs(Number(left.total_amount || 0) - Number(right.total_amount || 0)) >= 0.01;
}

function persistCheckoutContext(checkoutToken: string | null) {
  if (typeof window === "undefined" || !checkoutToken) {
    return;
  }

  window.sessionStorage.setItem("lastCheckoutToken", checkoutToken);
}

function buildThankYouUrl(checkoutToken: string | null) {
  if (!checkoutToken) {
    return "/thank-you";
  }

  return `/thank-you?checkout_token=${encodeURIComponent(checkoutToken)}`;
}

export function PayPalPaymentForm({
  clientId,
  customerDetails,
  initialQuote,
  onQuoteUpdated,
  onSessionExpired
}: PayPalPaymentFormProps) {
  const router = useRouter();
  const [quote, setQuote] = useState(initialQuote);
  const [checkoutToken, setCheckoutToken] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const suppressNextSdkError = useRef(false);

  function updateQuote(nextQuote: CheckoutQuote) {
    setQuote(nextQuote);
    onQuoteUpdated(nextQuote);
  }

  function handleSessionExpired() {
    onSessionExpired();
  }

  const handleCreateOrder: PayPalCreateOrderHandler = async () => {
    const token = getToken();
    if (!token) {
      handleSessionExpired();
      throw new Error("SESSION_EXPIRED");
    }

    setFeedback(null);

    try {
      const freshQuote = await getCheckoutQuote(token);
      if (hasTotalChanged(quote, freshQuote)) {
        updateQuote(freshQuote);
        setFeedback({
          type: "info",
          message:
            "Hemos actualizado el importe final con el cálculo de MetalWolft. Revisa el resumen y vuelve a pulsar PayPal."
        });
        suppressNextSdkError.current = true;
        throw new Error("QUOTE_CHANGED");
      }

      const paypalOrder = await createPayPalOrder(token, {
        checkout_token: checkoutToken,
        customer_data: buildCustomerData(customerDetails)
      });

      if (paypalOrder.checkout_summary && hasTotalChanged(freshQuote, paypalOrder.checkout_summary)) {
        updateQuote(paypalOrder.checkout_summary);
        setCheckoutToken(paypalOrder.public_checkout_token || null);
        setFeedback({
          type: "info",
          message:
            "Hemos actualizado el importe final con el cálculo de MetalWolft. Revisa el resumen y vuelve a pulsar PayPal."
        });
        suppressNextSdkError.current = true;
        throw new Error("QUOTE_CHANGED");
      }

      if (!paypalOrder.provider_order_id) {
        throw new CheckoutClientError("No se pudo crear la orden de PayPal.", 0);
      }

      setCheckoutToken(paypalOrder.public_checkout_token || null);
      return paypalOrder.provider_order_id;
    } catch (error) {
      if (isCheckoutSessionError(error)) {
        handleSessionExpired();
      }

      if (error instanceof CheckoutClientError) {
        setFeedback({
          type: "error",
          message:
            error.status === 0
              ? "No se pudo conectar con la API. Inténtalo de nuevo."
              : "No se pudo preparar PayPal. Inténtalo de nuevo."
        });
      }

      throw error;
    }
  };

  const handleApprove: PayPalApproveHandler = async (data: PayPalApproveData) => {
    if (isProcessing) {
      return;
    }

    const token = getToken();
    if (!token) {
      handleSessionExpired();
      return;
    }

    if (!data.orderID) {
      setFeedback({
        type: "error",
        message: "PayPal no devolvió un identificador de orden válido."
      });
      return;
    }

    setIsProcessing(true);
    setFeedback(null);

    try {
      const capture = await capturePayPalOrder(token, {
        checkout_token: checkoutToken,
        provider_order_id: data.orderID,
        customer_data: buildCustomerData(customerDetails)
      });

      const nextCheckoutToken = capture.public_checkout_token || checkoutToken;
      if (capture.checkout_summary) {
        updateQuote(capture.checkout_summary);
      }

      persistCheckoutContext(nextCheckoutToken);
      setFeedback({
        type: "success",
        message: "Pago recibido. Te llevamos a la página de seguimiento del pedido."
      });
      router.push(buildThankYouUrl(nextCheckoutToken));
    } catch (error) {
      if (isCheckoutSessionError(error)) {
        handleSessionExpired();
        return;
      }

      setFeedback({
        type: "error",
        message:
          error instanceof CheckoutClientError && error.status === 0
            ? "No se pudo conectar con la API. Inténtalo de nuevo."
            : "No hemos podido confirmar el pago con PayPal. Inténtalo de nuevo."
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="mw-payment-form">
      <div className="mw-payment-card">
        <p className="mw-payment-method-note">
          Pagarás {formatCurrency(quote.total_amount)} mediante PayPal Sandbox. El pedido se
          confirmará cuando Flask capture el pago.
        </p>
        <PayPalScriptProvider
          options={{
            clientId,
            currency: "EUR",
            intent: "capture"
          }}
        >
          <PayPalButtons
            createOrder={handleCreateOrder}
            disabled={isProcessing}
            forceReRender={[clientId, quote.total_amount, checkoutToken]}
            onApprove={handleApprove}
            onCancel={() => {
              setFeedback({
                type: "info",
                message: "Pago con PayPal cancelado. Tu carrito sigue intacto."
              });
            }}
            onError={() => {
              if (suppressNextSdkError.current) {
                suppressNextSdkError.current = false;
                return;
              }

              setFeedback({
                type: "error",
                message: "PayPal no pudo completar la operación. Inténtalo de nuevo."
              });
            }}
            style={{
              color: "gold",
              layout: "vertical",
              shape: "rect",
              label: "paypal"
            }}
          />
        </PayPalScriptProvider>
      </div>

      {feedback ? (
        <p
          aria-live="polite"
          className={`mw-alert ${
            feedback.type === "error" ? "mw-alert--error" : "mw-alert--success"
          }`}
        >
          {feedback.message}
        </p>
      ) : null}
    </div>
  );
}

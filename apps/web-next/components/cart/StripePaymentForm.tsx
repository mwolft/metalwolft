"use client";

import { CardElement, useElements, useStripe } from "@stripe/react-stripe-js";
import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth-client";
import {
  CheckoutClientError,
  createStripePaymentIntent,
  finalizeStripeOrder,
  isCheckoutSessionError,
  type CheckoutQuote
} from "@/lib/checkout-client";
import { buildCustomerData, type CheckoutCustomerDetails } from "@/lib/checkout-details";

type StripePaymentFormProps = {
  customerDetails: CheckoutCustomerDetails;
  initialQuote: CheckoutQuote;
  onQuoteUpdated: (quote: CheckoutQuote) => void;
  onSessionExpired: () => void;
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

function createIdempotencyKey() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function persistCheckoutContext(paymentIntentId: string | null, checkoutToken: string | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (paymentIntentId) {
    window.sessionStorage.setItem("lastPaymentIntentId", paymentIntentId);
  }

  if (checkoutToken) {
    window.sessionStorage.setItem("lastCheckoutToken", checkoutToken);
  }
}

function buildThankYouUrl(paymentIntentId: string | null, checkoutToken: string | null) {
  const searchParams = new URLSearchParams();

  if (checkoutToken) {
    searchParams.set("checkout_token", checkoutToken);
  }

  if (paymentIntentId) {
    searchParams.set("payment_intent_id", paymentIntentId);
  }

  const queryString = searchParams.toString();
  return queryString ? `/thank-you?${queryString}` : "/thank-you";
}

function hasTotalChanged(left: CheckoutQuote, right: CheckoutQuote) {
  return Math.abs(Number(left.total_amount || 0) - Number(right.total_amount || 0)) >= 0.01;
}

export function StripePaymentForm({
  customerDetails,
  initialQuote,
  onQuoteUpdated,
  onSessionExpired
}: StripePaymentFormProps) {
  const router = useRouter();
  const stripe = useStripe();
  const elements = useElements();
  const [quote, setQuote] = useState(initialQuote);
  const [idempotencyKey] = useState(createIdempotencyKey);
  const [paymentIntentId, setPaymentIntentId] = useState<string | null>(null);
  const [checkoutToken, setCheckoutToken] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "error" | "info" | "success"; message: string } | null>(
    null
  );

  async function finalizeSucceededPayment(nextPaymentIntentId: string, nextCheckoutToken: string | null) {
    const token = getToken();
    if (!token) {
      onSessionExpired();
      return;
    }

    try {
      await finalizeStripeOrder(token, nextPaymentIntentId);
      persistCheckoutContext(nextPaymentIntentId, nextCheckoutToken);
      router.push(buildThankYouUrl(nextPaymentIntentId, nextCheckoutToken));
    } catch (error) {
      if (isCheckoutSessionError(error)) {
        onSessionExpired();
        return;
      }

      if (error instanceof CheckoutClientError && error.status === 409) {
        persistCheckoutContext(nextPaymentIntentId, nextCheckoutToken);
        router.push(buildThankYouUrl(nextPaymentIntentId, nextCheckoutToken));
        return;
      }

      setFeedback({
        type: "error",
        message:
          "El pago se ha confirmado, pero no hemos podido cerrar el pedido todavía. Inténtalo de nuevo en unos segundos."
      });
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    const token = getToken();
    if (!token) {
      onSessionExpired();
      return;
    }

    if (!stripe || !elements) {
      setFeedback({
        type: "error",
        message: "Stripe todavía no está listo. Espera unos segundos e inténtalo de nuevo."
      });
      return;
    }

    const cardElement = elements.getElement(CardElement);
    if (!cardElement) {
      setFeedback({
        type: "error",
        message: "No hemos podido cargar el campo de tarjeta."
      });
      return;
    }

    setIsSubmitting(true);
    setFeedback(null);

    try {
      const { error: paymentMethodError, paymentMethod } = await stripe.createPaymentMethod({
        type: "card",
        card: cardElement
      });

      if (paymentMethodError || !paymentMethod) {
        setFeedback({
          type: "error",
          message: paymentMethodError?.message || "No hemos podido validar la tarjeta."
        });
        return;
      }

      const paymentIntentResponse = await createStripePaymentIntent(token, {
        payment_method_id: paymentMethod.id,
        payment_intent_id: paymentIntentId,
        idempotency_key: idempotencyKey,
        email: customerDetails.email,
        customer_data: buildCustomerData(customerDetails)
      });

      const nextPaymentIntentId = paymentIntentResponse.paymentIntent?.id || null;
      const nextCheckoutToken = paymentIntentResponse.public_checkout_token || null;

      setPaymentIntentId(nextPaymentIntentId);
      setCheckoutToken(nextCheckoutToken);

      if (paymentIntentResponse.checkout_summary && hasTotalChanged(quote, paymentIntentResponse.checkout_summary)) {
        setQuote(paymentIntentResponse.checkout_summary);
        onQuoteUpdated(paymentIntentResponse.checkout_summary);
        setFeedback({
          type: "info",
          message:
            "Hemos actualizado el importe final con el cálculo de MetalWolft. Revisa el resumen y vuelve a pulsar pagar."
        });
        return;
      }

      if (!paymentIntentResponse.clientSecret || !nextPaymentIntentId) {
        setFeedback({
          type: "error",
          message: "No hemos podido preparar la confirmación del pago."
        });
        return;
      }

      if (paymentIntentResponse.paymentIntent.status === "succeeded") {
        await finalizeSucceededPayment(nextPaymentIntentId, nextCheckoutToken);
        return;
      }

      const { error: confirmError, paymentIntent } = await stripe.confirmCardPayment(
        paymentIntentResponse.clientSecret
      );

      if (confirmError) {
        setFeedback({
          type: "error",
          message: confirmError.message || "El pago ha sido rechazado. Revisa la tarjeta e inténtalo de nuevo."
        });
        return;
      }

      if (paymentIntent?.status === "succeeded") {
        await finalizeSucceededPayment(paymentIntent.id, nextCheckoutToken);
        return;
      }

      if (paymentIntent?.status === "processing") {
        persistCheckoutContext(paymentIntent.id, nextCheckoutToken);
        setFeedback({
          type: "info",
          message: "El pago se está procesando. Te llevamos a la página de seguimiento."
        });
        router.push(buildThankYouUrl(paymentIntent.id, nextCheckoutToken));
        return;
      }

      setFeedback({
        type: "error",
        message: "No hemos podido confirmar el pago. Revisa los datos e inténtalo de nuevo."
      });
    } catch (error) {
      if (isCheckoutSessionError(error)) {
        onSessionExpired();
        return;
      }

      setFeedback({
        type: "error",
        message:
          error instanceof CheckoutClientError && error.status === 0
            ? "No se pudo conectar con la API. Inténtalo de nuevo."
            : "No hemos podido procesar el pago. Inténtalo de nuevo."
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="mw-payment-form" onSubmit={handleSubmit}>
      <div className="mw-payment-card">
        <label className="mw-field">
          <span>Datos de la tarjeta</span>
          <div className="mw-stripe-card">
            <CardElement options={{ hidePostalCode: true }} />
          </div>
        </label>
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

      <button className="mw-button mw-button--primary mw-checkout-submit" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Procesando..." : `Pagar ${formatCurrency(quote.total_amount)}`}
      </button>
    </form>
  );
}

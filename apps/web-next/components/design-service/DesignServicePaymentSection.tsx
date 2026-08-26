"use client";

import { CardElement, useElements, useStripe } from "@stripe/react-stripe-js";
import { Elements } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import { PayPalButtons, PayPalScriptProvider } from "@paypal/react-paypal-js";
import { useMemo, useRef, useState, type ComponentProps, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { capturePayPalOrder, finalizeStripeOrder } from "@/lib/checkout-client";
import { getToken } from "@/lib/auth-client";
import {
  createDesignServicePayPalOrder,
  createDesignServiceStripePaymentIntent,
  type DesignServiceCheckoutQuote,
  type DesignServiceCustomerData
} from "@/lib/design-service-client";
import type { AuthUser } from "@/lib/auth-client";

const stripeKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY?.trim();
const stripePromise = stripeKey ? loadStripe(stripeKey) : null;
const paypalClientId = process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID?.trim();

type PaymentMethod = "card" | "paypal";
type Feedback = { type: "error" | "info"; message: string };
type PayPalApproveData = { orderID?: string };
type PayPalCreateOrderHandler = NonNullable<ComponentProps<typeof PayPalButtons>["createOrder"]>;

function newKey() {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function formatCurrency(value: string, currency: string) {
  return new Intl.NumberFormat("es-ES", { style: "currency", currency }).format(Number(value));
}

function initialCustomer(user: AuthUser | null): DesignServiceCustomerData {
  const firstname = user?.firstname || "";
  const lastname = user?.lastname || "";
  return {
    firstname,
    lastname,
    email: user?.email || "",
    phone: user?.phone || "",
    legal_name: [firstname, lastname].filter(Boolean).join(" "),
    tax_id: user?.CIF || "",
    billing_address: user?.billing_address || "",
    billing_city: user?.billing_city || "",
    billing_postal_code: user?.billing_postal_code || ""
  };
}

function hasCustomerData(data: DesignServiceCustomerData) {
  return Object.values(data).every((value) => value.trim().length > 0);
}

function confirmationUrl(designRequestId: number) {
  return `/diseno-previo/confirmado?design_request_id=${designRequestId}`;
}

function DesignStripeForm({
  designRequestId,
  quote,
  customerData,
  onSessionExpired
}: {
  designRequestId: number;
  quote: DesignServiceCheckoutQuote;
  customerData: DesignServiceCustomerData;
  onSessionExpired: () => void;
}) {
  const stripe = useStripe();
  const elements = useElements();
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const idempotencyKey = useMemo(newKey, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) return;
    const token = getToken();
    if (!token) return onSessionExpired();
    if (!stripe || !elements) {
      setFeedback({ type: "error", message: "Stripe todavía no está listo. Inténtalo de nuevo en unos segundos." });
      return;
    }
    const card = elements.getElement(CardElement);
    if (!card) return;
    setIsSubmitting(true);
    setFeedback(null);
    try {
      const { error, paymentMethod } = await stripe.createPaymentMethod({ type: "card", card });
      if (error || !paymentMethod) {
        setFeedback({ type: "error", message: error?.message || "No hemos podido validar la tarjeta." });
        return;
      }
      const prepared = await createDesignServiceStripePaymentIntent(token, designRequestId, {
        payment_method_id: paymentMethod.id,
        idempotency_key: idempotencyKey,
        customer_data: customerData
      });
      const { error: confirmError, paymentIntent } = await stripe.confirmCardPayment(prepared.clientSecret);
      if (confirmError || !paymentIntent) {
        setFeedback({ type: "error", message: confirmError?.message || "No hemos podido confirmar el pago." });
        return;
      }
      if (paymentIntent.status === "succeeded") {
        await finalizeStripeOrder(token, paymentIntent.id);
        router.replace(confirmationUrl(designRequestId));
        return;
      }
      if (paymentIntent.status === "processing") {
        router.replace(confirmationUrl(designRequestId));
        return;
      }
      setFeedback({ type: "error", message: "El pago no se ha completado. Revisa los datos e inténtalo de nuevo." });
    } catch {
      setFeedback({ type: "error", message: "No hemos podido procesar el pago. Inténtalo de nuevo." });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="mw-payment-form" onSubmit={submit}>
      <div className="mw-payment-card">
        <label className="mw-field">
          <span>Datos de la tarjeta</span>
          <div className="mw-stripe-card"><CardElement options={{ hidePostalCode: true }} /></div>
        </label>
      </div>
      {feedback ? <p className="mw-alert mw-alert--error" aria-live="polite">{feedback.message}</p> : null}
      <button className="mw-button mw-button--primary mw-checkout-submit" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Procesando..." : `Pagar ${formatCurrency(quote.total_amount, quote.currency)}`}
      </button>
    </form>
  );
}

function DesignPayPalForm({
  designRequestId,
  quote,
  customerData,
  onSessionExpired
}: {
  designRequestId: number;
  quote: DesignServiceCheckoutQuote;
  customerData: DesignServiceCustomerData;
  onSessionExpired: () => void;
}) {
  const router = useRouter();
  const [checkoutToken, setCheckoutToken] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const creating = useRef(false);
  const idempotencyKey = useMemo(newKey, []);

  const createOrder: PayPalCreateOrderHandler = async () => {
    if (creating.current || isProcessing) throw new Error("PAYPAL_CREATE_IN_PROGRESS");
    const token = getToken();
    if (!token) {
      onSessionExpired();
      throw new Error("SESSION_EXPIRED");
    }
    creating.current = true;
    try {
      const prepared = await createDesignServicePayPalOrder(token, designRequestId, {
        idempotency_key: idempotencyKey,
        customer_data: customerData
      });
      if (!prepared.provider_order_id) throw new Error("PAYPAL_ORDER_MISSING");
      setCheckoutToken(prepared.public_checkout_token);
      return prepared.provider_order_id;
    } finally {
      creating.current = false;
    }
  };

  async function approve(data: PayPalApproveData) {
    const token = getToken();
    if (!token) return onSessionExpired();
    if (!data.orderID) return;
    setIsProcessing(true);
    setFeedback(null);
    try {
      await capturePayPalOrder(token, {
        checkout_token: checkoutToken,
        provider_order_id: data.orderID,
        customer_data: customerData
      });
      router.replace(confirmationUrl(designRequestId));
    } catch {
      setFeedback({ type: "error", message: "No hemos podido confirmar el pago con PayPal. Inténtalo de nuevo." });
    } finally {
      setIsProcessing(false);
    }
  }

  if (!paypalClientId) return <p className="mw-alert mw-alert--error">PayPal no está configurado en este entorno.</p>;
  return (
    <div className="mw-payment-form">
      <div className="mw-payment-card">
        <p className="mw-payment-method-note">Pagarás {formatCurrency(quote.total_amount, quote.currency)} mediante PayPal.</p>
        <PayPalScriptProvider options={{ clientId: paypalClientId, currency: "EUR", intent: "capture" }}>
          <PayPalButtons
            createOrder={createOrder}
            disabled={isProcessing}
            forceReRender={[quote.total_amount, checkoutToken]}
            onApprove={approve}
            onCancel={() => setFeedback({ type: "info", message: "El pago con PayPal se ha cancelado." })}
            onError={() => setFeedback({ type: "error", message: "PayPal no pudo completar la operación." })}
            style={{ color: "gold", layout: "vertical", shape: "rect", label: "paypal" }}
          />
        </PayPalScriptProvider>
      </div>
      {feedback ? <p className="mw-alert mw-alert--error" aria-live="polite">{feedback.message}</p> : null}
    </div>
  );
}

export function DesignServicePaymentSection({
  designRequestId,
  quote,
  user,
  onSessionExpired
}: {
  designRequestId: number;
  quote: DesignServiceCheckoutQuote;
  user: AuthUser | null;
  onSessionExpired: () => void;
}) {
  const [customerData, setCustomerData] = useState(() => initialCustomer(user));
  const [method, setMethod] = useState<PaymentMethod>("card");
  const isReady = hasCustomerData(customerData);

  function update(field: keyof DesignServiceCustomerData, value: string) {
    setCustomerData((current) => ({ ...current, [field]: value }));
  }

  return (
    <section className="mw-design-payment" aria-label="Pago seguro">
      <h2>Datos de facturación</h2>
      <p>Necesitamos estos datos para emitir la factura. No solicitamos dirección de envío.</p>
      <div className="mw-checkout-form-grid">
        {(["firstname", "lastname", "phone", "legal_name", "tax_id", "billing_address", "billing_postal_code", "billing_city"] as const).map((field) => (
          <label className="mw-field" key={field}>
            <span>{({ firstname: "Nombre", lastname: "Apellidos", phone: "Teléfono", legal_name: "Nombre o razón social", tax_id: "NIF / CIF", billing_address: "Dirección fiscal", billing_postal_code: "Código postal", billing_city: "Población" } as Record<string, string>)[field]}</span>
            <input onChange={(event) => update(field, event.target.value)} required value={customerData[field]} />
          </label>
        ))}
      </div>
      {!isReady ? <p className="mw-alert mw-alert--error">Completa los datos de facturación para continuar al pago.</p> : null}
      {isReady ? (
        <>
          <div className="mw-payment-methods" aria-label="Método de pago">
            <button aria-pressed={method === "card"} className={`mw-payment-method ${method === "card" ? "is-active" : ""}`} onClick={() => setMethod("card")} type="button">Tarjeta</button>
            <button aria-pressed={method === "paypal"} className={`mw-payment-method ${method === "paypal" ? "is-active" : ""}`} onClick={() => setMethod("paypal")} type="button">PayPal</button>
          </div>
          {method === "card" ? (
            stripePromise ? <Elements stripe={stripePromise}><DesignStripeForm customerData={customerData} designRequestId={designRequestId} onSessionExpired={onSessionExpired} quote={quote} /></Elements> : <p className="mw-alert mw-alert--error">Stripe no está configurado en este entorno.</p>
          ) : <DesignPayPalForm customerData={customerData} designRequestId={designRequestId} onSessionExpired={onSessionExpired} quote={quote} />}
        </>
      ) : null}
    </section>
  );
}

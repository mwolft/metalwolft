"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getToken } from "@/lib/auth-client";
import { getCart, isSessionError } from "@/lib/cart-client";
import {
  getCheckoutQuote,
  isCheckoutSessionError,
  type CheckoutQuote
} from "@/lib/checkout-client";
import {
  loadStoredCheckoutDetails,
  type CheckoutCustomerDetails,
  validateCheckoutDetails
} from "@/lib/checkout-details";
import {
  clearStoredCheckoutDiscountCode,
  loadStoredCheckoutDiscountCode,
  saveStoredCheckoutDiscountCode
} from "@/lib/checkout-discount";
import { CheckoutPaymentSummary } from "@/components/cart/CheckoutPaymentSummary";
import { PayPalPaymentForm } from "@/components/cart/PayPalPaymentForm";

const StripePaymentSection = dynamic(
  () => import("@/components/cart/StripePaymentSection").then((module) => module.StripePaymentSection),
  { ssr: false }
);
const paypalClientId = process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID?.trim();

type PaymentStatus = "loading" | "empty" | "missing-details" | "ready" | "error";
type PaymentMethod = "card" | "paypal";

function isApiSessionError(error: unknown) {
  return isSessionError(error) || isCheckoutSessionError(error);
}

export function CartPaymentStep({ deliveryEstimate }: { deliveryEstimate?: ReactNode }) {
  const router = useRouter();
  const [status, setStatus] = useState<PaymentStatus>("loading");
  const [quote, setQuote] = useState<CheckoutQuote | null>(null);
  const [customerDetails, setCustomerDetails] = useState<CheckoutCustomerDetails | null>(null);
  const [discountCode, setDiscountCode] = useState<string | null>(null);
  const [discountNotice, setDiscountNotice] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("card");

  function redirectToLogin() {
    clearSession();
    router.replace("/login?next=/cart%3Fstep%3Dpayment");
  }

  function updateCheckoutQuote(nextQuote: CheckoutQuote, requestedDiscountCode: string | null = null) {
    setQuote(nextQuote);

    if (nextQuote.discount_code_valid && nextQuote.discount_code) {
      saveStoredCheckoutDiscountCode(nextQuote.discount_code);
      setDiscountCode(nextQuote.discount_code);
      setDiscountNotice("");
      return;
    }

    if (requestedDiscountCode || discountCode) {
      setDiscountNotice("El codigo de descuento ya no es valido y se ha retirado del resumen.");
    }

    clearStoredCheckoutDiscountCode();
    setDiscountCode(null);
  }

  async function loadPaymentStep() {
    const token = getToken();
    if (!token) {
      redirectToLogin();
      return;
    }

    setStatus("loading");
    setErrorMessage("");

    const storedDetails = loadStoredCheckoutDetails();
    const validation = storedDetails ? validateCheckoutDetails(storedDetails) : null;

    if (!validation?.isValid) {
      setStatus("missing-details");
      return;
    }

    try {
      const cartItems = await getCart(token);
      if (cartItems.length === 0) {
        setQuote(null);
        setStatus("empty");
        return;
      }

      const storedDiscountCode = loadStoredCheckoutDiscountCode();
      const nextQuote = await getCheckoutQuote(token, { discountCode: storedDiscountCode });
      setCustomerDetails(validation.details);
      updateCheckoutQuote(nextQuote, storedDiscountCode);
      setStatus("ready");
    } catch (error) {
      if (isApiSessionError(error)) {
        redirectToLogin();
        return;
      }

      setQuote(null);
      setErrorMessage("No se pudo preparar el pago. Inténtalo de nuevo.");
      setStatus("error");
    }
  }

  useEffect(() => {
    void loadPaymentStep();
  }, []);

  if (status === "loading") {
    return (
      <PaymentState
        title="Preparando pago seguro"
        description="Estamos comprobando tu sesión, carrito y resumen final."
      />
    );
  }

  if (status === "missing-details") {
    return (
      <PaymentState
        title="Faltan datos para pagar"
        description="Completa tus datos de contacto, facturación y política antes de continuar."
      >
        <Link className="mw-button mw-button--primary" href="/cart?step=details">
          Volver a datos
        </Link>
      </PaymentState>
    );
  }

  if (status === "empty") {
    return (
      <PaymentState
        title="Tu carrito está vacío"
        description="Configura una reja para ventanas antes de continuar con el pago."
      >
        <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
          Ver rejas para ventanas
        </Link>
      </PaymentState>
    );
  }

  if (status === "error" || !quote || !customerDetails) {
    return (
      <PaymentState title="No se pudo preparar el pago" description={errorMessage}>
        <button className="mw-button mw-button--primary" onClick={loadPaymentStep} type="button">
          Reintentar
        </button>
        <Link className="mw-button mw-button--secondary" href="/cart?step=details">
          Volver a datos
        </Link>
      </PaymentState>
    );
  }

  return (
    <section className="mw-checkout-layout" aria-label="Pago seguro">
      <div className="mw-checkout-panel">
        <div className="mw-checkout-heading">
          <p className="mw-note">Paso 3 de 3</p>
          <h2>Elige método de pago</h2>
          <p>
            Puedes pagar con tarjeta mediante Stripe o con PayPal Sandbox. MetalWolft no almacena
            datos de tarjeta.
          </p>
        </div>

        <div className="mw-payment-methods" aria-label="Método de pago">
          <button
            aria-pressed={paymentMethod === "card"}
            className={`mw-payment-method ${paymentMethod === "card" ? "is-active" : ""}`}
            onClick={() => setPaymentMethod("card")}
            type="button"
          >
            Tarjeta
          </button>
          <button
            aria-pressed={paymentMethod === "paypal"}
            className={`mw-payment-method ${paymentMethod === "paypal" ? "is-active" : ""}`}
            onClick={() => setPaymentMethod("paypal")}
            type="button"
          >
            PayPal
          </button>
        </div>

        {discountNotice ? (
          <p className="mw-alert mw-alert--error" aria-live="polite">
            {discountNotice}
          </p>
        ) : null}

        {paymentMethod === "card" ? (
          <StripePaymentSection
            customerDetails={customerDetails}
            discountCode={discountCode}
            initialQuote={quote}
            onQuoteUpdated={updateCheckoutQuote}
            onSessionExpired={redirectToLogin}
          />
        ) : null}

        {paymentMethod === "paypal" && !paypalClientId ? (
          <p className="mw-alert mw-alert--error">
            PayPal no está configurado en este entorno. Puedes continuar con tarjeta.
          </p>
        ) : null}

        {paymentMethod === "paypal" && paypalClientId ? (
          <PayPalPaymentForm
            clientId={paypalClientId}
            customerDetails={customerDetails}
            discountCode={discountCode}
            initialQuote={quote}
            onQuoteUpdated={updateCheckoutQuote}
            onSessionExpired={redirectToLogin}
          />
        ) : null}
      </div>

      <aside className="mw-checkout-summary" aria-label="Resumen final del pago">
        <div className="mw-checkout-panel">
          <div className="mw-checkout-summary__header">
            <div>
              <p className="mw-note">Total</p>
              <h2>Importe final</h2>
            </div>
            <Link href="/cart?step=details">Editar datos</Link>
          </div>

          <CheckoutPaymentSummary customerDetails={customerDetails} quote={quote} />
          {deliveryEstimate}
        </div>
      </aside>
    </section>
  );
}

function PaymentState({
  title,
  description,
  children
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <section className="mw-cart-state">
      <p className="mw-eyebrow">Pago</p>
      <h2 className="mw-title mw-title--compact">{title}</h2>
      <p className="mw-lead">{description}</p>
      {children ? <div className="mw-actions">{children}</div> : null}
    </section>
  );
}

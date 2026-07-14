"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { clearSession, getToken } from "@/lib/auth-client";
import {
  getCheckoutStatus,
  isCheckoutSessionError,
  type CheckoutStatusResponse
} from "@/lib/checkout-client";

const MAX_STATUS_POLLS = 8;
const STATUS_POLL_DELAY_MS = 3000;

function formatCurrency(value: number | null | undefined) {
  if (typeof value !== "number") {
    return null;
  }

  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

function readStoredCheckoutIdentifier() {
  if (typeof window === "undefined") {
    return {
      checkoutToken: null,
      paymentIntentId: null
    };
  }

  return {
    checkoutToken: window.sessionStorage.getItem("lastCheckoutToken"),
    paymentIntentId: window.sessionStorage.getItem("lastPaymentIntentId")
  };
}

export function ThankYouStatus() {
  const searchParams = useSearchParams();
  const pollCountRef = useRef(0);
  const [statusData, setStatusData] = useState<CheckoutStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const identifiers = useMemo(() => {
    const stored = readStoredCheckoutIdentifier();
    return {
      checkoutToken:
        searchParams.get("checkout_token") ||
        searchParams.get("public_checkout_token") ||
        stored.checkoutToken,
      paymentIntentId: searchParams.get("payment_intent_id") || stored.paymentIntentId
    };
  }, [searchParams]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    if (identifiers.checkoutToken) {
      window.sessionStorage.setItem("lastCheckoutToken", identifiers.checkoutToken);
    }

    if (identifiers.paymentIntentId) {
      window.sessionStorage.setItem("lastPaymentIntentId", identifiers.paymentIntentId);
    }
  }, [identifiers.checkoutToken, identifiers.paymentIntentId]);

  useEffect(() => {
    let isCancelled = false;
    let timeoutId: number | null = null;

    async function fetchStatus() {
      const token = getToken();

      if (!identifiers.checkoutToken && !identifiers.paymentIntentId) {
        setStatusData({
          state: "not_found",
          message: "No hemos encontrado información de esta compra.",
          public_checkout_token: null,
          payment_intent_id: null
        });
        setIsLoading(false);
        return;
      }

      if (!token) {
        setStatusData({
          state: "auth_required",
          message: "Necesitamos que inicies sesión para consultar el estado real de la compra.",
          public_checkout_token: identifiers.checkoutToken,
          payment_intent_id: identifiers.paymentIntentId
        });
        setIsLoading(false);
        return;
      }

      try {
        const nextStatus = await getCheckoutStatus(token, identifiers);
        if (isCancelled) return;

        setStatusData(nextStatus);
        setIsLoading(false);

        if (nextStatus.state === "processing" && pollCountRef.current < MAX_STATUS_POLLS) {
          pollCountRef.current += 1;
          timeoutId = window.setTimeout(fetchStatus, STATUS_POLL_DELAY_MS);
        }
      } catch (error) {
        if (isCancelled) return;

        if (isCheckoutSessionError(error)) {
          clearSession();
          setStatusData({
            state: "auth_required",
            message: "Tu sesión ha caducado. Inicia sesión para consultar el estado del pedido.",
            public_checkout_token: identifiers.checkoutToken,
            payment_intent_id: identifiers.paymentIntentId
          });
          setIsLoading(false);
          return;
        }

        setStatusData({
          state: "not_found",
          message: "No hemos podido comprobar el estado de tu compra.",
          public_checkout_token: identifiers.checkoutToken,
          payment_intent_id: identifiers.paymentIntentId
        });
        setIsLoading(false);
      }
    }

    void fetchStatus();

    return () => {
      isCancelled = true;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [identifiers]);

  if (isLoading) {
    return (
      <ThankYouState
        title="Estamos comprobando tu pedido"
        description="Un momento, estamos consultando el estado real de tu compra."
      />
    );
  }

  if (statusData?.state === "confirmed") {
    const total = formatCurrency(statusData.total_amount || statusData.order?.total_amount);

    return (
      <ThankYouState
        title="Gracias por tu compra"
        description="Tu pedido ha quedado confirmado correctamente."
      >
        {statusData.order?.locator ? (
          <p>
            <strong>Localizador:</strong> {statusData.order.locator}
          </p>
        ) : null}
        {total ? (
          <p>
            <strong>Total:</strong> {total}
          </p>
        ) : null}
        <div className="mw-actions">
          <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
            Seguir comprando
          </Link>
        </div>
      </ThankYouState>
    );
  }

  if (statusData?.state === "processing") {
    return (
      <ThankYouState
        title="Estamos confirmando tu pedido"
        description="El pago se está procesando. Actualizaremos este estado automáticamente durante unos segundos."
      >
        <p>{statusData.message}</p>
      </ThankYouState>
    );
  }

  if (statusData?.state === "failed") {
    return (
      <ThankYouState
        title="No hemos podido confirmar tu pedido"
        description={statusData.message || "El pago no se ha completado correctamente."}
      >
        <div className="mw-actions">
          <Link className="mw-button mw-button--primary" href="/cart?step=payment">
            Volver al pago
          </Link>
          <Link className="mw-button mw-button--secondary" href="/cart">
            Volver al carrito
          </Link>
        </div>
      </ThankYouState>
    );
  }

  if (statusData?.state === "auth_required") {
    return (
      <ThankYouState
        title="Necesitamos confirmar tu sesión"
        description={statusData.message}
      >
        <Link className="mw-button mw-button--primary" href="/login?next=/thank-you">
          Iniciar sesión
        </Link>
      </ThankYouState>
    );
  }

  return (
    <ThankYouState
      title="No hemos encontrado tu pedido"
      description={statusData?.message || "No hemos podido localizar esta compra."}
    >
      <div className="mw-actions">
        <Link className="mw-button mw-button--primary" href="/cart">
          Volver al carrito
        </Link>
        <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
          Seguir comprando
        </Link>
      </div>
    </ThankYouState>
  );
}

function ThankYouState({
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
      <p className="mw-eyebrow">Pedido</p>
      <h1 className="mw-title mw-title--compact">{title}</h1>
      <p className="mw-lead">{description}</p>
      {children}
    </section>
  );
}

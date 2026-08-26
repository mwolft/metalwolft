"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getToken } from "@/lib/auth-client";
import { useAuthSession } from "@/hooks/useAuthSession";
import {
  DesignServiceClientError,
  getDesignServiceCheckoutQuote,
  type DesignServiceCheckoutQuote
} from "@/lib/design-service-client";
import { DesignServicePaymentSection } from "@/components/design-service/DesignServicePaymentSection";

type DesignServiceCheckoutViewProps = {
  designRequestId: number | null;
};

function formatCurrency(value: string, currency: string) {
  return new Intl.NumberFormat("es-ES", { style: "currency", currency }).format(Number(value));
}

function formatMeasure(value: string) {
  return Number(value).toLocaleString("es-ES");
}

function checkoutLoginHref(designRequestId: number) {
  const nextPath = `/diseno-previo/checkout?design_request_id=${designRequestId}`;
  return `/login?next=${encodeURIComponent(nextPath)}`;
}

function checkoutErrorMessage(error: unknown) {
  if (!(error instanceof DesignServiceClientError)) {
    return "No hemos podido preparar la compra del diseño previo. Inténtalo de nuevo.";
  }
  if (error.kind === "service_unavailable") {
    return "El servicio de diseño previo no está disponible en este momento.";
  }
  if (error.kind === "validation") {
    return "Esta solicitud no está disponible para tu cuenta.";
  }
  return "No hemos podido preparar la compra del diseño previo. Inténtalo de nuevo.";
}

export function DesignServiceCheckoutView({ designRequestId }: DesignServiceCheckoutViewProps) {
  const router = useRouter();
  const { user, isAuthenticated, isReady } = useAuthSession();
  const [quote, setQuote] = useState<DesignServiceCheckoutQuote | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isReady || designRequestId === null) return;
    if (!isAuthenticated) {
      router.replace(checkoutLoginHref(designRequestId));
      return;
    }

    const token = getToken();
    if (!token) {
      router.replace(checkoutLoginHref(designRequestId));
      return;
    }

    const controller = new AbortController();
    setQuote(null);
    setError(null);
    getDesignServiceCheckoutQuote(token, designRequestId, { signal: controller.signal })
      .then((nextQuote) => {
        if (!controller.signal.aborted) setQuote(nextQuote);
      })
      .catch((requestError: unknown) => {
        if (controller.signal.aborted) return;
        if (requestError instanceof DesignServiceClientError && requestError.kind === "authentication") {
          clearSession();
          router.replace(checkoutLoginHref(designRequestId));
          return;
        }
        setError(checkoutErrorMessage(requestError));
      });

    return () => controller.abort();
  }, [designRequestId, isAuthenticated, isReady, router]);

  if (designRequestId === null) {
    return (
      <section className="mw-section mw-design-checkout-state">
        <h1>Solicitud de diseño no válida</h1>
        <p>Vuelve al diseño previo para preparar tu solicitud.</p>
        <Link className="mw-button mw-button--secondary" href="/diseno-previo">Volver al diseño previo</Link>
      </section>
    );
  }

  if (!isReady || !isAuthenticated || (!quote && !error)) {
    return (
      <section className="mw-section mw-design-checkout-state" aria-live="polite">
        <h1>Preparando tu solicitud</h1>
        <p>Estamos comprobando los datos de tu diseño previo.</p>
      </section>
    );
  }

  if (error || !quote) {
    return (
      <section className="mw-section mw-design-checkout-state" aria-live="polite">
        <h1>No podemos preparar esta solicitud</h1>
        <p>{error || "La solicitud de diseño no está disponible."}</p>
        <Link className="mw-button mw-button--secondary" href="/diseno-previo">Volver al diseño previo</Link>
      </section>
    );
  }

  return (
    <section className="mw-design-checkout" aria-labelledby="design-checkout-title">
      <div className="mw-design-checkout__heading">
        <p className="mw-eyebrow">Preparación de compra</p>
        <h1 className="mw-title mw-title--compact" id="design-checkout-title">Tu solicitud de diseño</h1>
        <p className="mw-lead">Revisa los diseños y el importe confirmado antes de pasar al pago.</p>
      </div>
      <div className="mw-design-checkout__layout">
        <div className="mw-design-checkout__panel">
          <h2>Diseños incluidos</h2>
          <ul className="mw-design-checkout__items">
            {quote.items.map((item) => (
              <li key={`${item.product_id}:${item.width_cm}:${item.height_cm}`}>
                <strong>{item.product_name}</strong>
                <span>{formatMeasure(item.width_cm)} × {formatMeasure(item.height_cm)} cm</span>
              </li>
            ))}
          </ul>
          <section className="mw-design-checkout__contact" aria-label="Entrega del diseño">
            <h2>Entrega del diseño</h2>
            <p>{user?.email || "Correo de contacto"}</p>
            <p>Enviaremos el diseño terminado a este correo electrónico cuando esté listo.</p>
          </section>
        </div>
        <aside className="mw-design-checkout__summary" aria-label="Resumen de la solicitud">
          <p className="mw-design-summary__eyebrow">Resumen</p>
          <div className="mw-design-checkout__row">
            <span>Subtotal</span>
            <strong>{formatCurrency(quote.subtotal, quote.currency)}</strong>
          </div>
          {Number(quote.discount_amount) > 0 ? (
            <div className="mw-design-checkout__row mw-design-checkout__row--discount">
              <span>Descuento</span>
              <strong>-{formatCurrency(quote.discount_amount, quote.currency)}</strong>
            </div>
          ) : null}
          <div className="mw-design-checkout__row mw-design-checkout__row--tax">
            <span>IVA incluido ({quote.tax_rate} %)</span>
            <strong>{formatCurrency(quote.tax_amount, quote.currency)}</strong>
          </div>
          <div className="mw-design-checkout__total">
            <span>Total</span>
            <strong>{formatCurrency(quote.total_amount, quote.currency)}</strong>
          </div>
          <p className="mw-design-checkout__lead-time">Entrega estimada: {quote.lead_time_hours} h</p>
        </aside>
      </div>
      <DesignServicePaymentSection
        designRequestId={designRequestId}
        onSessionExpired={() => {
          clearSession();
          router.replace(checkoutLoginHref(designRequestId));
        }}
        quote={quote}
        user={user}
      />
    </section>
  );
}

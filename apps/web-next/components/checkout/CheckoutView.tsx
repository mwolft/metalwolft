"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getToken } from "@/lib/auth-client";
import { type CartItem, CartClientError, getCart, isSessionError } from "@/lib/cart-client";
import {
  CheckoutClientError,
  type CheckoutQuote,
  type CheckoutQuoteLine,
  getCheckoutQuote,
  isCheckoutSessionError
} from "@/lib/checkout-client";

type CheckoutStatus = "loading" | "empty" | "ready" | "error";

const colorLabels: Record<string, string> = {
  satinado_blanco: "Blanco liso",
  satinado_negro: "Negro liso",
  satinado_gris: "Gris medio liso",
  satinado_verde: "Verde carruajes liso",
  forja_negro: "Negro forja",
  forja_gris: "Gris acero forja",
  forja_marron: "Marron castano forja",
  forja_azul: "Azul forja",
  forja_verde: "Verde bronce forja",
  forja_dorado: "Dorado forja"
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

function formatDimension(value: number | null | undefined) {
  return typeof value === "number" ? `${value.toLocaleString("es-ES")} cm` : "-";
}

function formatColor(value: string | null | undefined) {
  if (!value) {
    return "-";
  }

  return colorLabels[value] || value.replace(/_/g, " ");
}

function isApiSessionError(error: unknown) {
  return isSessionError(error) || isCheckoutSessionError(error);
}

function apiErrorMessage(error: unknown) {
  if (error instanceof CartClientError || error instanceof CheckoutClientError) {
    return error.status === 0
      ? "No se pudo conectar con la API. Intentalo de nuevo."
      : error.message;
  }

  return "No se pudo preparar el checkout. Intentalo de nuevo.";
}

function lineKey(line: CheckoutQuoteLine) {
  return [line.product_id, line.alto, line.ancho, line.anclaje, line.color].join("|");
}

export function CheckoutView() {
  const router = useRouter();
  const [status, setStatus] = useState<CheckoutStatus>("loading");
  const [quote, setQuote] = useState<CheckoutQuote | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  function redirectToLogin() {
    clearSession();
    router.replace("/login?next=/checkout");
  }

  async function loadCheckout() {
    const token = getToken();

    if (!token) {
      redirectToLogin();
      return;
    }

    setStatus("loading");
    setErrorMessage("");

    try {
      const cartItems = await getCart(token);

      if (cartItems.length === 0) {
        setQuote(null);
        setStatus("empty");
        return;
      }

      const nextQuote = await getCheckoutQuote(token);

      if (nextQuote.comparison?.has_difference) {
        console.warn("Checkout quote comparison detected a difference. Backend totals are displayed.");
      }

      setQuote(nextQuote);
      setStatus("ready");
    } catch (error) {
      if (isApiSessionError(error)) {
        redirectToLogin();
        return;
      }

      setQuote(null);
      setErrorMessage(apiErrorMessage(error));
      setStatus("error");
    }
  }

  useEffect(() => {
    void loadCheckout();
  }, []);

  if (status === "loading") {
    return (
      <CheckoutState
        title="Preparando tu checkout..."
        description="Estamos verificando tu carrito y calculando el importe final con MetalWolft."
      />
    );
  }

  if (status === "empty") {
    return (
      <CheckoutState
        title="Tu carrito esta vacio"
        description="Configura una reja para ventanas antes de continuar con el checkout."
      >
        <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
          Ver rejas para ventanas
        </Link>
        <Link className="mw-button mw-button--secondary" href="/cart">
          Volver al carrito
        </Link>
      </CheckoutState>
    );
  }

  if (status === "error") {
    return (
      <CheckoutState title="No se pudo preparar el checkout" description={errorMessage}>
        <button className="mw-button mw-button--primary" onClick={loadCheckout} type="button">
          Reintentar
        </button>
        <Link className="mw-button mw-button--secondary" href="/cart">
          Volver al carrito
        </Link>
      </CheckoutState>
    );
  }

  if (!quote) {
    return (
      <CheckoutState
        title="No se pudo calcular el resumen"
        description="Vuelve al carrito e intentalo de nuevo."
      >
        <Link className="mw-button mw-button--secondary" href="/cart">
          Volver al carrito
        </Link>
      </CheckoutState>
    );
  }

  return (
    <section className="mw-checkout-layout" aria-label="Checkout">
      <div className="mw-checkout-panel">
        <div className="mw-checkout-heading">
          <p className="mw-note">Pedido verificado</p>
          <h2>Resumen del checkout</h2>
          <p>
            Tus productos y el importe ya estan verificados. El pago seguro se
            habilitara en la siguiente fase.
          </p>
        </div>

        <CheckoutLines lines={quote.lines} />
      </div>

      <aside className="mw-checkout-summary" aria-label="Resumen economico">
        <div className="mw-checkout-panel">
          <div className="mw-checkout-summary__header">
            <div>
              <p className="mw-note">Total</p>
              <h2>Importe final</h2>
            </div>
            <Link href="/cart">Volver al carrito</Link>
          </div>

          <CheckoutTotals quote={quote} />

          <button className="mw-button mw-button--primary mw-checkout-submit" disabled type="button">
            Continuar al pago
          </button>
          <p className="mw-checkout-next-step">El pago se habilitara en la siguiente fase.</p>
        </div>
      </aside>
    </section>
  );
}

function CheckoutLines({ lines }: { lines: CheckoutQuoteLine[] }) {
  return (
    <div className="mw-checkout-lines">
      {lines.map((line) => (
        <article className="mw-checkout-line" key={lineKey(line)}>
          <div>
            <h3>{line.product_name}</h3>
            <p>
              {formatDimension(line.alto)} x {formatDimension(line.ancho)}
            </p>
            <p>
              {line.anclaje || "-"} · {formatColor(line.color)}
            </p>
          </div>
          <div className="mw-checkout-line__price">
            <span>{line.quantity} ud.</span>
            <strong>{formatCurrency(line.line_total)}</strong>
          </div>
        </article>
      ))}
    </div>
  );
}

function CheckoutTotals({ quote }: { quote: CheckoutQuote }) {
  return (
    <div className="mw-checkout-totals" aria-live="polite">
      <div className="mw-checkout-total-row">
        <span>Subtotal</span>
        <strong>{formatCurrency(quote.subtotal)}</strong>
      </div>
      <div className="mw-checkout-total-row">
        <span>Envio</span>
        <strong>{quote.shipping_cost === 0 ? "GRATIS" : formatCurrency(quote.shipping_cost)}</strong>
      </div>
      {quote.discount_amount > 0 ? (
        <div className="mw-checkout-total-row mw-checkout-total-row--discount">
          <span>Descuento {quote.discount_code ? `(${quote.discount_code})` : ""}</span>
          <strong>-{formatCurrency(quote.discount_amount)}</strong>
        </div>
      ) : null}
      <div className="mw-checkout-total-row mw-checkout-total-row--final">
        <span>Total</span>
        <strong>{formatCurrency(quote.total_amount)}</strong>
      </div>
    </div>
  );
}

function CheckoutState({
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
      <p className="mw-eyebrow">Checkout</p>
      <h2 className="mw-title mw-title--compact">{title}</h2>
      <p className="mw-lead">{description}</p>
      {children ? <div className="mw-actions">{children}</div> : null}
    </section>
  );
}

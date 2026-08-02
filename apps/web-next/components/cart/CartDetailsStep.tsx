"use client";

import Link from "next/link";
import { useEffect, useState, type ChangeEvent, type FormEvent, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getStoredUser, getToken } from "@/lib/auth-client";
import { CartClientError, getCart, isSessionError } from "@/lib/cart-client";
import {
  buildCheckoutDetailsFromUser,
  EMPTY_CHECKOUT_CUSTOMER_DETAILS,
  loadStoredCheckoutDetails,
  saveCheckoutDetails,
  sanitizeCheckoutDetails,
  type CheckoutCustomerDetails,
  type CheckoutDetailsErrors,
  validateCheckoutDetails
} from "@/lib/checkout-details";
import {
  CheckoutClientError,
  type CheckoutQuote,
  type CheckoutQuoteLine,
  getCheckoutQuote,
  isCheckoutSessionError
} from "@/lib/checkout-client";
import {
  clearStoredCheckoutDiscountCode,
  loadStoredCheckoutDiscountCode,
  normalizeCheckoutDiscountCode,
  saveStoredCheckoutDiscountCode
} from "@/lib/checkout-discount";
import { CheckoutDiscountForm } from "@/components/cart/CheckoutDiscountForm";

type CheckoutStatus = "loading" | "empty" | "ready" | "error";

type CartDetailsStepProps = {
  loginNextPath?: string;
  backHref?: string;
  deliveryEstimate?: ReactNode;
};

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

function buildLoginHref(nextPath: string) {
  const [pathname, query] = nextPath.split("?");
  return query ? `/login?next=${pathname}%3F${encodeURIComponent(query)}` : `/login?next=${nextPath}`;
}

export function CartDetailsStep({
  loginNextPath = "/cart?step=details",
  backHref = "/cart",
  deliveryEstimate
}: CartDetailsStepProps) {
  const router = useRouter();
  const [status, setStatus] = useState<CheckoutStatus>("loading");
  const [quote, setQuote] = useState<CheckoutQuote | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [details, setDetails] = useState<CheckoutCustomerDetails>(EMPTY_CHECKOUT_CUSTOMER_DETAILS);
  const [detailsErrors, setDetailsErrors] = useState<CheckoutDetailsErrors>({});
  const [discountInput, setDiscountInput] = useState("");
  const [discountFeedback, setDiscountFeedback] = useState<{
    type: "error" | "success";
    message: string;
  } | null>(null);
  const [isApplyingDiscount, setIsApplyingDiscount] = useState(false);
  const loginHref = buildLoginHref(loginNextPath);

  function redirectToLogin() {
    clearSession();
    router.replace(loginHref);
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

      const storedDiscountCode = loadStoredCheckoutDiscountCode();
      const nextQuote = await getCheckoutQuote(token, { discountCode: storedDiscountCode });
      if (storedDiscountCode && nextQuote.discount_code_valid && nextQuote.discount_code) {
        setDiscountInput(nextQuote.discount_code);
        saveStoredCheckoutDiscountCode(nextQuote.discount_code);
      } else if (storedDiscountCode) {
        clearStoredCheckoutDiscountCode();
        setDiscountInput(storedDiscountCode);
        setDiscountFeedback({
          type: "error",
          message: "Ese codigo no es valido o ya no esta disponible."
        });
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
    const storedDetails = loadStoredCheckoutDetails();
    setDetails(storedDetails || buildCheckoutDetailsFromUser(getStoredUser()));
    void loadCheckout();
  }, []);

  function handleDetailChange(event: ChangeEvent<HTMLInputElement>) {
    const { name, value, type, checked } = event.target;

    setDetails((currentDetails) => {
      const nextDetails = sanitizeCheckoutDetails({
        ...currentDetails,
        [name]: type === "checkbox" ? checked : value
      });

      if (name === "useDifferentShipping" && !checked) {
        nextDetails.shipping_address = "";
        nextDetails.shipping_city = "";
        nextDetails.shipping_postal_code = "";
      }

      return nextDetails;
    });

    setDetailsErrors((currentErrors) => ({
      ...currentErrors,
      [name]: undefined
    }));
  }

  function handleDiscountInputChange(value: string) {
    setDiscountInput(value);
    setDiscountFeedback(null);
  }

  async function refreshQuoteWithDiscount(nextDiscountCode: string | null) {
    const token = getToken();
    if (!token) {
      redirectToLogin();
      return null;
    }

    const nextQuote = await getCheckoutQuote(token, { discountCode: nextDiscountCode });
    setQuote(nextQuote);
    return nextQuote;
  }

  async function handleApplyDiscount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (isApplyingDiscount) {
      return;
    }

    const normalizedCode = normalizeCheckoutDiscountCode(discountInput);
    setIsApplyingDiscount(true);
    setDiscountFeedback(null);

    try {
      if (!normalizedCode) {
        clearStoredCheckoutDiscountCode();
        await refreshQuoteWithDiscount(null);
        setDiscountFeedback({
          type: "success",
          message: "Codigo de descuento retirado."
        });
        return;
      }

      const nextQuote = await refreshQuoteWithDiscount(normalizedCode);
      if (nextQuote?.discount_code_valid && nextQuote.discount_code) {
        saveStoredCheckoutDiscountCode(nextQuote.discount_code);
        setDiscountInput(nextQuote.discount_code);
        setDiscountFeedback({
          type: "success",
          message: "Codigo de descuento aplicado."
        });
        return;
      }

      clearStoredCheckoutDiscountCode();
      setDiscountFeedback({
        type: "error",
        message: "Ese codigo no es valido o no esta disponible."
      });
    } catch (error) {
      if (isApiSessionError(error)) {
        redirectToLogin();
        return;
      }

      setDiscountFeedback({
        type: "error",
        message: apiErrorMessage(error)
      });
    } finally {
      setIsApplyingDiscount(false);
    }
  }

  async function handleRemoveDiscount() {
    if (isApplyingDiscount) {
      return;
    }

    setIsApplyingDiscount(true);
    setDiscountFeedback(null);

    try {
      clearStoredCheckoutDiscountCode();
      setDiscountInput("");
      await refreshQuoteWithDiscount(null);
      setDiscountFeedback({
        type: "success",
        message: "Codigo de descuento retirado."
      });
    } catch (error) {
      if (isApiSessionError(error)) {
        redirectToLogin();
        return;
      }

      setDiscountFeedback({
        type: "error",
        message: apiErrorMessage(error)
      });
    } finally {
      setIsApplyingDiscount(false);
    }
  }

  function handleContinueToPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const validation = validateCheckoutDetails(details);
    setDetails(validation.details);
    setDetailsErrors(validation.errors);

    if (!validation.isValid) {
      return;
    }

    saveCheckoutDetails(validation.details);
    router.push("/cart?step=payment");
  }

  if (status === "loading") {
    return (
      <CheckoutState
        title="Preparando tus datos"
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
        <Link className="mw-button mw-button--secondary" href={backHref}>
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
        <Link className="mw-button mw-button--secondary" href={backHref}>
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
        <Link className="mw-button mw-button--secondary" href={backHref}>
          Volver al carrito
        </Link>
      </CheckoutState>
    );
  }

  return (
    <section className="mw-checkout-layout" aria-label="Datos del pedido">
      <div className="mw-checkout-panel">
        <div className="mw-checkout-heading">
          <p className="mw-note">Datos</p>
          <h2>Datos de contacto y entrega</h2>
          <p>
            Completa los datos necesarios para preparar la factura, el envío y el
            pago seguro. No guardaremos datos de tarjeta en MetalWolft.
          </p>
        </div>

        <form className="mw-checkout-form" onSubmit={handleContinueToPayment}>
          <div className="mw-checkout-form-grid">
            <CheckoutTextField
              error={detailsErrors.firstname}
              label="Nombre"
              name="firstname"
              onChange={handleDetailChange}
              value={details.firstname}
            />
            <CheckoutTextField
              error={detailsErrors.lastname}
              label="Apellidos"
              name="lastname"
              onChange={handleDetailChange}
              value={details.lastname}
            />
            <CheckoutTextField
              error={detailsErrors.email}
              label="Correo electrónico"
              name="email"
              onChange={handleDetailChange}
              type="email"
              value={details.email}
            />
            <CheckoutTextField
              error={detailsErrors.phone}
              label="Teléfono"
              name="phone"
              onChange={handleDetailChange}
              type="tel"
              value={details.phone}
            />
            <CheckoutTextField
              error={detailsErrors.billing_address}
              label="Dirección de facturación"
              name="billing_address"
              onChange={handleDetailChange}
              value={details.billing_address}
              wide
            />
            <CheckoutTextField
              error={detailsErrors.billing_postal_code}
              label="Código postal"
              name="billing_postal_code"
              onChange={handleDetailChange}
              value={details.billing_postal_code}
            />
            <CheckoutTextField
              error={detailsErrors.billing_city}
              label="Ciudad"
              name="billing_city"
              onChange={handleDetailChange}
              value={details.billing_city}
            />
            <CheckoutTextField
              error={detailsErrors.CIF}
              label="DNI / CIF"
              name="CIF"
              onChange={handleDetailChange}
              value={details.CIF}
            />
          </div>

          <label className="mw-checkout-option">
            <input
              checked={details.useDifferentShipping}
              name="useDifferentShipping"
              onChange={handleDetailChange}
              type="checkbox"
            />
            <span>La dirección de envío es diferente a la de facturación</span>
          </label>

          {details.useDifferentShipping ? (
            <div className="mw-checkout-form-grid">
              <CheckoutTextField
                error={detailsErrors.shipping_address}
                label="Dirección de envío"
                name="shipping_address"
                onChange={handleDetailChange}
                value={details.shipping_address}
                wide
              />
              <CheckoutTextField
                error={detailsErrors.shipping_postal_code}
                label="Código postal de envío"
                name="shipping_postal_code"
                onChange={handleDetailChange}
                value={details.shipping_postal_code}
              />
              <CheckoutTextField
                error={detailsErrors.shipping_city}
                label="Ciudad de envío"
                name="shipping_city"
                onChange={handleDetailChange}
                value={details.shipping_city}
              />
            </div>
          ) : null}

          <label className="mw-checkout-option mw-checkout-option--policy">
            <input
              checked={details.acceptedPolicy}
              name="acceptedPolicy"
              onChange={handleDetailChange}
              type="checkbox"
            />
            <span>
              He leído y acepto la{" "}
              <Link href="/politica-devolucion">política de devoluciones y garantías</Link>.
            </span>
          </label>
          {detailsErrors.acceptedPolicy ? (
            <p className="mw-field-error" role="alert">
              {detailsErrors.acceptedPolicy}
            </p>
          ) : null}

          <button className="mw-button mw-button--primary mw-checkout-submit" type="submit">
            Continuar al pago
          </button>
        </form>

        <div className="mw-checkout-heading mw-checkout-heading--compact">
          <p className="mw-note">Pedido</p>
          <h2>Líneas verificadas</h2>
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
            <Link href={backHref}>Volver al carrito</Link>
          </div>

          <CheckoutDiscountForm
            appliedCode={quote.discount_code}
            feedback={discountFeedback}
            inputValue={discountInput}
            isApplying={isApplyingDiscount}
            onApply={handleApplyDiscount}
            onChange={handleDiscountInputChange}
            onRemove={handleRemoveDiscount}
          />
          <CheckoutTotals quote={quote} />
          {deliveryEstimate}
        </div>
      </aside>
    </section>
  );
}

function CheckoutTextField({
  error,
  label,
  name,
  onChange,
  type = "text",
  value,
  wide = false
}: {
  error?: string;
  label: string;
  name: keyof CheckoutCustomerDetails;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  type?: string;
  value: string;
  wide?: boolean;
}) {
  const errorId = error ? `${name}-error` : undefined;

  return (
    <label className={`mw-field${wide ? " mw-field--wide" : ""}`}>
      <span>{label}</span>
      <input
        aria-describedby={errorId}
        aria-invalid={Boolean(error)}
        autoComplete={name === "email" ? "email" : undefined}
        name={name}
        onChange={onChange}
        type={type}
        value={value}
      />
      {error ? (
        <span className="mw-field-error" id={errorId}>
          {error}
        </span>
      ) : null}
    </label>
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
              {line.anclaje || "-"} - {formatColor(line.color)}
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

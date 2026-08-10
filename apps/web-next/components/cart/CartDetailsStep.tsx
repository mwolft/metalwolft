"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getStoredUser, getToken, saveSession } from "@/lib/auth-client";
import { CartClientError, getCart, isSessionError } from "@/lib/cart-client";
import {
  buildCheckoutDetailsFromUser,
  changeCheckoutBillingType,
  EMPTY_CHECKOUT_CUSTOMER_DETAILS,
  loadStoredCheckoutDetails,
  mergeCheckoutDetailsWithUser,
  saveCheckoutDetails,
  type CheckoutCustomerDetails,
  type CheckoutBillingType,
  type CheckoutDraftField,
  type CheckoutDetailsErrors,
  updateCheckoutDraftField,
  validateCheckoutDetails
} from "@/lib/checkout-details";
import { fetchCustomerProfile } from "@/lib/customer-profile-client";
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
type CheckoutDetailsErrorField = keyof CheckoutCustomerDetails;

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
  return [
    line.product_id,
    line.alto,
    line.ancho,
    line.anclaje,
    line.color,
    line.screw_option
  ].join("|");
}

function buildLoginHref(nextPath: string) {
  const [pathname, query] = nextPath.split("?");
  return query ? `/login?next=${pathname}%3F${encodeURIComponent(query)}` : `/login?next=${nextPath}`;
}

function buildCheckoutErrorSummary(
  errors: CheckoutDetailsErrors,
  billingType: CheckoutBillingType
) {
  const requiredMessages: Partial<Record<CheckoutDetailsErrorField, string>> = {
    firstname: "Falta completar el nombre.",
    lastname: "Falta completar los apellidos.",
    email: "Falta completar el correo electrónico.",
    phone: "Falta completar el teléfono.",
    legal_name:
      billingType === "company"
        ? "Falta indicar la razón social."
        : "Falta completar el nombre fiscal.",
    tax_id:
      billingType === "company"
        ? "Falta indicar el NIF / CIF."
        : "Falta indicar el NIF / NIE.",
    billing_address: "Falta indicar la dirección de facturación.",
    billing_city: "Falta indicar la ciudad de facturación.",
    billing_postal_code: "Falta indicar el código postal de facturación.",
    shipping_address: "Falta indicar la dirección de envío.",
    shipping_city: "Falta indicar la ciudad de envío.",
    shipping_postal_code: "Falta indicar el código postal de envío.",
    acceptedPolicy: "Debes aceptar la política de devoluciones y garantías."
  };

  return (Object.entries(errors) as Array<[CheckoutDetailsErrorField, string | undefined]>)
    .flatMap(([field, error]) => {
      if (!error) {
        return [];
      }

      return [{
        field,
        message: error === "Campo obligatorio." ? requiredMessages[field] ?? error : error
      }];
    });
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
  const [hasAttemptedContinue, setHasAttemptedContinue] = useState(false);
  const [discountInput, setDiscountInput] = useState("");
  const [discountFeedback, setDiscountFeedback] = useState<{
    type: "error" | "success";
    message: string;
  } | null>(null);
  const [isApplyingDiscount, setIsApplyingDiscount] = useState(false);
  const dirtyDetailFieldsRef = useRef<Set<CheckoutDraftField>>(new Set());
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
    const storedUser = getStoredUser();
    setDetails(
      storedDetails
        ? mergeCheckoutDetailsWithUser(storedDetails, storedUser)
        : buildCheckoutDetailsFromUser(storedUser)
    );

    const token = getToken();
    const profileRequest = new AbortController();
    if (token) {
      void fetchCustomerProfile(token, profileRequest.signal)
        .then((profile) => {
          saveSession(token, profile);
          setDetails((currentDetails) =>
            mergeCheckoutDetailsWithUser(
              currentDetails,
              profile,
              Array.from(dirtyDetailFieldsRef.current)
            )
          );
        })
        .catch(() => {
          // The cached profile remains a safe, non-blocking fallback for checkout.
        });
    }

    void loadCheckout();

    return () => profileRequest.abort();
  }, []);

  function handleDetailChange(event: ChangeEvent<HTMLInputElement>) {
    const { name, value, type, checked } = event.target;

    if (name === "billing_type") {
      dirtyDetailFieldsRef.current.add("legal_name");
      dirtyDetailFieldsRef.current.add("tax_id");
    } else {
      dirtyDetailFieldsRef.current.add(name as CheckoutDraftField);
    }

    setDetails((currentDetails) => {
      if (name === "billing_type") {
        return changeCheckoutBillingType(currentDetails, value as CheckoutBillingType);
      }

      return updateCheckoutDraftField(
        currentDetails,
        name as CheckoutDraftField,
        type === "checkbox" ? checked : value
      );
    });

    setDetailsErrors((currentErrors) => ({
      ...currentErrors,
      [name]: undefined,
      ...(name === "billing_type" ? { legal_name: undefined, tax_id: undefined } : {})
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
    setHasAttemptedContinue(true);
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

  const currentDetailsErrors = hasAttemptedContinue
    ? validateCheckoutDetails(details).errors
    : detailsErrors;
  const checkoutErrorSummary = hasAttemptedContinue
    ? buildCheckoutErrorSummary(currentDetailsErrors, details.billing_type)
    : [];

  function focusCheckoutField(field: CheckoutDetailsErrorField) {
    const fieldElement = document.querySelector<HTMLInputElement>(
      `#mw-checkout-details-form [name="${field}"]`
    );
    if (!fieldElement) {
      return;
    }

    const behavior = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? "auto"
      : "smooth";
    fieldElement.scrollIntoView({ behavior, block: "center" });
    fieldElement.focus({ preventScroll: true });
  }

  return (
    <section className="mw-checkout-layout" aria-label="Datos del pedido">
      <div className="mw-checkout-panel">
        <div className="mw-checkout-heading">
          <p className="mw-note">Datos</p>
          <h2>Datos de contacto, facturación y entrega</h2>
          <p>
            Completa los datos necesarios para preparar la factura, el envío y el
            pago seguro. No guardaremos datos de tarjeta en MetalWolft.
          </p>
        </div>

        <form
          className="mw-checkout-form"
          id="mw-checkout-details-form"
          onSubmit={handleContinueToPayment}
        >
          <section className="mw-checkout-form-section" aria-labelledby="checkout-contact-title">
            <h3 id="checkout-contact-title">Datos de contacto</h3>
            <div className="mw-checkout-form-grid">
              <CheckoutTextField
                autoComplete="given-name"
                error={currentDetailsErrors.firstname}
                label="Nombre"
                name="firstname"
                onChange={handleDetailChange}
                value={details.firstname}
              />
              <CheckoutTextField
                autoComplete="family-name"
                error={currentDetailsErrors.lastname}
                label="Apellidos"
                name="lastname"
                onChange={handleDetailChange}
                value={details.lastname}
              />
              <CheckoutTextField
                autoComplete="email"
                error={currentDetailsErrors.email}
                label="Correo electrónico"
                name="email"
                onChange={handleDetailChange}
                type="email"
                value={details.email}
              />
              <CheckoutTextField
                autoComplete="tel"
                error={currentDetailsErrors.phone}
                label="Teléfono"
                name="phone"
                onChange={handleDetailChange}
                type="tel"
                value={details.phone}
              />
            </div>
          </section>

          <section
            className="mw-checkout-form-section mw-checkout-form-section--divided"
            aria-labelledby="checkout-billing-title"
          >
            <h3 id="checkout-billing-title">Datos de facturación</h3>
            <fieldset className="mw-checkout-billing-type">
              <legend>¿A nombre de quién se emitirá la factura?</legend>
              <div className="mw-checkout-billing-type__options">
                <label>
                  <input
                    checked={details.billing_type === "individual"}
                    name="billing_type"
                    onChange={handleDetailChange}
                    type="radio"
                    value="individual"
                  />
                  <span>Particular / autónomo</span>
                </label>
                <label>
                  <input
                    checked={details.billing_type === "company"}
                    name="billing_type"
                    onChange={handleDetailChange}
                    type="radio"
                    value="company"
                  />
                  <span>Empresa</span>
                </label>
              </div>
            </fieldset>

            <div className="mw-checkout-form-grid">
              <CheckoutTextField
                autoComplete={details.billing_type === "company" ? "organization" : "name"}
                error={currentDetailsErrors.legal_name}
                helper={
                  details.billing_type === "company"
                    ? "El nombre legal que debe aparecer en la factura."
                    : undefined
                }
                label={details.billing_type === "company" ? "Razón social" : "Nombre fiscal"}
                maxLength={255}
                name="legal_name"
                onChange={handleDetailChange}
                value={details.legal_name}
                wide
              />
              <CheckoutTextField
                error={currentDetailsErrors.tax_id}
                label={details.billing_type === "company" ? "NIF / CIF" : "NIF / NIE"}
                maxLength={20}
                name="tax_id"
                onChange={handleDetailChange}
                value={details.tax_id}
              />
              <CheckoutTextField
                autoComplete="billing street-address"
                error={currentDetailsErrors.billing_address}
                label="Dirección de facturación"
                name="billing_address"
                onChange={handleDetailChange}
                value={details.billing_address}
                wide
              />
              <CheckoutTextField
                autoComplete="billing postal-code"
                error={currentDetailsErrors.billing_postal_code}
                label="Código postal"
                name="billing_postal_code"
                onChange={handleDetailChange}
                value={details.billing_postal_code}
              />
              <CheckoutTextField
                autoComplete="billing address-level2"
                error={currentDetailsErrors.billing_city}
                label="Ciudad"
                name="billing_city"
                onChange={handleDetailChange}
                value={details.billing_city}
              />
            </div>
          </section>

          <section
            className="mw-checkout-form-section mw-checkout-form-section--divided"
            aria-labelledby="checkout-shipping-title"
          >
            <h3 id="checkout-shipping-title">Dirección de entrega</h3>
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
                  autoComplete="shipping street-address"
                  error={currentDetailsErrors.shipping_address}
                  label="Dirección de envío"
                  name="shipping_address"
                  onChange={handleDetailChange}
                  value={details.shipping_address}
                  wide
                />
                <CheckoutTextField
                  autoComplete="shipping postal-code"
                  error={currentDetailsErrors.shipping_postal_code}
                  label="Código postal de envío"
                  name="shipping_postal_code"
                  onChange={handleDetailChange}
                  value={details.shipping_postal_code}
                />
                <CheckoutTextField
                  autoComplete="shipping address-level2"
                  error={currentDetailsErrors.shipping_city}
                  label="Ciudad de envío"
                  name="shipping_city"
                  onChange={handleDetailChange}
                  value={details.shipping_city}
                />
              </div>
            ) : null}
          </section>

          <label className="mw-checkout-option mw-checkout-option--policy">
            <input
              aria-invalid={Boolean(currentDetailsErrors.acceptedPolicy)}
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
          <section className="mw-checkout-order" aria-labelledby="checkout-order-title">
            <h2 id="checkout-order-title">Tu pedido</h2>
            <CheckoutLines lines={quote.lines} />
          </section>

        </form>
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
          {checkoutErrorSummary.length > 0 ? (
            <section
              aria-label="Campos pendientes"
              className="mw-checkout-validation-summary"
              role="alert"
            >
              <span aria-hidden="true" className="mw-checkout-validation-summary__icon">
                !
              </span>
              <ul>
                {checkoutErrorSummary.map((item) => (
                  <li key={item.field}>
                    <button onClick={() => focusCheckoutField(item.field)} type="button">
                      {item.message}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
          <button
            className="mw-button mw-button--primary mw-checkout-submit"
            form="mw-checkout-details-form"
            type="submit"
          >
            Continuar al pago
          </button>
        </div>
      </aside>
    </section>
  );
}

function CheckoutTextField({
  autoComplete,
  error,
  helper,
  label,
  maxLength,
  name,
  onChange,
  type = "text",
  value,
  wide = false
}: {
  autoComplete?: string;
  error?: string;
  helper?: string;
  label: string;
  maxLength?: number;
  name: keyof CheckoutCustomerDetails;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  type?: string;
  value: string;
  wide?: boolean;
}) {
  const helperId = helper ? `${name}-helper` : undefined;

  return (
    <label className={`mw-field${wide ? " mw-field--wide" : ""}`}>
      <span>{label}</span>
      <input
        aria-describedby={helperId}
        aria-invalid={Boolean(error)}
        autoComplete={autoComplete}
        maxLength={maxLength}
        name={name}
        onChange={onChange}
        type={type}
        value={value}
      />
      {helper ? (
        <small className="mw-field-helper" id={helperId}>
          {helper}
        </small>
      ) : null}
    </label>
  );
}

function CheckoutLines({ lines }: { lines: CheckoutQuoteLine[] }) {
  return (
    <div className="mw-checkout-lines">
      {lines.map((line) => {
        const screwLength = Number(line.screw_length_mm);
        const hasScrewLength = Number.isFinite(screwLength) && screwLength > 0;
        return (
          <article className="mw-checkout-line" key={lineKey(line)}>
            <div>
              <h3>{line.product_name}</h3>
              <p className="mw-checkout-line__technical">
                <strong>Alto:</strong> {formatDimension(line.alto)} · <strong>Ancho:</strong>{" "}
                {formatDimension(line.ancho)}
              </p>
              <p className="mw-checkout-line__technical">
                <strong>Instalación:</strong> {line.anclaje || "-"}
              </p>
              {hasScrewLength ? (
                <p className="mw-checkout-line__technical">
                  <strong>Tornillos:</strong> {screwLength.toLocaleString("es-ES")} mm
                </p>
              ) : null}
              <p className="mw-checkout-line__technical">
                <strong>Color:</strong> {formatColor(line.color)} · <strong>Acabado:</strong>{" "}
                Esmalte sintético
              </p>
            </div>
            <div className="mw-checkout-line__price">
              <span>{line.quantity} ud.</span>
              <strong>{formatCurrency(line.line_total)}</strong>
            </div>
          </article>
        );
      })}
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

"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  builderInputsToDraftItems,
  draftItemToBuilderInput,
  isCompleteDesignServiceBuilderInput,
  type DesignServiceBuilderInput,
  type DesignServiceProductOption
} from "@/lib/design-service-builder";
import {
  clearDesignServiceDraft,
  saveDesignServiceDraft,
  startDesignServiceDraft,
  type DesignServiceDraftItem
} from "@/lib/design-service-draft";
import {
  DesignServiceClientError,
  createDesignServiceRequest,
  requestDesignServiceQuote,
  type DesignServiceQuote
} from "@/lib/design-service-client";
import { clearSession, getStoredUser, getToken } from "@/lib/auth-client";
import {
  getOrCreateDesignServiceCreationKey,
  rememberDesignServiceRequest
} from "@/lib/design-service-request-session";

type DesignServiceBuilderProps = {
  products: DesignServiceProductOption[];
  initialSeed?: DesignServiceDraftItem | null;
  resumeDraftAfterAuth?: boolean;
};

const QUOTE_DEBOUNCE_MS = 450;

function makeInputId() {
  return `design-${Math.random().toString(36).slice(2, 10)}`;
}

function emptyDesign(): DesignServiceBuilderInput {
  return { id: makeInputId(), product_id: "", width_cm: "", height_cm: "" };
}

function formatCurrency(value: string, currency: string) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency
  }).format(Number(value));
}

function errorMessage(error: unknown) {
  if (!(error instanceof DesignServiceClientError)) {
    return "No hemos podido actualizar el precio ahora mismo. Inténtalo de nuevo en unos segundos.";
  }

  switch (error.kind) {
    case "service_unavailable":
      return "El servicio de diseño previo no está disponible en este momento.";
    case "rate_limited":
      return "Has realizado varias consultas seguidas. Espera un momento antes de volver a intentarlo.";
    case "validation":
      return "Revisa el modelo y las medidas de cada diseño para poder calcular el precio.";
    default:
      return "No hemos podido actualizar el precio ahora mismo. Inténtalo de nuevo en unos segundos.";
  }
}

function creationErrorMessage(error: unknown) {
  if (!(error instanceof DesignServiceClientError)) {
    return "No hemos podido preparar tu solicitud ahora mismo. Inténtalo de nuevo.";
  }

  switch (error.kind) {
    case "service_unavailable":
      return "El servicio de diseño previo no está disponible en este momento.";
    case "validation":
      return "Revisa los modelos y las medidas antes de continuar.";
    case "rate_limited":
      return "Has realizado varias consultas seguidas. Espera un momento antes de continuar.";
    default:
      return "No hemos podido preparar tu solicitud ahora mismo. Inténtalo de nuevo.";
  }
}

export function DesignServiceBuilder({
  products,
  initialSeed = null,
  resumeDraftAfterAuth = false
}: DesignServiceBuilderProps) {
  const router = useRouter();
  const [designs, setDesigns] = useState<DesignServiceBuilderInput[]>([emptyDesign()]);
  const [hydrated, setHydrated] = useState(false);
  const [quote, setQuote] = useState<DesignServiceQuote | null>(null);
  const [quoteError, setQuoteError] = useState<string | null>(null);
  const [isQuoting, setIsQuoting] = useState(false);
  const [isContinuing, setIsContinuing] = useState(false);
  const [continuationError, setContinuationError] = useState<string | null>(null);
  const headingId = useId();
  const requestVersion = useRef(0);

  useEffect(() => {
    // A seeded URL always starts a fresh request. Normal visits never revive abandoned selections.
    const initialItems = startDesignServiceDraft(initialSeed, resumeDraftAfterAuth);

    setDesigns(
      initialItems.length
        ? initialItems.map((item) => draftItemToBuilderInput(item, makeInputId()))
        : [emptyDesign()]
    );
    setHydrated(true);
  }, [initialSeed, resumeDraftAfterAuth]);

  const { items: validItems, duplicateInputIds } = builderInputsToDraftItems(designs, products);
  const validItemsKey = JSON.stringify(validItems);
  const hasIncompleteDesign = designs.some(
    (design) => !isCompleteDesignServiceBuilderInput(design, products)
  );

  useEffect(() => {
    const version = ++requestVersion.current;
    if (!hydrated || !validItems.length || hasIncompleteDesign) {
      setQuote(null);
      setQuoteError(null);
      setIsQuoting(false);
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      setIsQuoting(true);
      setQuoteError(null);
      requestDesignServiceQuote(validItems, { signal: controller.signal })
        .then((nextQuote) => {
          if (requestVersion.current === version) setQuote(nextQuote);
        })
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          if (requestVersion.current === version) {
            setQuote(null);
            setQuoteError(errorMessage(error));
          }
        })
        .finally(() => {
          if (requestVersion.current === version) setIsQuoting(false);
        });
    }, QUOTE_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [hasIncompleteDesign, hydrated, validItemsKey]);

  function updateDesign(id: string, field: Exclude<keyof DesignServiceBuilderInput, "id">, value: string) {
    setDesigns((current) =>
      current.map((design) => (design.id === id ? { ...design, [field]: value } : design))
    );
  }

  function addDesign() {
    setDesigns((current) => [...current, emptyDesign()]);
  }

  function removeDesign(id: string) {
    setDesigns((current) => (current.length > 1 ? current.filter((design) => design.id !== id) : current));
  }

  async function continueToCheckout() {
    if (!quote || hasIncompleteDesign || !validItems.length || isContinuing) {
      return;
    }

    const token = getToken();
    const user = getStoredUser();
    if (!token || !user?.id) {
      saveDesignServiceDraft(validItems);
      router.push(`/login?next=${encodeURIComponent("/diseno-previo?resume=auth")}`);
      return;
    }

    setIsContinuing(true);
    setContinuationError(null);
    try {
      // Revalidate prices and active configuration immediately before creating the request.
      const freshQuote = await requestDesignServiceQuote(validItems);
      setQuote(freshQuote);

      const sessionRequest = getOrCreateDesignServiceCreationKey(user.id, validItems);
      if (sessionRequest.design_request_id) {
        clearDesignServiceDraft();
        router.push(`/diseno-previo/checkout?design_request_id=${sessionRequest.design_request_id}`);
        return;
      }

      const result = await createDesignServiceRequest(
        token,
        validItems,
        sessionRequest.creation_key
      );
      rememberDesignServiceRequest(user.id, validItems, result.id);
      clearDesignServiceDraft();
      router.push(`/diseno-previo/checkout?design_request_id=${result.id}`);
    } catch (error) {
      if (error instanceof DesignServiceClientError && error.kind === "authentication") {
        clearSession();
        saveDesignServiceDraft(validItems);
        router.push(`/login?next=${encodeURIComponent("/diseno-previo?resume=auth")}`);
        return;
      }
      setContinuationError(creationErrorMessage(error));
    } finally {
      setIsContinuing(false);
    }
  }

  const canContinue = Boolean(quote && validItems.length && !hasIncompleteDesign && !isQuoting && !quoteError);

  return (
    <section className="mw-design-builder" aria-labelledby={headingId}>
      <div className="mw-design-builder__intro">
        <div>
          <p className="mw-eyebrow">Tu solicitud</p>
          <h2 id={headingId}>Elige los modelos y sus medidas</h2>
          <p>
            Solo necesitamos el modelo, el ancho y el alto. Calcularemos el precio exacto antes de continuar.
          </p>
        </div>
        <p className="mw-design-builder__multi-note">
          ¿Necesitas visualizar varias rejas? Añade más diseños y obtén mejor precio por unidad.
        </p>
      </div>

      <div className="mw-design-builder__layout">
        <div className="mw-design-builder__cards">
          {designs.map((design, index) => {
            const duplicate = duplicateInputIds.has(design.id);
            const modelId = `design-model-${design.id}`;
            const widthId = `design-width-${design.id}`;
            const heightId = `design-height-${design.id}`;
            return (
              <fieldset className="mw-design-card" key={design.id} aria-describedby={duplicate ? `${design.id}-duplicate` : undefined}>
                <legend>Diseño {index + 1}</legend>
                <div className="mw-design-card__fields">
                  <label className="mw-field mw-field--wide" htmlFor={modelId}>
                    <span>Modelo</span>
                    <select
                      id={modelId}
                      value={design.product_id}
                      onChange={(event) => updateDesign(design.id, "product_id", event.target.value)}
                    >
                      <option value="">Selecciona un modelo</option>
                      {products.map((product) => (
                        <option key={product.id} value={product.id}>
                          {product.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="mw-field" htmlFor={widthId}>
                    <span>Ancho</span>
                    <span className="mw-design-card__measure">
                      <input
                        id={widthId}
                        inputMode="decimal"
                        min="0"
                        placeholder="200"
                        value={design.width_cm}
                        onChange={(event) => updateDesign(design.id, "width_cm", event.target.value)}
                      />
                      <small>cm</small>
                    </span>
                  </label>
                  <label className="mw-field" htmlFor={heightId}>
                    <span>Alto</span>
                    <span className="mw-design-card__measure">
                      <input
                        id={heightId}
                        inputMode="decimal"
                        min="0"
                        placeholder="120"
                        value={design.height_cm}
                        onChange={(event) => updateDesign(design.id, "height_cm", event.target.value)}
                      />
                      <small>cm</small>
                    </span>
                  </label>
                </div>
                {duplicate ? (
                  <p className="mw-field-error" id={`${design.id}-duplicate`} role="status">
                    Este diseño ya está incluido en tu solicitud.
                  </p>
                ) : null}
                {designs.length > 1 ? (
                  <button className="mw-design-card__remove" type="button" onClick={() => removeDesign(design.id)}>
                    Eliminar este diseño
                  </button>
                ) : null}
              </fieldset>
            );
          })}
          <button className="mw-design-builder__add" type="button" onClick={addDesign}>
            <span aria-hidden="true">+</span> Añadir otro diseño
          </button>
        </div>

        <aside className="mw-design-summary" aria-live="polite">
          <p className="mw-design-summary__eyebrow">Resumen</p>
          {!validItems.length ? (
            <p className="mw-design-summary__empty">Añade un modelo y sus medidas para ver el precio.</p>
          ) : hasIncompleteDesign ? (
            <p className="mw-design-summary__empty">Completa todos los diseños para actualizar el precio.</p>
          ) : isQuoting ? (
            <p className="mw-design-summary__empty">Actualizando precio…</p>
          ) : quoteError ? (
            <p className="mw-alert mw-alert--error">{quoteError}</p>
          ) : quote ? (
            <div className="mw-design-summary__quote">
              <p className="mw-design-summary__count">
                {quote.items.length} {quote.items.length === 1 ? "diseño" : "diseños"}
              </p>
              {quote.items.length === 1 ? (
                <div className="mw-design-summary__single">
                  <span>Diseño previo a medida</span>
                  <strong>{formatCurrency(quote.total_amount, quote.currency)}</strong>
                </div>
              ) : (
                <>
                  <div className="mw-design-summary__row">
                    <span>Precio sin descuento</span>
                    <strong>{formatCurrency(quote.base_price_gross, quote.currency)}</strong>
                  </div>
                  <div className="mw-design-summary__row mw-design-summary__row--discount">
                    <span>Descuento</span>
                    <strong>-{formatCurrency(quote.discount_amount, quote.currency)}</strong>
                  </div>
                </>
              )}
              <div className="mw-design-summary__total">
                <span>Total</span>
                <strong>{formatCurrency(quote.total_amount, quote.currency)}</strong>
              </div>
              {Number(quote.discount_amount) > 0 ? (
                <p className="mw-design-summary__saving">
                  Ahorras {formatCurrency(quote.discount_amount, quote.currency)}
                </p>
              ) : null}
              <p className="mw-design-summary__tax">IVA incluido. Entrega estimada: {quote.lead_time_hours} h.</p>
            </div>
          ) : null}
          <button
            className="mw-button mw-button--primary mw-design-summary__continue"
            type="button"
            disabled={!canContinue || isContinuing}
            onClick={continueToCheckout}
          >
            {isContinuing ? "Preparando solicitud…" : "Continuar"}
          </button>
          {continuationError ? <p className="mw-alert mw-alert--error">{continuationError}</p> : null}
        </aside>
      </div>
    </section>
  );
}

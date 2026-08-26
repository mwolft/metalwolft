import type { DesignServiceDraftItem } from "@/lib/design-service-draft";

const CLIENT_LOCAL_API_URL = "http://127.0.0.1:3001";

export type DesignServiceQuoteItem = Pick<
  DesignServiceDraftItem,
  "product_id" | "width_cm" | "height_cm"
>;

export type DesignServiceQuote = {
  checkout_kind: "design_service";
  currency: "EUR";
  requires_shipping: false;
  shipping_cost: string;
  subtotal: string;
  base_price_gross: string;
  discount_amount: string;
  total_amount: string;
  tax_rate: string;
  tax_base: string;
  tax_amount: string;
  lead_time_hours: number;
  pricing_tier_min_design_count: number | null;
  items: Array<{
    product_id: number;
    product_name: string;
    width_cm: string;
    height_cm: string;
  }>;
};

export type CreateDesignRequestResponse = {
  id: number;
  reference: string;
  status: "pending_payment";
  created: boolean;
};

export type DesignServiceCheckoutQuote = DesignServiceQuote & {
  design_request_id: number;
};

export type DesignServiceCustomerData = {
  firstname: string;
  lastname: string;
  email: string;
  phone: string;
  legal_name: string;
  tax_id: string;
  billing_address: string;
  billing_city: string;
  billing_postal_code: string;
};

export type DesignServicePaymentSession = {
  checkout_session_id: number;
  checkout_session_status: string;
  payment_provider: "stripe" | "paypal";
  payment_intent_id: string | null;
  provider_order_id: string | null;
  provider_capture_id: string | null;
  provider_status: string | null;
  public_checkout_token: string | null;
  checkout_summary: DesignServiceCheckoutQuote;
};

export type DesignServiceStripePaymentResponse = DesignServicePaymentSession & {
  clientSecret: string;
  paymentIntent: { id: string; status: string };
  amount_used_cents: number;
};

export type DesignServiceConfirmation = {
  id: number;
  reference: string;
  status: "pending_payment" | "pending" | "in_progress" | "delivered";
  lead_time_hours: number;
  total_amount: string;
  currency: "EUR";
  items: Array<{ product_name: string; width_cm: string; height_cm: string }>;
  order: { id: number; locator: string } | null;
  checkout_status: string | null;
};

type DesignServiceClientErrorKind =
  | "configuration"
  | "network"
  | "service_unavailable"
  | "validation"
  | "duplicate"
  | "rate_limited"
  | "authentication"
  | "contract";

export class DesignServiceClientError extends Error {
  kind: DesignServiceClientErrorKind;
  status: number;

  constructor(message: string, kind: DesignServiceClientErrorKind, status = 0) {
    super(message);
    this.name = "DesignServiceClientError";
    this.kind = kind;
    this.status = status;
  }
}

type RequestOptions = {
  apiBaseUrl?: string;
  fetcher?: typeof fetch;
  signal?: AbortSignal;
};

function designServiceApiUrl(override?: string) {
  const configuredApiUrl = override ?? process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configuredApiUrl) {
    return configuredApiUrl.replace(/\/$/, "");
  }
  if (process.env.NODE_ENV !== "production") {
    return CLIENT_LOCAL_API_URL;
  }
  throw new DesignServiceClientError(
    "La API del diseño previo no está configurada.",
    "configuration"
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isMoney(value: unknown): value is string {
  return typeof value === "string" && /^-?\d+\.\d{2}$/.test(value);
}

function isQuoteItem(value: unknown) {
  return (
    isRecord(value) &&
    typeof value.product_id === "number" &&
    Number.isInteger(value.product_id) &&
    typeof value.product_name === "string" &&
    typeof value.width_cm === "string" &&
    typeof value.height_cm === "string"
  );
}

function isQuote(value: unknown): value is DesignServiceQuote {
  if (!isRecord(value)) {
    return false;
  }
  return (
    value.checkout_kind === "design_service" &&
    value.currency === "EUR" &&
    value.requires_shipping === false &&
    isMoney(value.shipping_cost) &&
    isMoney(value.subtotal) &&
    isMoney(value.base_price_gross) &&
    isMoney(value.discount_amount) &&
    isMoney(value.total_amount) &&
    isMoney(value.tax_rate) &&
    isMoney(value.tax_base) &&
    isMoney(value.tax_amount) &&
    typeof value.lead_time_hours === "number" &&
    Number.isInteger(value.lead_time_hours) &&
    (value.pricing_tier_min_design_count === null ||
      (typeof value.pricing_tier_min_design_count === "number" &&
        Number.isInteger(value.pricing_tier_min_design_count))) &&
    Array.isArray(value.items) &&
    value.items.every(isQuoteItem)
  );
}

function isCheckoutQuote(value: unknown): value is DesignServiceCheckoutQuote {
  if (!isRecord(value)) return false;
  const designRequestId = value["design_request_id"];
  return isQuote(value) && typeof designRequestId === "number" &&
    Number.isInteger(designRequestId) && designRequestId > 0;
}

function isPaymentSession(value: unknown): value is DesignServicePaymentSession {
  return (
    isRecord(value) &&
    typeof value.checkout_session_id === "number" &&
    typeof value.checkout_session_status === "string" &&
    (value.payment_provider === "stripe" || value.payment_provider === "paypal") &&
    isCheckoutQuote(value.checkout_summary)
  );
}

function responseMessage(payload: unknown, fallback: string) {
  return isRecord(payload) && typeof payload.message === "string" ? payload.message : fallback;
}

function errorKind(status: number, message: string): DesignServiceClientErrorKind {
  if (status === 401 || status === 403) return "authentication";
  if (status === 429) return "rate_limited";
  if (status >= 500) return "network";
  const normalized = message.toLocaleLowerCase("es-ES");
  if (normalized.includes("no disponible actualmente") || normalized.includes("configuración")) {
    return "service_unavailable";
  }
  if (normalized.includes("repetir")) return "duplicate";
  return "validation";
}

function quoteRequestItems(items: readonly DesignServiceQuoteItem[]) {
  return items.map((item) => ({
    product_id: item.product_id,
    width_cm: item.width_cm,
    height_cm: item.height_cm
  }));
}

export async function requestDesignServiceQuote(
  items: readonly DesignServiceQuoteItem[],
  options: RequestOptions = {}
) {
  const fetcher = options.fetcher ?? fetch;
  let response: Response;
  try {
    response = await fetcher(`${designServiceApiUrl(options.apiBaseUrl)}/api/design-requests/quote`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: quoteRequestItems(items) }),
      signal: options.signal
    });
  } catch (error) {
    if (isRecord(error) && error.name === "AbortError") throw error;
    throw new DesignServiceClientError(
      "No se pudo conectar con el servicio de diseño previo.",
      "network"
    );
  }

  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    const message = responseMessage(payload, "No se pudo calcular el diseño previo.");
    throw new DesignServiceClientError(message, errorKind(response.status, message), response.status);
  }
  if (!isQuote(payload)) {
    throw new DesignServiceClientError(
      "El servicio de diseño previo devolvió una respuesta no válida.",
      "contract",
      response.status
    );
  }
  return payload;
}

export async function createDesignServiceRequest(
  token: string,
  items: readonly DesignServiceQuoteItem[],
  creationKey: string,
  options: RequestOptions = {}
) {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(`${designServiceApiUrl(options.apiBaseUrl)}/api/design-requests`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": creationKey
    },
    body: JSON.stringify({ items: quoteRequestItems(items) }),
    signal: options.signal
  }).catch(() => {
    throw new DesignServiceClientError(
      "No se pudo conectar con el servicio de diseño previo.",
      "network"
    );
  });
  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    const message = responseMessage(payload, "No se pudo crear la solicitud de diseño.");
    throw new DesignServiceClientError(message, errorKind(response.status, message), response.status);
  }
  if (
    !isRecord(payload) ||
    typeof payload.id !== "number" ||
    typeof payload.reference !== "string" ||
    payload.status !== "pending_payment" ||
    typeof payload.created !== "boolean"
  ) {
    throw new DesignServiceClientError(
      "El servicio de diseño previo devolvió una respuesta no válida.",
      "contract",
      response.status
    );
  }
  return payload as CreateDesignRequestResponse;
}

export async function getDesignServiceCheckoutQuote(
  token: string,
  designRequestId: number,
  options: RequestOptions = {}
) {
  if (!Number.isInteger(designRequestId) || designRequestId <= 0) {
    throw new DesignServiceClientError("La solicitud de diseño no es válida.", "validation");
  }

  const fetcher = options.fetcher ?? fetch;
  let response: Response;
  try {
    response = await fetcher(
      `${designServiceApiUrl(options.apiBaseUrl)}/api/design-requests/${designRequestId}/checkout-quote`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        signal: options.signal
      }
    );
  } catch {
    throw new DesignServiceClientError(
      "No se pudo preparar la compra del diseño previo.",
      "network"
    );
  }

  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    const message = responseMessage(payload, "No se pudo preparar la compra del diseño previo.");
    throw new DesignServiceClientError(message, errorKind(response.status, message), response.status);
  }
  if (!isCheckoutQuote(payload)) {
    throw new DesignServiceClientError(
      "El servicio de diseño previo devolvió una respuesta no válida.",
      "contract",
      response.status
    );
  }
  return payload;
}

async function requestPrivateDesignService<T>(
  token: string,
  path: string,
  body: Record<string, unknown> | undefined,
  options: RequestOptions = {}
) {
  const fetcher = options.fetcher ?? fetch;
  let response: Response;
  try {
    response = await fetcher(`${designServiceApiUrl(options.apiBaseUrl)}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        ...(body === undefined ? {} : { "Content-Type": "application/json" })
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      signal: options.signal
    });
  } catch {
    throw new DesignServiceClientError("No se pudo conectar con el pago del diseño previo.", "network");
  }
  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    const message = responseMessage(payload, "No se pudo completar el pago del diseño previo.");
    throw new DesignServiceClientError(message, errorKind(response.status, message), response.status);
  }
  return payload as T;
}

export async function createDesignServiceStripePaymentIntent(
  token: string,
  designRequestId: number,
  input: { payment_method_id: string; idempotency_key: string; customer_data: DesignServiceCustomerData },
  options: RequestOptions = {}
) {
  const payload = await requestPrivateDesignService<unknown>(
    token,
    `/api/design-requests/${designRequestId}/stripe/payment-intent`,
    input,
    options
  );
  if (!isRecord(payload) || typeof payload.clientSecret !== "string" || !isPaymentSession(payload)) {
    throw new DesignServiceClientError("El pago del diseño previo devolvió una respuesta no válida.", "contract");
  }
  return payload as DesignServiceStripePaymentResponse;
}

export async function createDesignServicePayPalOrder(
  token: string,
  designRequestId: number,
  input: { idempotency_key: string; customer_data: DesignServiceCustomerData },
  options: RequestOptions = {}
) {
  const payload = await requestPrivateDesignService<unknown>(
    token,
    `/api/design-requests/${designRequestId}/paypal/create-order`,
    input,
    options
  );
  if (!isPaymentSession(payload)) {
    throw new DesignServiceClientError("El pago del diseño previo devolvió una respuesta no válida.", "contract");
  }
  return payload;
}

export async function getDesignServiceConfirmation(
  token: string,
  designRequestId: number,
  options: RequestOptions = {}
) {
  const payload = await requestPrivateDesignService<unknown>(
    token,
    `/api/design-requests/${designRequestId}/confirmation`,
    undefined,
    options
  );
  if (
    !isRecord(payload) ||
    typeof payload.reference !== "string" ||
    typeof payload.total_amount !== "string" ||
    !Array.isArray(payload.items)
  ) {
    throw new DesignServiceClientError("La confirmación del diseño previo no es válida.", "contract");
  }
  return payload as DesignServiceConfirmation;
}

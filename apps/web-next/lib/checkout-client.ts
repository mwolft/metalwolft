const CLIENT_LOCAL_API_URL = "http://127.0.0.1:3001";

export type CheckoutQuoteLine = {
  product_id: number;
  producto_id: number;
  product_name: string;
  quantity: number;
  alto: number;
  ancho: number;
  anclaje: string | null;
  color: string | null;
  unit_price: number;
  line_total: number;
  shipping_type: "normal" | "A" | "B" | string;
  shipping_cost: number;
};

export type CheckoutQuote = {
  lines: CheckoutQuoteLine[];
  subtotal: number;
  shipping_cost: number;
  discount_code: string | null;
  discount_code_valid: boolean;
  discount_percent: number;
  discount_amount: number;
  total_amount: number;
  comparison?: {
    has_difference?: boolean;
  };
};

export type CreateStripePaymentIntentInput = {
  payment_method_id: string;
  payment_intent_id?: string | null;
  idempotency_key: string;
  email: string;
  customer_data: Record<string, string>;
};

export type StripePaymentIntentSummary = {
  id: string;
  status: string;
  client_secret?: string | null;
};

export type CreateStripePaymentIntentResponse = {
  clientSecret: string;
  paymentIntent: StripePaymentIntentSummary;
  amount_source: string;
  amount_used_cents: number;
  checkout_summary: CheckoutQuote;
  amount_comparison?: {
    has_difference?: boolean;
  };
  checkout_session_id: number;
  checkout_session_status: string;
  payment_provider: string;
  provider_status: string | null;
  public_checkout_token: string | null;
};

export type CreatePayPalOrderInput = {
  checkout_token?: string | null;
  customer_data: Record<string, string>;
};

export type CreatePayPalOrderResponse = {
  checkout_session_id: number;
  checkout_session_status: string;
  payment_provider: string;
  provider_order_id: string | null;
  provider_capture_id: string | null;
  provider_status: string | null;
  public_checkout_token: string | null;
  checkout_summary: CheckoutQuote;
  approve_url?: string | null;
  provider?: string;
};

export type CapturePayPalOrderInput = {
  checkout_token?: string | null;
  provider_order_id: string;
  customer_data: Record<string, string>;
};

export type CapturePayPalOrderResponse = CreatePayPalOrderResponse & {
  message?: string;
};

export type FinalizeStripeOrderResponse = {
  data?: {
    id?: number;
    locator?: string;
    total_amount?: number;
  };
  message?: string;
};

export type CheckoutStatusResponse = {
  state: "confirmed" | "processing" | "failed" | "not_found" | string;
  message: string;
  public_checkout_token: string | null;
  payment_intent_id: string | null;
  checkout_session_id?: number | null;
  checkout_session_status?: string | null;
  payment_provider?: string | null;
  provider_status?: string | null;
  order_id?: number | null;
  order?: {
    id?: number;
    locator?: string;
    total_amount?: number;
  } | null;
  email?: string | null;
  total_amount?: number | null;
  shipping_cost?: number | null;
  discount_code?: string | null;
  discount_percent?: number | null;
};

export class CheckoutClientError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "CheckoutClientError";
    this.status = status;
  }
}

function checkoutApiUrl(path: string) {
  const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (configuredApiUrl) {
    return `${configuredApiUrl.replace(/\/$/, "")}${path}`;
  }

  if (process.env.NODE_ENV !== "production") {
    return `${CLIENT_LOCAL_API_URL}${path}`;
  }

  throw new CheckoutClientError("La API del checkout no esta configurada.", 0);
}

function hasMessage(payload: unknown): payload is { message: string } {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "message" in payload &&
    typeof payload.message === "string"
  );
}

function getPayloadMessage(payload: unknown, fallback: string) {
  if (hasMessage(payload)) {
    return payload.message;
  }

  if (
    typeof payload === "object" &&
    payload !== null &&
    "error" in payload &&
    typeof payload.error === "string"
  ) {
    return payload.error;
  }

  return fallback;
}

function isCheckoutQuote(payload: unknown): payload is CheckoutQuote {
  if (typeof payload !== "object" || payload === null) {
    return false;
  }

  const quote = payload as Partial<CheckoutQuote>;
  return (
    Array.isArray(quote.lines) &&
    typeof quote.subtotal === "number" &&
    typeof quote.shipping_cost === "number" &&
    typeof quote.discount_amount === "number" &&
    typeof quote.total_amount === "number"
  );
}

export function isCheckoutSessionError(error: unknown) {
  return error instanceof CheckoutClientError && (error.status === 401 || error.status === 422);
}

export async function getCheckoutQuote(token: string) {
  const response = await fetch(checkoutApiUrl("/api/checkout/quote"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({})
  }).catch(() => {
    throw new CheckoutClientError("No se pudo conectar con la API.", 0);
  });

  const payload = (await response.json().catch(() => null)) as unknown;

  if (!response.ok) {
    const message = hasMessage(payload) ? payload.message : "No se pudo calcular el checkout.";
    throw new CheckoutClientError(message, response.status);
  }

  if (!isCheckoutQuote(payload)) {
    throw new CheckoutClientError("La respuesta del checkout no es valida.", 0);
  }

  return payload;
}

async function requestCheckout<T>(token: string, path: string, init: RequestInit = {}) {
  const response = await fetch(checkoutApiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init.headers || {})
    }
  }).catch(() => {
    throw new CheckoutClientError("No se pudo conectar con la API.", 0);
  });

  const payload = (await response.json().catch(() => null)) as unknown;

  if (!response.ok) {
    throw new CheckoutClientError(
      getPayloadMessage(payload, "No se pudo completar la operación de checkout."),
      response.status
    );
  }

  return payload as T;
}

export function createStripePaymentIntent(
  token: string,
  input: CreateStripePaymentIntentInput
) {
  return requestCheckout<CreateStripePaymentIntentResponse>(token, "/api/create-payment-intent", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function finalizeStripeOrder(token: string, paymentIntentId: string) {
  return requestCheckout<FinalizeStripeOrderResponse>(token, "/api/orders", {
    method: "POST",
    body: JSON.stringify({
      payment_intent_id: paymentIntentId
    })
  });
}

export function createPayPalOrder(token: string, input: CreatePayPalOrderInput) {
  return requestCheckout<CreatePayPalOrderResponse>(token, "/api/paypal/create-order", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function capturePayPalOrder(token: string, input: CapturePayPalOrderInput) {
  return requestCheckout<CapturePayPalOrderResponse>(token, "/api/paypal/capture-order", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function getCheckoutStatus(
  token: string,
  identifier: { checkoutToken?: string | null; paymentIntentId?: string | null }
) {
  const query = new URLSearchParams();

  if (identifier.checkoutToken) {
    query.set("checkout_token", identifier.checkoutToken);
  } else if (identifier.paymentIntentId) {
    query.set("payment_intent_id", identifier.paymentIntentId);
  }

  return requestCheckout<CheckoutStatusResponse>(token, `/api/checkout/status?${query.toString()}`, {
    method: "GET"
  });
}

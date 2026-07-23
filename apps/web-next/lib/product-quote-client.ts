const CLIENT_LOCAL_API_URL = "http://127.0.0.1:3001";

export type ProductQuoteRequest = {
  productId: number;
  alto: number;
  ancho: number;
  anclaje: string;
  color: string;
  quantity?: number;
};

export type ProductQuoteResponse = {
  product_id: number;
  quantity: number;
  alto: number;
  ancho: number;
  anclaje: string;
  color: string;
  currency: string;
  base_unit_price: number;
  anchorage_supplement: number;
  unit_price: number;
  subtotal: number;
};

type ProductQuoteErrorKind = "configuration" | "network" | "http" | "contract";

export class ProductQuoteClientError extends Error {
  kind: ProductQuoteErrorKind;
  status: number;

  constructor(message: string, kind: ProductQuoteErrorKind, status = 0) {
    super(message);
    this.name = "ProductQuoteClientError";
    this.kind = kind;
    this.status = status;
  }
}

type RequestProductQuoteOptions = {
  signal?: AbortSignal;
  apiBaseUrl?: string;
  fetcher?: typeof fetch;
};

function quoteApiBaseUrl(override?: string) {
  const configuredApiUrl = override ?? process.env.NEXT_PUBLIC_API_URL?.trim();

  if (configuredApiUrl) {
    return configuredApiUrl.replace(/\/$/, "");
  }

  if (process.env.NODE_ENV !== "production") {
    return CLIENT_LOCAL_API_URL;
  }

  throw new ProductQuoteClientError(
    "La API de presupuestos no está configurada.",
    "configuration"
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isProductQuoteResponse(
  value: unknown,
  expectedProductId: number
): value is ProductQuoteResponse {
  return (
    isRecord(value) &&
    value.product_id === expectedProductId &&
    isFiniteNumber(value.quantity) &&
    Number.isInteger(value.quantity) &&
    isFiniteNumber(value.alto) &&
    isFiniteNumber(value.ancho) &&
    typeof value.anclaje === "string" &&
    typeof value.color === "string" &&
    typeof value.currency === "string" &&
    isFiniteNumber(value.base_unit_price) &&
    isFiniteNumber(value.anchorage_supplement) &&
    isFiniteNumber(value.unit_price) &&
    isFiniteNumber(value.subtotal)
  );
}

function responseMessage(payload: unknown, fallback: string) {
  return isRecord(payload) && typeof payload.message === "string" ? payload.message : fallback;
}

function isAbortError(error: unknown) {
  return isRecord(error) && error.name === "AbortError";
}

export function isTemporaryQuoteNetworkError(error: unknown) {
  return error instanceof ProductQuoteClientError && error.kind === "network";
}

export async function requestProductQuote(
  request: ProductQuoteRequest,
  options: RequestProductQuoteOptions = {}
) {
  const url = `${quoteApiBaseUrl(options.apiBaseUrl)}/api/products/${request.productId}/quote`;
  const fetcher = options.fetcher ?? fetch;
  let response: Response;

  try {
    response = await fetcher(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        alto: request.alto,
        ancho: request.ancho,
        anclaje: request.anclaje,
        color: request.color,
        quantity: request.quantity ?? 1
      }),
      signal: options.signal
    });
  } catch (error) {
    if (isAbortError(error)) {
      throw error;
    }

    throw new ProductQuoteClientError(
      "No se pudo conectar con el servicio de presupuestos.",
      "network"
    );
  }

  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    const isValidationError = response.status === 400 || response.status === 422;
    const fallbackMessage =
      response.status >= 500
        ? "El servicio de presupuestos no está disponible temporalmente."
        : "No se pudo calcular el presupuesto.";
    throw new ProductQuoteClientError(
      isValidationError ? responseMessage(payload, fallbackMessage) : fallbackMessage,
      "http",
      response.status
    );
  }

  if (!isProductQuoteResponse(payload, request.productId)) {
    throw new ProductQuoteClientError(
      "El servicio de presupuestos devolvió una respuesta no válida.",
      "contract",
      response.status
    );
  }

  return payload;
}

const CLIENT_LOCAL_API_URL = "http://127.0.0.1:3001";

export type ProductConfigurationDimension = {
  min_cm: number;
  max_cm: number;
};

export type ProductConfigurationResponse = {
  schema_version: number;
  product_id: number;
  dimensions: {
    alto: ProductConfigurationDimension;
    ancho: ProductConfigurationDimension;
    max_sum_cm: number;
  };
  anchorages: Array<{
    value: string;
    name: string;
    label: string;
    description: string;
    supplement: number;
    enabled: boolean;
  }>;
  colors: Array<{
    value: string;
    name: string;
    label: string;
    finish: string;
    finish_label: string;
    enabled: boolean;
  }>;
  defaults: {
    anchorage: string;
    color: string;
  };
};

type ProductConfigurationErrorKind = "configuration" | "network" | "http" | "contract";

export class ProductConfigurationClientError extends Error {
  kind: ProductConfigurationErrorKind;
  status: number;

  constructor(message: string, kind: ProductConfigurationErrorKind, status = 0) {
    super(message);
    this.name = "ProductConfigurationClientError";
    this.kind = kind;
    this.status = status;
  }
}

type RequestProductConfigurationOptions = {
  signal?: AbortSignal;
  apiBaseUrl?: string;
  fetcher?: typeof fetch;
};

function configurationApiBaseUrl(override?: string) {
  const configuredApiUrl = override ?? process.env.NEXT_PUBLIC_API_URL?.trim();

  if (configuredApiUrl) {
    return configuredApiUrl.replace(/\/$/, "");
  }

  if (process.env.NODE_ENV !== "production") {
    return CLIENT_LOCAL_API_URL;
  }

  throw new ProductConfigurationClientError(
    "La API de configuración no está configurada.",
    "configuration"
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isDimension(value: unknown): value is ProductConfigurationDimension {
  return (
    isRecord(value) &&
    isFiniteNumber(value.min_cm) &&
    isFiniteNumber(value.max_cm) &&
    value.min_cm > 0 &&
    value.max_cm >= value.min_cm
  );
}

function isProductConfigurationResponse(
  value: unknown,
  expectedProductId: number
): value is ProductConfigurationResponse {
  if (
    !isRecord(value) ||
    value.schema_version !== 1 ||
    value.product_id !== expectedProductId ||
    !isRecord(value.dimensions) ||
    !isDimension(value.dimensions.alto) ||
    !isDimension(value.dimensions.ancho) ||
    !isFiniteNumber(value.dimensions.max_sum_cm) ||
    !Array.isArray(value.anchorages) ||
    !Array.isArray(value.colors) ||
    !isRecord(value.defaults) ||
    typeof value.defaults.anchorage !== "string" ||
    typeof value.defaults.color !== "string"
  ) {
    return false;
  }

  const anchoragesValid = value.anchorages.every(
    (option) =>
      isRecord(option) &&
      typeof option.value === "string" &&
      typeof option.name === "string" &&
      typeof option.label === "string" &&
      typeof option.description === "string" &&
      isFiniteNumber(option.supplement) &&
      typeof option.enabled === "boolean"
  );
  const colorsValid = value.colors.every(
    (option) =>
      isRecord(option) &&
      typeof option.value === "string" &&
      typeof option.name === "string" &&
      typeof option.label === "string" &&
      typeof option.finish === "string" &&
      typeof option.finish_label === "string" &&
      typeof option.enabled === "boolean"
  );
  if (!anchoragesValid || !colorsValid) {
    return false;
  }

  const enabledAnchorages = value.anchorages.filter((option) => option.enabled);
  const enabledColors = value.colors.filter((option) => option.enabled);
  const defaults = value.defaults as ProductConfigurationResponse["defaults"];

  return (
    enabledAnchorages.some((option) => option.value === defaults.anchorage) &&
    enabledColors.some((option) => option.value === defaults.color)
  );
}

function responseMessage(payload: unknown, fallback: string) {
  return isRecord(payload) && typeof payload.message === "string" ? payload.message : fallback;
}

function isAbortError(error: unknown) {
  return isRecord(error) && error.name === "AbortError";
}

export function isTemporaryConfigurationNetworkError(error: unknown) {
  return error instanceof ProductConfigurationClientError && error.kind === "network";
}

export async function requestProductConfiguration(
  productId: number,
  options: RequestProductConfigurationOptions = {}
) {
  const url = `${configurationApiBaseUrl(options.apiBaseUrl)}/api/products/${productId}/configuration`;
  const fetcher = options.fetcher ?? fetch;
  let response: Response;

  try {
    response = await fetcher(url, { signal: options.signal });
  } catch (error) {
    if (isAbortError(error)) {
      throw error;
    }

    throw new ProductConfigurationClientError(
      "No se pudo conectar con el servicio de configuración.",
      "network"
    );
  }

  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    const isValidationError = response.status === 400 || response.status === 422;
    const fallbackMessage =
      response.status >= 500
        ? "El servicio de configuración no está disponible temporalmente."
        : "No se pudo cargar la configuración del producto.";
    throw new ProductConfigurationClientError(
      isValidationError ? responseMessage(payload, fallbackMessage) : fallbackMessage,
      "http",
      response.status
    );
  }

  if (!isProductConfigurationResponse(payload, productId)) {
    throw new ProductConfigurationClientError(
      "El servicio de configuración devolvió una respuesta no válida.",
      "contract",
      response.status
    );
  }

  return payload;
}

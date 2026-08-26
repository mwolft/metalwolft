import { getApiBaseUrl } from "@/lib/api";
import { formatCivilDateEs } from "@/lib/delivery-estimate";

export type CustomerOrderStatus = {
  code: string;
  label: string;
};

export type CustomerOrderType = "physical" | "design_service";

type CustomerOrderCommon = {
  id: number;
  reference: string | null;
  created_at: string | null;
  total: string;
  currency: string;
  status: CustomerOrderStatus;
  estimated_delivery_at: string | null;
};

export type CustomerOrderDesignService = {
  reference: string;
  status: CustomerOrderStatus;
  lead_time_hours: number;
};

export type CustomerPhysicalOrderSummary = CustomerOrderCommon & {
  order_type: "physical";
  design_service: null;
  design_count: null;
};

export type CustomerDesignServiceOrderSummary = CustomerOrderCommon & {
  order_type: "design_service";
  estimated_delivery_at: null;
  design_service: CustomerOrderDesignService;
  design_count: number;
};

export type CustomerOrderSummary =
  | CustomerPhysicalOrderSummary
  | CustomerDesignServiceOrderSummary;

export type CustomerOrdersResponse = {
  orders: CustomerOrderSummary[];
};

export type CustomerOrderInvoice = {
  available: boolean;
  number: string | null;
  issued_at: string | null;
};

export type CustomerOrderShippingAddress = {
  recipient: string | null;
  address: string | null;
  postal_code: string | null;
  city: string | null;
};

export type CustomerPhysicalOrderLineConfiguration = {
  alto: string | null;
  ancho: string | null;
  color: string | null;
  anclaje: string | null;
  screw_option: string | null;
  screw_length_mm: number | null;
  screw_supplement: string | null;
};

export type CustomerDesignServiceLineConfiguration = {
  alto: string | null;
  ancho: string | null;
};

export type CustomerPhysicalOrderLine = {
  id: number;
  line_type: "physical";
  product_name: string | null;
  quantity: number;
  configuration: CustomerPhysicalOrderLineConfiguration;
};

export type CustomerDesignServiceOrderLine = {
  id: number;
  line_type: "design_service";
  product_name: string | null;
  quantity: number;
  configuration: CustomerDesignServiceLineConfiguration;
};

export type CustomerOrderLine = CustomerPhysicalOrderLine | CustomerDesignServiceOrderLine;
export type CustomerOrderLineConfiguration = CustomerPhysicalOrderLineConfiguration;

export type CustomerPhysicalOrderDetail = CustomerPhysicalOrderSummary & {
  shipping_address: CustomerOrderShippingAddress;
  lines: CustomerPhysicalOrderLine[];
  invoice: CustomerOrderInvoice;
};

export type CustomerDesignServiceOrderDetail = CustomerDesignServiceOrderSummary & {
  shipping_address: null;
  lines: CustomerDesignServiceOrderLine[];
  invoice: CustomerOrderInvoice;
};

export type CustomerOrderDetail = CustomerPhysicalOrderDetail | CustomerDesignServiceOrderDetail;

export type CustomerOrderDetailResponse = {
  order: CustomerOrderDetail;
};

export type CustomerOrderInvoiceDownload = {
  blob: Blob;
  filename: string;
};

export class CustomerOrdersClientError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "CustomerOrdersClientError";
    this.status = status;
  }
}

function customerOrdersApiUrl(path: string) {
  return `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isNullableString(value: unknown): value is string | null {
  return typeof value === "string" || value === null;
}

function isNullableCivilDate(value: unknown): value is string | null {
  return value === null || (typeof value === "string" && formatCivilDateEs(value) !== null);
}

function isCustomerOrderStatus(value: unknown): value is CustomerOrderStatus {
  return (
    isRecord(value) &&
    typeof value.code === "string" &&
    typeof value.label === "string"
  );
}

function isCustomerOrderCommon(value: unknown): value is CustomerOrderCommon {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    Number.isFinite(value.id) &&
    isNullableString(value.reference) &&
    isNullableString(value.created_at) &&
    typeof value.total === "string" &&
    typeof value.currency === "string" &&
    isCustomerOrderStatus(value.status) &&
    isNullableCivilDate(value.estimated_delivery_at)
  );
}

function isCustomerOrderDesignService(value: unknown): value is CustomerOrderDesignService {
  return (
    isRecord(value) &&
    typeof value.reference === "string" &&
    isCustomerOrderStatus(value.status) &&
    typeof value.lead_time_hours === "number" &&
    Number.isFinite(value.lead_time_hours)
  );
}

function isCustomerOrderSummary(value: unknown): value is CustomerOrderSummary {
  if (!isCustomerOrderCommon(value)) {
    return false;
  }
  const fields = value as CustomerOrderCommon & Record<string, unknown>;

  if (fields.order_type === "physical") {
    return fields.design_service === null && fields.design_count === null;
  }

  return (
    fields.order_type === "design_service" &&
    fields.estimated_delivery_at === null &&
    isCustomerOrderDesignService(fields.design_service) &&
    typeof fields.design_count === "number" &&
    Number.isInteger(fields.design_count) &&
    fields.design_count > 0
  );
}

function isCustomerOrderInvoice(value: unknown): value is CustomerOrderInvoice {
  return (
    isRecord(value) &&
    typeof value.available === "boolean" &&
    isNullableString(value.number) &&
    isNullableString(value.issued_at)
  );
}

function isCustomerOrderShippingAddress(value: unknown): value is CustomerOrderShippingAddress {
  return (
    isRecord(value) &&
    isNullableString(value.recipient) &&
    isNullableString(value.address) &&
    isNullableString(value.postal_code) &&
    isNullableString(value.city)
  );
}

function isCustomerPhysicalOrderLineConfiguration(
  value: unknown
): value is CustomerPhysicalOrderLineConfiguration {
  return (
    isRecord(value) &&
    isNullableString(value.alto) &&
    isNullableString(value.ancho) &&
    isNullableString(value.color) &&
    isNullableString(value.anclaje) &&
    isNullableString(value.screw_option) &&
    (value.screw_length_mm === null ||
      (typeof value.screw_length_mm === "number" && Number.isFinite(value.screw_length_mm))) &&
    isNullableString(value.screw_supplement)
  );
}

function isCustomerDesignServiceLineConfiguration(
  value: unknown
): value is CustomerDesignServiceLineConfiguration {
  return isRecord(value) && isNullableString(value.alto) && isNullableString(value.ancho);
}

function isCustomerPhysicalOrderLine(value: unknown): value is CustomerPhysicalOrderLine {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    Number.isFinite(value.id) &&
    isNullableString(value.product_name) &&
    typeof value.quantity === "number" &&
    Number.isFinite(value.quantity) &&
    value.line_type === "physical" &&
    isCustomerPhysicalOrderLineConfiguration(value.configuration)
  );
}

function isCustomerDesignServiceOrderLine(value: unknown): value is CustomerDesignServiceOrderLine {
  return (
    isRecord(value) &&
    typeof value.id === "number" &&
    Number.isFinite(value.id) &&
    value.line_type === "design_service" &&
    isNullableString(value.product_name) &&
    typeof value.quantity === "number" &&
    Number.isFinite(value.quantity) &&
    isCustomerDesignServiceLineConfiguration(value.configuration)
  );
}

function isCustomerOrderDetail(value: unknown): value is CustomerOrderDetail {
  if (!isRecord(value) || !isCustomerOrderSummary(value)) {
    return false;
  }
  const fields = value as CustomerOrderSummary & Record<string, unknown>;
  if (!Array.isArray(fields.lines) || !isCustomerOrderInvoice(fields.invoice)) {
    return false;
  }
  const lines = fields.lines;

  if (fields.order_type === "physical") {
    return (
      isCustomerOrderShippingAddress(fields.shipping_address) &&
      lines.every(isCustomerPhysicalOrderLine)
    );
  }

  return fields.shipping_address === null && lines.every(isCustomerDesignServiceOrderLine);
}

function parseCustomerOrdersResponse(payload: unknown): CustomerOrdersResponse {
  if (!isRecord(payload) || !Array.isArray(payload.orders)) {
    throw new CustomerOrdersClientError(
      "La respuesta de pedidos no tiene el formato esperado.",
      0
    );
  }

  if (!payload.orders.every(isCustomerOrderSummary)) {
    throw new CustomerOrdersClientError(
      "La respuesta de pedidos no tiene el formato esperado.",
      0
    );
  }

  return {
    orders: payload.orders
  };
}

function parseCustomerOrderDetailResponse(payload: unknown): CustomerOrderDetailResponse {
  if (!isRecord(payload) || !isCustomerOrderDetail(payload.order)) {
    throw new CustomerOrdersClientError(
      "La respuesta del pedido no tiene el formato esperado.",
      0
    );
  }

  return {
    order: payload.order
  };
}

export function isCustomerOrdersSessionError(error: unknown) {
  return (
    error instanceof CustomerOrdersClientError &&
    (error.status === 401 || error.status === 422)
  );
}

export function isCustomerOrdersNotFoundError(error: unknown) {
  return error instanceof CustomerOrdersClientError && error.status === 404;
}

async function requestCustomerOrders<T>(
  token: string,
  path: string,
  parsePayload: (payload: unknown) => T,
  notFoundMessage = "No hemos encontrado este pedido."
): Promise<T> {
  if (!token) {
    throw new CustomerOrdersClientError("Necesitas iniciar sesión para ver tus pedidos.", 401);
  }

  const response = await fetch(customerOrdersApiUrl(path), {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`
    }
  }).catch(() => {
    throw new CustomerOrdersClientError("No se pudo conectar con la API de pedidos.", 0);
  });

  const payload = (await response.json().catch(() => null)) as unknown;

  if (!response.ok) {
    throw new CustomerOrdersClientError(
      response.status === 401 || response.status === 422
        ? "Tu sesión ha caducado. Vuelve a iniciar sesión."
        : response.status === 404
          ? notFoundMessage
        : "No se pudieron cargar tus pedidos. Inténtalo de nuevo.",
      response.status
    );
  }

  return parsePayload(payload);
}

export function fetchCustomerOrders(token: string): Promise<CustomerOrdersResponse> {
  return requestCustomerOrders(
    token,
    "/api/customer/orders",
    parseCustomerOrdersResponse,
    "No se pudieron cargar tus pedidos. Inténtalo de nuevo."
  );
}

export function fetchCustomerOrderDetail(
  token: string,
  orderId: number
): Promise<CustomerOrderDetailResponse> {
  return requestCustomerOrders(
    token,
    `/api/customer/orders/${orderId}`,
    parseCustomerOrderDetailResponse
  );
}

function filenameFromContentDisposition(header: string | null) {
  if (!header) {
    return null;
  }

  const encodedFilename = /filename\*=UTF-8''([^;]+)/i.exec(header)?.[1];
  if (encodedFilename) {
    try {
      return decodeURIComponent(encodedFilename);
    } catch {
      return null;
    }
  }

  const quotedFilename = /filename="([^"]+)"/i.exec(header)?.[1];
  if (quotedFilename) {
    return quotedFilename;
  }

  return /filename=([^;]+)/i.exec(header)?.[1]?.trim() || null;
}

function safeDownloadFilename(value: string | null, fallback: string) {
  if (!value) {
    return fallback;
  }

  const normalized = value.trim().replace(/\\/g, "/");
  if (
    !normalized ||
    normalized.includes("/") ||
    normalized === "." ||
    normalized === ".." ||
    !normalized.toLowerCase().endsWith(".pdf")
  ) {
    return fallback;
  }

  return normalized.replace(/[^A-Za-z0-9._-]+/g, "_") || fallback;
}

export async function fetchCustomerOrderInvoicePdf(
  token: string,
  orderId: number
): Promise<CustomerOrderInvoiceDownload> {
  if (!token) {
    throw new CustomerOrdersClientError("Necesitas iniciar sesión para descargar la factura.", 401);
  }

  const response = await fetch(customerOrdersApiUrl(`/api/customer/orders/${orderId}/invoice`), {
    headers: {
      Accept: "application/pdf",
      Authorization: `Bearer ${token}`
    }
  }).catch(() => {
    throw new CustomerOrdersClientError("No se pudo conectar con la API de pedidos.", 0);
  });

  if (!response.ok) {
    throw new CustomerOrdersClientError(
      response.status === 401 || response.status === 422
        ? "Tu sesión ha caducado. Vuelve a iniciar sesión."
        : response.status === 404
          ? "La factura ya no está disponible."
          : "No se pudo descargar la factura. Inténtalo de nuevo.",
      response.status
    );
  }

  const blob = await response.blob();
  return {
    blob,
    filename: safeDownloadFilename(
      filenameFromContentDisposition(response.headers.get("Content-Disposition")),
      `factura_pedido_${orderId}.pdf`
    )
  };
}

import { getApiBaseUrl } from "@/lib/api";
import type { AuthUser } from "@/lib/auth-client";
import type {
  CustomerProfileEditableField,
  CustomerProfileUpdate
} from "@/lib/customer-profile";

export type CustomerProfile = AuthUser & {
  id: number;
  email: string;
};

export class CustomerProfileClientError extends Error {
  status: number;
  field?: CustomerProfileEditableField;

  constructor(message: string, status: number, field?: CustomerProfileEditableField) {
    super(message);
    this.name = "CustomerProfileClientError";
    this.status = status;
    this.field = field;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isNullableString(value: unknown) {
  return typeof value === "string" || value === null;
}

function parseCustomerProfile(payload: unknown): CustomerProfile {
  if (
    !isRecord(payload) ||
    typeof payload.id !== "number" ||
    typeof payload.email !== "string"
  ) {
    throw new CustomerProfileClientError(
      "La respuesta del perfil no tiene el formato esperado.",
      0
    );
  }

  const optionalFields = [
    "firstname",
    "lastname",
    "phone",
    "shipping_address",
    "shipping_city",
    "shipping_postal_code",
    "billing_address",
    "billing_city",
    "billing_postal_code",
    "CIF"
  ] as const;

  if (optionalFields.some((field) => !isNullableString(payload[field]))) {
    throw new CustomerProfileClientError(
      "La respuesta del perfil no tiene el formato esperado.",
      0
    );
  }

  return payload as CustomerProfile;
}

async function requestCustomerProfile(
  token: string,
  init: RequestInit = {}
): Promise<CustomerProfile> {
  if (!token) {
    throw new CustomerProfileClientError(
      "Necesitas iniciar sesión para consultar tu perfil.",
      401
    );
  }

  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/api/me`, {
      ...init,
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${token}`,
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...(init.headers || {})
      }
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new CustomerProfileClientError("No se pudo conectar con la API del perfil.", 0);
  }

  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    const message =
      isRecord(payload) && typeof payload.message === "string"
        ? payload.message
        : "No se pudieron guardar los datos del perfil.";
    const field =
      isRecord(payload) && typeof payload.field === "string"
        ? (payload.field as CustomerProfileEditableField)
        : undefined;
    throw new CustomerProfileClientError(message, response.status, field);
  }

  return parseCustomerProfile(payload);
}

export function fetchCustomerProfile(token: string, signal?: AbortSignal) {
  return requestCustomerProfile(token, { signal });
}

export function updateCustomerProfile(token: string, update: CustomerProfileUpdate) {
  return requestCustomerProfile(token, {
    method: "PATCH",
    body: JSON.stringify(update)
  });
}

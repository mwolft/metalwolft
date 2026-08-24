import { CartClientError } from "@/lib/cart-client";

const CLIENT_LOCAL_API_URL = "http://127.0.0.1:3001";

function budgetApiUrl(path: string) {
  const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (configuredApiUrl) {
    return `${configuredApiUrl.replace(/\/$/, "")}${path}`;
  }

  if (process.env.NODE_ENV !== "production") {
    return `${CLIENT_LOCAL_API_URL}${path}`;
  }

  throw new CartClientError("La API del presupuesto no está configurada.", 0);
}

function responseMessage(payload: unknown, fallback: string) {
  if (
    typeof payload === "object" &&
    payload !== null &&
    "message" in payload &&
    typeof payload.message === "string"
  ) {
    return payload.message;
  }

  return fallback;
}

function filenameFromDisposition(value: string | null) {
  const match = value?.match(/filename="?([^";]+)"?/i);
  return match?.[1] || "presupuesto-metalwolft.pdf";
}

export async function downloadCartBudget(token: string, discountCode: string | null) {
  const response = await fetch(budgetApiUrl("/api/cart/budget/pdf"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(discountCode ? { discount_code: discountCode } : {})
  }).catch(() => {
    throw new CartClientError("No se pudo conectar con la API.", 0);
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new CartClientError(
      responseMessage(payload, "No se pudo generar el presupuesto."),
      response.status
    );
  }

  const blob = await response.blob();
  if (blob.type !== "application/pdf") {
    throw new CartClientError("El servidor no devolvió un presupuesto PDF válido.", 0);
  }

  return {
    blob,
    filename: filenameFromDisposition(response.headers.get("content-disposition"))
  };
}

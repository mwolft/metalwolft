export type CartItem = {
  id: number;
  usuario_id: number;
  producto_id: number;
  nombre: string;
  descripcion: string;
  imagen: string | null;
  slug: string | null;
  category_slug: string | null;
  alto: number | null;
  ancho: number | null;
  anclaje: string | null;
  color: string | null;
  precio_total: number;
  quantity: number;
  added_at: string;
};

export type AddCartItemInput = {
  product_id: number;
  alto: number;
  ancho: number;
  anclaje: string;
  color: string;
  quantity: number;
};

const CLIENT_LOCAL_API_URL = "http://127.0.0.1:3001";

export class CartClientError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "CartClientError";
    this.status = status;
  }
}

type DeleteCartResponse = {
  message?: string;
  updated_cart?: CartItem[];
};

function cartApiUrl(path: string) {
  const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (configuredApiUrl) {
    return `${configuredApiUrl.replace(/\/$/, "")}${path}`;
  }

  if (process.env.NODE_ENV !== "production") {
    return `${CLIENT_LOCAL_API_URL}${path}`;
  }

  throw new CartClientError("La API del carrito no está configurada.", 0);
}

function cartLineBody(item: CartItem, quantity?: number) {
  return JSON.stringify({
    alto: item.alto,
    ancho: item.ancho,
    anclaje: item.anclaje,
    color: item.color,
    ...(quantity !== undefined ? { quantity } : {})
  });
}

function hasMessage(payload: unknown): payload is { message: string } {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "message" in payload &&
    typeof payload.message === "string"
  );
}

async function requestCart<T>(token: string, path: string, init: RequestInit = {}) {
  const response = await fetch(cartApiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init.headers || {})
    }
  }).catch(() => {
    throw new CartClientError("No se pudo conectar con la API.", 0);
  });

  const payload = (await response.json().catch(() => null)) as T | { message?: string } | null;

  if (!response.ok) {
    const message = hasMessage(payload) ? payload.message : "No se pudo actualizar el carrito.";
    throw new CartClientError(message, response.status);
  }

  return payload as T;
}

export function isSessionError(error: unknown) {
  return error instanceof CartClientError && (error.status === 401 || error.status === 422);
}

export function getCart(token: string) {
  return requestCart<CartItem[]>(token, "/api/cart");
}

export function addCartItem(token: string, item: AddCartItemInput) {
  return requestCart<CartItem[]>(token, "/api/cart", {
    method: "POST",
    body: JSON.stringify(item)
  });
}

export function updateCartItemQuantity(token: string, item: CartItem, quantity: number) {
  return requestCart<CartItem[]>(token, `/api/cart/${item.producto_id}`, {
    method: "PUT",
    body: cartLineBody(item, quantity)
  });
}

export async function deleteCartItem(token: string, item: CartItem) {
  const payload = await requestCart<DeleteCartResponse>(token, `/api/cart/${item.producto_id}`, {
    method: "DELETE",
    body: cartLineBody(item)
  });

  return Array.isArray(payload.updated_cart) ? payload.updated_cart : [];
}

export async function clearCart(token: string) {
  await requestCart<{ message?: string }>(token, "/api/cart/clear", {
    method: "POST"
  });

  return [];
}

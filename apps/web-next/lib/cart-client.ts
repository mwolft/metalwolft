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
  screw_option?: string | null;
  screw_length_mm?: number | null;
  screw_supplement?: number | null;
  precio_total: number;
  quantity: number;
  added_at: string;
  available_for_sale: boolean;
};

export type AddCartItemInput = {
  product_id: number;
  alto: number;
  ancho: number;
  anclaje: string;
  color: string;
  screw_option: string;
  quantity: number;
};

export function countCartLines(items: readonly CartItem[]) {
  return items.length;
}

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

export const CART_SNAPSHOT_CHANGED_EVENT = "mw_cart_snapshot_changed";

export type CartSnapshotChange = {
  items: CartItem[];
  reason: "sync" | "mutation";
};

type GetCartOptions = {
  publishSnapshot?: boolean;
};

function emitCartSnapshotChanged(change: CartSnapshotChange) {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(
    new CustomEvent<CartSnapshotChange>(CART_SNAPSHOT_CHANGED_EVENT, { detail: change })
  );
}

export function subscribeToCartSnapshotChanges(
  listener: (change: CartSnapshotChange) => void
) {
  if (typeof window === "undefined") {
    return () => {};
  }

  const handleChange = (event: Event) => {
    listener((event as CustomEvent<CartSnapshotChange>).detail);
  };

  window.addEventListener(CART_SNAPSHOT_CHANGED_EVENT, handleChange);
  return () => window.removeEventListener(CART_SNAPSHOT_CHANGED_EVENT, handleChange);
}

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
    screw_option: item.screw_option ?? "standard",
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

export async function getCart(token: string, options: GetCartOptions = {}) {
  const items = await requestCart<CartItem[]>(token, "/api/cart");
  if (options.publishSnapshot !== false) {
    emitCartSnapshotChanged({ items, reason: "sync" });
  }
  return items;
}

export async function addCartItem(token: string, item: AddCartItemInput) {
  const items = await requestCart<CartItem[]>(token, "/api/cart", {
    method: "POST",
    body: JSON.stringify(item)
  });
  emitCartSnapshotChanged({ items, reason: "mutation" });
  return items;
}

export async function updateCartItemQuantity(token: string, item: CartItem, quantity: number) {
  const items = await requestCart<CartItem[]>(token, `/api/cart/${item.producto_id}`, {
    method: "PUT",
    body: cartLineBody(item, quantity)
  });
  emitCartSnapshotChanged({ items, reason: "mutation" });
  return items;
}

export async function deleteCartItem(token: string, item: CartItem) {
  const payload = await requestCart<DeleteCartResponse>(token, `/api/cart/${item.producto_id}`, {
    method: "DELETE",
    body: cartLineBody(item)
  });

  const items = Array.isArray(payload.updated_cart) ? payload.updated_cart : [];
  emitCartSnapshotChanged({ items, reason: "mutation" });
  return items;
}

export async function clearCart(token: string) {
  await requestCart<{ message?: string }>(token, "/api/cart/clear", {
    method: "POST"
  });

  emitCartSnapshotChanged({ items: [], reason: "mutation" });
  return [];
}

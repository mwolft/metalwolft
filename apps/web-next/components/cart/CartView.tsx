"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getToken } from "@/lib/auth-client";
import {
  type CartItem,
  CartClientError,
  clearCart,
  deleteCartItem,
  getCart,
  isSessionError,
  updateCartItemQuantity
} from "@/lib/cart-client";
import {
  PRODUCT_UNAVAILABLE_MESSAGE,
  isAvailableForSale
} from "@/lib/product-lifecycle";

const colorLabels: Record<string, string> = {
  satinado_blanco: "Blanco liso",
  satinado_negro: "Negro liso",
  satinado_gris: "Gris medio liso",
  satinado_verde: "Verde carruajes liso",
  forja_negro: "Negro forja",
  forja_gris: "Gris acero forja",
  forja_marron: "Marrón castaño forja",
  forja_azul: "Azul forja",
  forja_verde: "Verde bronce forja",
  forja_dorado: "Dorado forja"
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

function formatDimension(value: number | null) {
  return typeof value === "number" ? `${value.toLocaleString("es-ES")} cm` : "-";
}

function formatColor(value: string | null) {
  if (!value) {
    return "-";
  }

  return colorLabels[value] || value.replace(/_/g, " ");
}

function cartLineKey(item: CartItem) {
  return [item.id, item.producto_id, item.alto, item.ancho, item.anclaje, item.color].join("|");
}

function productHref(item: CartItem) {
  return item.category_slug && item.slug ? `/${item.category_slug}/${item.slug}` : null;
}

export function CartView({ deliveryEstimate }: { deliveryEstimate?: ReactNode }) {
  const router = useRouter();
  const [items, setItems] = useState<CartItem[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "empty" | "unauthenticated" | "error">(
    "loading"
  );
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(
    null
  );
  const isBusy = pendingAction !== null;
  const hasUnavailableItems = items.some((item) => !isAvailableForSale(item));

  const subtotal = useMemo(
    () =>
      items.reduce(
        (total, item) => total + Number(item.precio_total || 0) * Number(item.quantity || 1),
        0
      ),
    [items]
  );

  function redirectToLogin(message = "Tu sesión ha caducado. Vuelve a iniciar sesión.") {
    clearSession();
    setItems([]);
    setStatus("unauthenticated");
    setFeedback({ type: "error", message });
    window.setTimeout(() => {
      router.replace("/login?next=/cart");
    }, 900);
  }

  function handleCartError(error: unknown) {
    if (isSessionError(error)) {
      redirectToLogin();
      return;
    }

    setFeedback({
      type: "error",
      message:
        error instanceof CartClientError && error.status === 0
          ? "No se pudo conectar con la API. Inténtalo de nuevo."
          : "No se pudo actualizar el carrito. Inténtalo de nuevo."
    });
    setStatus((current) => (current === "loading" ? "error" : current));
  }

  useEffect(() => {
    let isActive = true;
    const token = getToken();

    if (!token) {
      setStatus("unauthenticated");
      return;
    }

    getCart(token)
      .then((cartItems) => {
        if (!isActive) {
          return;
        }

        setItems(cartItems);
        setStatus(cartItems.length > 0 ? "ready" : "empty");
      })
      .catch((error) => {
        if (isActive) {
          handleCartError(error);
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  async function changeQuantity(item: CartItem, quantity: number) {
    if (isBusy) {
      return;
    }

    if (quantity < 1) {
      await removeItem(item);
      return;
    }

    if (!isAvailableForSale(item)) {
      setFeedback({ type: "error", message: PRODUCT_UNAVAILABLE_MESSAGE });
      return;
    }

    const token = getToken();
    if (!token) {
      redirectToLogin("Inicia sesión para modificar el carrito.");
      return;
    }

    const actionKey = cartLineKey(item);
    setPendingAction(actionKey);
    setFeedback(null);

    try {
      const updatedCart = await updateCartItemQuantity(token, item, quantity);
      setItems(updatedCart);
      setStatus(updatedCart.length > 0 ? "ready" : "empty");
      setFeedback({ type: "success", message: "Cantidad actualizada." });
    } catch (error) {
      handleCartError(error);
    } finally {
      setPendingAction(null);
    }
  }

  async function removeItem(item: CartItem) {
    if (isBusy) {
      return;
    }

    const token = getToken();
    if (!token) {
      redirectToLogin("Inicia sesión para modificar el carrito.");
      return;
    }

    const actionKey = `remove:${cartLineKey(item)}`;
    setPendingAction(actionKey);
    setFeedback(null);

    try {
      const updatedCart = await deleteCartItem(token, item);
      setItems(updatedCart);
      setStatus(updatedCart.length > 0 ? "ready" : "empty");
      setFeedback({ type: "success", message: "Producto eliminado del carrito." });
    } catch (error) {
      handleCartError(error);
    } finally {
      setPendingAction(null);
    }
  }

  async function handleClearCart() {
    if (isBusy || items.length === 0) {
      return;
    }

    if (!window.confirm("¿Vaciar todo el carrito?")) {
      return;
    }

    const token = getToken();
    if (!token) {
      redirectToLogin("Inicia sesión para modificar el carrito.");
      return;
    }

    setPendingAction("clear");
    setFeedback(null);

    try {
      await clearCart(token);
      setItems([]);
      setStatus("empty");
      setFeedback({ type: "success", message: "Carrito vaciado correctamente." });
    } catch (error) {
      handleCartError(error);
    } finally {
      setPendingAction(null);
    }
  }

  if (status === "loading") {
    return <CartState title="Cargando carrito" description="Estamos recuperando tus productos." />;
  }

  if (status === "unauthenticated") {
    return (
      <CartState
        title="Inicia sesión para ver tu carrito"
        description="Tu carrito está asociado a tu cuenta de MetalWolft."
      >
        <Link className="mw-button mw-button--primary" href="/login?next=/cart">
          Iniciar sesión
        </Link>
        <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
          Seguir comprando
        </Link>
      </CartState>
    );
  }

  if (status === "error") {
    return (
      <CartState
        title="No se pudo cargar el carrito"
        description="Inténtalo de nuevo en unos segundos o vuelve al catálogo."
      >
        <button className="mw-button mw-button--primary" type="button" onClick={() => window.location.reload()}>
          Reintentar
        </button>
        <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
          Ver catálogo
        </Link>
      </CartState>
    );
  }

  if (status === "empty") {
    return (
      <CartState
        title="Tu carrito está vacío"
        description="Elige un modelo de reja para ventanas y configura tus medidas."
      >
        <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
          Ver rejas para ventanas
        </Link>
      </CartState>
    );
  }

  return (
    <section className="mw-cart-layout" aria-label="Carrito de compra">
      <div className="mw-cart-list">
        <div className="mw-cart-toolbar">
          <p>{items.length === 1 ? "1 línea en el carrito" : `${items.length} líneas en el carrito`}</p>
          <button
            className="mw-cart-clear"
            disabled={isBusy}
            onClick={handleClearCart}
            type="button"
          >
            Vaciar carrito
          </button>
        </div>

        {feedback ? (
          <p
            aria-live="polite"
            className={`mw-alert ${
              feedback.type === "success" ? "mw-alert--success" : "mw-alert--error"
            }`}
          >
            {feedback.message}
          </p>
        ) : null}

        {items.map((item) => {
          const key = cartLineKey(item);
          const href = productHref(item);
          const quantity = Number(item.quantity || 1);
          const lineTotal = Number(item.precio_total || 0) * quantity;
          const availableForSale = isAvailableForSale(item);

          return (
            <article className="mw-cart-line" key={key}>
              <div className="mw-cart-line__media">
                {item.imagen ? (
                  <img src={item.imagen} alt={item.nombre} loading="lazy" />
                ) : (
                  <span aria-hidden="true">MW</span>
                )}
              </div>

              <div className="mw-cart-line__content">
                <div className="mw-cart-line__heading">
                  <div>
                    <p className="mw-note">Producto</p>
                    <h2>
                      {href ? <Link href={href}>{item.nombre}</Link> : item.nombre}
                    </h2>
                    {!availableForSale ? (
                      <p className="mw-alert" role="status">
                        {PRODUCT_UNAVAILABLE_MESSAGE}
                      </p>
                    ) : null}
                  </div>
                  <div className="mw-cart-line__prices">
                    <span>{formatCurrency(Number(item.precio_total || 0))} / unidad</span>
                    <strong>{formatCurrency(lineTotal)}</strong>
                  </div>
                </div>

                <dl className="mw-cart-config">
                  <div>
                    <dt>Alto</dt>
                    <dd>{formatDimension(item.alto)}</dd>
                  </div>
                  <div>
                    <dt>Ancho</dt>
                    <dd>{formatDimension(item.ancho)}</dd>
                  </div>
                  <div>
                    <dt>Instalación</dt>
                    <dd>{item.anclaje || "-"}</dd>
                  </div>
                  <div>
                    <dt>Color</dt>
                    <dd>{formatColor(item.color)}</dd>
                  </div>
                </dl>

                <div className="mw-cart-line__actions">
                  <div className="mw-cart-quantity" aria-label={`Cantidad de ${item.nombre}`}>
                    <button
                      aria-label={`Reducir cantidad de ${item.nombre}`}
                      disabled={isBusy || !availableForSale}
                      onClick={() => changeQuantity(item, quantity - 1)}
                      type="button"
                    >
                      -
                    </button>
                    <span aria-live="polite">{quantity}</span>
                    <button
                      aria-label={`Aumentar cantidad de ${item.nombre}`}
                      disabled={isBusy || !availableForSale}
                      onClick={() => changeQuantity(item, quantity + 1)}
                      type="button"
                    >
                      +
                    </button>
                  </div>
                  <button
                    className="mw-cart-remove"
                    disabled={isBusy}
                    onClick={() => removeItem(item)}
                    type="button"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>

      <aside className="mw-cart-summary" aria-label="Resumen del carrito">
        <p className="mw-note">Resumen</p>
        <h2>Subtotal del carrito</h2>
        <div className="mw-cart-summary__line">
          <span>Subtotal</span>
          <strong>{formatCurrency(subtotal)}</strong>
        </div>
        <p>Envío calculado en el checkout.</p>
        {deliveryEstimate}
        {hasUnavailableItems ? (
          <p className="mw-alert" role="alert">
            Elimina los productos no disponibles antes de continuar.
          </p>
        ) : null}
        <div className="mw-cart-summary__actions">
          {isBusy || hasUnavailableItems ? (
            <button className="mw-button mw-button--primary" disabled type="button">
              {hasUnavailableItems ? "Revisa el carrito" : "Preparando checkout"}
            </button>
          ) : (
            <Link className="mw-button mw-button--primary" href="/cart?step=details">
              Continuar
            </Link>
          )}
          <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
            Seguir comprando
          </Link>
        </div>
      </aside>
    </section>
  );
}

function CartState({
  title,
  description,
  children
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <section className="mw-cart-state">
      <p className="mw-eyebrow">Carrito</p>
      <h2 className="mw-title mw-title--compact">{title}</h2>
      <p className="mw-lead">{description}</p>
      {children ? <div className="mw-actions">{children}</div> : null}
    </section>
  );
}

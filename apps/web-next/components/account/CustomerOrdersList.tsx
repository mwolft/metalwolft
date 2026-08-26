"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { useAuthSession } from "@/hooks/useAuthSession";
import { clearSession, getToken } from "@/lib/auth-client";
import {
  CustomerOrdersClientError,
  fetchCustomerOrders,
  isCustomerOrdersSessionError,
  type CustomerOrderSummary
} from "@/lib/customer-orders-client";
import { formatCivilDateEs } from "@/lib/delivery-estimate";

type OrdersStatus = "loading" | "ready" | "empty" | "unauthenticated" | "error";

const LOGIN_NEXT = "/login?next=/mi-cuenta/pedidos";

function formatOrderDate(value: string | null) {
  if (!value) {
    return "Fecha no disponible";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Fecha no disponible";
  }

  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "long",
    year: "numeric"
  }).format(date);
}

function formatOrderTotal(order: CustomerOrderSummary) {
  const amount = Number(order.total);

  if (!Number.isFinite(amount)) {
    return `${order.total} ${order.currency}`;
  }

  try {
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: order.currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  } catch {
    return `${order.total} ${order.currency}`;
  }
}

function CustomerOrdersState({
  title,
  description,
  children
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <section className="mw-account-state" aria-live="polite">
      <h2>{title}</h2>
      <p>{description}</p>
      {children ? <div className="mw-actions">{children}</div> : null}
    </section>
  );
}

export function CustomerOrdersList() {
  const router = useRouter();
  const { isAuthenticated, isReady } = useAuthSession();
  const [orders, setOrders] = useState<CustomerOrderSummary[]>([]);
  const [status, setStatus] = useState<OrdersStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const redirectToLogin = useCallback(() => {
    clearSession();
    setOrders([]);
    setStatus("unauthenticated");
    router.replace(LOGIN_NEXT);
  }, [router]);

  const loadOrders = useCallback(async () => {
    const token = getToken();

    if (!token) {
      redirectToLogin();
      return;
    }

    setStatus("loading");
    setErrorMessage(null);

    try {
      const response = await fetchCustomerOrders(token);
      setOrders(response.orders);
      setStatus(response.orders.length > 0 ? "ready" : "empty");
    } catch (error) {
      if (isCustomerOrdersSessionError(error)) {
        redirectToLogin();
        return;
      }

      setStatus("error");
      setErrorMessage(
        error instanceof CustomerOrdersClientError
          ? error.message
          : "No se pudieron cargar tus pedidos. Inténtalo de nuevo."
      );
    }
  }, [redirectToLogin]);

  useEffect(() => {
    if (!isReady) {
      return;
    }

    if (!isAuthenticated) {
      redirectToLogin();
      return;
    }

    void loadOrders();
  }, [isAuthenticated, isReady, loadOrders, redirectToLogin]);

  if (status === "loading") {
    return (
      <CustomerOrdersState
        title="Cargando pedidos"
        description="Estamos recuperando tus pedidos de MetalWolft."
      />
    );
  }

  if (status === "unauthenticated") {
    return (
      <CustomerOrdersState
        title="Inicia sesión para ver tus pedidos"
        description="Tu historial de pedidos está asociado a tu cuenta."
      >
        <Link className="mw-button mw-button--primary" href={LOGIN_NEXT}>
          Iniciar sesión
        </Link>
      </CustomerOrdersState>
    );
  }

  if (status === "error") {
    return (
      <CustomerOrdersState
        title="No se pudieron cargar tus pedidos"
        description={errorMessage || "Inténtalo de nuevo en unos segundos."}
      >
        <button className="mw-button mw-button--primary" type="button" onClick={loadOrders}>
          Reintentar
        </button>
      </CustomerOrdersState>
    );
  }

  if (status === "empty") {
    return (
      <CustomerOrdersState
        title="Aún no tienes pedidos"
        description="Cuando completes una compra, aparecerá aquí para que puedas consultarla."
      >
        <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
          Ver rejas para ventanas
        </Link>
      </CustomerOrdersState>
    );
  }

  return (
    <section className="mw-customer-orders" aria-labelledby="customer-orders-title">
      <div className="mw-account-section-heading">
        <p className="mw-note">Historial</p>
        <h2 id="customer-orders-title">Mis pedidos</h2>
      </div>

      <div className="mw-customer-orders__list">
        {orders.map((order) => {
          const isDesignService = order.order_type === "design_service";
          const estimatedDeliveryDate = !isDesignService && order.estimated_delivery_at
            ? formatCivilDateEs(order.estimated_delivery_at)
            : null;

          return (
            <article className="mw-customer-order-card" key={order.id}>
              <div>
                <p className="mw-customer-order-card__reference">
                  {isDesignService ? "Diseño previo a medida" : (order.reference || `Pedido #${order.id}`)}
                </p>
                <p className="mw-customer-order-card__date">{formatOrderDate(order.created_at)}</p>
                {isDesignService ? (
                  <p className="mw-customer-order-card__service-summary">
                    {order.design_count} {order.design_count === 1 ? "diseño" : "diseños"}
                  </p>
                ) : null}
                {estimatedDeliveryDate ? (
                  <div className="mw-customer-order-estimate">
                    <p>
                      <strong>Entrega estimada:</strong>{" "}
                      <time dateTime={order.estimated_delivery_at || undefined}>
                        {estimatedDeliveryDate}
                      </time>
                    </p>
                    <p>Fecha orientativa sujeta al proceso de fabricación y transporte.</p>
                  </div>
                ) : null}
              </div>

              <div className="mw-customer-order-card__meta">
                <span>{order.status.label}</span>
                <strong>{formatOrderTotal(order)}</strong>
              </div>

              <Link
                className="mw-button mw-button--secondary"
                href={`/mi-cuenta/pedidos/${order.id}`}
              >
                Ver pedido
              </Link>
            </article>
          );
        })}
      </div>
    </section>
  );
}

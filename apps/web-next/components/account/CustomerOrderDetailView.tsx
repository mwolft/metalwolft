"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { useAuthSession } from "@/hooks/useAuthSession";
import { clearSession, getToken } from "@/lib/auth-client";
import {
  CustomerOrdersClientError,
  fetchCustomerOrderInvoicePdf,
  fetchCustomerOrderDetail,
  isCustomerOrdersNotFoundError,
  isCustomerOrdersSessionError,
  type CustomerOrderDetail,
  type CustomerOrderLineConfiguration
} from "@/lib/customer-orders-client";

type OrderDetailStatus = "loading" | "ready" | "not-found" | "unauthenticated" | "error";

function loginNext(orderId: number) {
  return `/login?next=${encodeURIComponent(`/mi-cuenta/pedidos/${orderId}`)}`;
}

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

function formatOrderTotal(order: Pick<CustomerOrderDetail, "total" | "currency">) {
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

function hasText(value: string | null) {
  return typeof value === "string" && value.trim().length > 0;
}

function formatDimension(value: string | null) {
  return hasText(value) ? `${value} cm` : null;
}

function configurationRows(configuration: CustomerOrderLineConfiguration) {
  return [
    { label: "Alto", value: formatDimension(configuration.alto) },
    { label: "Ancho", value: formatDimension(configuration.ancho) },
    { label: "Color", value: hasText(configuration.color) ? configuration.color : null },
    { label: "Anclaje", value: hasText(configuration.anclaje) ? configuration.anclaje : null }
  ].filter((row): row is { label: string; value: string } => Boolean(row.value));
}

function OrderDetailState({
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

export function CustomerOrderDetailView({ orderId }: { orderId: number }) {
  const router = useRouter();
  const { isAuthenticated, isReady } = useAuthSession();
  const [order, setOrder] = useState<CustomerOrderDetail | null>(null);
  const [status, setStatus] = useState<OrderDetailStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDownloadingInvoice, setIsDownloadingInvoice] = useState(false);
  const [invoiceDownloadError, setInvoiceDownloadError] = useState<string | null>(null);

  const redirectToLogin = useCallback(() => {
    clearSession();
    setOrder(null);
    setStatus("unauthenticated");
    router.replace(loginNext(orderId));
  }, [orderId, router]);

  const loadOrder = useCallback(async () => {
    const token = getToken();

    if (!token) {
      redirectToLogin();
      return;
    }

    setStatus("loading");
    setErrorMessage(null);

    try {
      const response = await fetchCustomerOrderDetail(token, orderId);
      setOrder(response.order);
      setStatus("ready");
    } catch (error) {
      if (isCustomerOrdersSessionError(error)) {
        redirectToLogin();
        return;
      }

      if (isCustomerOrdersNotFoundError(error)) {
        setOrder(null);
        setStatus("not-found");
        return;
      }

      setStatus("error");
      setErrorMessage(
        error instanceof CustomerOrdersClientError
          ? error.message
          : "No se pudo cargar el pedido. Inténtalo de nuevo."
      );
    }
  }, [orderId, redirectToLogin]);

  const handleDownloadInvoice = async () => {
    if (isDownloadingInvoice) {
      return;
    }

    const token = getToken();
    if (!token) {
      redirectToLogin();
      return;
    }

    setIsDownloadingInvoice(true);
    setInvoiceDownloadError(null);

    let downloadUrl: string | null = null;
    try {
      const download = await fetchCustomerOrderInvoicePdf(token, orderId);
      downloadUrl = window.URL.createObjectURL(download.blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = download.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      if (isCustomerOrdersSessionError(error)) {
        redirectToLogin();
        return;
      }

      setInvoiceDownloadError(
        error instanceof CustomerOrdersClientError
          ? error.message
        : "No se pudo descargar la factura. Inténtalo de nuevo."
      );
    } finally {
      if (downloadUrl) {
        const urlToRevoke = downloadUrl;
        window.setTimeout(() => window.URL.revokeObjectURL(urlToRevoke), 0);
      }
      setIsDownloadingInvoice(false);
    }
  };

  useEffect(() => {
    if (!isReady) {
      return;
    }

    if (!isAuthenticated) {
      redirectToLogin();
      return;
    }

    void loadOrder();
  }, [isAuthenticated, isReady, loadOrder, redirectToLogin]);

  if (status === "loading") {
    return (
      <OrderDetailState
        title="Cargando pedido"
        description="Estamos recuperando el detalle de tu pedido."
      />
    );
  }

  if (status === "unauthenticated") {
    return (
      <OrderDetailState
        title="Inicia sesión para ver este pedido"
        description="El detalle del pedido está asociado a tu cuenta."
      >
        <Link className="mw-button mw-button--primary" href={loginNext(orderId)}>
          Iniciar sesión
        </Link>
      </OrderDetailState>
    );
  }

  if (status === "not-found") {
    return (
      <OrderDetailState
        title="No hemos encontrado este pedido."
        description="Revisa el enlace o vuelve al listado de tus pedidos."
      >
        <Link className="mw-button mw-button--primary" href="/mi-cuenta/pedidos">
          Volver a Mis pedidos
        </Link>
      </OrderDetailState>
    );
  }

  if (status === "error" || !order) {
    return (
      <OrderDetailState
        title="No se pudo cargar el pedido"
        description={errorMessage || "Inténtalo de nuevo en unos segundos."}
      >
        <button className="mw-button mw-button--primary" type="button" onClick={loadOrder}>
          Reintentar
        </button>
        <Link className="mw-button mw-button--secondary" href="/mi-cuenta/pedidos">
          Volver a Mis pedidos
        </Link>
      </OrderDetailState>
    );
  }

  const hasShippingAddress =
    hasText(order.shipping_address.recipient) || hasText(order.shipping_address.city);

  return (
    <article className="mw-customer-order-detail" aria-labelledby="customer-order-title">
      <Link className="mw-account-back-link" href="/mi-cuenta/pedidos">
        Volver a Mis pedidos
      </Link>

      <header className="mw-customer-order-detail__header">
        <div>
          <p className="mw-note">Pedido</p>
          <h2 id="customer-order-title">{order.reference || `Pedido #${order.id}`}</h2>
          <p>{formatOrderDate(order.created_at)}</p>
        </div>

        <div className="mw-customer-order-detail__summary" aria-label="Resumen del pedido">
          <span>{order.status.label}</span>
          <strong>{formatOrderTotal(order)}</strong>
        </div>
      </header>

      <section className="mw-account-card" aria-labelledby="customer-order-lines-title">
        <div className="mw-account-section-heading">
          <p className="mw-note">Productos</p>
          <h3 id="customer-order-lines-title">Productos comprados</h3>
        </div>

        <div className="mw-customer-order-lines">
          {order.lines.map((line) => {
            const rows = configurationRows(line.configuration);

            return (
              <div className="mw-customer-order-line" key={line.id}>
                <div className="mw-customer-order-line__heading">
                  <h4>{line.product_name || "Producto"}</h4>
                  <span>Cantidad: {line.quantity}</span>
                </div>

                {rows.length > 0 ? (
                  <dl className="mw-customer-order-config">
                    {rows.map((row) => (
                      <div key={row.label}>
                        <dt>{row.label}</dt>
                        <dd>{row.value}</dd>
                      </div>
                    ))}
                  </dl>
                ) : null}
              </div>
            );
          })}
        </div>
      </section>

      {hasShippingAddress ? (
        <section className="mw-account-card" aria-labelledby="customer-order-shipping-title">
          <div className="mw-account-section-heading">
            <p className="mw-note">Entrega</p>
            <h3 id="customer-order-shipping-title">Datos de entrega</h3>
          </div>

          <dl className="mw-customer-order-shipping">
            {hasText(order.shipping_address.recipient) ? (
              <div>
                <dt>Destinatario</dt>
                <dd>{order.shipping_address.recipient}</dd>
              </div>
            ) : null}
            {hasText(order.shipping_address.city) ? (
              <div>
                <dt>Ciudad</dt>
                <dd>{order.shipping_address.city}</dd>
              </div>
            ) : null}
          </dl>
        </section>
      ) : null}

      <section className="mw-account-card" aria-labelledby="customer-order-invoice-title">
        <div className="mw-account-section-heading">
          <p className="mw-note">Factura</p>
          <h3 id="customer-order-invoice-title">Factura del pedido</h3>
        </div>

        {order.invoice.available ? (
          <div className="mw-customer-order-invoice">
            <dl className="mw-customer-order-shipping">
              {hasText(order.invoice.number) ? (
                <div>
                  <dt>Número</dt>
                  <dd>{order.invoice.number}</dd>
                </div>
              ) : null}
              {hasText(order.invoice.issued_at) ? (
                <div>
                  <dt>Fecha de emisión</dt>
                  <dd>{formatOrderDate(order.invoice.issued_at)}</dd>
                </div>
              ) : null}
            </dl>

            <button
              className="mw-button mw-button--primary mw-customer-order-invoice__button"
              disabled={isDownloadingInvoice}
              type="button"
              onClick={handleDownloadInvoice}
            >
              {isDownloadingInvoice ? "Descargando..." : "Descargar factura"}
            </button>

            {invoiceDownloadError ? (
              <p className="mw-customer-order-invoice__error" role="alert">
                {invoiceDownloadError}
              </p>
            ) : null}
          </div>
        ) : (
          <p className="mw-customer-order-invoice__unavailable">
            La factura todavía no está disponible.
          </p>
        )}
      </section>
    </article>
  );
}

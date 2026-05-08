import React, { useEffect, useMemo, useState } from "react";
import { authenticatedFetch } from "../../../../utils/authenticatedFetch.js";

const formatCalendarDateLabel = (value) => {
  if (!value) {
    return "Sin fecha";
  }

  const [year, month, day] = String(value).split("-").map(Number);
  if (!year || !month || !day) {
    return value;
  }

  const parsedDate = new Date(year, month - 1, day);

  return new Intl.DateTimeFormat("es-ES", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(parsedDate);
};

const formatCurrency = (value) =>
  new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
  }).format(Number(value || 0));

const formatOrderStatus = (value) => {
  if (!value) {
    return "Sin estado";
  }

  const normalized = String(value).replace(/_/g, " ").trim();
  if (!normalized) {
    return "Sin estado";
  }

  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
};

const DeliveryCalendarPage = () => {
  const [records, setRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    const loadDeliveryCalendar = async () => {
      setIsLoading(true);
      setError("");

      try {
        const result = await authenticatedFetch(
          `${process.env.REACT_APP_BACKEND_URL}/api/admin/delivery-calendar`
        );

        if (ignore) {
          return;
        }

        if (!result.ok) {
          setRecords([]);
          setError(
            result.data?.message ||
              result.data?.error ||
              "No se pudo cargar el calendario de entregas."
          );
          return;
        }

        setRecords(Array.isArray(result.data) ? result.data : []);
      } catch (fetchError) {
        if (ignore) {
          return;
        }

        console.error("Error loading delivery calendar:", fetchError);
        setRecords([]);
        setError("No se pudo cargar el calendario de entregas.");
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    };

    loadDeliveryCalendar();

    return () => {
      ignore = true;
    };
  }, []);

  const groupedDeliveries = useMemo(() => {
    const groupedMap = records.reduce((accumulator, record) => {
      const dateKey = record.estimated_delivery_at || "Sin fecha";

      if (!accumulator[dateKey]) {
        accumulator[dateKey] = [];
      }

      accumulator[dateKey].push(record);
      return accumulator;
    }, {});

    return Object.entries(groupedMap).sort(([leftDate], [rightDate]) =>
      leftDate.localeCompare(rightDate)
    );
  }, [records]);

  return (
    <section className="delivery-calendar-page">
      <header className="delivery-calendar-header">
        <div>
          <h2 className="delivery-calendar-title">Calendario de Entregas</h2>
          <p className="delivery-calendar-subtitle">
            Pedidos agrupados por fecha estimada de entrega.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="admin-native-empty">Cargando calendario de entregas...</p>
      ) : null}

      {!isLoading && error ? (
        <div className="delivery-calendar-error" role="alert">
          {error}
        </div>
      ) : null}

      {!isLoading && !error && !groupedDeliveries.length ? (
        <p className="admin-native-empty">
          No hay pedidos con fecha estimada de entrega.
        </p>
      ) : null}

      {!isLoading && !error && groupedDeliveries.length ? (
        <div className="delivery-calendar-groups">
          {groupedDeliveries.map(([dateKey, items]) => (
            <section key={dateKey} className="delivery-calendar-group">
              <div className="delivery-calendar-group-header">
                <h3 className="delivery-calendar-group-title">
                  {formatCalendarDateLabel(dateKey)}
                </h3>
                <span className="delivery-calendar-group-count">
                  {items.length} pedido{items.length === 1 ? "" : "s"}
                </span>
              </div>

              <div className="delivery-calendar-cards">
                {items.map((item) => (
                  <article
                    key={item.order_id}
                    className="delivery-calendar-card"
                  >
                    <div className="delivery-calendar-card-top">
                      <div>
                        <p className="delivery-calendar-card-label">
                          Localizador
                        </p>
                        <p className="delivery-calendar-card-locator">
                          {item.locator || `Pedido #${item.order_id}`}
                        </p>
                      </div>
                      <span className="delivery-calendar-status-pill">
                        {formatOrderStatus(item.order_status)}
                      </span>
                    </div>

                    <dl className="delivery-calendar-meta">
                      <div className="delivery-calendar-meta-row">
                        <dt>Cliente</dt>
                        <dd>{item.customer_email || "Sin email"}</dd>
                      </div>
                      <div className="delivery-calendar-meta-row">
                        <dt>Líneas</dt>
                        <dd>{item.line_count || 0}</dd>
                      </div>
                      <div className="delivery-calendar-meta-row">
                        <dt>Cantidad total</dt>
                        <dd>{item.total_quantity || 0}</dd>
                      </div>
                      <div className="delivery-calendar-meta-row">
                        <dt>Total</dt>
                        <dd>{formatCurrency(item.total_amount)}</dd>
                      </div>
                    </dl>

                    {item.estimated_delivery_note ? (
                      <div className="delivery-calendar-note">
                        <p className="delivery-calendar-card-label">
                          Nota de entrega
                        </p>
                        <p>{item.estimated_delivery_note}</p>
                      </div>
                    ) : null}
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : null}
    </section>
  );
};

export default DeliveryCalendarPage;

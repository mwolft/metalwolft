import React, { useContext, useEffect, useMemo, useState } from "react";
import { Context } from "../store/appContext";
import { Helmet } from "react-helmet";

const ORDER_STEPS = ["pendiente", "fabricacion", "pintura", "embalaje", "enviado", "entregado"];

const StatusStepper = ({ status }) => {
  const currentIdx = Math.max(0, ORDER_STEPS.indexOf((status || "").toLowerCase()));
  return (
    <div className="d-flex align-items-center flex-wrap" style={{ gap: 8 }}>
      {ORDER_STEPS.map((s, i) => (
        <span
          key={s}
          className={`badge ${i <= currentIdx ? "bg-success" : "bg-secondary"}`}
          title={s}
          style={{ minWidth: 90, textTransform: "capitalize" }}
        >
          {s}
        </span>
      ))}
    </div>
  );
};
const formatDateShort = (d) => (d ? new Date(d).toLocaleDateString() : "—");
const formatMoney = (n) => `${Number(n || 0).toFixed(2)} €`;
const formatDate = (d) => (d ? new Date(d).toLocaleString() : "—");

export const AccountPage = () => {
  const { store, actions } = useContext(Context);
  const [expanded, setExpanded] = useState(null);

  const fetchedOnceRef = React.useRef(false);

  useEffect(() => {
    if (!store.isLoged) {
      fetchedOnceRef.current = false;
      return;
    }
    if (fetchedOnceRef.current) return;
    fetchedOnceRef.current = true;
    actions.fetchOrders();
  }, [store.isLoged]);

  // ✅ Normaliza orders para evitar undefined/null
  const orders = Array.isArray(store.orders) ? store.orders : [];

  // (Opcional debug, quitar luego)
  useEffect(() => {
    if (store.isLoged) console.log("orders:", orders);
  }, [store.isLoged, orders]);

  // Última orden con detalles (para Direcciones)
  const lastOrderWithDetails = useMemo(() => {
    const list = [...orders];
    list.sort((a, b) => new Date(b.order_date || 0) - new Date(a.order_date || 0));
    return list.find(o => Array.isArray(o.order_details) && o.order_details.length > 0);
  }, [orders]);

  // Extraemos el primer detalle (direcciones vienen repetidas por línea)
  const d0 = lastOrderWithDetails?.order_details?.[0] || null;

  // Facturación (tal cual)
  const billing = d0
    ? {
      name: `${d0.firstname || ""} ${d0.lastname || ""}`.trim(),
      address: (d0.billing_address || "").trim(),
      city: (d0.billing_city || "").trim(),
      postal: (d0.billing_postal_code || "").trim(),
      cif: (d0.CIF || "").trim()
    }
    : null;

  // Envío con fallback a facturación
  const shippingRaw = d0
    ? {
      address: (d0.shipping_address || "").trim(),
      city: (d0.shipping_city || "").trim(),
      postal: (d0.shipping_postal_code || "").trim()
    }
    : null;

  const shipping = shippingRaw && billing
    ? {
      address: shippingRaw.address || billing.address || "",
      city: shippingRaw.city || billing.city || "",
      postal: shippingRaw.postal || billing.postal || ""
    }
    : (shippingRaw || null);

  const hasBilling = !!(billing && (billing.address || billing.city || billing.postal));
  const hasShipping = !!(shipping && (shipping.address || shipping.city || shipping.postal));

  const sameAsBilling =
    !!(hasBilling && hasShipping &&
      billing.address && shipping.address &&
      billing.address === shipping.address &&
      (billing.city || "") === (shipping.city || "") &&
      (billing.postal || "") === (shipping.postal || ""));

  return (
    <div className="container" style={{ marginTop: "6rem", marginBottom: "10rem" }}>
      <Helmet>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      <h1 className="h1-categories mb-4">Mi cuenta</h1>

      {!store.isLoged && (
        <div className="alert alert-warning">Debes iniciar sesión para ver tu cuenta.</div>
      )}

      {store.isLoged && (
        <>
          {/* Apartado: Datos personales */}
          <section className="mb-5">
            <h2 className="h2-categories">Datos personales</h2>
            <div className="card shadow-sm">
              <div className="card-body">
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label">Email</label>
                    <input className="form-control" value={store.currentUser?.email || ""} readOnly />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Nombre</label>
                    <input className="form-control" value={store.currentUser?.firstname || ""} readOnly />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Apellidos</label>
                    <input className="form-control" value={store.currentUser?.lastname || ""} readOnly />
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Apartado: Pedidos */}
          <section className="mb-5">
            <h2 className="h2-categories">Pedidos</h2>

            {(orders.length === 0) ? (
              <div className="alert alert-light border">No tienes pedidos todavía.</div>
            ) : (
              <div className="row g-3">
                {orders
                  .slice()
                  .sort((a, b) => new Date(b.order_date || 0) - new Date(a.order_date || 0))
                  .map(order => (
                    <div className="col-12" key={order.id}>
                      <div className="card shadow-sm">
                        <div className="card-body">
                          <div className="d-flex flex-wrap justify-content-between align-items-start">
                            <div className="me-3">
                              <div className="mb-1">
                                <span className="text-muted">Localizador:&nbsp;</span>
                                <code>{order.locator || "—"}</code>
                              </div>
                              <div className="mb-1">
                                <span className="text-muted">Factura:&nbsp;</span>
                                <strong>{order.invoice_number || "—"}</strong>
                              </div>
                              <div className="mb-1">
                                <span className="text-muted">Fecha:&nbsp;</span>
                                {formatDate(order.order_date)}
                              </div>
                            </div>

                            <div className="text-end ms-auto">
                              <div className="mb-1">
                                <span className="badge bg-primary text-uppercase">{order.order_status || "—"}</span>
                              </div>
                              <div className="fs-5 fw-bold">{formatMoney(order.total_amount)}</div>
                            </div>
                          </div>

                          <div className="mt-3">
                            <StatusStepper status={order.order_status} />
                          </div>

                          {/* Fecha estimada de entrega (visible solo si existe) */}
                          {order?.estimated_delivery_at && (
                            <div className="mt-3 alert alert-info d-flex align-items-center" role="alert" style={{ gap: 8 }}>
                              <span style={{ fontSize: 18 }}>🚚</span>
                              <div>
                                <div>
                                  Fecha estimada de entrega:&nbsp;
                                  <strong>{formatDateShort(order.estimated_delivery_at)}</strong>
                                </div>
                                {order?.estimated_delivery_note && (
                                  <div className="small text-muted">{order.estimated_delivery_note}</div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Detalles del pedido */}
                          {Array.isArray(order.order_details) && order.order_details.length > 0 && (
                            <>
                              <button
                                className="btn btn-link p-0 mt-3"
                                onClick={() => setExpanded(expanded === order.id ? null : order.id)}
                              >
                                {expanded === order.id ? "Ocultar detalles" : "Ver detalles"}
                              </button>

                              {expanded === order.id && (
                                <div className="table-responsive mt-2">
                                  <table className="table table-sm align-middle">
                                    <thead>
                                      <tr>
                                        <th>Alto</th>
                                        <th>Ancho</th>
                                        <th>Anclaje</th>
                                        <th>Color</th>
                                        <th>Ud.</th>
                                        <th className="text-end">Importe</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {order.order_details.map(d => (
                                        <tr key={d.id}>
                                          <td>{d.alto ?? "—"}</td>
                                          <td>{d.ancho ?? "—"}</td>
                                          <td>{d.anclaje || "—"}</td>
                                          <td style={{ textTransform: "capitalize" }}>{d.color || "—"}</td>
                                          <td>{d.quantity || 1}</td>
                                          <td className="text-end">{formatMoney(d.precio_total)}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </section>

          {/* Apartado: Facturas */}
          <section className="mb-5">
            <h2 className="h2-categories">Facturas</h2>
            {(orders.length === 0) ? (
              <div className="alert alert-light border">Aún no hay facturas disponibles.</div>
            ) : (
              <div className="row g-3">
                {orders
                  .filter(o => !!o.invoice_number)
                  .map(o => (
                    <div className="col-md-6 col-12" key={`inv-${o.id}`}>
                      <div className="card shadow-sm">
                        <div className="card-body d-flex justify-content-between align-items-start">
                          <div>
                            <div className="fw-semibold">Factura {o.invoice_number}</div>
                            <div className="text-muted small">Fecha: {formatDate(o.order_date)}</div>
                            <div className="text-muted small">Localizador: <code>{o.locator || "—"}</code></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                {orders.filter(o => !!o.invoice_number).length === 0 && (
                  <div className="col-12">
                    <div className="alert alert-light border">No hay facturas emitidas todavía.</div>
                  </div>
                )}
              </div>
            )}
          </section>

          {/* Apartado: Direcciones */}
          <section>
            <h2 className="h2-categories">Direcciones</h2>
            <div className="row g-3">
              <div className="col-md-6 col-12">
                <div className="card shadow-sm h-100">
                  <div className="card-body">
                    <h5 className="card-title mb-3">Facturación</h5>
                    {hasBilling ? (
                      <>
                        <div className="mb-1">{billing.name || "—"}</div>
                        <div className="mb-1">{billing.address || "—"}</div>
                        <div className="mb-1">{billing.city || "—"} {billing.postal || ""}</div>
                        <div className="text-muted small">CIF/NIF: {billing.cif || "—"}</div>
                      </>
                    ) : (
                      <p className="text-muted mb-0">Se completará al realizar un pedido.</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="col-md-6 col-12">
                <div className="card shadow-sm h-100">
                  <div className="card-body">
                    <h5 className="card-title mb-3">Envío</h5>
                    {hasShipping ? (
                      <>
                        <div className="mb-1">{shipping.address || "—"}</div>
                        <div className="mb-1">{shipping.city || "—"} {shipping.postal || ""}</div>
                        {sameAsBilling && (
                          <div className="text-muted small">Igual que facturación</div>
                        )}
                      </>
                    ) : (
                      <p className="text-muted mb-0">Se completará al realizar un pedido.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
};

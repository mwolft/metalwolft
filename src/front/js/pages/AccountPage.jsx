import React, { useContext, useEffect, useState } from "react";
import { Context } from "../store/appContext";
import { Helmet } from "react-helmet";

const ORDER_STEPS = ["pendiente", "fabricacion", "pintura", "embalaje", "enviado", "entregado"];
const ORDER_STEP_LABELS = {
    pendiente: "Pendiente",
    fabricacion: "Fabricación",
    pintura: "Pintura",
    embalaje: "Embalaje",
    enviado: "Enviado",
    entregado: "Entregado"
};

const StatusStepper = ({ status }) => {
    const currentIdx = Math.max(0, ORDER_STEPS.indexOf((status || "").toLowerCase()));

    return (
        <div className="account-order-stepper">
            {ORDER_STEPS.map((step, index) => (
                <span
                    key={step}
                    className={`account-order-step ${index <= currentIdx ? "account-order-step--active" : ""}`}
                >
                    {ORDER_STEP_LABELS[step] || step}
                </span>
            ))}
        </div>
    );
};

const formatMoney = (amount) => `${Number(amount || 0).toFixed(2)} €`;
const formatDate = (value) => (value ? new Date(value).toLocaleString() : "—");

export const AccountPage = () => {
    const { store, actions } = useContext(Context);
    const [expanded, setExpanded] = useState(null);
    const [profile, setProfile] = useState(null);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [cancelled, setCancelled] = useState(false);
    const [editPassword, setEditPassword] = useState(false);
    const [confirmPassword, setConfirmPassword] = useState("");
    const [downloadingInvoiceId, setDownloadingInvoiceId] = useState(null);
    const [invoiceFeedback, setInvoiceFeedback] = useState({ orderId: null, type: "", message: "" });

    useEffect(() => {
        if (!store.isLoged) return;

        actions.fetchOrders();
        actions.fetchProfile().then((data) => {
            if (data) setProfile(data);
        });
    }, [store.isLoged]);

    const handleSaveProfile = async () => {
        if (editPassword) {
            if (profile.password !== confirmPassword) {
                alert("Las contraseñas no coinciden");
                return;
            }
            if (profile.password.length < 6) {
                alert("La nueva contraseña debe tener al menos 6 caracteres");
                return;
            }
        }

        setSaving(true);
        const success = await actions.updateProfile(profile);
        if (success) {
            setSaved(true);
            setEditPassword(false);
            setConfirmPassword("");
            setTimeout(() => setSaved(false), 2000);
        }
        setSaving(false);
    };

    const handleCancel = () => {
        if (store.currentUser) {
            setProfile(store.currentUser);
            setEditPassword(false);
            setConfirmPassword("");
            setCancelled(true);
            setTimeout(() => setCancelled(false), 2000);
        }
    };

    const handleDownloadInvoice = async (order) => {
        if (!order?.invoice_number) return;

        const token = localStorage.getItem("token");
        if (!token) {
            setInvoiceFeedback({
                orderId: order.id,
                type: "error",
                message: "Debes iniciar sesión de nuevo para descargar la factura."
            });
            return;
        }

        const backendUrl = process.env.REACT_APP_BACKEND_URL;
        const filename = `invoice_${order.invoice_number}.pdf`;
        const downloadUrl = `${backendUrl}/api/download-invoice/${filename}`;

        setDownloadingInvoiceId(order.id);
        setInvoiceFeedback({ orderId: null, type: "", message: "" });

        try {
            const response = await fetch(downloadUrl, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error("La factura no está disponible todavía. Contacta con nosotros si la necesitas.");
            }

            const blob = await response.blob();
            const objectUrl = window.URL.createObjectURL(blob);
            const link = document.createElement("a");

            link.href = objectUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(objectUrl);
        } catch (error) {
            setInvoiceFeedback({
                orderId: order.id,
                type: "error",
                message: error.message || "La factura no está disponible todavía. Contacta con nosotros si la necesitas."
            });
        } finally {
            setDownloadingInvoiceId(null);
        }
    };

    const orders = Array.isArray(store.orders) ? store.orders : [];

    if (!store.isLoged) {
        return <div className="container mt-5 alert alert-warning">Debes iniciar sesión.</div>;
    }

    if (!profile) {
        return <div className="container mt-5 text-center">Cargando datos de cuenta...</div>;
    }

    return (
        <div className="container account-page">
            <Helmet>
                <meta name="robots" content="noindex, nofollow" />
            </Helmet>

            <header className="account-page-header">
                <p className="account-page-eyebrow">Área de cliente</p>
                <h1 className="h1-categories mb-2">Mi cuenta</h1>
                <p className="account-page-subtitle">
                    Revisa tus datos, descarga tus facturas disponibles y sigue el estado de cada pedido.
                </p>
            </header>

            <section className="account-section">
                <div className="account-section-heading">
                    <div>
                        <h2 className="h2-categories mb-2">Datos personales</h2>
                        <p className="account-section-copy mb-0">
                            Mantén actualizadas tus direcciones y tus datos de facturación para agilizar futuros pedidos.
                        </p>
                    </div>
                </div>
                <div className="card shadow-sm border-0 account-card">
                    <div className="card-body">
                        <div className="row g-3">
                            <div className="col-md-3">
                                <label className="form-label fw-bold">Nombre</label>
                                <input
                                    className="form-control"
                                    value={profile.firstname || ""}
                                    onChange={(e) => setProfile({ ...profile, firstname: e.target.value })}
                                />
                            </div>
                            <div className="col-md-3">
                                <label className="form-label fw-bold">Apellidos</label>
                                <input
                                    className="form-control"
                                    value={profile.lastname || ""}
                                    onChange={(e) => setProfile({ ...profile, lastname: e.target.value })}
                                />
                            </div>
                            <div className="col-md-6">
                                <label className="form-label fw-bold">Email</label>
                                <input className="form-control bg-light" value={profile.email || ""} readOnly />
                                <div className="col-12 mt-3">
                                    <button
                                        type="button"
                                        className="btn btn-sm btn-outline-secondary mb-3"
                                        onClick={() => setEditPassword(!editPassword)}
                                    >
                                        {editPassword ? "Cerrar cambio de contraseña" : "¿Cambiar contraseña?"}
                                    </button>
                                </div>

                                {editPassword && (
                                    <div className="row g-3 animate__animated animate__fadeIn mb-3">
                                        <div className="col-md-6">
                                            <label className="form-label fw-bold">Nueva contraseña</label>
                                            <input
                                                type="password"
                                                autoComplete="new-password"
                                                className="form-control"
                                                placeholder="Nueva clave"
                                                onChange={(e) => setProfile({ ...profile, password: e.target.value })}
                                            />
                                        </div>
                                        <div className="col-md-6">
                                            <label className="form-label fw-bold">Confirmar nueva contraseña</label>
                                            <input
                                                type="password"
                                                className="form-control"
                                                placeholder="Repite la nueva clave"
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="col-md-6">
                                <label className="form-label fw-bold">Dirección de facturación</label>
                                <input
                                    className="form-control mb-2"
                                    placeholder="Dirección"
                                    value={profile.billing_address || ""}
                                    onChange={(e) => setProfile({ ...profile, billing_address: e.target.value })}
                                />
                                <input
                                    className="form-control mb-2"
                                    placeholder="Ciudad"
                                    value={profile.billing_city || ""}
                                    onChange={(e) => setProfile({ ...profile, billing_city: e.target.value })}
                                />
                                <input
                                    className="form-control mb-2"
                                    placeholder="Código Postal"
                                    value={profile.billing_postal_code || ""}
                                    onChange={(e) => setProfile({ ...profile, billing_postal_code: e.target.value })}
                                />

                                <label className="form-label fw-bold">CIF / NIF</label>
                                <input
                                    className="form-control"
                                    placeholder="CIF / NIF"
                                    value={profile.CIF || ""}
                                    onChange={(e) => setProfile({ ...profile, CIF: e.target.value })}
                                />
                            </div>
                            <div className="col-md-6">
                                <label className="form-label fw-bold">Dirección de envío</label>
                                <input
                                    className="form-control mb-2"
                                    placeholder="Dirección de envío"
                                    value={profile.shipping_address || ""}
                                    onChange={(e) => setProfile({ ...profile, shipping_address: e.target.value })}
                                />
                                <input
                                    className="form-control mb-2"
                                    placeholder="Ciudad"
                                    value={profile.shipping_city || ""}
                                    onChange={(e) => setProfile({ ...profile, shipping_city: e.target.value })}
                                />
                                <input
                                    className="form-control mb-2"
                                    placeholder="Código Postal"
                                    value={profile.shipping_postal_code || ""}
                                    onChange={(e) => setProfile({ ...profile, shipping_postal_code: e.target.value })}
                                />
                            </div>

                            <div className="mt-4 d-flex align-items-center justify-content-end shadow-top pt-3">
                                {saved && <span className="me-3 text-success animate__animated animate__fadeIn">✔ Guardado con éxito</span>}
                                {cancelled && <span className="me-3 text-secondary animate__animated animate__fadeIn">✖ Cambios revertidos</span>}

                                <button
                                    type="button"
                                    className="btn btn-secondary me-2"
                                    onClick={handleCancel}
                                    disabled={saving}
                                >
                                    {cancelled ? "Cancelado" : "Cancelar"}
                                </button>

                                <button
                                    type="button"
                                    className="btn btn-success"
                                    onClick={handleSaveProfile}
                                    disabled={saving}
                                >
                                    {saving ? (
                                        <>
                                            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                            Guardando...
                                        </>
                                    ) : "Guardar"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="account-section">
                <div className="account-section-heading">
                    <div>
                        <h2 className="h2-categories mb-2">Historial de pedidos</h2>
                        <p className="account-section-copy mb-0">
                            Consulta el estado de fabricación, revisa los detalles de cada reja y descarga tu factura cuando esté disponible.
                        </p>
                    </div>
                </div>
                {orders.length === 0 ? (
                    <div className="alert alert-light border account-empty-state">No tienes pedidos todavía.</div>
                ) : (
                    orders
                        .slice()
                        .sort((a, b) => new Date(b.order_date) - new Date(a.order_date))
                        .map((order) => (
                            <div className="card shadow-sm mb-3 border-0 account-order-card" key={order.id}>
                                <div className="card-body">
                                    <div className="account-order-topbar">
                                        <div className="account-order-meta">
                                            <div className="account-order-locator-row">
                                                <span className="account-order-label">Localizador</span>
                                                <code>{order.locator}</code>
                                            </div>
                                            <div className="account-order-date">Fecha: {formatDate(order.order_date)}</div>
                                            <div className="account-order-tags">
                                                <span className="account-order-tag">
                                                    {order.order_details?.length || 0} {order.order_details?.length === 1 ? "línea" : "líneas"}
                                                </span>
                                                {order.invoice_number ? (
                                                    <span className="account-order-tag account-order-tag--invoice">Factura disponible</span>
                                                ) : (
                                                    <span className="account-order-tag account-order-tag--pending">Factura pendiente</span>
                                                )}
                                            </div>

                                            {order.invoice_number ? (
                                                <div className="account-order-invoice">
                                                    <div className="small mb-2">
                                                        <strong>Factura:</strong> <span>{order.invoice_number}</span>
                                                    </div>
                                                    <button
                                                        type="button"
                                                        className="btn btn-sm btn-outline-primary account-order-download-btn"
                                                        onClick={() => handleDownloadInvoice(order)}
                                                        disabled={downloadingInvoiceId === order.id}
                                                    >
                                                        {downloadingInvoiceId === order.id ? "Descargando..." : "Descargar factura"}
                                                    </button>
                                                    {invoiceFeedback.orderId === order.id && invoiceFeedback.message && (
                                                        <div className="mt-2 small text-danger account-order-feedback">
                                                            {invoiceFeedback.message}
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                <div className="mt-2 small text-muted">Factura pendiente</div>
                                            )}
                                        </div>

                                        <div className="account-order-summary">
                                            <div className="account-order-total-label">Total del pedido</div>
                                            <div className="account-order-total">{formatMoney(order.total_amount)}</div>
                                            <span className="account-order-status-badge">
                                                {ORDER_STEP_LABELS[(order.order_status || "").toLowerCase()] || order.order_status}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="mt-3">
                                        <StatusStepper status={order.order_status} />
                                    </div>

                                    <button
                                        className="btn btn-sm btn-outline-secondary mt-3 account-order-toggle-btn"
                                        onClick={() => setExpanded(expanded === order.id ? null : order.id)}
                                    >
                                        {expanded === order.id ? "Ocultar detalles" : "Ver detalles del pedido"}
                                    </button>

                                    {expanded === order.id && order.order_details && (
                                        <div className="table-responsive mt-3 animate__animated animate__fadeIn account-order-details">
                                            <table className="table table-sm account-order-table">
                                                <thead>
                                                    <tr>
                                                        <th>Producto/Medidas</th>
                                                        <th>Color</th>
                                                        <th>Cant.</th>
                                                        <th className="text-end">Total</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {order.order_details.map((detail) => (
                                                        <tr key={detail.id}>
                                                            <td>{detail.alto}x{detail.ancho} cm ({detail.anclaje})</td>
                                                            <td className="text-capitalize">{detail.color}</td>
                                                            <td>{detail.quantity}</td>
                                                            <td className="text-end">{formatMoney(detail.precio_total)}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                )}
            </section>
        </div>
    );
};

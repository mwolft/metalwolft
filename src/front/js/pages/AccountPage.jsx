import React, { useContext, useEffect, useState, useMemo } from "react";
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
                    style={{ minWidth: 90, textTransform: "capitalize" }}
                >
                    {s}
                </span>
            ))}
        </div>
    );
};

const formatMoney = (n) => `${Number(n || 0).toFixed(2)} €`;
const formatDate = (d) => (d ? new Date(d).toLocaleString() : "—");
const formatDateShort = (d) => (d ? new Date(d).toLocaleDateString() : "—");

export const AccountPage = () => {
    const { store, actions } = useContext(Context);
    const [expanded, setExpanded] = useState(null);
    const [profile, setProfile] = useState(null);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [cancelled, setCancelled] = useState(false);
    const [editPassword, setEditPassword] = useState(false);
    const [confirmPassword, setConfirmPassword] = useState("");

    useEffect(() => {
        if (!store.isLoged) return;

        actions.fetchOrders();
        actions.fetchProfile().then(data => {
            if (data) setProfile(data);
        });
    }, [store.isLoged]);

    const handleSaveProfile = async () => {
        // Si el usuario intentó cambiar la contraseña, validamos
        if (editPassword) {
            if (profile.password !== confirmPassword) {
                alert("Las contraseñas no coinciden"); // O usa un setErrorMessage si tienes uno
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
            setEditPassword(false); // Cerramos el desplegable tras guardar
            setConfirmPassword(""); // Limpiamos el campo extra
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

    const orders = Array.isArray(store.orders) ? store.orders : [];

    if (!store.isLoged) {
        return <div className="container mt-5 alert alert-warning">Debes iniciar sesión.</div>;
    }

    if (!profile) {
        return <div className="container mt-5 text-center">Cargando datos de cuenta...</div>;
    }

    return (
        <div className="container" style={{ marginTop: "6rem", marginBottom: "10rem" }}>
            <Helmet>
                <meta name="robots" content="noindex, nofollow" />
            </Helmet>

            <h1 className="h1-categories mb-4">Mi cuenta</h1>

            {/* SECCIÓN: DATOS PERSONALES */}
            <section className="mb-5">
                <h2 className="h2-categories">Datos personales</h2>
                <div className="card shadow-sm border-0">
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
                                {/* SECCIÓN CAMBIO DE CONTRASEÑA */}
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
                                            <label className="form-label fw-bold">Nueva Contraseña</label>
                                            <input
                                                type="password"
                                                autoComplete="new-password"
                                                className="form-control"
                                                placeholder="Nueva clave"
                                                onChange={(e) => setProfile({ ...profile, password: e.target.value })}
                                            />
                                        </div>
                                        <div className="col-md-6">
                                            <label className="form-label fw-bold">Confirmar Nueva Contraseña</label>
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
                                <input className="form-control mb-2" placeholder="Dirección" value={profile.billing_address || ""} onChange={(e) => setProfile({ ...profile, billing_address: e.target.value })} />
                                <input className="form-control mb-2" placeholder="Ciudad" value={profile.billing_city || ""} onChange={(e) => setProfile({ ...profile, billing_city: e.target.value })} />
                                <input className="form-control mb-2" placeholder="Código Postal" value={profile.billing_postal_code || ""} onChange={(e) => setProfile({ ...profile, billing_postal_code: e.target.value })} />

                                <label className="form-label fw-bold">CIF / NIF</label>
                                <input className="form-control" placeholder="CIF / NIF" value={profile.CIF || ""} onChange={(e) => setProfile({ ...profile, CIF: e.target.value })} />

                            </div>
                            <div className="col-md-6">
                                <label className="form-label fw-bold">Dirección de envío</label>
                                <input className="form-control mb-2" placeholder="Dirección de envío" value={profile.shipping_address || ""} onChange={(e) => setProfile({ ...profile, shipping_address: e.target.value })} />
                                <input className="form-control mb-2" placeholder="Ciudad" value={profile.shipping_city || ""} onChange={(e) => setProfile({ ...profile, shipping_city: e.target.value })} />
                                <input className="form-control mb-2" placeholder="Código Postal" value={profile.shipping_postal_code || ""} onChange={(e) => setProfile({ ...profile, shipping_postal_code: e.target.value })} />
                            </div>



                            <div className="mt-4 d-flex align-items-center justify-content-end shadow-top pt-3">
                                {/* Mensaje de Guardado */}
                                {saved && <span className="me-3 text-success animate__animated animate__fadeIn">✔ Guardado con éxito</span>}

                                {/* Mensaje de Cancelado */}
                                {cancelled && <span className="me-3 text-secondary animate__animated animate__fadeIn">✖ Cambios revertidos</span>}

                                {/* Botón Cancelar */}
                                <button
                                    type="button"
                                    className="btn btn-secondary me-2"
                                    onClick={handleCancel}
                                    disabled={saving}
                                >
                                    {cancelled ? "Cancelado" : "Cancelar"}
                                </button>

                                {/* Botón Guardar */}
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

            {/* SECCIÓN: PEDIDOS (Historial Detallado) */}
            <section className="mb-5">
                <h2 className="h2-categories">Historial de Pedidos</h2>
                {orders.length === 0 ? (
                    <div className="alert alert-light border">No tienes pedidos todavía.</div>
                ) : (
                    orders.slice().sort((a, b) => new Date(b.order_date) - new Date(a.order_date)).map((order) => (
                        <div className="card shadow-sm mb-3 border-0" key={order.id}>
                            <div className="card-body">
                                <div className="d-flex justify-content-between align-items-start flex-wrap">
                                    <div>
                                        <div className="mb-1"><strong>Localizador:</strong> <code>{order.locator}</code></div>
                                        <div className="mb-1 text-muted small">Fecha: {formatDate(order.order_date)}</div>
                                    </div>
                                    <div className="text-end">
                                        <div className="fs-5 fw-bold text-primary">{formatMoney(order.total_amount)}</div>
                                        <span className="badge bg-info text-dark">{order.order_status}</span>
                                    </div>
                                </div>
                                <div className="mt-3">
                                    <StatusStepper status={order.order_status} />
                                </div>

                                {/* Botón Detalles */}
                                <button
                                    className="btn btn-sm btn-outline-secondary mt-3"
                                    onClick={() => setExpanded(expanded === order.id ? null : order.id)}
                                >
                                    {expanded === order.id ? "Ocultar detalles" : "Ver detalles del pedido"}
                                </button>

                                {expanded === order.id && order.order_details && (
                                    <div className="table-responsive mt-3 animate__animated animate__fadeIn">
                                        <table className="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>Producto/Medidas</th>
                                                    <th>Color</th>
                                                    <th>Cant.</th>
                                                    <th className="text-end">Total</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {order.order_details.map(d => (
                                                    <tr key={d.id}>
                                                        <td>{d.alto}x{d.ancho} cm ({d.anclaje})</td>
                                                        <td className="text-capitalize">{d.color}</td>
                                                        <td>{d.quantity}</td>
                                                        <td className="text-end">{formatMoney(d.precio_total)}</td>
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
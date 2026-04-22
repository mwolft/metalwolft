import React, { useContext, useState, useEffect } from "react";
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Table } from "react-bootstrap";
import { Notification } from "../component/Notification.jsx";
import "../../styles/cart.css";
import "../../styles/favorites.css";
import { Link, useNavigate } from "react-router-dom";
import { calcularEnvio } from "../../utils/shippingCalculator.js";
import DeliveryEstimate from "../component/DeliveryEstimate.jsx";
import { Helmet } from "react-helmet-async";

// Funcion auxiliar para determinar tipo de envio segun SEUR
const getShippingType = (product) => {
    const alto = parseFloat(product.alto);
    const ancho = parseFloat(product.ancho);
    const profundidad = 4; // cm
    const peso = 10; // kg estimado
    const sumaDimensiones = alto + ancho + profundidad;

    if (peso > 60 || sumaDimensiones > 500) {
        return { tipo: "B", coste: 99, motivo: "Excede dimensiones máximas permitidas (500 cm)" };
    }
    if (peso > 40 || alto > 175 || sumaDimensiones > 300) {
        return { tipo: "A", coste: 49, motivo: "Excede altura o volumen permitido (300 cm)" };
    }
    return { tipo: "normal", coste: null, motivo: null };
};

export const Cart = () => {
    const { store, actions } = useContext(Context);
    const [notification, setNotification] = useState(null);
    const [discountCode, setDiscountCode] = useState("");
    const [discountPercent, setDiscountPercent] = useState(0);
    const navigate = useNavigate();
    const [metaData, setMetaData] = useState({});

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/cart`)
            .then((response) => {
                if (!response.ok) throw new Error(`Error SEO: ${response.status}`);
                return response.json();
            })
            .then((data) => setMetaData(data))
            .catch((error) => console.error("Error loading cart SEO:", error));
    }, []);

    useEffect(() => {
        actions.loadCart();
    }, []);

    const handleRemoveFromCart = (product) => {
        if (!product.producto_id) {
            console.error("Error: Falta el producto_id en el carrito", product);
            return;
        }

        actions.removeFromCart(product);
        setNotification("Producto eliminado del carrito");
    };

    const { totalShipping: shippingCost, subtotal, finalTotal } = calcularEnvio(store.cart);

    const handleCheckout = () => {
        navigate("/checkout-form");
    };

    const lastCategorySlug = store.cart.length > 0 ? store.cart[store.cart.length - 1].category_slug : null;

    const discountCodes = {
        BIENVENIDO: 5,
        REJAS10: 10,
        WOLFT15: 15,
        SERGIO99: 99,
    };

    const colorLabels = {
        satinado_blanco: "Blanco liso",
        satinado_negro: "Negro liso",
        satinado_gris: "Gris medio liso",
        satinado_verde: "Verde carruajes liso",
        forja_negro: "Negro forja",
        forja_gris: "Gris acero forja",
        forja_marron: "Marron castano forja",
        forja_azul: "Azul forja",
        forja_verde: "Verde bronce forja",
        forja_dorado: "Dorado forja"
    };

    const handleApplyDiscount = () => {
        const codeUpper = discountCode.trim().toUpperCase();

        if (discountCodes[codeUpper]) {
            const percent = discountCodes[codeUpper];

            setDiscountPercent(percent);
            actions.setDiscountPercent(percent);
            actions.setDiscountCode(codeUpper);

            setNotification(`Codigo ${codeUpper} aplicado: ${percent}% de descuento`);
        } else {
            setDiscountPercent(0);
            actions.setDiscountPercent(0);
            actions.setDiscountCode(null);

            setNotification("Codigo no valido");
        }
    };

    const handleDownloadBudget = async () => {
        try {
            const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
                ? process.env.REACT_APP_BACKEND_URL
                : process.env.NODE_ENV === "production"
                    ? "https://api.metalwolft.com"
                    : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

            const payload = {
                cart: store.cart.map(item => ({
                    nombre: item.nombre,
                    alto: item.alto,
                    ancho: item.ancho,
                    quantity: item.quantity ?? 1,
                    total: (item.precio_total ?? 0) * (item.quantity ?? 1)
                })),
                subtotal,
                shipping: shippingCost,
                discount_percent: discountPercent,
                discount_amount: subtotal * (discountPercent / 100),
                total: finalTotal * (1 - discountPercent / 100)
            };

            const response = await fetch(`${apiBaseUrl}/api/budget/pdf`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${store.token}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error("Error al generar el presupuesto");

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = "presupuesto-metalwolft.pdf";
            document.body.appendChild(a);
            a.click();
            a.remove();

            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error(error);
            setNotification("No se pudo generar el presupuesto");
        }
    };

    const cartTablePanelStyle = {
        border: "1px solid #eceff3",
        borderRadius: "18px",
        backgroundColor: "#ffffff",
        padding: "24px",
        boxShadow: "0 14px 32px rgba(15, 23, 42, 0.05)"
    };

    const cartSummaryStickyStyle = {
        position: "sticky",
        top: "118px"
    };

    const cartSummaryCardStyle = {
        border: "1px solid #eceff3",
        borderRadius: "20px",
        backgroundColor: "#ffffff",
        padding: "24px",
        boxShadow: "0 16px 36px rgba(15, 23, 42, 0.08)"
    };

    const summarySectionStyle = {
        border: "1px solid #eef1f4",
        borderRadius: "14px",
        backgroundColor: "#fbfcfd",
        padding: "16px 18px"
    };

    const paymentBadgeStyle = {
        display: "inline-flex",
        alignItems: "center",
        gap: "8px",
        padding: "8px 12px",
        borderRadius: "999px",
        backgroundColor: "#f3f5f7",
        color: "#495057",
        fontSize: "0.82rem",
        fontWeight: 600
    };

    const summaryLineStyle = {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "16px",
        marginBottom: "10px",
        fontSize: "0.98rem"
    };

    const trustItemStyle = {
        display: "flex",
        alignItems: "flex-start",
        gap: "12px"
    };

    const couponInputStyle = {
        padding: "10px 12px",
        borderRadius: "10px",
        border: "1px solid #d6dbe1",
        width: "100%",
        minHeight: "42px"
    };

    return (
        <>
            <Helmet htmlAttributes={{ lang: "es" }}>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="robots" content={metaData.robots} />
                <meta name="theme-color" content={metaData.theme_color || "#ff324d"} />
                {metaData.canonical && (
                    <link rel="canonical" href={metaData.canonical} />
                )}
                <meta property="og:type" content={metaData.og_type} />
                <meta property="og:title" content={metaData.og_title} />
                <meta property="og:description" content={metaData.og_description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:title" content={metaData.twitter_title} />
                <meta name="twitter:description" content={metaData.twitter_description} />
                <meta name="twitter:image" content={metaData.twitter_image} />
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>

            <Container fluid style={{ marginTop: "95px", paddingBottom: "80px" }}>
                <h2 className="h2-categories text-center my-2">Carrito de compra</h2>

                {store.cart.length === 0 ? (
                    <p className="text-center" style={{ marginTop: "100px", marginBottom: "300px" }}>
                        No tiene productos en su carrito aun. <br /><br />
                        <Link to="/" className="link-categories">
                            <i className="fa-solid fa-arrow-left"></i> Volver
                        </Link>
                    </p>
                ) : (
                    <Row className="g-4 g-xl-5 mt-2 align-items-start">
                        <Col xl={8} lg={7}>
                            <div style={cartTablePanelStyle}>
                                <div className="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
                                    <div>
                                        <p className="text-uppercase text-muted small mb-1" style={{ letterSpacing: "0.08em" }}>
                                            Tu compra
                                        </p>
                                        <h4 className="mb-0" style={{ fontSize: "1.4rem", fontWeight: 600 }}>
                                            Productos del carrito
                                        </h4>
                                    </div>
                                    <span className="text-muted small">
                                        {store.cart.length} {store.cart.length === 1 ? "producto" : "productos"} configurados a medida
                                    </span>
                                </div>

                                <Table responsive className="table-shopping-cart mb-0">
                                    <thead>
                                        <tr>
                                            <th>Imagen</th>
                                            <th>Producto</th>
                                            <th>Alto(cm)</th>
                                            <th>Ancho(cm)</th>
                                            <th>Anclaje</th>
                                            <th>Color</th>
                                            <th>Cantidad</th>
                                            <th>Precio</th>
                                            <th>Total</th>
                                            <th></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {store.cart.map((product, index) => {
                                            const shippingInfo = getShippingType(product);
                                            return (
                                                <tr key={index} className="cart-line-item">
                                                    <td className="table-shopping-cart-img">
                                                        <Link to={`/${product.category_slug}/${product.slug}`}>
                                                            <img
                                                                src={product.imagen}
                                                                alt={product.nombre}
                                                                style={{ maxWidth: "80px", height: "auto", display: "block" }}
                                                            />
                                                        </Link>
                                                    </td>
                                                    <td>
                                                        <Link
                                                            to={`/${product.category_slug}/${product.slug}`}
                                                            style={{ textDecoration: "none", color: "inherit" }}
                                                        >
                                                            {product.nombre}
                                                        </Link>

                                                        {shippingInfo.tipo !== "normal" && (
                                                            <>
                                                                <p className="d-none d-md-block text-warning mt-1" style={{ fontSize: "0.85rem" }}>
                                                                    Este producto requiere envío especial ({shippingInfo.coste} EUR)<br />
                                                                    Supera las dimensiones maximas del envío estandar:<br />
                                                                    - Lado mas largo &gt; 175 cm, o<br />
                                                                    - Suma de dimensiones &gt; 300 cm.
                                                                </p>

                                                                <span
                                                                    className="d-inline d-md-none text-warning mt-1"
                                                                    style={{ fontSize: "1rem", cursor: "pointer" }}
                                                                    aria-label="Aviso de envío especial"
                                                                    title="Aviso de envío especial"
                                                                    onClick={() =>
                                                                        alert(
                                                                            `Este producto requiere envío especial (${shippingInfo.coste} EUR).\n\n` +
                                                                            `Se aplica cuando:\n` +
                                                                            `- El lado mas largo supera los 175 cm,\n` +
                                                                            `- O la suma de dimensiones supera los 300 cm.\n\n` +
                                                                            `Por este motivo tiene una tarifa especial de transporte.`
                                                                        )
                                                                    }
                                                                >
                                                                    <i className="fa-solid fa-triangle-exclamation" aria-hidden="true"></i>
                                                                </span>
                                                            </>
                                                        )}
                                                    </td>
                                                    <td>{product.alto}</td>
                                                    <td>{product.ancho}</td>
                                                    <td>{product.anclaje}</td>
                                                    <td>{colorLabels[product.color] ?? product.color}</td>
                                                    <td>{product.quantity ?? 1}</td>
                                                    <td>{(product.precio_total ?? 0).toFixed(2)} EUR</td>
                                                    <td>{((product.precio_total ?? 0) * (product.quantity ?? 1)).toFixed(2)} EUR</td>
                                                    <td className="cart_remove">
                                                        <Button
                                                            className="btn-style-background-color"
                                                            onClick={() => handleRemoveFromCart(product)}
                                                        >
                                                            Eliminar
                                                        </Button>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </Table>
                            </div>

                            {lastCategorySlug && (
                                <Link
                                    to={`/${lastCategorySlug}`}
                                    className="mt-4 d-inline-block text-decoration-none"
                                    style={{ fontWeight: "bold", color: "#ff324d" }}
                                >
                                    <i className="fa-solid fa-arrow-left"></i> Volver al catálogo de {lastCategorySlug.replaceAll("-", " ")}
                                </Link>
                            )}
                        </Col>

                        <Col xl={4} lg={5}>
                            <div style={cartSummaryStickyStyle}>
                                <div style={cartSummaryCardStyle}>
                                    <div className="mb-4">
                                        <p className="text-uppercase text-muted small mb-2" style={{ letterSpacing: "0.08em" }}>
                                            Resumen del pedido
                                        </p>
                                        <h4 className="mb-2" style={{ fontSize: "1.55rem", fontWeight: 700 }}>
                                            Listo para continuar al pago
                                        </h4>
                                        <p className="text-muted mb-0" style={{ fontSize: "0.97rem" }}>
                                            Revisa tu pedido y continua al siguiente paso con pago seguro mediante tarjeta o PayPal.
                                        </p>
                                    </div>

                                    <div className="d-flex flex-wrap gap-2 mb-4">
                                        <span style={paymentBadgeStyle}><i className="fa-regular fa-credit-card"></i> Tarjeta</span>
                                        <span style={paymentBadgeStyle}><i className="fa-brands fa-paypal"></i> PayPal</span>
                                        <span style={paymentBadgeStyle}><i className="fa-solid fa-shield-halved"></i> Pago seguro</span>
                                    </div>

                                    <div style={summarySectionStyle}>
                                        <div style={summaryLineStyle}>
                                            <span className="text-muted">Subtotal</span>
                                            <strong>{subtotal.toFixed(2)} EUR</strong>
                                        </div>

                                        <div style={summaryLineStyle}>
                                            <span className="text-muted">Envío</span>
                                            {shippingCost === 0 ? (
                                                <strong className="text-success">GRATIS</strong>
                                            ) : (
                                                <strong>{shippingCost.toFixed(2)} EUR</strong>
                                            )}
                                        </div>

                                        {discountPercent > 0 && (
                                            <div style={{ ...summaryLineStyle, color: "green", marginBottom: "0px" }}>
                                                <span>Descuento aplicado</span>
                                                <strong>-{discountPercent}%</strong>
                                            </div>
                                        )}

                                        <hr style={{ margin: "16px 0" }} />

                                        <div className="d-flex justify-content-between align-items-end gap-3">
                                            <div>
                                                <p className="text-muted mb-1 small">Total final</p>
                                                <h3 className="mb-0" style={{ fontSize: "1.9rem", fontWeight: 700 }}>
                                                    {(finalTotal * (1 - discountPercent / 100)).toFixed(2)} EUR
                                                </h3>
                                                <p className="text-muted small mb-0">IVA incluido</p>
                                            </div>
                                            <Button
                                                onClick={handleDownloadBudget}
                                                title="Guardar presupuesto"
                                                className="d-inline-flex align-items-center justify-content-center p-0 border-0"
                                                style={{
                                                    backgroundColor: "transparent",
                                                    color: "#282c30",
                                                    transition: "opacity 0.2s"
                                                }}
                                                onMouseOver={(e) => e.currentTarget.style.opacity = "0.7"}
                                                onMouseOut={(e) => e.currentTarget.style.opacity = "1"}
                                            >
                                                <i className="fa-solid fa-file-arrow-down fa-lg"></i>
                                            </Button>
                                        </div>
                                    </div>

                                    <div className="mt-4" style={summarySectionStyle}>
                                        <div className="d-flex justify-content-between align-items-center gap-3 mb-2">
                                            <h5 className="mb-0" style={{ fontSize: "1rem", fontWeight: 600 }}>Plazo estimado</h5>
                                            <span className="text-muted small">Fabricacion a medida</span>
                                        </div>
                                        <DeliveryEstimate />
                                    </div>

                                    <div className="mt-4" style={summarySectionStyle}>
                                        <div className="d-flex justify-content-between align-items-center gap-3 mb-3">
                                            <h5 className="mb-0" style={{ fontSize: "1rem", fontWeight: 600 }}>Código promocional</h5>
                                            <span className="text-muted small">Opcional</span>
                                        </div>
                                        <div className="d-flex flex-column flex-sm-row gap-2">
                                            <input
                                                type="text"
                                                placeholder="Introduce tu codigo de descuento"
                                                value={discountCode}
                                                onChange={(e) => setDiscountCode(e.target.value)}
                                                style={couponInputStyle}
                                            />
                                            <Button
                                                variant="secondary"
                                                onClick={handleApplyDiscount}
                                                style={{ minWidth: "120px" }}
                                            >
                                                Aplicar
                                            </Button>
                                        </div>
                                    </div>

                                    <Button
                                        className="btn-style-background-color w-100 mt-4"
                                        onClick={handleCheckout}
                                        style={{ minHeight: "52px", fontWeight: 600, fontSize: "1rem" }}
                                    >
                                        Continuar al pago seguro
                                    </Button>

                                    <p className="text-muted small text-center mt-3 mb-0">
                                        En el siguiente paso podrás pagar con tarjeta o PayPal.
                                    </p>

                                    <div className="mt-4 pt-4" style={{ borderTop: "1px solid #eef1f4" }}>
                                        <div className="d-flex flex-column gap-3">
                                            <div style={trustItemStyle}>
                                                <i className="fa-solid fa-shield-halved" style={{ color: "#ff324d", marginTop: "2px" }}></i>
                                                <div>
                                                    <p className="mb-1" style={{ fontWeight: 600 }}>Pago protegido</p>
                                                    <p className="text-muted small mb-0">Aceptamos tarjeta y PayPal dentro de una compra segura.</p>
                                                </div>
                                            </div>

                                            <div style={trustItemStyle}>
                                                <i className="fa-solid fa-hammer" style={{ color: "#ff324d", marginTop: "2px" }}></i>
                                                <div>
                                                    <p className="mb-1" style={{ fontWeight: 600 }}>Fabricacion a medida</p>
                                                    <p className="text-muted small mb-0">Tu pedido se fabrica según las medidas y opciones elegidas.</p>
                                                </div>
                                            </div>

                                            <div style={trustItemStyle}>
                                                <i className="fa-solid fa-headset" style={{ color: "#ff324d", marginTop: "2px" }}></i>
                                                <div>
                                                    <p className="mb-1" style={{ fontWeight: 600 }}>Te ayudamos antes de pagar</p>
                                                    <p className="text-muted small mb-0">
                                                        Si necesitas ayuda con medidas o plazos, <Link to="/contact" style={{ color: "#ff324d", textDecoration: "none", fontWeight: 600 }}>contáctanos</Link>.
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="text-center mt-4 pt-3" style={{ borderTop: "1px solid #eef1f4" }}>
                                        <img
                                            src="https://kompozits.lv/app/uploads/2021/02/secure-600x123.png"
                                            alt="Pago Seguro Autorizado"
                                            style={{ maxWidth: "250px", width: "100%", height: "auto" }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </Col>
                    </Row>
                )}

                {notification && (
                    <Notification
                        message={notification}
                        duration={3000}
                        onClose={() => setNotification(null)}
                    />
                )}
            </Container>
        </>
    );
};

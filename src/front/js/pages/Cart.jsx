import React, { useContext, useState, useEffect } from "react";
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Table } from "react-bootstrap";
import { Notification } from "../component/Notification.jsx";
import "../../styles/cart.css";
import "../../styles/favorites.css";
import { Link, useNavigate } from "react-router-dom";
import { calcularEnvio } from "../../utils/shippingCalculator.js";
import DeliveryEstimate from "../component/DeliveryEstimate.jsx"
import { Helmet } from "react-helmet-async";

// Función auxiliar para determinar tipo de envío según SEUR
const getShippingType = (product) => {
    const alto = parseFloat(product.alto);
    const ancho = parseFloat(product.ancho);
    const profundidad = 4; // cm
    const peso = 10; // kg estimado
    const sumaDimensiones = alto + ancho + profundidad;

    if (peso > 60 || sumaDimensiones > 500) {
        return { tipo: 'B', coste: 99, motivo: 'Excede dimensiones máximas permitidas (500 cm)' };
    }
    if (peso > 40 || alto > 175 || sumaDimensiones > 300) {
        return { tipo: 'A', coste: 49, motivo: 'Excede altura o volumen permitido (300 cm)' };
    }
    return { tipo: 'normal', coste: null, motivo: null };
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
        blanco: "Blanco (RAL 9016)",
        negro: "Negro (RAL 9005)",
        gris: "Gris (RAL 7016)",
        marrón: "Marrón (RAL 8014)",
        verde: "Verde (RAL 6009)"
    };


    const handleApplyDiscount = () => {
        const codeUpper = discountCode.trim().toUpperCase();

        if (discountCodes[codeUpper]) {
            const percent = discountCodes[codeUpper];

            // 🔹 Guardar local y globalmente
            setDiscountPercent(percent);
            actions.setDiscountPercent(percent);
            actions.setDiscountCode(codeUpper);

            setNotification(`Código ${codeUpper} aplicado: ${percent}% de descuento`);
        } else {
            setDiscountPercent(0);
            actions.setDiscountPercent(0);
            actions.setDiscountCode(null);

            setNotification("Código no válido");
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


    return (
        <>
            <Helmet htmlAttributes={{ lang: "es" }}>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />

                {/* Robots */}
                <meta name="robots" content={metaData.robots} />

                {/* Theme color */}
                <meta name="theme-color" content={metaData.theme_color || "#ff324d"} />

                {/* Canonical */}
                {metaData.canonical && (
                    <link rel="canonical" href={metaData.canonical} />
                )}

                {/* OG */}
                <meta property="og:type" content={metaData.og_type} />
                <meta property="og:title" content={metaData.og_title} />
                <meta property="og:description" content={metaData.og_description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />

                {/* Twitter */}
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:title" content={metaData.twitter_title} />
                <meta name="twitter:description" content={metaData.twitter_description} />
                <meta name="twitter:image" content={metaData.twitter_image} />

                {/* JSON-LD */}
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            <Container fluid style={{ marginTop: "95px" }}>
                <h2 className="h2-categories text-center my-2">Carrito de compra</h2>
                {store.cart.length === 0 ? (
                    <p className="text-center" style={{ marginTop: "100px", marginBottom: "300px" }}>
                        No tiene productos en su carrito aún. <br /><br />
                        <Link to="/" className="link-categories">
                            <i className="fa-solid fa-arrow-left"></i> Volver
                        </Link>
                    </p>
                ) : (
                    <Row>
                        <Col md={11} className="mx-auto">
                            <Table responsive className="table-shopping-cart">
                                <thead>
                                    <tr>
                                        <th>Imágen</th>
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
                                                            style={{ maxWidth: '80px', height: 'auto', display: 'block' }}
                                                        />
                                                    </Link>
                                                </td>
                                                <td>
                                                    <Link
                                                        to={`/${product.category_slug}/${product.slug}`}
                                                        style={{ textDecoration: 'none', color: 'inherit' }}
                                                    >
                                                        {product.nombre}
                                                    </Link>

                                                    {shippingInfo.tipo !== 'normal' && (
                                                        <>
                                                            {/* Pantallas grandes: mostrar texto completo */}
                                                            <p className="d-none d-md-block text-warning mt-1" style={{ fontSize: '0.85rem' }}>
                                                                🚚 Este producto requiere envío especial ({shippingInfo.coste} €)<br />
                                                                Supera las dimensiones máximas del envío estándar:<br />
                                                                – Lado más largo &gt; 175 cm, o<br />
                                                                – Suma de dimensiones &gt; 300 cm.
                                                            </p>

                                                            {/* Pantallas pequeñas: solo icono ℹ️ con alert al hacer clic */}
                                                            <span
                                                                className="d-inline d-md-none text-warning mt-1"
                                                                style={{ fontSize: '1rem', cursor: 'pointer' }}
                                                                onClick={() =>
                                                                    alert(
                                                                        `🚚 Este producto requiere envío especial (${shippingInfo.coste} €).\n\n` +
                                                                        `Se aplica cuando:\n` +
                                                                        `• El lado más largo supera los 175 cm,\n` +
                                                                        `• O la suma de dimensiones supera los 300 cm.\n\n` +
                                                                        `Por este motivo tiene una tarifa especial de transporte.`
                                                                    )
                                                                }
                                                            >
                                                                ⚠️
                                                            </span>
                                                        </>
                                                    )}
                                                </td>
                                                <td>{product.alto}</td>
                                                <td>{product.ancho}</td>
                                                <td>{product.anclaje}</td>
                                                <td>{colorLabels[product.color] ?? product.color}</td>
                                                <td>{product.quantity ?? 1}</td>
                                                <td>{(product.precio_total ?? 0).toFixed(2)}€</td>
                                                <td>{((product.precio_total ?? 0) * (product.quantity ?? 1)).toFixed(2)}€</td>
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

                            <Row className="mt-3 mb-5 mx-3">
                                <Col className="text-end">
                                    <p style={{ fontSize: "16px", marginBottom: "0px" }}>
                                        {subtotal.toFixed(2)}€ (IVA incl.)
                                    </p>
                                    {shippingCost === 0 ? (
                                        <p className="text-success" style={{ fontSize: "16px", marginBottom: "0px" }}>
                                            Envío: GRATIS ✔️
                                        </p>
                                    ) : (
                                        <p className="text-danger" style={{ fontSize: "16px", marginBottom: "0px" }}>
                                            Envío: {shippingCost.toFixed(2)}€
                                        </p>
                                    )}
                                    <DeliveryEstimate />
                                    <div className="my-3 text-end">
                                        <input
                                            type="text"
                                            placeholder="Introduce tu código de descuento"
                                            value={discountCode}
                                            onChange={(e) => setDiscountCode(e.target.value)}
                                            style={{
                                                padding: "5px",
                                                borderRadius: "5px",
                                                border: "1px solid #ccc",
                                                marginRight: "8px"
                                            }}
                                        />
                                        <Button
                                            variant="secondary"
                                            size="sm"
                                            onClick={handleApplyDiscount}
                                        >
                                            Aplicar
                                        </Button>
                                    </div>

                                    <hr />

                                    {discountPercent > 0 && (
                                        <p style={{ fontSize: "16px", color: "green" }}>
                                            Descuento aplicado: -{discountPercent}%
                                        </p>
                                    )}
                                    <p style={{ fontSize: "22px", fontWeight: "bold" }}>
                                        Total: {(finalTotal * (1 - discountPercent / 100)).toFixed(2)}€ (IVA incl.)
                                        <Button
                                            onClick={handleDownloadBudget}
                                            title="Guardar presupuesto"
                                            className="d-inline-flex align-items-center justify-content-center ms-md-2 p-0 border-0"
                                            style={{
                                                backgroundColor: 'transparent',
                                                color: '#282c30',
                                                transition: 'opacity 0.2s',
                                                marginLeft: '5px'
                                            }}
                                            onMouseOver={(e) => e.currentTarget.style.opacity = '0.7'}
                                            onMouseOut={(e) => e.currentTarget.style.opacity = '1'}
                                        >
                                            <i className="fa-solid fa-file-arrow-down fa-lg"></i>
                                        </Button>
                                    </p>
                                    <Button
                                        className="btn-style-background-color"
                                        onClick={handleCheckout}
                                    >
                                        Formulario de Pago
                                    </Button>
                                    <div className="text-right">
                                        <img
                                            src="https://kompozits.lv/app/uploads/2021/02/secure-600x123.png"
                                            alt="Pago Seguro Autorizado"
                                            style={{ maxWidth: '280px', height: 'auto', marginBottom: '30px', marginTop: '15px' }}
                                        />
                                    </div>
                                </Col>
                                {lastCategorySlug && (
                                    <Link
                                        to={`/${lastCategorySlug}`}
                                        className="my-3 d-inline-block text-decoration-none"
                                        style={{ fontWeight: 'bold', color: '#ff324d' }}
                                    >
                                        ← Volver al catálogo de {lastCategorySlug.replaceAll("-", " ")}
                                    </Link>
                                )}
                            </Row>
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

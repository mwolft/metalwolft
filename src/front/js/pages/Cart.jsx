import React, { useContext, useState, useEffect } from "react";
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Table } from "react-bootstrap";
import { Notification } from "../component/Notification.jsx";
import "../../styles/cart.css";
import "../../styles/favorites.css";
import { Link, useNavigate } from "react-router-dom";
import { calcularEnvio } from "../../utils/shippingCalculator.js";

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
    const navigate = useNavigate();

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

    return (
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
                    <Col md={12} className="mx-auto">
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
                                                            🚚 Este producto requiere envío especial ({shippingInfo.coste} €)<br />
                                                            Supera el tamaño máximo estándar permitido para envío normal.<br />
                                                            (más de 300 cm entre largo, ancho y alto).
                                                        </p>

                                                        {/* Pantallas pequeñas: solo icono ℹ️ con alert al hacer clic */}
                                                        <span
                                                            className="d-inline d-md-none text-warning mt-1"
                                                            style={{ fontSize: '1rem', cursor: 'pointer' }}
                                                            onClick={() =>
                                                                alert(`🚚 Este producto requiere envío especial (${shippingInfo.coste} €).\n\nSupera el tamaño máximo estándar permitido para envío normal (más de 300 cm entre largo, ancho y alto).`)
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
                                            <td>{product.color}</td>
                                            <td>{product.quantity ?? 1}</td>
                                            <td>{(product.precio_total ?? 0).toFixed(2)} €</td>
                                            <td>{((product.precio_total ?? 0) * (product.quantity ?? 1)).toFixed(2)} €</td>
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
                                    {subtotal.toFixed(2)} € (IVA incl.)
                                </p>
                                {shippingCost === 0 ? (
                                    <p className="text-success" style={{ fontSize: "16px", marginBottom: "0px" }}>
                                        Envío: GRATIS ✔️
                                    </p>
                                ) : (
                                    <p className="text-danger" style={{ fontSize: "16px", marginBottom: "0px" }}>
                                        Envío: {shippingCost.toFixed(2)} €
                                    </p>
                                )}
                                <hr />
                                <p style={{ fontSize: "22px", fontWeight: "bold" }}>
                                    Total: {finalTotal.toFixed(2)} € (IVA incl.)
                                </p>
                                <Button
                                    className="btn-style-background-color"
                                    onClick={handleCheckout}
                                >
                                    Formulario de Pago
                                </Button>
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
    );
};

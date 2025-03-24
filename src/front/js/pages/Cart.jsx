import React, { useContext, useState, useEffect } from "react";
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Table } from "react-bootstrap";
import { Notification } from "../component/Notification.jsx";
import "../../styles/cart.css";
import "../../styles/favorites.css";
import { Link, useNavigate } from "react-router-dom";

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

    // Calcular el subtotal de todos los productos
    const subtotal = store.cart.reduce((acc, product) => acc + parseFloat(product.precio_total), 0);

    // Configuración de envío
    const shippingThreshold = 350;
    const shippingRatePerKg = 1.70; // €/kg
    const weightPerProduct = 10; // kg por reja
    const shippingCost = subtotal >= shippingThreshold ? 0 : store.cart.length * (weightPerProduct * shippingRatePerKg);
    const finalTotal = subtotal + shippingCost;

    const handleCheckout = () => {
        navigate("/checkout-form");
    };

    return (
        <Container style={{ marginTop: "95px" }}>
            <h2 className="h2-categories text-center my-2">Carrito de compra</h2>
            {store.cart.length === 0 ? (
                <p className="text-center" style={{ marginTop: "100px", marginBottom: "300px" }}>
                    No tiene productos en su carrito aún. <br />
                    <br />
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
                                    <th>Total</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {store.cart.map((product, index) => (
                                    <tr key={index} className="cart-line-item">
                                        <td className="table-shopping-cart-img">
                                            <img src={product.imagen} alt={product.nombre} />
                                        </td>
                                        <td>{product.nombre}</td>
                                        <td>{product.alto}</td>
                                        <td>{product.ancho}</td>
                                        <td>{product.anclaje}</td>
                                        <td>{product.color}</td>
                                        <td>{product.precio_total} €</td>
                                        <td className="cart_remove">
                                            <Button
                                                className="btn-style-background-color"
                                                onClick={() => handleRemoveFromCart(product)}
                                            >
                                                Eliminar
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </Table>
                        <Row className="mt-3 mb-5 mx-3">
                            <Col className="text-end">
                                <p style={{ fontSize: "16px", marginBottom: "0px"}}>
                                    {subtotal.toFixed(2)} € (IVA incl.)
                                </p>
                                {subtotal >= shippingThreshold ? (
                                    <p
                                        className="text-success"
                                        style={{
                                            fontSize: "16px",
                                            marginBottom: "0px"
                                        }}
                                    >
                                        Envío: GRATIS ✔️
                                    </p>
                                ) : (
                                    <p
                                        className="text-danger"
                                        style={{
                                            fontSize: "16px",
                                            marginBottom: "0px"
                                        }}
                                    >
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

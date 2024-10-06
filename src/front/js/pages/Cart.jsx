import React, { useContext, useState } from "react";
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Table } from "react-bootstrap";
import { Notification } from "../component/Notification.jsx";
import "../../styles/cart.css";

export const Cart = () => {
    const { store, actions } = useContext(Context);
    const [notification, setNotification] = useState(null);

    const handleRemoveFromCart = (productId) => {
        actions.removeFromCart(productId);
        setNotification("Producto eliminado del carrito");
    };

    const calculateTotal = (product) => {
        const area = (parseFloat(product.height) * parseFloat(product.width)) / 10000; // cm² a m²
        return area * product.precio;
    };

    return (
        <Container className="mt-5">
            <h2 className="text-center my-4">Carrito de compra</h2>
            {store.cart.length === 0 ? (
                <p className="text-center">No tiene productos en su carrito aún.</p>
            ) : (
                <Row>
                    <Col md={{ span: 10, offset: 1 }}>
                        <Table responsive className="table-shopping-cart">
                            <thead>
                                <tr>
                                    <th>Producto</th>
                                    <th>Altura</th>
                                    <th>Anchura</th>
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
                                            <img className="cart__image" src={product.imagen} alt={product.nombre} />
                                            <div className="table-shopping-cart-item">
                                                <p className="table-shopping-cart-item-title">{product.nombre}</p>
                                                <p className="table-shopping-cart-item-description">{product.descripcion}</p>
                                            </div>
                                        </td>
                                        <td className="cart__dimension">{product.height} cm</td>
                                        <td className="cart__dimension">{product.width} cm</td>
                                        <td className="cart__mounting">{product.mounting}</td>
                                        <td className="cart__color">{product.color}</td>
                                        <td className="cart__price-wrapper">
                                            <span className="money table-shopping-cart-item-price-total">
                                                {calculateTotal(product).toFixed(2)} €
                                            </span>
                                        </td>
                                        <td className="cart_remove">
                                            <Button
                                                variant="danger"
                                                className="cart-remove-btn"
                                                onClick={() => handleRemoveFromCart(product.id)}
                                            >
                                                Eliminar
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </Table>
                    </Col>
                </Row>
            )}
            <div className="text-center mt-4">
                {store.cart.length > 0 && (
                    <Button variant="success" onClick={() => alert("Continuar con la compra no está implementado todavía")}>
                        Proceder al Pago
                    </Button>
                )}
            </div>

            {/* Notificación */}
            {notification && (
                <Notification
                    message={notification}
                    duration={3000} // Duración de 3 segundos
                    onClose={() => setNotification(null)}
                />
            )}
        </Container>
    );
};

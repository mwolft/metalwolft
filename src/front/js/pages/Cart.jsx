import React, { useContext, useState } from "react";
import { Context } from "../store/appContext";
import { Link } from "react-router-dom";
import { Button, Container, Row, Col, Card } from "react-bootstrap";
import { Notification } from "../component/Notification.jsx";

export const Cart = () => {
    const { store, actions } = useContext(Context);
    const [notification, setNotification] = useState(null);

    const handleAddToCart = (product) => {
        actions.addToCart(product);
        setNotification("Producto añadido al carrito");
    };

    const handleRemoveFromCart = (productId) => {
        actions.removeFromCart(productId);
        setNotification("Producto eliminado del carrito");
    };

    return (
        <Container className="mt-5">
            <h2 className="text-center my-4">Mi Carrito</h2>
            {store.cart.length === 0 ? (
                <p className="text-center">No tiene productos en su carrito aún.</p>
            ) : (
                <Row>
                    {store.cart.map((product, index) => (
                        <Col key={index} md={4} className="mb-4">
                            <Card>
                                <Card.Img variant="top" src={product.imagen} />
                                <Card.Body>
                                    <Card.Title>{product.nombre}</Card.Title>
                                    <Card.Text>{product.descripcion}</Card.Text>
                                    <Card.Text>Precio: {product.precio} €/m²</Card.Text>
                                    <Button
                                        variant="danger"
                                        onClick={() => handleRemoveFromCart(product.id)}
                                    >
                                        Eliminar del Carrito
                                    </Button>
                                </Card.Body>
                            </Card>
                        </Col>
                    ))}
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

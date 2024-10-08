import React, { useContext, useState, useEffect } from "react";
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Table } from "react-bootstrap";
import { Notification } from "../component/Notification.jsx";
import "../../styles/cart.css";

export const Cart = () => {
    const { store, actions } = useContext(Context);
    const [notification, setNotification] = useState(null);
    const [notes, setNotes] = useState(""); // Campo para las notas del pedido

    useEffect(() => {
        actions.loadCart();  // Asegurarnos de cargar los datos del carrito al cargar el componente
    }, []);

    // Verificar qué datos se están recibiendo
    console.log("Carrito:", store.cart);

    const handleRemoveFromCart = (product) => {
        if (!product.producto_id) {
            console.error("Error: Falta el producto_id en el carrito", product);
            return;
        }

        actions.removeFromCart({
            producto_id: product.producto_id,
            alto: product.alto,
            ancho: product.ancho,
            anclaje: product.anclaje,
            color: product.color,
            precio_total: product.precio_total,
            imagen: product.imagen
        });
        setNotification("Producto eliminado del carrito");
    };

    // Calcular el subtotal de todos los productos en el carrito
    const subtotal = store.cart.reduce((acc, product) => acc + parseFloat(product.precio_total), 0);

    return (
        <Container className="mt-5">
            <h2 className="text-center my-4">Carrito de compra</h2>
            {store.cart.length === 0 ? (
                <p className="text-center">No tiene productos en su carrito aún.</p>
            ) : (
                <Row>
                    <Col md={12} className="mx-auto">
                        <Table responsive className="table-shopping-cart">
                            <thead>
                                <tr>
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
                                            <img className="cart__image" src={product.imagen} alt={product.nombre} />
                                            <div className="table-shopping-cart-item">
                                                <p className="table-shopping-cart-item-title">{product.nombre}</p>
                                            </div>
                                        </td>
                                        <td className="cart__dimension">{product.alto}</td>
                                        <td className="cart__dimension">{product.ancho}</td>
                                        <td className="cart__mounting">{product.anclaje}</td>
                                        <td className="cart__color">{product.color}</td>
                                        <td className="cart__price-wrapper">
                                            <span className="money table-shopping-cart-item-price-total">
                                                {product.precio_total} €
                                            </span>
                                        </td>
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

                        {/* Sección del subtotal y notas */}
                        {store.cart.length > 0 && (
                            <Row className="mt-4 mb-5 mx-3">
                                <Col className="text-end"> {/* Usamos text-end para alinear todo a la derecha */}
                                    <p className="cart-total">
                                        <span className="sign">Subtotal:</span>
                                        <span className="money"> {subtotal.toFixed(2)} €</span>
                                    </p>
                                    <div className="text-end"> {/* Alineamos el botón dentro del div */}
                                        <Button
                                            className="btn-style-background-color"
                                            onClick={() => alert("Continuar con la compra no está implementado todavía")}
                                        >
                                            Pagar ahora
                                        </Button>
                                    </div>
                                </Col>
                            </Row>
                        )}
                    </Col>
                </Row>
            )}

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

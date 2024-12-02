import React, { useContext, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Context } from "../store/appContext";
import { Button, Container, Row, Col, Card, Carousel } from "react-bootstrap";

export const ProductDetail = () => {
    const { store, actions } = useContext(Context);
    const { id } = useParams();
    const navigate = useNavigate();
    const [product, setProduct] = useState(null);

    useEffect(() => {
        const fetchProduct = async () => {
            try {
                const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/products/${id}`);
                if (!response.ok) throw new Error("Producto no encontrado");
                const data = await response.json();
                setProduct(data);
            } catch (error) {
                console.error("Error al cargar el producto:", error);
                navigate("/"); // Redirigir al inicio si el producto no se encuentra
            }
        };

        fetchProduct();
    }, [id, navigate]);

    if (!product) return <div className="text-center mt-5">Cargando producto...</div>;

    const handleFavoriteClick = () => {
        if (store.isLoged) {
            if (actions.isFavorite(product)) {
                actions.removeFavorite(product.id);
            } else {
                actions.addFavorite(product);
            }
        } else {
            alert("Debe iniciar sesión para añadir a favoritos");
        }
    };

    return (
        <Container className="mt-5">
            <Row>
                <Col md={6}>
                    <Carousel>
                        {[product.imagen, ...product.images.map(img => img.image_url)].map((src, index) => (
                            <Carousel.Item key={index}>
                                <img src={src} alt={`Imagen ${index + 1}`} className="d-block w-100 img-fluid" />
                            </Carousel.Item>
                        ))}
                    </Carousel>
                </Col>
                <Col md={6}>
                    <Card>
                        <Card.Body>
                            <Card.Title>{product.nombre}</Card.Title>
                            <Card.Text>{product.descripcion}</Card.Text>
                            <Card.Text>Precio: {product.precio} €/m²</Card.Text>
                            <Button
                                variant="danger"
                                onClick={handleFavoriteClick}
                                className="me-2"
                            >
                                {actions.isFavorite(product) ? "Eliminar de Favoritos" : "Añadir a Favoritos"}
                            </Button>
                            <Button
                                variant="primary"
                                onClick={() => actions.addToCart(product)}
                            >
                                Añadir al Carrito
                            </Button>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

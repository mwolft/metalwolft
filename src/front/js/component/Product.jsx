import React, { useState, useContext } from 'react';
import "../../styles/cards-carrusel.css";
import Button from 'react-bootstrap/Button';
import Rating from 'react-rating';
import Card from 'react-bootstrap/Card';
import Modal from 'react-bootstrap/Modal';
import Carousel from 'react-bootstrap/Carousel';
import Form from 'react-bootstrap/Form';
import { Context } from "../store/appContext";
import { Notification } from "./Notification.jsx";

export const Product = ({ product }) => {
    const [showModal, setShowModal] = useState(false);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [notification, setNotification] = useState(null);
    const [height, setHeight] = useState('');
    const [width, setWidth] = useState('');
    const [mounting, setMounting] = useState('con obra');
    const [color, setColor] = useState('blanco');
    const [calculatedPrice, setCalculatedPrice] = useState(null);
    const { store, actions } = useContext(Context);

    const handleShow = () => setShowModal(true);
    const handleClose = () => setShowModal(false);

    const handleSelect = (selectedIndex) => {
        setCurrentIndex(selectedIndex);
    };

    const handleFavorite = async () => {
        if (store.isLoged) {
            if (actions.isFavorite(product)) {
                await actions.removeFavorite(product.id);
                setNotification("Producto eliminado de favoritos");
            } else {
                await actions.addFavorite(product);
                setNotification("Producto añadido a favoritos");
            }
        } else {
            setNotification("Debe registrarse para añadir favoritos");
        }
    };

    const handleAddToCart = async () => {
        if (store.isLoged) {
            if (height && width) {
                const area = (parseFloat(height) * parseFloat(width)) / 10000; // Convertir cm² a m²
                const price = area * product.precio;
    
                const productDetails = {
                    product_id: product.id,
                    alto: parseFloat(height),
                    ancho: parseFloat(width),
                    anclaje: mounting,
                    color: color,
                    precio_total: price.toFixed(2),
                };
    
                await actions.addToCart(productDetails);
                setNotification("Producto añadido al carrito");
            } else {
                setNotification("Debe ingresar altura y anchura para calcular el precio");
            }
        } else {
            setNotification("Debe registrarse para añadir productos al carrito");
        }
    };
    

    const handleCalculatePrice = () => {
        if (height && width) {
            const area = (parseFloat(height) * parseFloat(width)) / 10000; // convertir cm² a m²
            const price = area * product.precio;
            setCalculatedPrice(price.toFixed(2));
        } else {
            setNotification("Debe ingresar altura y anchura válidas");
        }
    };

    const allImages = [
        { image_url: product.imagen },
        ...product.images.filter(image => image.image_url !== product.imagen),
    ];

    return (
        <>
            <div className="col">
                <Card className="px-2 my-3" style={{ width: 'auto' }}>
                    <Card.Img variant="top" src={product.imagen} />
                    <Card.Body>
                        <h6 className="card-title">{product.nombre}</h6>
                        <p className="card-text-carrusel">
                            <span className="current-price">{product.precio} €/m²</span>
                        </p>
                        <div className="rating">
                            <Rating
                                emptySymbol="fa fa-star-o"
                                fullSymbol="fa fa-star"
                                fractions={2}
                                initialRating={4}
                                readonly
                            />
                        </div>
                        <div className="my-1 d-flex justify-content-between align-items-center">
                            <Button className="btn-style-background-color" onClick={handleShow}>
                                Ver más
                            </Button>
                            <i
                                className={`fa-regular fa-heart ${actions.isFavorite(product) ? 'fa-solid' : ''}`}
                                onClick={handleFavorite}
                                style={{ cursor: 'pointer', color: '#ff324d', fontSize: '1.5rem' }}
                            ></i>
                        </div>
                    </Card.Body>
                </Card>
            </div>

            {/* Modal */}
            <Modal show={showModal} onHide={handleClose} size="lg">
                <Modal.Header closeButton>
                    <Modal.Title className="d-flex align-items-center">
                        {product.nombre}
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Carousel activeIndex={currentIndex} onSelect={handleSelect}>
                        {allImages.map((image, index) => (
                            <Carousel.Item key={index}>
                                <img
                                    src={image.image_url}
                                    alt={`Producto ${index + 1}`}
                                    className="d-block w-100 img-fluid"
                                />
                            </Carousel.Item>
                        ))}
                    </Carousel>

                    <div className="thumbnail-gallery d-flex justify-content-center mt-3">
                        {allImages.map((image, index) => (
                            <img
                                key={index}
                                src={image.image_url}
                                alt={`Producto Miniatura ${index + 1}`}
                                className={`img-thumbnail mx-1 ${currentIndex === index ? 'active-thumbnail' : ''}`}
                                style={{ width: '80px', height: '80px', cursor: 'pointer' }}
                                onClick={() => handleSelect(index)}
                            />
                        ))}
                    </div>

                    <div className="product-details mt-4">
                        <h5>Precio: {product.precio} €/m²</h5>
                        <p>{product.descripcion}</p>
                        <div className="rating">
                            <Rating
                                emptySymbol="fa fa-star-o"
                                fullSymbol="fa fa-star"
                                fractions={2}
                                initialRating={product.rating || 4}
                                readonly
                            />
                        </div>

                        <Form className="mt-4">
                            <Form.Group controlId="height">
                                <Form.Label>Altura (cm)</Form.Label>
                                <Form.Control
                                    type="number"
                                    value={height}
                                    onChange={(e) => setHeight(e.target.value)}
                                    placeholder="Ingrese la altura en cm"
                                />
                            </Form.Group>
                            <Form.Group controlId="width" className="mt-2">
                                <Form.Label>Anchura (cm)</Form.Label>
                                <Form.Control
                                    type="number"
                                    value={width}
                                    onChange={(e) => setWidth(e.target.value)}
                                    placeholder="Ingrese la anchura en cm"
                                />
                            </Form.Group>
                            <Form.Group controlId="mounting" className="mt-2">
                                <Form.Label>Tipo de anclaje</Form.Label>
                                <Form.Control
                                    as="select"
                                    value={mounting}
                                    onChange={(e) => setMounting(e.target.value)}
                                >
                                    <option value="con obra">Con obra</option>
                                    <option value="sin obra">Sin obra</option>
                                </Form.Control>
                            </Form.Group>
                            <Form.Group controlId="color" className="mt-2">
                                <Form.Label>Color</Form.Label>
                                <Form.Control
                                    as="select"
                                    value={color}
                                    onChange={(e) => setColor(e.target.value)}
                                >
                                    <option value="blanco">Blanco</option>
                                    <option value="negro">Negro</option>
                                    <option value="gris">Gris</option>
                                    <option value="verde">Verde</option>
                                    <option value="marrón">Marrón</option>
                                </Form.Control>
                            </Form.Group>
                            <Button className="btn-style-background-color mt-3" onClick={handleCalculatePrice}>
                                Calcular precio
                            </Button>
                        </Form>

                        {calculatedPrice && (
                            <h5 className="mt-3">Precio calculado: {calculatedPrice} €</h5>
                        )}
                    </div>
                </Modal.Body>
                <Modal.Footer className="d-flex justify-content-between align-items-center">
                    <i
                        className={`fa-regular fa-heart ${actions.isFavorite(product) ? 'fa-solid' : ''}`}
                        onClick={handleFavorite}
                        style={{ cursor: 'pointer', color: '#ff324d', fontSize: '1.5rem' }}
                    ></i>
                    <Button className="btn-style-background-color" onClick={handleAddToCart}>
                        Añadir al carrito
                    </Button>
                </Modal.Footer>
            </Modal>

            {/* Notificación */}
            {notification && (
                <Notification
                    message={notification}
                    duration={3000}
                    onClose={() => setNotification(null)}
                />
            )}
        </>
    );
};

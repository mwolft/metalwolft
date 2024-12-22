import React, { useState, useContext } from 'react';
import { Link } from "react-router-dom";
import "../../styles/cards-carrusel.css";
import Button from 'react-bootstrap/Button';
import Rating from 'react-rating';
import Card from 'react-bootstrap/Card';
import Modal from 'react-bootstrap/Modal';
import Carousel from 'react-bootstrap/Carousel';
import Form from 'react-bootstrap/Form';
import { Context } from "../store/appContext";
import { Notification } from "./Notification.jsx";
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Popover from 'react-bootstrap/Popover';
import AlbanyImg from '../../img/rejas-para-ventanas-sin-obra.png'

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
                const area = (parseFloat(height) * parseFloat(width)) / 10000;
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

                // Reset values after adding to cart
                setHeight('');
                setWidth('');
                setMounting('con obra');
                setColor('blanco');
            } else {
                setNotification("Debe ingresar altura y anchura para calcular el precio");
            }
        } else {
            setNotification("Debe registrarse para añadir productos al carrito");
        }
    };

    const handleCalculatePrice = () => {
        if (height && width) {
            const area = (parseFloat(height) * parseFloat(width)) / 10000;
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
                        <h3 className="card-title" style={{fontSize: '14px'}}>{product.nombre}</h3>
                        <p className="card-text-carrusel">
                            <span className="current-price">{product.precio} €/m²</span>
                        </p>
                        <div className="my-1 d-flex justify-content-between align-items-center">
                            <Button className="btn-style-background-color" onClick={handleShow}>
                                Comprar
                            </Button>
                            <i className={`fa-regular fa-heart ${actions.isFavorite(product) ? 'fa-solid' : ''}`}
                                onClick={handleFavorite}
                                style={{ cursor: 'pointer', color: '#ff324d', fontSize: '1.5rem' }}>
                            </i>
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
                    <div className="row">
                        <div className="col-lg-6 col-md-6 mb-4 mb-md-0">
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
                        </div>
                        <div className="col-lg-6 col-md-6">
                            <div className="pr_detail">
                                <h5>Precio: {product.precio} €/m²</h5>
                                <p>{product.descripcion}</p>
                                <div className="d-flex mt-4">
                                    <Form.Group controlId="height" className="me-3" style={{ flex: 1 }}>
                                        <Form.Label>Alto (cm):</Form.Label>
                                        <Form.Control
                                            type="number"
                                            value={height}
                                            onChange={(e) => setHeight(e.target.value)}
                                            placeholder="cm" />
                                    </Form.Group>
                                    <Form.Group controlId="width" style={{ flex: 1 }}>
                                        <Form.Label>Ancho (cm):</Form.Label>
                                        <Form.Control
                                            type="number"
                                            value={width}
                                            onChange={(e) => setWidth(e.target.value)}
                                            placeholder="cm" />
                                    </Form.Group>
                                </div>
                                <div className="d-flex mt-2">
                                    <Form.Group controlId="mounting" className="me-3" style={{ flex: 1 }}>
                                        <OverlayTrigger
                                            trigger={['hover', 'focus']}
                                            placement="top"
                                            rootClose={false}
                                            overlay={
                                                <Popover id="popover-mounting">
                                                    <Popover.Header as="h3">Instalación de rejas para ventanas</Popover.Header>
                                                    <Popover.Body>
                                                        <p className='p-popover'>
                                                            <span style={{ textDecoration: 'underline', fontWeight: 'bold' }}>Sin obra: </span>
                                                            Tornillos Inviolables.
                                                        </p>
                                                        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSWeCVUg3hSyUQj2YKAzXEAScWZ170dqvQ_mQ&s"
                                                                style={{ width: '70px', height: 'auto', marginBottom: '10px', marginTop: '5px'}}
                                                                alt="rejas para ventanas sin obra" />
                                                        <p className='p-popover'>
                                                            <span style={{ textDecoration: 'underline', fontWeight: 'bold' }}>Con obra: </span>
                                                            Anclaje con garras.
                                                        </p>
                                                            <img src={AlbanyImg}
                                                                style={{ width: '110px', height: 'auto', marginBottom: '10px', marginTop: '5px'}}
                                                                alt="rejas para ventanas con obra" />
                                                    </Popover.Body>
                                                </Popover>
                                            }
                                        >
                                            <Form.Label>
                                                Instalación: <i className="fa-solid fa-info-circle ms-2" style={{ color: '#007bff', cursor: 'pointer' }}></i>
                                            </Form.Label>
                                        </OverlayTrigger>
                                        <Form.Control
                                            as="select"
                                            value={mounting}
                                            onChange={(e) => setMounting(e.target.value)}
                                        >
                                            <option value="sin obra">Sin obra</option>
                                            <option value="con obra">Con obra</option>
                                        </Form.Control>
                                    </Form.Group>
                                    <Form.Group controlId="color" style={{ flex: 1 }}>
                                        <Form.Label>Color:</Form.Label>
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
                                </div>
                                <Button className="btn-style-background-color mt-3" onClick={handleCalculatePrice}>
                                    <i className="fa-solid fa-calculator" style={{ marginRight: '7px' }}></i> Calcular precio
                                </Button>
                                {calculatedPrice && (
                                    <h5 className="mt-3">Precio calculado: {calculatedPrice} €</h5>
                                )}
                            </div>
                        </div>
                    </div>
                </Modal.Body>
                <Modal.Footer className="d-flex justify-content-end align-items-center">
                    <i
                        className={`fa-regular fa-heart ${actions.isFavorite(product) ? 'fa-solid' : ''}`}
                        onClick={handleFavorite}
                        style={{ cursor: 'pointer', color: '#ff324d', fontSize: '1.5rem', marginRight: '5px' }}>
                    </i>
                    <Button className="btn-style-background-color" onClick={handleAddToCart}>
                        <i className="fa-solid fa-cart-shopping" style={{ marginRight: '7px' }}></i> Añadir al carrito
                    </Button>
                </Modal.Footer>
            </Modal>

            {/* Notification */}
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

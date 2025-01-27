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
import { Helmet } from "react-helmet";

export const Product = ({ product }) => {
    const [showModal, setShowModal] = useState(false);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [notification, setNotification] = useState(null);
    const [height, setHeight] = useState('');
    const [width, setWidth] = useState('');
    const [mounting, setMounting] = useState('Sin obra: con pletinas');
    const [color, setColor] = useState('blanco');
    const [calculatedPrice, setCalculatedPrice] = useState(null);
    const { store, actions } = useContext(Context);

    const handleShow = () => setShowModal(true);
    const handleClose = () => setShowModal(false);

    const [isHovered, setIsHovered] = useState(false);

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
                const pricePerM2 = product.precio_rebajado || product.precio; 
                let price = area * pricePerM2;


                // Aplicar precio mínimo de 50€
                if (price < 50) {
                    price = 50;
                }

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

                // Reset valores después de añadir al carrito
                setHeight('');
                setWidth('');
                setMounting('Sin obra: con pletinas');
                setColor('blanco');
            } else {
                setNotification("Debe ingresar altura y anchura para calcular el precio");
            }
        } else {
            setNotification("Debe registrarse para añadir productos al carrito");
        }
    };


    const handleCalculatePrice = () => {
        const parsedHeight = parseFloat(height);
        const parsedWidth = parseFloat(width);
    
        if (isNaN(parsedHeight) || isNaN(parsedWidth)) {
            setNotification("Debe ingresar altura y anchura válidas");
            return;
        }
    
        if (parsedHeight < 20 || parsedWidth < 20) {
            setNotification("El alto y el ancho deben ser al menos 20 cm");
            return;
        }
    
        // Seleccionar el precio correcto
        const basePricePerM2 = product.precio_rebajado || product.precio;
    
        // Cálculo base
        const area = (parsedHeight * parsedWidth) / 10000; // Área en metros cuadrados
        let price = area * basePricePerM2;
    
        // Aplicar precio mínimo o ajustes
        const basePrice = 50; // Precio mínimo por producto (puedes ajustarlo)
        const smallAreaMultiplier = area < 0.5 ? 1.2 : 1; // Multiplicador para áreas pequeñas (< 0.5 m²)
    
        price = Math.max(price * smallAreaMultiplier, basePrice);
    
        setCalculatedPrice(price.toFixed(2));
    };

    
    const determinePlacement = () => {
        return window.innerWidth > 768 ? "right" : "top";
    };


    const allImages = [
        { image_url: product.imagen },
        ...product.images.filter(image => image.image_url !== product.imagen),
    ];

    const formatPrice = (price) => {
        return Number.isInteger(price) ? price : price.toFixed(2);
    };

    return (
        <>
            <div className="col">
                <Card className="px-2 my-3">
                    <div
                        style={{
                            position: "relative",
                            width: "100%",
                            height: "auto",
                            overflow: "hidden",
                            cursor: "pointer",
                        }}
                        onClick={handleShow}
                        onMouseEnter={() => setIsHovered(true)}
                        onMouseLeave={() => setIsHovered(false)}
                    >
                        <Card.Img
                            variant="top"
                            src={product.imagen}
                            alt={product.nombre}
                            className="img-fluid"
                            style={{
                                objectFit: "cover",
                                maxHeight: "600px",
                                transition: "transform 0.3s ease-in-out",
                                transform: isHovered ? "scale(1.1)" : "scale(1)",
                                filter: isHovered ? "brightness(50%)" : "brightness(100%)",
                            }}
                            loading="lazy"
                        />
                        {product.precio_rebajado && (
                            <div
                                style={{
                                    position: "absolute",
                                    top: "10px",
                                    left: "10px",
                                    backgroundColor: "#28a745",
                                    color: "#fff",
                                    padding: "4px 8px",
                                    borderRadius: "4px",
                                    fontSize: "12px",
                                    fontWeight: "bold",
                                    zIndex: 10,
                                }}
                            >
                                En oferta
                            </div>
                        )}
                        <div
                            style={{
                                position: "absolute",
                                top: "0",
                                left: "0",
                                width: "100%",
                                height: "100%",
                                display: "flex",
                                justifyContent: "center",
                                alignItems: "center",
                                backgroundColor: "rgba(0, 0, 0, 0.05)",
                                opacity: isHovered ? "1" : "0",
                                transition: "opacity 0.3s ease-in-out",
                            }}
                        >
                            <i
                                className="fa-solid fa-magnifying-glass-plus"
                                style={{
                                    color: "white",
                                    fontSize: "2rem",
                                }}
                            ></i>
                        </div>
                    </div>
                    <Card.Body>
                        <h3
                            className="card-title"
                            style={{ fontSize: '14px', cursor: 'pointer' }}
                            onClick={handleShow}
                        >
                            {product.nombre}
                        </h3>
                        <p className="card-text-carrusel">
                            {product.precio_rebajado ? (
                                <>
                                    <span className="price-original" style={{ textDecoration: 'line-through', color: '#999' }}>
                                        {formatPrice(product.precio)} €
                                    </span>
                                    <span className="price-discounted" style={{ color: '#e63946', fontWeight: 'bold', marginLeft: '8px' }}>
                                        {formatPrice(product.precio_rebajado)}€/m²
                                    </span>
                                    <span className="discount-percentage" style={{ color: '#28a745', padding: '2px 6px', marginLeft: '2px' }}>
                                        -{product.porcentaje_rebaja}%
                                    </span>
                                </>
                            ) : (
                                <span className="current-price">{formatPrice(product.precio)} €/m²</span>
                            )}
                        </p>
                        <div className="my-1 d-flex justify-content-between align-items-center">
                            <Button className="btn-style-background-color" onClick={handleShow}>
                                Detalles
                            </Button>
                            <i className={`fa-regular fa-heart ${actions.isFavorite(product) ? 'fa-solid' : ''}`}
                                onClick={handleFavorite}
                                style={{ cursor: 'pointer', color: '#ff324d', fontSize: '1.5rem', marginLeft: '5px' }}>
                            </i>
                        </div>
                    </Card.Body>
                </Card>
            </div>

            {/* Modal */}
            <Modal show={showModal} onHide={handleClose} size="lg" style={{ zIndex: 2000 }} backdropClassName="custom-backdrop">
                <Modal.Header closeButton>
                    <Modal.Title className="d-flex align-items-center">
                        {product.nombre}
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <div className="row">
                        <div className="col-lg-6 col-md-6 mb-4 mb-md-0">
                            {allImages.slice(0, 1).map((image, index) => (
                                <Helmet key={index}>
                                    <link
                                        rel="preload"
                                        as="image"
                                        href={image.image_url}
                                    />
                                </Helmet>
                            ))}
                            <Carousel activeIndex={currentIndex} onSelect={handleSelect}>
                                {allImages.map((image, index) => (
                                    <Carousel.Item key={index}>
                                        <img
                                            src={image.image_url}
                                            alt={`${product.nombre}`}
                                            className="d-block w-100 img-fluid"
                                            loading={index === 0 ? "eager" : "lazy"}
                                            width="540"
                                            height="600"
                                        />
                                    </Carousel.Item>
                                ))}
                            </Carousel>
                            <div className="thumbnail-gallery d-flex justify-content-center mt-3">
                                {allImages.map((image, index) => (
                                    <img
                                        key={index}
                                        src={image.image_url}
                                        alt={`${product.nombre}`}
                                        className={`img-thumbnail mx-1 ${currentIndex === index ? 'active-thumbnail' : ''}`}
                                        style={{ width: '72px', height: '80px', cursor: 'pointer' }}
                                        onClick={() => handleSelect(index)}
                                    />
                                ))}
                            </div>
                        </div>
                        <div className="col-lg-6 col-md-6">
                            <div className="pr_detail">
                                <h5>
                                    Precio:
                                    {product.precio_rebajado ? (
                                        <>
                                            <span className="price-original" style={{ textDecoration: 'line-through', color: '#999', marginLeft: '8px' }}>
                                                {formatPrice(product.precio)} €
                                            </span>
                                            <span className="price-discounted" style={{ color: '#e63946', fontWeight: 'bold', marginLeft: '8px' }}>
                                                {formatPrice(product.precio_rebajado)}€/m²
                                            </span>
                                            <span className="discount-percentage" style={{ color: '#28a745', padding: '2px 6px', marginLeft: '8px' }}>
                                                -{product.porcentaje_rebaja}% 
                                            </span>
                                        </>
                                    ) : (
                                        <span className="current-price" style={{ marginLeft: '8px' }}>{formatPrice(product.precio)} €/m²</span>
                                    )}
                                </h5>
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
                                            placement={determinePlacement()}
                                            rootClose={false}
                                            overlay={
                                                <Popover id="popover-mounting">
                                                    <Popover.Header as="h3">Instalación de rejas para ventanas</Popover.Header>
                                                    <Popover.Body>
                                                        <p className='p-popover'>
                                                            <span style={{ textDecoration: 'underline', fontWeight: 'bold' }}>Sin obra: </span>
                                                            con pletinas. <br /><b>(Opción recomendada)</b>
                                                        </p>
                                                        <img src="https://res.cloudinary.com/dewanllxn/image/upload/v1737278219/albany-pletinas-_e4ct2v.png"
                                                            style={{ width: '110px', height: 'auto', marginBottom: '10px', marginTop: '5px' }}
                                                            alt="rejas para ventanas sin obra" />
                                                        <p className='p-popover'>
                                                            <span style={{ textDecoration: 'underline', fontWeight: 'bold' }}>Sin obra: </span>
                                                            con agujeros interiores. <br /> (Recomendada si no hay espacio en la profundidad del muro)
                                                        </p>
                                                        <img src="https://res.cloudinary.com/dewanllxn/image/upload/v1737278219/albany-agujeros-interiores_akhaeg.png"
                                                            style={{ width: '110px', height: 'auto', marginBottom: '10px', marginTop: '5px' }}
                                                            alt="rejas para ventanas sin obra" />
                                                        <p className='p-popover'>
                                                            <span style={{ textDecoration: 'underline', fontWeight: 'bold' }}>Con obra: </span>
                                                            con garras metálicas. <br />(Recomendada para muro en construcción)
                                                        </p>
                                                        <img src="https://res.cloudinary.com/dewanllxn/image/upload/v1734888241/rejas-para-ventanas-sin-obra_wukdzi.png"
                                                            style={{ width: '110px', height: 'auto', marginBottom: '10px', marginTop: '5px' }}
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
                                            <option value="Sin obra: con agujeros interiores">Sin obra: con agujeros interiores</option>
                                            <option value="Sin obra: con pletinas">Sin obra: con pletinas</option>
                                            <option value="Con obra: con garras metálicas">Con obra: con garras metálicas</option>
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
                                    <>
                                        <h5 className="mt-3">Precio calculado: {calculatedPrice} €</h5>
                                        {calculatedPrice <= 50 && (
                                            <p className="text-warning mt-2">
                                                Precio mínimo por producto.
                                            </p>
                                        )}
                                    </>
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

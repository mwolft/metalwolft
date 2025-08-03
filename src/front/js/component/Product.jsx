import React, { useState, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
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
import AlbanyImg from '../../img/rejas-para-ventanas-sin-obra.png';
import { Helmet } from "react-helmet-async";

export const Product = ({ product }) => {
    const navigate = useNavigate();
    const [showModal, setShowModal] = useState(false);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [notification, setNotification] = useState(null);
    const [height, setHeight] = useState('');
    const [width, setWidth] = useState('');
    const [mounting, setMounting] = useState('Sin obra: con pletinas');
    const [color, setColor] = useState('blanco');
    const [calculatedPrice, setCalculatedPrice] = useState(null);
    const [calcError, setCalcError] = useState("");
    const [calculatedArea, setCalculatedArea] = useState(null);

    const { store, actions } = useContext(Context);
    const productDetailUrl = `/${product.category_slug}/${product.slug}`;
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
        if (!store.isLoged) {
            setNotification("Debe registrarse para añadir productos al carrito");
            return;
        }
        if (!height || !width) {
            setNotification("Debe ingresar altura y anchura para calcular el precio");
            return;
        }
        if (!calculatedPrice) {
            setNotification("Primero calcule el precio");
            return;
        }
        const productDetails = {
            product_id: product.id,
            alto: parseFloat(height),
            ancho: parseFloat(width),
            anclaje: mounting,
            color: color,
            precio_total: calculatedPrice
        };
        await actions.addToCart(productDetails);
        setNotification("Producto añadido al carrito");
        // Reset
        setHeight('');
        setWidth('');
        setMounting('Sin obra: con pletinas');
        setColor('blanco');
    };

    const handleCalculatePrice = () => {
        const h = parseFloat(height), w = parseFloat(width);
        if (isNaN(h) || isNaN(w)) {
            setNotification("Debe ingresar altura y anchura válidas");
            return;
        }
        if (h < 30 || w < 30) {
            setNotification("El alto y el ancho deben ser al menos 30 cm");
            return;
        }
        if (h > 200 || w > 200 || h + w > 300) {
            setNotification("Dimensiones fuera de rango permitido");
            return;
        }
        const base = product.precio_rebajado || product.precio;
        const area = (h * w) / 10000;
        setCalculatedArea(area);
        let price = area * base;
        const basePrice = 80;
        let multiplier = area >= 0.9 ? 1
            : area >= 0.8 ? 1.1
                : area >= 0.7 ? 1.15
                    : area >= 0.6 ? 1.2
                        : area >= 0.5 ? 1.3
                            : area >= 0.4 ? 1.55
                                : area >= 0.3 ? 1.9
                                    : area >= 0.2 ? 2.5
                                        : 3.0;
        price = Math.max(price * multiplier, basePrice);
        setCalculatedPrice(price.toFixed(2));
    };

    const determinePlacement = () =>
        window.innerWidth > 768 ? "right" : "top";

    const allImages = [
        { image_url: product.imagen },
        ...product.images.filter(img => img.image_url !== product.imagen)
    ];

    const formatPrice = price =>
        Number.isInteger(price) ? price : price.toFixed(2);

    return (
        <>
            <div className="w-100 h-100">
                <Card className="h-100 d-flex flex-column px-0 my-3">
                    <Link
                        to={productDetailUrl}
                        style={{
                            position: "relative",
                            width: "100%",
                            height: "auto",
                            overflow: "hidden",
                            cursor: "pointer",
                        }}
                    >
                        <Card.Img
                            variant="top"
                            src={product.imagen}
                            alt={product.nombre}
                            width="540"
                            height="600"
                            className="img-fluid card-img-top"
                            style={{
                                objectFit: "cover",
                                width: "100%",
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
                                <i className="fa-solid fa-tag"></i> En oferta
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
                        {(product.has_abatible || product.has_door_model) && (
                            <div style={{
                                position: 'absolute',
                                bottom: '3px',
                                right: '3px',
                                backgroundColor: '#2b2d42',
                                color: '#fff',
                                padding: '4px 4px',
                                borderRadius: '4px',
                                fontSize: '6px',
                                fontWeight: 'bold',
                                zIndex: 10,
                                textAlign: 'center'
                            }}>
                                {product.has_abatible && <div>Disponible abatible <i className="fa-solid fa-door-open"></i></div>}
                                {product.has_door_model && <div>Disponible en versión para puerta</div>}
                            </div>
                        )}
                    </Link>
                    <Card.Body>
                        <Link to={productDetailUrl} style={{ textDecoration: 'none', color: 'inherit' }}>
                            <h3
                                className="card-title"
                                style={{ fontSize: 14, cursor: 'pointer' }}
                            >
                                {product.nombre}
                            </h3>
                        </Link>
                        <p className="card-text-carrusel">
                            {product.precio_rebajado ? (
                                <>
                                    <span className="price-original" style={{ textDecoration: 'line-through', color: '#999' }}>
                                        {formatPrice(product.precio)}
                                    </span>
                                    <span className="price-discounted" style={{ color: '#e63946', fontWeight: 'bold', marginLeft: '8px' }}>
                                        {formatPrice(product.precio_rebajado)}€/m²
                                    </span>
                                    <span className="discount-percentage" style={{ color: '#28a745', padding: '2px 6px', marginLeft: '2px' }}>
                                        -{Math.round(product.porcentaje_rebaja)}%
                                    </span>
                                </>
                            ) : (
                                <span className="current-price">{formatPrice(product.precio)} €/m²</span>
                            )}
                        </p>
                        <div className="d-flex justify-content-between align-items-center">
                            <Link to={productDetailUrl} className="btn-style-background-color" style={{ textDecoration: 'none' }}>
                                <i className="fa-solid fa-calculator"></i> Más
                            </Link>
                            <i className={`fa-regular fa-heart ${actions.isFavorite(product) ? 'fa-solid' : ''}`}
                                onClick={handleFavorite}
                                style={{ cursor: 'pointer', color: '#ff324d', fontSize: '1.5rem', marginLeft: '5px' }}>
                            </i>
                        </div>
                    </Card.Body>
                </Card>
            </div>

        </>
    );
};

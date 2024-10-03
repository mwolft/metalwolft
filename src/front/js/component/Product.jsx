import React, { useState, useContext } from 'react'; 
import "../../styles/cards-carrusel.css";
import Button from 'react-bootstrap/Button';
import Rating from 'react-rating';
import Card from 'react-bootstrap/Card';
import Modal from 'react-bootstrap/Modal';
import Carousel from 'react-bootstrap/Carousel';
import { Context } from "../store/appContext";

export const Product = ({ product }) => {
    const [showModal, setShowModal] = useState(false);
    const [currentIndex, setCurrentIndex] = useState(0);
    const { store, actions } = useContext(Context);

    const handleShow = () => setShowModal(true);
    const handleClose = () => setShowModal(false);

    const handleSelect = (selectedIndex) => {
        setCurrentIndex(selectedIndex);
    };

    const handleFavorite = () => {
        if (store.isLoged) {
            if (actions.isFavorite(product)) {
                actions.removeFavorite(product.id);
                alert('Producto eliminado de favoritos');
            } else {
                actions.addFavorite(product);
                alert('Producto añadido a favoritos');
            }
        } else {
            alert('Debe registrarse para añadir favoritos');
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
                                style={{ cursor: 'pointer', color: 'red', fontSize: '1.5rem' }}
                            ></i>
                        </div>
                    </Card.Body>
                </Card>
            </div>

            {/* Modal */}
            <Modal show={showModal} onHide={handleClose} size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>{product.nombre}</Modal.Title>
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
                    </div>
                </Modal.Body>
                <Modal.Footer>
                    <Button className="btn-style-background-color">
                        Añadir al carrito
                    </Button>
                </Modal.Footer>
            </Modal>
        </>
    );
};

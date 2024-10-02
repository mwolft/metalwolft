import React, { useState } from 'react';
import "../../styles/cards-carrusel.css";
import Button from 'react-bootstrap/Button';
import Rating from 'react-rating';
import Card from 'react-bootstrap/Card';
import Modal from 'react-bootstrap/Modal';
import Carousel from 'react-bootstrap/Carousel';

export const Product = ({ product }) => {
    const [showModal, setShowModal] = useState(false);
    const [currentIndex, setCurrentIndex] = useState(0);

    const handleShow = () => setShowModal(true);
    const handleClose = () => setShowModal(false);

    const handleSelect = (selectedIndex) => {
        setCurrentIndex(selectedIndex);
    };

    const allImages = [
        { image_url: product.imagen }, // Incluimos la imagen principal
        ...product.images.filter(image => image.image_url !== product.imagen), // Imágenes adicionales sin duplicar la principal
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
                        <div className="my-1">
                            <Button className="btn-style-background-color" onClick={handleShow}>
                                Ver más
                            </Button>
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
                    {/* Carrusel con imágenes */}
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

                    {/* Miniaturas debajo del carrusel */}
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

                    {/* Detalles del producto */}
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

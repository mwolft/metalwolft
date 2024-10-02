import React from 'react';
import "../../styles/cards-carrusel.css";
import Button from 'react-bootstrap/Button';
import Rating from 'react-rating';
import Card from 'react-bootstrap/Card';

export const Product = ({ product }) => {
    return (
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
                        <Button className="btn-style-background-color">Ver más</Button>{' '}
                    </div>
                </Card.Body>
            </Card>
        </div>
    );
};

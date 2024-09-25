import React from 'react';
import Button from 'react-bootstrap/Button';
import "../../styles/cards-carrusel.css";
import OwlCarousel from 'react-owl-carousel';
import 'owl.carousel/dist/assets/owl.carousel.css';
import 'owl.carousel/dist/assets/owl.theme.default.css';
import albanyImage from "../../img/cards-carrusel/rejas-para-ventanas.avif";
import Rating from 'react-rating'; 

export const CardsCarrusel = () => {
    const options = {
        margin: 10,
        responsive: {
            0: { items: 1 },
            481: { items: 2 },
            768: { items: 3 },
            1199: { items: 4 }
        },
        nav: false,
        dots: true,
        loop: true
    };

    return (
        <div className="container mb-5">
            <div className="row">
                <OwlCarousel className='owl-theme' {...options}>
                    {[1, 2, 3, 4, 5, 6].map((item) => (
                        <div className="item p-2 mb-5" key={item}>
                            <div className="card-carrusel bg-light">
                                <div className="card-body-carrusel">
                                    <img src={albanyImage} alt="Rejas para ventanas" />
                                </div>
                                <div className="card-body-carrusel-info">
                                    <h6 className="card-title">Rejas Albany</h6>
                                    <p className="card-text-carrusel">
                                        <span className="current-price">120€/m²</span>
                                        <span className="discounted-price">150€/m2</span>
                                        <span className="discount-percent">20% OFF</span>
                                    </p>
                                    <div className="rating">
                                        <Rating
                                            emptySymbol="fa fa-star-o"
                                            fullSymbol="fa fa-star"
                                            fractions={2}
                                            initialRating={4} // Ajusta la puntuación inicial aquí
                                            readonly // Pone el rating en modo solo lectura
                                        />
                                    </div>
                                    <div className="my-1">
                                        <Button className="btn-style-background-color">ver</Button>{' '}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </OwlCarousel>
            </div>
        </div>
    );
};

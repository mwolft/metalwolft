import React from 'react';
import "../../styles/cards-carrusel.css";
import OwlCarousel from 'react-owl-carousel';
import 'owl.carousel/dist/assets/owl.carousel.css';
import 'owl.carousel/dist/assets/owl.theme.default.css';
import albanyImage from "../../img/cards-carrusel/rejas-para-ventanas.avif";

export const CardsCarrusel = () => {
    const options = {
        margin: 10,
        responsive: {
            0: {
                items: 1
            },
            481: {
                items: 2
            },
            768: {
                items: 3
            },
            1199: {
                items: 4
            }
        },
        nav: false,  
        dots: true,  
        loop: true
    };

    return (
        <div className="container mb-5">
            <div className="row">
                <OwlCarousel className='owl-theme' {...options}>
                    <div className="item">
                        <div className="card">
                            <div className="card-body bg-light">
                                <img src={albanyImage} alt="Rejas para ventanas" />
                            </div>
                        </div>
                    </div>
                    <div className="item">
                        <div className="card">
                            <div className="card-body bg-light">
                                <img src={albanyImage} alt="Rejas para ventanas" />
                            </div>
                        </div>
                    </div>
                    <div className="item">
                        <div className="card">
                            <div className="card-body bg-light">
                                <img src={albanyImage} alt="Rejas para ventanas" />
                            </div>
                        </div>
                    </div>
                    <div className="item">
                        <div className="card">
                            <div className="card-body bg-light">
                                <img src={albanyImage} alt="Rejas para ventanas" />
                            </div>
                        </div>
                    </div>
                    <div className="item">
                        <div className="card">
                            <div className="card-body bg-light">
                                <img src={albanyImage} alt="Rejas para ventanas" />
                            </div>
                        </div>
                    </div>
                    <div className="item">
                        <div className="card">
                            <div className="card-body bg-light">
                                <img src={albanyImage} alt="Rejas para ventanas" />
                            </div>
                        </div>
                    </div>
                    <div className="item">
                        <div className="card">
                            <div className="card-body bg-light">
                                <img src={albanyImage} alt="Rejas para ventanas" />
                            </div>
                        </div>
                    </div>
                    <div className="item">
                        <div className="card">
                            <div className="card-body bg-light">
                                <img src={albanyImage} alt="Rejas para ventanas" />
                            </div>
                        </div>
                    </div>
                    <div className="item">
                        <div className="card">
                            <div className="card-body bg-light">
                                <img src={albanyImage} alt="Rejas para ventanas" />
                            </div>
                        </div>
                    </div>
                    <div className="item">
                        <div className="card">
                            <div className="card-body bg-light">
                                <img src={albanyImage} alt="Rejas para ventanas" />
                            </div>
                        </div>
                    </div>
                </OwlCarousel>
            </div>
        </div>
    );
};

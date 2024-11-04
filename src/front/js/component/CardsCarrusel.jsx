import React, { useEffect, useContext, useState } from 'react';
import Button from 'react-bootstrap/Button';
import "../../styles/cards-carrusel.css";
import OwlCarousel from 'react-owl-carousel';
import 'owl.carousel/dist/assets/owl.carousel.css';
import 'owl.carousel/dist/assets/owl.theme.default.css';
import { Context } from "../store/appContext.js";
import { useNavigate } from "react-router-dom";

export const CardsCarrusel = ({ currentCategoryId = null }) => {
    const { store, actions } = useContext(Context);
    const [categoriesForCarousel, setCategoriesForCarousel] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchCategories = async () => {
            const categories = await actions.getOtherCategories(currentCategoryId);
            setCategoriesForCarousel(categories);
        };
        fetchCategories();
    }, [currentCategoryId]);

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

    const handleCategoryNavigation = (categorySlug) => {
        navigate(`/${categorySlug}`);
    };

    return (
        <div className="container mb-5">
            <div className="row">
                <OwlCarousel className='owl-theme' {...options}>
                    {categoriesForCarousel.length > 0 ? (
                        categoriesForCarousel.map((category, index) => (
                            <div className="item p-2 mb-5" key={index}>
                                <div className="card-carrusel bg-light">
                                    <div className="card-body-carrusel">
                                        <img
                                            src={category.image_url || "/path/to/default/image.jpg"}
                                            alt={category.nombre}
                                            style={{ width: '100%', height: '300px', objectFit: 'cover'}}/>
                                    </div>
                                    <div className="card-body-carrusel-info">
                                        <h6 className="card-title">{category.nombre}</h6>
                                        <div className="my-1">
                                            <Button
                                                className="btn-style-background-color"
                                                onClick={() => handleCategoryNavigation(category.slug)}
                                            >
                                                Ver
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <p>Cargando categorías...</p>
                    )}
                </OwlCarousel>
            </div>
        </div>
    );
};

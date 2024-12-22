import React, { useEffect, useContext, useState } from "react";
import { Context } from "../store/appContext.js";
import { useNavigate } from "react-router-dom";
import "../../styles/categories-pages.css";

export const AsideOthersCategories = ({ currentCategoryId }) => {
    const { store, actions } = useContext(Context);
    const [otherCategories, setOtherCategories] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchOtherCategories = async () => {
            const categories = await actions.getOtherCategories(currentCategoryId);
            setOtherCategories(categories);
        };
        fetchOtherCategories();
    }, [currentCategoryId]);

    const handleCategoryNavigation = (categorySlug) => {
        navigate(`/${categorySlug}`);
    };
    
    return (
        <aside className="widget my-5">
            <h2 className="widget_title">Otras Categorías</h2>
            <hr className="hr-home" />
            {otherCategories.length > 0 ? (
                <ul className="widget_categories">
                    {otherCategories.map((category, index) => (
                        <li key={index} className="others-categories">
                            <img 
                                className="img-other-categories" 
                                src={category.image_url || "/path/to/default/image.jpg"} 
                                alt={category.nombre} 
                                style={{
                                    width: "80px",
                                    height: "100%",
                                    objectFit: "cover"
                                }}
                            />
                            <p className="p-other-categories">
                                {category.nombre}<br />
                                <button 
                                    className="buton-other-categories" 
                                    onClick={() => handleCategoryNavigation(category.slug)}
                                    aria-label={`Ir a categoría ${category.nombre}`}
                                >
                                    Ir a categoría
                                </button>
                            </p>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>Cargando otras categorías...</p>
            )}
        </aside>
    );    
};

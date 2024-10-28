import React, { useEffect, useContext } from "react";
import { Context } from "../store/appContext.js";
import { useNavigate } from "react-router-dom";

export const AsideCategories = () => {
    const { store, actions } = useContext(Context);
    const navigate = useNavigate();

    useEffect(() => {
        actions.getCategories();  // Carga las categorías cuando se monta el componente
    }, []);

    const handleCategoryClick = (categoryId) => {
        actions.fetchProducts(categoryId);  // Filtra productos por categoría
        navigate("/products");  // Redirige a la página de productos si es necesario
    };

    return (
        <div className="widget">
            <h5 className="widget_title">Categories</h5>
            <ul className="widget_categories">
                {store.categories && store.categories.length > 0 ? (
                    store.categories.map((category) => (
                        <li key={category.id}>
                            <a href="#" onClick={() => handleCategoryClick(category.id)}>
                                <span className="categories_name">{category.nombre}</span>
                                <span className="categories_num">({category.product_count || 0})</span>
                            </a>
                        </li>
                    ))
                ) : (
                    <li>No categories available</li>
                )}
            </ul>
        </div>
    );
};

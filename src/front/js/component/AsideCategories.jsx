import React, { useEffect, useContext, useState } from "react";
import { Context } from "../store/appContext.js";
import "../../styles/categories-pages.css";

export const AsideCategories = ({ onSelectCategory, onSelectSubcategory, categoryId }) => {
    const { store, actions } = useContext(Context);
    const [selectedSubcategory, setSelectedSubcategory] = useState(null);

    useEffect(() => {
        actions.getCategories();
    }, []);

    useEffect(() => {
        // Al cambiar de categoría, reiniciar subcategoría seleccionada
        setSelectedSubcategory(null);
        onSelectSubcategory(null); // Mostrar todos los productos
    }, [categoryId]);

    const handleChange = (subId) => {
        const newValue = subId === selectedSubcategory ? null : subId;
        setSelectedSubcategory(newValue);
        onSelectSubcategory(newValue);
    };

    const category = store.categories?.find(cat => cat.id === categoryId);

    return (
        <aside className="widget my-5">
            <p className="widget_title"><b>Categorías</b></p>
            <hr className="hr-home" />
            {category ? (
                <ul className="widget_categories">
                    <li key={category.id}>
                        <button
                            type="button"
                            onClick={() => {
                                setSelectedSubcategory(null);
                                onSelectCategory(category.id);
                                onSelectSubcategory(null);
                            }}
                            className="category-button"
                            aria-label={`Seleccionar categoría ${category.nombre}`}
                        >
                            <span className="categories_name">Todas las Rejas</span>
                            <span className="categories_num"> ({category.product_count || 0})</span>
                        </button>
                        {category.subcategories && category.subcategories.length > 0 && (
                            <ul className="subcategory-list mt-2">
                                {category.subcategories.map(sub => (
                                    <li key={sub.id} className="d-flex align-items-center mb-2">
                                        <input
                                            type="radio"
                                            id={`subcat-${sub.id}`}
                                            name="subcategories"
                                            checked={selectedSubcategory === sub.id}
                                            onChange={() => handleChange(sub.id)}
                                            className="subcategory-radio"
                                        />
                                        <label htmlFor={`subcat-${sub.id}`} className="subcategory-button ms-2">
                                            <span className="categories_name">{sub.nombre}</span>
                                            <span className="categories_num"> ({sub.product_count || 0})</span>
                                        </label>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </li>
                </ul>
            ) : (
                <div className="skeleton-category-list">
                    {Array.from({ length: 3 }).map((_, index) => (
                        <div key={index} className="skeleton-category mb-3" />
                    ))}
                </div>
            )}
        </aside>
    );
};

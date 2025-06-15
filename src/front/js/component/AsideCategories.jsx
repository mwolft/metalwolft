import React, { useEffect, useContext } from "react";
import { Context } from "../store/appContext.js";
import "../../styles/categories-pages.css";

export const AsideCategories = ({ onSelectCategory, onSelectSubcategory, categoryId }) => {
    const { store, actions } = useContext(Context);

    useEffect(() => {
        actions.getCategories();
    }, []);

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
                            onClick={() => onSelectCategory(category.id)}
                            className="category-button"
                            aria-label={`Seleccionar categoría ${category.nombre}`}
                        >
                            <i className="fas fa-chevron-right category-icon"></i>
                            <span className="categories_name">{category.nombre}</span>
                            <span className="categories_num"> ({category.product_count || 0})</span>
                        </button>
                        {category.subcategories && category.subcategories.length > 0 && (
                            <ul className="subcategory-list">
                                {category.subcategories.map(sub => (
                                    <li key={sub.id}>
                                        <button
                                            type="button"
                                            onClick={() => onSelectSubcategory(sub.id)}
                                            className="subcategory-button"
                                            aria-label={`Seleccionar subcategoría ${sub.nombre}`}
                                        >
                                            <i className="fas fa-caret-right subcategory-icon"></i>
                                            <span className="categories_name">{sub.nombre}</span>
                                            <span className="categories_num"> ({sub.product_count || 0})</span>
                                        </button>
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

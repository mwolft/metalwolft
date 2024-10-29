import React, { useEffect, useContext } from "react";
import { Context } from "../store/appContext.js";
import "../../styles/categories-pages.css";

export const AsideCategories = ({ onSelectCategory, onSelectSubcategory }) => {
    const { store, actions } = useContext(Context);

    useEffect(() => {
        actions.getCategories();
    }, []);

    const handleCategoryClick = (categoryId) => {
        onSelectCategory(categoryId);
    };

    const handleSubcategoryClick = (subcategoryId) => {
        onSelectSubcategory(subcategoryId);
    };

    return (
        <div className="widget">
            <h5 className="widget_title">Categorías</h5>
            <ul className="widget_categories">
                {store.categories && store.categories.map(category => (
                    <li key={category.id}>
                        <button type="button" onClick={() => handleCategoryClick(category.id)} className="category-button">
                            <i className="fas fa-chevron-right category-icon"></i>
                            <span className="categories_name">{category.nombre}</span>
                            <span className="categories_num"> ({category.product_count || 0})</span>
                        </button>
                        {category.subcategories && category.subcategories.length > 0 && (
                            <ul className="subcategory-list">
                                {category.subcategories.map(sub => (
                                    <li key={sub.id}>
                                        <button type="button" onClick={() => handleSubcategoryClick(sub.id)} className="subcategory-button">
                                            <i className="fas fa-caret-right subcategory-icon"></i>
                                            <span className="categories_name">{sub.nombre}</span>
                                            <span className="categories_num"> ({sub.product_count || 0})</span>
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
};

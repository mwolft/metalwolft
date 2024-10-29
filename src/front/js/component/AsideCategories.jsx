import React, { useEffect, useContext } from "react";
import { Context } from "../store/appContext.js";

export const AsideCategories = ({ onSelectCategory }) => {
    const { store, actions } = useContext(Context);

    useEffect(() => {
        actions.getCategories();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleCategoryClick = (categoryId, isSubcategory = false) => {
        onSelectCategory(categoryId, isSubcategory);
    };

    return (
        <div className="widget">
            <h5 className="widget_title">Categorías</h5>
            <ul className="widget_categories">
                {store.categories && store.categories.map(category => (
                    <li key={category.id}>
                        <button type="button" onClick={() => handleCategoryClick(category.id)} className="category-button">
                            <span className="categories_name">{category.nombre}</span>
                            <span className="categories_num">({category.product_count || 0})</span>
                        </button>
                        {category.subcategories && (
                            <ul>
                                {category.subcategories.map(sub => (
                                    <li key={sub.id}>
                                        <button type="button" onClick={() => handleCategoryClick(sub.id, true)} className="subcategory-button">
                                            <span className="categories_name">{sub.nombre}</span>
                                            <span className="categories_num">({sub.product_count || 0})</span>
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

import React, { useEffect, useContext, useState } from "react";
import { Context } from "../store/appContext.js";
import { Link } from "react-router-dom";
import "../../styles/categories-pages.css";

export const AsideOthersCategories = ({ currentCategoryId }) => {
    const { store, actions } = useContext(Context);
    const [otherCategories, setOtherCategories] = useState([]);

    useEffect(() => {
        const fetchOtherCategories = async () => {
            const categories = await actions.getOtherCategories(currentCategoryId);
            setOtherCategories(categories);
        };
        fetchOtherCategories();
    }, [currentCategoryId]);

    return (
        <aside className="widget my-5">
            <p className="widget_title"><b>Otras Categorías</b></p>
            <hr className="hr-home" />
            {otherCategories.length > 0 ? (
                <ul className="widget_categories">
                    {otherCategories.map((category, index) => (
                        <li key={index} className="others-categories">
                            <img
                                className="img-other-categories"
                                src={category.image_url || "/path/to/default/image.jpg"}
                                alt={category.nombre}
                                style={{ width: "80px", height: "100%", objectFit: "cover" }}
                            />
                            <p className="p-other-categories">
                                {category.nombre}<br />
                                <Link
                                    to={`/${category.slug}`}
                                    className="buton-other-categories"
                                    aria-label={`Ir a categoría ${category.nombre}`}
                                >
                                    Ir a categoría
                                </Link>
                            </p>
                        </li>
                    ))}
                </ul>
            ) : (
                <div className="skeleton-other-category-list">
                    {Array.from({ length: 3 }).map((_, index) => (
                        <div key={index} className="skeleton-other-category mb-3 d-flex" />
                    ))}
                </div>
            )}
        </aside>
    );
};

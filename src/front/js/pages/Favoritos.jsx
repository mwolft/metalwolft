import React, { useContext, useEffect } from "react";
import { Context } from "../store/appContext";
import { Link, useNavigate } from "react-router-dom";
import "../../styles/favorites.css";
import { Helmet } from "react-helmet";

const getFavoritePriceLabel = (product) => {
    const resolvedPrice = product?.precio_rebajado ?? product?.precio;

    if (resolvedPrice === null || resolvedPrice === undefined || resolvedPrice === "") {
        return null;
    }

    return `${resolvedPrice} €/m²`;
};

const getShortDescription = (description) => {
    if (!description) {
        return "Guarda tus modelos favoritos para volver a configurarlos cuando quieras.";
    }

    const normalized = String(description).replace(/\s+/g, " ").trim();
    if (normalized.length <= 150) {
        return normalized;
    }

    return `${normalized.slice(0, 147).trim()}...`;
};

export const Favoritos = () => {
    const { store, actions } = useContext(Context);
    const navigate = useNavigate();

    useEffect(() => {
        if (!store.isLoged) {
            alert("Debe iniciar sesión para ver sus favoritos");
            navigate("/login");
        } else if (!store.favoritesLoaded) {
            actions.loadFavorites();
            actions.setFavoritesLoaded(true);
        }
    }, [actions, navigate, store.favoritesLoaded, store.isLoged]);

    return (
        <>
            <Helmet>
                <meta name="robots" content="noindex, nofollow" />
                <meta name="theme-color" content="#ff324d" />
            </Helmet>

            <div className="favorites-page container">
                <header className="favorites-page__header text-center">
                    <p className="favorites-page__eyebrow">Inspiración guardada</p>
                    <h2 className="h2-categories favorites-page__title">Favoritos</h2>
                    <p className="favorites-page__subtitle">
                        Revisa tus modelos guardados, compáralos visualmente y vuelve a configurarlos cuando quieras.
                    </p>
                </header>

                {store.favorites.length === 0 ? (
                    <section className="favorites-empty-state text-center">
                        <div className="favorites-empty-state__icon" aria-hidden="true">
                            <i className="fa-regular fa-heart"></i>
                        </div>
                        <h3 className="favorites-empty-state__title">
                            Tu lista de favoritos está vacía
                        </h3>
                        <p className="favorites-empty-state__copy">
                            Guarda las rejas que más te gusten para volver luego, comparar diseños y dar el siguiente paso hacia tu pedido.
                        </p>
                        <Link to="/rejas-para-ventanas" className="favorites-primary-link">
                            Ver catálogo
                        </Link>
                    </section>
                ) : (
                    <section className="favorites-grid" aria-label="Productos favoritos">
                        {store.favorites.map((product) => (
                            <article key={product.id} className="favorite-card">
                                <Link
                                    to={`/${product.category_slug}/${product.slug}`}
                                    className="favorite-card__media"
                                    aria-label={`Ver ${product.nombre}`}
                                >
                                    {product.imagen ? (
                                        <img
                                            src={product.imagen}
                                            alt={product.nombre}
                                            className="favorite-card__image"
                                        />
                                    ) : (
                                        <div className="favorite-card__image-placeholder">
                                            MetalWolft
                                        </div>
                                    )}
                                </Link>

                                <div className="favorite-card__body">
                                    <div className="favorite-card__top">
                                        <h3 className="favorite-card__title">{product.nombre}</h3>
                                        {getFavoritePriceLabel(product) ? (
                                            <p className="favorite-card__price">
                                                {getFavoritePriceLabel(product)}
                                            </p>
                                        ) : null}
                                    </div>

                                    <p className="favorite-card__description">
                                        {getShortDescription(product.descripcion)}
                                    </p>

                                    <div className="favorite-card__actions">
                                        <Link
                                            to={`/${product.category_slug}/${product.slug}`}
                                            className="favorites-primary-link"
                                        >
                                            Configurar medidas
                                        </Link>

                                        <button
                                            type="button"
                                            className="favorites-secondary-button"
                                            onClick={() => actions.removeFavorite(product.id)}
                                        >
                                            <i className="fa-regular fa-trash-can"></i>
                                            <span>Quitar de favoritos</span>
                                        </button>
                                    </div>
                                </div>
                            </article>
                        ))}
                    </section>
                )}
            </div>
        </>
    );
};

export default Favoritos;

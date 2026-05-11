import React, { useContext, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet";
import { Context } from "../store/appContext";
import "../../styles/favorites.css";

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

const getProductPath = (product) => `/${product.category_slug}/${product.slug}`;
const getProductUrl = (product) => new URL(getProductPath(product), window.location.origin).toString();

export const Favoritos = () => {
    const { store, actions } = useContext(Context);
    const navigate = useNavigate();
    const [shareFeedback, setShareFeedback] = useState({ productId: null, message: "" });
    const shareFeedbackTimeoutRef = useRef(null);

    useEffect(() => {
        if (!store.isLoged) {
            alert("Debe iniciar sesion para ver sus favoritos");
            navigate("/login");
        } else if (!store.favoritesLoaded) {
            actions.loadFavorites();
            actions.setFavoritesLoaded(true);
        }
    }, [actions, navigate, store.favoritesLoaded, store.isLoged]);

    useEffect(() => {
        return () => {
            if (shareFeedbackTimeoutRef.current) {
                window.clearTimeout(shareFeedbackTimeoutRef.current);
            }
        };
    }, []);

    const showShareFeedback = (productId, message) => {
        if (shareFeedbackTimeoutRef.current) {
            window.clearTimeout(shareFeedbackTimeoutRef.current);
        }

        setShareFeedback({ productId, message });
        shareFeedbackTimeoutRef.current = window.setTimeout(() => {
            setShareFeedback({ productId: null, message: "" });
        }, 2200);
    };

    const handleShareFavorite = async (product) => {
        const productUrl = getProductUrl(product);

        try {
            if (navigator.share) {
                await navigator.share({
                    title: product?.nombre || "Favorito MetalWolft",
                    text: product?.nombre || "Mira este producto de MetalWolft",
                    url: productUrl
                });
                showShareFeedback(product.id, "Enlace compartido");
                return;
            }

            if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(productUrl);
                showShareFeedback(product.id, "Enlace copiado");
                return;
            }

            const temporaryInput = document.createElement("input");
            temporaryInput.value = productUrl;
            document.body.appendChild(temporaryInput);
            temporaryInput.select();
            document.execCommand("copy");
            temporaryInput.remove();
            showShareFeedback(product.id, "Enlace copiado");
        } catch (error) {
            if (error?.name === "AbortError") {
                return;
            }

            showShareFeedback(product.id, "No se pudo compartir");
        }
    };

    return (
        <>
            <Helmet>
                <meta name="robots" content="noindex, nofollow" />
                <meta name="theme-color" content="#ff324d" />
            </Helmet>

            <div className="favorites-page container">
                <header className="favorites-page__header text-center">
                    <p className="favorites-page__eyebrow">Inspiracion guardada</p>
                    <h2 className="h2-categories">Favoritos</h2>
                    <p className="favorites-page__subtitle">
                        Revisa tus modelos guardados, comparalos visualmente y vuelve a configurarlos cuando quieras.
                    </p>
                </header>

                {store.favorites.length === 0 ? (
                    <section className="favorites-empty-state text-center">
                        <div className="favorites-empty-state__icon" aria-hidden="true">
                            <i className="fa-regular fa-heart"></i>
                        </div>
                        <h3 className="favorites-empty-state__title">
                            Tu lista de favoritos esta vacia
                        </h3>
                        <p className="favorites-empty-state__copy">
                            Guarda las rejas que mas te gusten para volver luego, comparar disenos y dar el siguiente paso hacia tu pedido.
                        </p>
                        <Link to="/rejas-para-ventanas" className="favorites-primary-link">
                            Ver catalogo
                        </Link>
                    </section>
                ) : (
                    <section className="favorites-list" aria-label="Productos favoritos">
                        {store.favorites.map((product) => (
                            <article key={product.id} className="favorite-list-item">
                                <Link
                                    to={getProductPath(product)}
                                    className="favorite-list-item__media"
                                    aria-label={`Ver ${product.nombre}`}
                                >
                                    {product.imagen ? (
                                        <img
                                            src={product.imagen}
                                            alt={product.nombre}
                                            className="favorite-list-item__image"
                                        />
                                    ) : (
                                        <div className="favorite-list-item__image-placeholder">
                                            MetalWolft
                                        </div>
                                    )}
                                </Link>

                                <div className="favorite-list-item__body">
                                    <div className="favorite-list-item__top">
                                        <h3 className="favorite-list-item__title">{product.nombre}</h3>
                                        {getFavoritePriceLabel(product) ? (
                                            <p className="favorite-list-item__price">
                                                {getFavoritePriceLabel(product)}
                                            </p>
                                        ) : null}
                                    </div>

                                    <p className="favorite-list-item__description">
                                        {getShortDescription(product.descripcion)}
                                    </p>

                                    <div className="favorite-list-item__actions">
                                        <Link
                                            to={getProductPath(product)}
                                            className="favorites-primary-link"
                                        >
                                            Configurar medidas
                                        </Link>

                                        <button
                                            type="button"
                                            className="favorites-tertiary-button"
                                            onClick={() => handleShareFavorite(product)}
                                        >
                                            <i className="fa-solid fa-share-nodes"></i>
                                            <span>Compartir enlace</span>
                                        </button>

                                        <button
                                            type="button"
                                            className="favorites-secondary-button"
                                            onClick={() => actions.removeFavorite(product.id)}
                                        >
                                            <i className="fa-regular fa-trash-can"></i>
                                            <span>Quitar de favoritos</span>
                                        </button>
                                    </div>

                                    {shareFeedback.productId === product.id && shareFeedback.message ? (
                                        <p className="favorite-list-item__feedback" role="status">
                                            {shareFeedback.message}
                                        </p>
                                    ) : null}
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

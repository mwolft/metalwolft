import React, { useContext, useEffect } from 'react';
import { Context } from "../store/appContext";
import { Link, useNavigate } from "react-router-dom";
import "../../styles/favorites.css";
import { Helmet } from "react-helmet";

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
    }, [store.isLoged]);

    return (
        <>
            <Helmet>
                <meta name="robots" content="noindex, nofollow" />
                <meta name="theme-color" content="#ff324d" />
            </Helmet>
            <div className="container" style={{ marginTop: '100px' }}>
                <h2 className="h2-categories text-center my-3">Favoritos</h2>
                {store.favorites.length === 0 ? (
                    <p className="text-center" style={{ marginBottom: '300px' }}>
                        No hay productos en tu lista de favoritos.<br /><br />
                        <Link to="/" className="link-categories"><i className="fa-solid fa-arrow-left"></i> Volver</Link>
                    </p>
                ) : (
                    <div className="table-responsive wishlist_table">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Imagen</th>
                                    <th>Producto</th>
                                    <th>Descripción</th>
                                    <th>Precio</th>
                                    <th>Eliminar</th>
                                </tr>
                            </thead>
                            <tbody>
                                {store.favorites.map((product, index) => (
                                    <tr key={index}>
                                        <td className="product-thumbnail">
                                            <img src={product.imagen} alt={product.nombre} className="img-fluid" />
                                        </td>
                                        <td className="product-name">
                                            {product.nombre}
                                        </td>
                                        <td className="product-name">
                                            {product.descripcion}
                                        </td>
                                        <td className="product-price">{product.precio} €/m²</td>
                                        <td className="product-remove">
                                            <button onClick={() => actions.removeFavorite(product.id)}>
                                                <i className="fa-regular fa-trash-can"></i>
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </>
    );
};

export default Favoritos;
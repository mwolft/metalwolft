import React, { useContext, useEffect } from 'react';
import { Context } from "../store/appContext";
import { Link, useNavigate } from "react-router-dom";
import "../../styles/favorites.css"; // Asegúrate de tener estilos específicos para la tabla de favoritos

export const Favoritos = () => {
    const { store, actions } = useContext(Context);
    const navigate = useNavigate();

    useEffect(() => {
        if (!store.isLoged) {
            alert("Debe iniciar sesión para ver sus favoritos");
            navigate("/login");
        } else if (!store.favoritesLoaded) {
            actions.loadFavorites(); // Cargar los favoritos del backend solo si no están ya cargados
            actions.setFavoritesLoaded(true); // Marcar los favoritos como cargados para evitar la recarga
        }
    }, [store.isLoged]);
        

    return (
        <div className="container">
            <div className="row" style={{ marginTop: '100px' }}>
                <div className="col-12">
                    <div className="table-responsive wishlist_table">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th className="product-thumbnail">&nbsp;</th>
                                    <th className="product-name">Producto</th>
                                    <th className="product-price">Precio</th>
                                    <th className="product-add-to-cart"></th>
                                    <th className="product-remove">Eliminar</th>
                                </tr>
                            </thead>
                            <tbody>
                                {store.favorites.length > 0 ? (
                                    store.favorites.map((product, index) => (
                                        <tr key={index}>
                                            <td className="product-thumbnail">
                                                <Link to={`/product/${product.id}`}>
                                                    <img src={product.imagen} alt={product.nombre} className="img-fluid" />
                                                </Link>
                                            </td>
                                            <td className="product-name" data-title="Producto">
                                                <Link to={`/product/${product.id}`}>{product.nombre}</Link>
                                            </td>
                                            <td className="product-price" data-title="Precio">
                                                {product.precio} €/m²
                                            </td>
                                            <td className="product-add-to-cart">
                                                <button
                                                    className="btn btn-fill-out"
                                                    onClick={() => actions.addToCart(product)}
                                                >
                                                    <i className="icon-basket-loaded"></i> Añadir al carrito
                                                </button>
                                            </td>
                                            <td className="product-remove" data-title="Eliminar">
                                                <button onClick={() => actions.removeFavorite(product.id)}>
                                                    <i className="fa-regular fa-trash-can"></i>
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="6" className="text-center">
                                            No hay productos en tu lista de favoritos.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Favoritos;

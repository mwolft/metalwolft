import React, { useContext } from 'react';
import { Context } from "../store/appContext";
import { Link } from "react-router-dom";

export const Favoritos = () => {
    const { store, actions } = useContext(Context);

    return (
        <div className="section">
            <div className="container">
                <div className="row">
                    <div className="col-12">
                        <div className="table-responsive wishlist_table">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th className="product-thumbnail">&nbsp;</th>
                                        <th className="product-name">Producto</th>
                                        <th className="product-price">Precio</th>
                                        <th className="product-stock-status">Disponibilidad</th>
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
                                                        <img src={product.imagen} alt={product.nombre} />
                                                    </Link>
                                                </td>
                                                <td className="product-name" data-title="Producto">
                                                    <Link to={`/product/${product.id}`}>{product.nombre}</Link>
                                                </td>
                                                <td className="product-price" data-title="Precio">
                                                    {product.precio} €/m²
                                                </td>
                                                <td className="product-stock-status" data-title="Disponibilidad">
                                                    <span className={`badge rounded-pill ${product.stock ? 'text-bg-success' : 'text-bg-danger'}`}>
                                                        {product.stock ? 'En Stock' : 'Agotado'}
                                                    </span>
                                                </td>
                                                <td className="product-add-to-cart">
                                                    <button className="btn btn-fill-out" onClick={() => actions.addToCart(product)}>
                                                        <i className="icon-basket-loaded"></i> Añadir al carrito
                                                    </button>
                                                </td>
                                                <td className="product-remove" data-title="Eliminar">
                                                    <button onClick={() => actions.removeFavorite(product.id)}>
                                                        <i className="ti-close"></i>
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
        </div>
    );
};

export default Favoritos;

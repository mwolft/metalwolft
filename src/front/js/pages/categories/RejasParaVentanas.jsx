import React, { useEffect, useContext } from "react";
import { Breadcrumb } from "../../component/Breadcrumb.jsx";
import { Product } from "../../component/Product.jsx";
import "../../../styles/categories.css";
import { useNavigate } from "react-router-dom";
import { AsideCategories } from "../../component/AsideCategories.jsx";
import { Context } from "../../store/appContext";

export const RejasParaVentanas = () => {
    const { store, actions } = useContext(Context);
    const navigate = useNavigate();

    useEffect(() => {
        actions.fetchProducts();  // Llamar a la acción para obtener productos
    }, []);

    return (
        <>
            <Breadcrumb />
            <div className="container">
                <div className="row">
                    <div className="col-12 col-lg-3 col-xl-3 order-2 order-sm-2 order-md-2 order-lg-1 order-xl-1">
                        <AsideCategories />
                    </div>
                    <div className="col-12 col-lg-9 col-xl-9 order-1 order-sm-1 order-md-1 order-lg-2 order-xl-2">
                        {store.products.length > 0 ? (
                            store.products.map((product, index) => (
                                <Product key={index} product={product} />
                            ))
                        ) : (
                            <p>No hay productos disponibles en esta categoría.</p>
                        )}
                    </div>
                </div>
            </div>
        </>
    );
};

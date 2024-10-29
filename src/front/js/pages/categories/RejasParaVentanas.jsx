import React, { useEffect, useContext, useState } from "react";
import { Breadcrumb } from "../../component/Breadcrumb.jsx";
import { Product } from "../../component/Product.jsx";
import { AsideCategories } from "../../component/AsideCategories.jsx";
import { Context } from "../../store/appContext.js";
import "../../../styles/categories-pages.css"; 

export const RejasParaVentanas = () => {
    const { store, actions } = useContext(Context);
    const [selectedCategoryId, setSelectedCategoryId] = useState(null);
    const [selectedSubcategoryId, setSelectedSubcategoryId] = useState(null);

    // Cargar todos los productos al inicio
    useEffect(() => {
        actions.fetchProducts();
    }, []);

    useEffect(() => {
        actions.fetchProducts(selectedCategoryId, selectedSubcategoryId);
    }, [selectedCategoryId, selectedSubcategoryId]);

    const handleCategorySelect = (categoryId) => {
        setSelectedCategoryId(categoryId);
        setSelectedSubcategoryId(null); // Resetear subcategoría al seleccionar una categoría
    };

    const handleSubcategorySelect = (subcategoryId) => {
        setSelectedSubcategoryId(subcategoryId);
    };

    return (
        <>
            <Breadcrumb />
            <div className="container">
                <div className="row">
                    <div className="col-12 col-lg-3 col-xl-3 order-2">
                        <AsideCategories 
                            onSelectCategory={handleCategorySelect} 
                            onSelectSubcategory={handleSubcategorySelect} // Pasar el manejador
                        />
                    </div>
                    <div className="col-12 col-lg-9 col-xl-9 order-1">
                        <div className="row">
                            {store.products && store.products.length > 0 ? (
                                store.products.map((product, index) => (
                                    <div key={index} className="col-6 col-sm-6 col-md-4 col-lg-4 col-xl-4 mb-4 d-flex">
                                        <Product product={product} className="w-100" />
                                    </div>
                                ))
                            ) : (
                                <p>Cargando productos o no hay productos disponibles para esta categoría.</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

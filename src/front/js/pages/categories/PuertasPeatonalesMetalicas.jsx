import React, { useEffect, useContext, useState } from "react";
import { Breadcrumb } from "../../component/Breadcrumb.jsx";
import { Product } from "../../component/Product.jsx";
import { AsideCategories } from "../../component/AsideCategories.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import { AsidePost } from "../../component/AsidePost.jsx";
import { Context } from "../../store/appContext.js";
import "../../../styles/categories-pages.css";

export const PuertasPeatonalesMetalicas = () => {
    const { store, actions } = useContext(Context);
    const puertasPeatonalesCategoryId = 3;
    const [selectedCategoryId, setSelectedCategoryId] = useState(puertasPeatonalesCategoryId);
    const [selectedSubcategoryId, setSelectedSubcategoryId] = useState(null);

    useEffect(() => {
        actions.fetchProducts(selectedCategoryId, selectedSubcategoryId);
    }, [selectedCategoryId, selectedSubcategoryId]);

    const handleCategorySelect = (categoryId) => {
        setSelectedCategoryId(categoryId);
        setSelectedSubcategoryId(null);
    };

    const handleSubcategorySelect = (subcategoryId) => {
        setSelectedSubcategoryId(subcategoryId);
    };

    return (
        <>
            <Breadcrumb />
            <div className="container">
                <div className="row">
                <div className="col-12 col-lg-3 col-xl-3 order-1">
                        <AsideCategories
                            onSelectCategory={handleCategorySelect}
                            onSelectSubcategory={handleSubcategorySelect}
                            categoryId={puertasPeatonalesCategoryId}
                        />
                        <div className="d-none d-lg-block">
                            <AsidePost />
                            <AsideOthersCategories currentCategoryId={puertasPeatonalesCategoryId} />
                        </div>
                    </div>
                    <div className="col-12 col-lg-9 col-xl-9 order-2">
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
                    <div className="col-12 d-block d-lg-none order-3">
                        <AsidePost />
                        <AsideOthersCategories currentCategoryId={puertasPeatonalesCategoryId} />
                    </div>
                </div>
            </div>
        </>
    );
};

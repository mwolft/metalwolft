import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Breadcrumb } from "../../component/Breadcrumb.jsx";
import { Product } from "../../component/Product.jsx";
import { AsideCategories } from "../../component/AsideCategories.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import { AsidePost } from "../../component/AsidePost.jsx";
import { Context } from "../../store/appContext.js";
import "../../../styles/categories-pages.css";
import { WhatsAppWidget } from "../../component/WhatsAppWidget.jsx";

export const CerramientoDeCocinaConCristal = () => {
    const { store, actions } = useContext(Context);
    const cerramientoCocinaCategoryId = 6;
    const [selectedCategoryId, setSelectedCategoryId] = useState(cerramientoCocinaCategoryId);
    const [selectedSubcategoryId, setSelectedSubcategoryId] = useState(null);
    const [metaData, setMetaData] = useState({});

    useEffect(() => {
        actions.fetchProducts(selectedCategoryId, selectedSubcategoryId);
    }, [selectedCategoryId, selectedSubcategoryId]);

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://scaling-umbrella-976gwrg7664j3grx-3001.app.github.dev";

        fetch(`${apiBaseUrl}/api/seo/cerramientos-de-cocina-con-cristal`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then((data) => setMetaData(data))
            .catch((error) => console.error("Error fetching SEO data:", error));
    }, []);


    const handleCategorySelect = (categoryId) => {
        setSelectedCategoryId(categoryId);
        setSelectedSubcategoryId(null);
    };

{/* const handleSubcategorySelect = (subcategoryId) => {
        setSelectedSubcategoryId(subcategoryId);
    };*/}

    return (
        <>
            <Helmet>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="keywords" content={metaData.keywords} />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ffffff"} />
                {/* Open Graph Meta Tags */}
                <meta property="og:type" content={metaData.og_type || "article"} />
                <meta property="og:title" content={metaData.title} />
                <meta property="og:description" content={metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:image:width" content={metaData.og_image_width || "400"} />
                <meta property="og:image:height" content={metaData.og_image_height || "300"} />
                <meta property="og:image:type" content={metaData.og_image_type || "image/jpg"} />
                <meta property="og:image:alt" content={metaData.og_image_alt || "cerramientos de cocina con cristal"} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta property="og:locale:alternate" content={metaData.og_locale_alternate || "en_US"} />
                {/* Canonical Link */}
                <link rel="canonical" href={metaData.canonical} />
                {/* JSON-LD Schema */}
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            {/*<Breadcrumb />*/}
            <div className="container" style={{ marginTop: "100px" }}>
                <div className="row">
                <h1 className="h2-categories mb-3">Cerramiento de Cocina con Cristal</h1>
                    <div className="col-12 col-lg-3 col-xl-3 order-1">
                        {/*<AsideCategories
                            onSelectCategory={handleCategorySelect}
                            onSelectSubcategory={handleSubcategorySelect}
                            categoryId={cerramientoCocinaCategoryId}
                        />*/}
                        <div className="d-none d-lg-block">
                            <AsidePost />
                            <AsideOthersCategories currentCategoryId={cerramientoCocinaCategoryId} />
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
                        <AsideOthersCategories currentCategoryId={cerramientoCocinaCategoryId} />
                    </div>
                </div>
            </div>
            <WhatsAppWidget
                whatsappNumber="34634112604"
                placeholderText="Escribenos por WhatsApp"
                widgetText="¿Le podemos ayudar?"
                botImage="https://res.cloudinary.com/dewanllxn/image/upload/v1735631180/welder-bot_tqxadc.png"
            />
        </>
    );
};

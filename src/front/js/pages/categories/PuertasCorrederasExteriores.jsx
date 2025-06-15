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
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

export const PuertasCorrederasExteriores = () => {
    const { store, actions } = useContext(Context);
    const puertasCorrederasExterioresCategoryId = 5;
    const [selectedCategoryId, setSelectedCategoryId] = useState(puertasCorrederasExterioresCategoryId);
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
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/puertas-correderas-exteriores`)
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
            <Helmet htmlAttributes={{ lang: metaData.lang || "es" }}>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="keywords" content={metaData.keywords} />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ffffff"} />
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:site" content={metaData.twitter_site} />
                <meta name="twitter:creator" content={metaData.twitter_creator} />
                <meta name="twitter:title" content={metaData.twitter_title || metaData.title} />
                <meta name="twitter:description" content={metaData.twitter_description || metaData.description} />
                <meta name="twitter:image" content={metaData.twitter_image || metaData.og_image} />
                <meta name="twitter:image:alt" content={metaData.twitter_image_alt || metaData.og_image_alt} />
                <meta property="og:type" content={metaData.og_type || "article"} />
                <meta property="og:title" content={metaData.title} />
                <meta property="og:description" content={metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:image:width" content={metaData.og_image_width || "400"} />
                <meta property="og:image:height" content={metaData.og_image_height || "300"} />
                <meta property="og:image:type" content={metaData.og_image_type || "image/jpg"} />
                <meta property="og:image:alt" content={metaData.og_image_alt || "puertas correderas exteriores"} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft Ciudad Real"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta property="og:locale:alternate" content={metaData.og_locale_alternate || "en_US"} />
                <link rel="canonical" href={metaData.canonical} />
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            {/*<Breadcrumb />*/}
            <div className="container" style={{ marginTop: "100px" }}>
                <div className="row">
                    <h1 className="h2-categories mb-3">Puertas Correderas Exteriores</h1>
                    <div className="col-12 col-lg-3 col-xl-3 order-1">
                        {/*<AsideCategories
                            onSelectCategory={handleCategorySelect}
                            onSelectSubcategory={handleSubcategorySelect}
                            categoryId={puertasCorrederasExterioresCategoryId}
                        />*/}
                        <div className="d-none d-lg-block">
                            <AsidePost />
                            <AsideOthersCategories currentCategoryId={puertasCorrederasExterioresCategoryId} />
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
                                Array.from({ length: 9 }).map((_, index) => (
                                    <div key={index} className="col-6 col-sm-6 col-md-4 col-lg-4 col-xl-4 mb-4 d-flex">
                                        <div className="w-100 skeleton-card" />
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                    <div className="col-12 d-block d-lg-none order-3">
                        <AsidePost />
                        <AsideOthersCategories currentCategoryId={puertasCorrederasExterioresCategoryId} />
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

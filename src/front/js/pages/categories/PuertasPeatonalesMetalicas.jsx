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

export const PuertasPeatonalesMetalicas = () => {
    const { store, actions } = useContext(Context);
    const puertasPeatonalesCategoryId = 3;
    const [selectedCategoryId, setSelectedCategoryId] = useState(puertasPeatonalesCategoryId);
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

        fetch(`${apiBaseUrl}/api/seo/puertas-peatonales-metalicas`)
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
                <meta property="og:image:alt" content={metaData.og_image_alt || "Puertas Peatonales Metálicas"} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta property="og:locale:alternate" content={metaData.og_locale_alternate || "en_US"} />
                <meta property="og:updated_time" content={metaData.og_updated_time} />
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
                    <h1 className="h2-categories mb-3">Puertas Peatonales Metálicas</h1>
                    <div className="col-12 col-lg-3 col-xl-3 order-1">
                        {/*<AsideCategories
                            onSelectCategory={handleCategorySelect}
                            onSelectSubcategory={handleSubcategorySelect}
                            categoryId={puertasPeatonalesCategoryId}
                        />*/}
                        <div className="d-none d-lg-block">
                            <AsidePost />
                            <AsideOthersCategories currentCategoryId={puertasPeatonalesCategoryId} />
                        </div>
                    </div>
                    <div className="col-12 col-lg-9 col-xl-9 order-2">
                        <div className="alert alert-primary" role="alert">
                            <p><b><i className="fa-regular fa-circle-question"></i> PREGUNTAS FRECUENTES</b></p>
                            <ul>
                                <li>
                                    <b>¿Qué incluye la puerta?</b>
                                    <ul className="list-unstyled">
                                        <li>✔ <b>Tirador redondo de acero inoxidable.</b></li>
                                        <li>✔ <b>Maneta interior</b> en color negro o blanco (según preferencia).</li>
                                        <li>✔ <b>Cerradura</b>, disponible en opción manual o electrónica.</li>
                                        <li>✔ <b>Tornillería necesaria</b> para su instalación.</li>
                                    </ul>
                                </li>
                                <li>
                                    <b>¿Qué no se incluye?</b>
                                    <ul className="list-unstyled">
                                        <li>❌ <b>Número de la puerta.</b></li>
                                        <li>❌ <b>Buzón integrado.</b></li>
                                        <li>❌ <b>Cableado para la cerradura electrónica.</b></li>
                                    </ul>
                                </li>
                                <li>
                                    <b>¿Dónde puedo elegir la cerradura electrónica?</b>  Actualmente, estamos implementando esta opción en nuestro sistema de compra.
                                    Por ahora, nos pondremos en contacto contigo tras la compra para asesorarte
                                    y asegurarnos de que eliges la mejor opción según tus necesidades.
                                </li>
                                <li>
                                    <b>¿Qué tipo de instalación es más aconsejable?</b> La opción más recomendada es con <b>agujeros interiores</b>, ya que ofrece una estética más limpia y discreta, manteniendo la seguridad sin afectar el diseño de la puerta.
                                </li>
                                <li>
                                    <b>¿Cómo puedo ponerme en contacto?</b> Puedes hacerlo a través de nuestro <a href="/contact" target="_blank" rel="noopener noreferrer">formulario de contacto</a>, enviándonos un mensaje por <a href="https://wa.me/634112604" target="_blank" rel="noopener noreferrer">WhatsApp</a> o llamándonos al <a href="tel:634112604">634112604</a>.
                                </li>
                            </ul>
                        </div>
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
                        <AsideOthersCategories currentCategoryId={puertasPeatonalesCategoryId} />
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

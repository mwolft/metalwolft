import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from "react-helmet";

export const ChangesInCookiePolicy = () => {
    const [metaData, setMetaData] = useState({});

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/cambios-politica-cookies`)
            .then((res) => {
                if (!res.ok) throw new Error("Error al cargar SEO");
                return res.json();
            })
            .then((data) => setMetaData(data))
            .catch((error) => console.error("Error SEO:", error));
    }, []);

    return (
        <>
            <Helmet htmlAttributes={{ lang: metaData.lang || "es" }}>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ff324d"} />

                {/* OpenGraph */}
                <meta property="og:type" content={metaData.og_type} />
                <meta property="og:title" content={metaData.og_title || metaData.title} />
                <meta property="og:description" content={metaData.og_description || metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />

                {/* Twitter */}
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:title" content={metaData.twitter_title || metaData.title} />
                <meta name="twitter:description" content={metaData.twitter_description || metaData.description} />
                <meta name="twitter:image" content={metaData.twitter_image || metaData.og_image} />

                <link rel="canonical" href={metaData.canonical} />

                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>

            <div className="container" style={{ marginTop: '65px' }}>
                <h1 className="h1-categories">Cambios en nuestra Política de Cookies</h1>

                <p>
                    Nos reservamos el derecho de realizar cambios en nuestra política de cookies en cualquier momento.
                    Te recomendamos revisarla periódicamente para estar al tanto de cualquier modificación.
                </p>

                <p>
                    Si se realizan cambios importantes que afecten tu experiencia o la forma en que procesamos tus datos,
                    te lo notificaremos de manera destacada.
                </p>

                <p>
                    Si tienes dudas sobre esta política o sus modificaciones, puedes contactarnos por los canales
                    disponibles en nuestro sitio web.
                </p>

                <hr className="my-4" />
                <div className="mt-4 mb-5">
                    <h2 className="h2-categories mb-3">Enlaces relacionados</h2>
                    <ul>
                        <li><Link to="/politica-cookies">Política de Cookies</Link></li>
                        <li><Link to="/politica-privacidad">Política de Privacidad</Link></li>
                        <li><Link to="/cambios-politica-cookies">Cambios en la Política de Cookies</Link></li>
                        <li><Link to="/contact">Contacto (Ejercicio de derechos RGPD)</Link></li>
                    </ul>
                </div>
            </div>
        </>
    );
};

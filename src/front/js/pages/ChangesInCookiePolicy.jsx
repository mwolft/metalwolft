import React from 'react';
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../component/Breadcrumb.jsx';
import { Helmet } from "react-helmet";

export const ChangesInCookiePolicy = () => {
    return (
        <>
            <Helmet htmlAttributes={{ lang: metaData.lang || "es" }}>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ff324d"} />

                {/* OpenGraph */}
                <meta property="og:type" content={metaData.og_type} />
                <meta property="og:title" content={metaData.og_title} />
                <meta property="og:description" content={metaData.og_description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name} />
                <meta property="og:locale" content={metaData.og_locale} />

                {/* Twitter */}
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:title" content={metaData.twitter_title} />
                <meta name="twitter:description" content={metaData.twitter_description} />
                <meta name="twitter:image" content={metaData.twitter_image} />

                {/* Canonical */}
                <link rel="canonical" href={metaData.canonical} />

                {/* JSON-LD */}
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
                    Los cambios serán efectivos tan pronto como se publiquen en esta página. Te recomendamos revisarla periódicamente
                    para estar al tanto de cualquier modificación.
                </p>
                <p>
                    Si realizamos cambios importantes que puedan afectar tu experiencia o la forma en que procesamos tus datos,
                    te notificaremos de manera destacada en nuestro sitio web. Así, podrás tomar una decisión informada sobre tu
                    consentimiento al uso de cookies.
                </p>
                <p>
                    Si tienes alguna pregunta o inquietud sobre nuestra política de cookies o los cambios que se realicen,
                    no dudes en ponerte en contacto con nosotros a través de los canales que se encuentran en nuestro sitio web.
                </p>
            </div>
        </>
    );
};

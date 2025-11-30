import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from "react-helmet";

export const CookiesPolicy = () => {
    const [metaData, setMetaData] = useState({});

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/politica-cookies`)
            .then((res) => {
                if (!res.ok) throw new Error("SEO fetch error");
                return res.json();
            })
            .then((data) => setMetaData(data))
            .catch((err) => console.error("Error cargando SEO:", err));
    }, []);

    return (
        <>
            <Helmet htmlAttributes={{ lang: metaData.lang || "es" }}>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="keywords" content={metaData.keywords} />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ff324d"} />

                {/* Canonical */}
                {metaData.canonical && (
                    <link rel="canonical" href={metaData.canonical} />
                )}

                {/* OpenGraph */}
                <meta property="og:type" content={metaData.og_type} />
                <meta property="og:title" content={metaData.og_title} />
                <meta property="og:description" content={metaData.og_description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />

                {/* Twitter */}
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:title" content={metaData.twitter_title} />
                <meta name="twitter:description" content={metaData.twitter_description} />
                <meta name="twitter:image" content={metaData.twitter_image} />

                {/* JSON-LD */}
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            <div className="container" style={{ marginTop: '65px' }}>
                <h1 className='h1-categories'>Política de Cookies</h1>
                <p>Este sitio web utiliza cookies para mejorar la experiencia del usuario. Al utilizar nuestro sitio web, aceptas el uso de cookies conforme a esta política.</p>

                <h2 className="h2-categories mb-3">¿Qué son las Cookies?</h2>
                <p>Las cookies son pequeños archivos de texto que se almacenan en tu dispositivo cuando visitas ciertos sitios web. Permiten que el sitio recuerde tus acciones y preferencias para mejorar tu experiencia de navegación.</p>

                <h2 className="h2-categories mb-3">Tipos de Cookies que Utilizamos</h2>
                <ul>
                    <li><strong>Cookies esenciales:</strong> Son necesarias para el funcionamiento básico del sitio, permitiéndote iniciar sesión y usar funciones esenciales.</li>
                    <li><strong>Cookies de rendimiento:</strong> Nos ayudan a entender cómo los visitantes interactúan con nuestro sitio, recopilando información de forma anónima.</li>
                    <li><strong>Cookies de funcionalidad:</strong> Recuerdan tus preferencias para ofrecer una experiencia personalizada.</li>
                    <li><strong>Cookies de publicidad:</strong> Utilizamos cookies para mostrar anuncios relevantes en nuestro sitio y en sitios de terceros.</li>
                </ul>

                <h2 className="h2-categories mb-3">Control de Cookies</h2>
                <p>Puedes gestionar tus preferencias de cookies desde la configuración de tu navegador. Sin embargo, desactivar ciertas cookies puede afectar la funcionalidad del sitio.</p>

                <h2 className="h2-categories mb-3">Cambios en nuestra Política de Cookies</h2>
                <p>Nos reservamos el derecho de realizar cambios en esta política en cualquier momento. Publicaremos las actualizaciones en esta página.</p>

                <p>Si tienes preguntas sobre nuestra política de cookies, contáctanos a través de nuestros canales de atención al cliente.</p>
                <h2 className="h2-categories mb-3">Enlaces relacionados</h2>
                <ul>
                    <li><Link to="/politica-privacidad">Política de Privacidad</Link></li>
                    <li><Link to="/informacion-recogida">Información que Recopilamos</Link></li>
                    <li><Link to="/cookies-esenciales">Cookies esenciales utilizadas</Link></li>
                    <li><Link to="/cambios-politica-cookies">Cambios en la Política de Cookies</Link></li>
                    <li><Link to="/contact">Contacto y ejercicio de derechos RGPD</Link></li>
                </ul>
            </div>
        </>
    );
};
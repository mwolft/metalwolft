import React, { useEffect, useState } from 'react';
import { Helmet } from "react-helmet";
import { Link } from "react-router-dom";

export const PrivacyPolicy = () => {
    const [metaData, setMetaData] = useState({});

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/politica-privacidad`)
            .then((response) => {
                if (!response.ok) throw new Error("SEO response error");
                return response.json();
            })
            .then((data) => setMetaData(data))
            .catch((error) => console.error("Error fetching SEO data:", error));
    }, []);

    return (
        <>
            <Helmet htmlAttributes={{ lang: metaData.lang || "es" }}>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ff324d"} />

                {/* OpenGraph */}
                <meta property="og:type" content={metaData.og_type || "article"} />
                <meta property="og:title" content={metaData.og_title || metaData.title} />
                <meta property="og:description" content={metaData.og_description || metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />

                {/* Twitter */}
                <meta name="twitter:card" content={metaData.twitter_card_type || "summary_large_image"} />
                <meta name="twitter:title" content={metaData.twitter_title || metaData.title} />
                <meta name="twitter:description" content={metaData.twitter_description || metaData.description} />
                <meta name="twitter:image" content={metaData.twitter_image || metaData.og_image} />

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
                <h1 className='h1-categories'>Política de Privacidad</h1>
                <p>Tu privacidad es importante para nosotros. Esta política describe cómo recopilamos, utilizamos y protegemos tu información personal.</p>

                <h2 className="h2-categories mb-3">Información que Recopilamos</h2>
                <p>Recopilamos información personal cuando te registras en nuestro sitio, realizas una compra o navegas en nuestra web. La información puede incluir tu nombre, correo electrónico, dirección postal y número de teléfono.</p>

                <h2 className="h2-categories mb-3">Uso de la Información</h2>
                <p>Utilizamos la información para procesar pedidos, enviar notificaciones importantes y mejorar tu experiencia en nuestro sitio web. También podemos usarla para responder a tus consultas.</p>

                <h2 className="h2-categories mb-3">Protección de Datos Personales</h2>
                <p>Implementamos medidas de seguridad, como cifrado y protocolos de protección de datos, para garantizar la seguridad de tu información personal. No compartiremos tus datos con terceros sin tu consentimiento, salvo en situaciones necesarias para cumplir con servicios solicitados por ti.</p>

                <h2 className="h2-categories mb-3">Derechos del Usuario</h2>
                <p>Tienes derecho a acceder, corregir y eliminar tus datos personales en cualquier momento. Además, puedes optar por no recibir comunicaciones de marketing.</p>

                <h2 className="h2-categories mb-3">Cambios en la Política de Privacidad</h2>
                <p>Nos reservamos el derecho de actualizar esta política en cualquier momento. Te notificaremos sobre cualquier cambio significativo.</p>

                <p>Para obtener más detalles o hacer preguntas sobre nuestra política de privacidad, contáctanos a través de nuestro servicio de atención al cliente.</p>

                {/* 🔗 OUTGOING LINKS para Ahrefs (muy importante) */}
                <hr className="my-4" />
                <div className="mt-4 mb-5">
                    <h2 className="h2-categories mb-3">Enlaces relacionados</h2>
                    <ul>
                        <li><Link to="/informacion-recogida">Información que Recopilamos</Link></li>
                        <li><Link to="/politica-cookies">Política de Cookies</Link></li>
                        <li><Link to="/cambios-politica-cookies">Cambios Política de Cookies</Link></li>
                        <li><Link to="/contact">Contacto / Ejercicio de derechos</Link></li>
                    </ul>
                </div>
            </div>
        </>
    );
};

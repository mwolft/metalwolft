import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from "react-helmet";

export const InformationCollected = () => {
    const [metaData, setMetaData] = useState({});

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/informacion-recogida`)
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

                {/* Twitter */}
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:title" content={metaData.twitter_title || metaData.title} />
                <meta name="twitter:description" content={metaData.twitter_description || metaData.description} />
                <meta name="twitter:image" content={metaData.twitter_image} />

                {/* OpenGraph */}
                <meta property="og:type" content={metaData.og_type} />
                <meta property="og:title" content={metaData.og_title || metaData.title} />
                <meta property="og:description" content={metaData.og_description || metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />

                <link rel="canonical" href={metaData.canonical} />

                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>

            <div className="container" style={{ marginTop: '65px' }}>
                <h1 className='h1-categories'>Información que Recopilamos</h1>
                <p>En Metal Wolft, recopilamos información para mejorar tu experiencia de usuario y para gestionar correctamente los pedidos y servicios que ofrecemos.</p>

                <h2 className="h2-categories mb-3">Tipos de Información Recopilada</h2>
                <ul>
                    <li><strong>Información no personal:</strong> Recopilamos datos de navegación, direcciones IP y cookies de los visitantes de nuestro sitio web. Estos datos se utilizan para analizar el tráfico y mejorar nuestra plataforma.</li>
                    <li><strong>Información personal:</strong> Al registrarte o realizar una compra, recopilamos datos como tu nombre, correo electrónico, dirección postal y número de teléfono, que son necesarios para procesar tu pedido y comunicarte cualquier actualización relevante.</li>
                </ul>

                <h2 className="h2-categories mb-3">Uso de la Información</h2>
                <p>Utilizamos la información recopilada para:</p>
                <ul>
                    <li>Procesar tus pedidos de manera eficaz.</li>
                    <li>Ofrecerte una experiencia personalizada en nuestra página web.</li>
                    <li>Enviar notificaciones sobre el estado de tus pedidos y cualquier novedad relevante.</li>
                </ul>

                <h2 className="h2-categories mb-3">Consentimiento y Derechos del Usuario</h2>
                <p>Al proporcionar tus datos personales, consientes que usemos esta información conforme a lo establecido en esta política. Tienes derecho a solicitar acceso, corrección o eliminación de tus datos en cualquier momento.</p>

                <h2 className="h2-categories mb-3">Actualización de la Información</h2>
                <p>Esta política puede ser actualizada para reflejar cambios en nuestras prácticas de manejo de datos. Te recomendamos revisar esta página periódicamente para estar informado.</p>

                <hr className="my-4" />

                <div className="mt-4 mb-5">
                    <h2 className="h2-categories mb-3">Enlaces relacionados</h2>
                    <ul>
                        <li><Link to="/politica-privacidad">Política de Privacidad</Link></li>
                        <li><Link to="/politica-cookies">Política de Cookies</Link></li>
                        <li><Link to="/cambios-politica-cookies">Cambios en la Política de Cookies</Link></li>
                        <li><Link to="/contact">Contacto (Ejercicio de derechos RGPD)</Link></li>
                    </ul>
                </div>
            </div>
        </>
    );
};

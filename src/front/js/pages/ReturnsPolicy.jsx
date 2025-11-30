import React, { useEffect, useState } from 'react';
import { Helmet } from "react-helmet";
import { Link } from "react-router-dom";

export const ReturnsPolicy = () => {
    const [metaData, setMetaData] = useState({});

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/politica-devolucion`)
            .then(res => {
                if (!res.ok) throw new Error("Error SEO");
                return res.json();
            })
            .then(data => setMetaData(data))
            .catch(err => console.error("SEO Error:", err));
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

                <link rel="canonical" href={metaData.canonical} />

                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>

            <div className="container" style={{ marginTop: '65px' }}>
                <h1 className='h1-categories'>Política de Devoluciones y Garantías</h1>

                {/* CONTENIDO ORIGINAL */}
                <p className='mb-5'>
                    En MetalWolft fabricamos cada reja de forma individual y personalizada según las medidas,
                    especificaciones y acabados seleccionados por el cliente. Por este motivo, nuestra política
                    de devoluciones se ajusta a la normativa española y europea sobre bienes confeccionados a
                    medida (art. 103.c del Real Decreto Legislativo 1/2007).
                </p>

                <h2 className="h2-categories mb-3">1. Productos Personalizados</h2>
                <p>
                    De acuerdo con la ley, los productos fabricados conforme a las especificaciones del consumidor o claramente personalizados <u>no admiten desistimiento ni devolución</u>, salvo defecto o error comprobado.
                </p>

                <p className='mb-5'>
                    Antes de confirmar tu pedido, deberás aceptar expresamente esta condición.
                </p>

                <h2 className="h2-categories mb-3">2. Tolerancias de Fabricación</h2>
                <ul className='mb-5'>
                    <li>Altura: tolerancia máxima ±5 mm.</li>
                    <li>Ancho: tolerancia máxima ±2 mm.</li>
                </ul>

                <h2 className="h2-categories mb-3">3. Acabado y Pintura</h2>
                <p>
                    Puede haber ligeras variaciones de tono o marcas propias del proceso artesanal. En caso de defectos evidentes:
                </p>
                <ul className='mb-5'>
                    <li>Kit de retoque gratuito.</li>
                    <li>Reposición parcial o total.</li>
                    <li>Compensación económica.</li>
                </ul>

                <h2 className="h2-categories mb-3">4. Diseños y Proporciones</h2>
                <p>Los modelos base se adaptan proporcionalmente a cada medida. Las variaciones no son defectos.</p>

                <h2 className="h2-categories mb-3">5. Productos Instalados o Manipulados</h2>
                <p className='mb-5'>
                    Una vez instalados no admiten devolución, salvo defecto existente previo a la instalación.
                </p>

                <h2 className="h2-categories mb-3">6. Procedimiento para Solicitar una Revisión</h2>
                <p className='mb-5'>
                    Formulario de incidencias + fotos → respuesta evaluada por MetalWolft.
                </p>

                <h2 className="h2-categories mb-3">7. Costes y Plazos</h2>
                <p className='mb-5'>
                    Si el defecto es confirmado, MetalWolft cubre los gastos.
                </p>

                <h2 className="h2-categories mb-3">8. Garantía Legal</h2>
                <p className='mb-5'>Mínimo 2 años según normativa vigente.</p>

                <h2 className="h2-categories mb-3">9. Cancelación de Pedidos</h2>
                <p className='mb-5'>Solo posible antes del inicio de fabricación.</p>

                <hr className="my-4" />
                
                <div className="mt-4 mb-5">
                    <h2 className="h2-categories mb-3">Enlaces relacionados</h2>
                    <ul>
                        <li><Link to="/politica-privacidad">Política de Privacidad</Link></li>
                        <li><Link to="/politica-cookies">Política de Cookies</Link></li>
                        <li><Link to="/cambios-politica-cookies">Cambios Política de Cookies</Link></li>
                        <li><Link to="/contact">Contacto / Ejercicio de derechos</Link></li>
                        <li><Link to="/formulario-incidencias">Formulario de Incidencias</Link></li>
                    </ul>
                </div>

            </div>
        </>
    );
};

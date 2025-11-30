import React, { useEffect, useState } from "react";
import { Helmet } from "react-helmet";
import { Link } from "react-router-dom";

export const License = () => {
    const [metaData, setMetaData] = useState({});

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/license`)
            .then((res) => {
                if (!res.ok) throw new Error("Error al cargar SEO");
                return res.json();
            })
            .then((data) => setMetaData(data))
            .catch((err) => console.error("SEO Error:", err));
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

            <div className="container" style={{ marginTop: '65px', marginBottom: '65px' }}>
                <h1 className='h1-categories'>Licencia de Imágenes</h1>

                <div className="col-12">
                    <p>
                        Todas las imágenes en este sitio web están protegidas por derechos de autor y tienen licencia para su uso de la siguiente manera:
                    </p>

                    <ul>
                        <li>
                            <strong>Uso Personal:</strong> Puedes descargar y utilizar estas imágenes para fines personales.
                        </li>
                        <li>
                            <strong>Uso Comercial:</strong> Para cualquier uso comercial, debes obtener una licencia comercial.
                        </li>
                        <li>
                            <strong>Modificación:</strong> No está permitido modificar las imágenes sin permiso explícito.
                        </li>
                        <li>
                            <strong>Atribución:</strong> Se requiere atribución adecuada cuando se utilicen.
                        </li>
                    </ul>

                    <p>
                        Para obtener una licencia comercial, por favor{" "}
                        <Link to="/contact"><u>contáctanos</u></Link>.
                    </p>

                    <p>
                        Recuerda siempre revisar y respetar las condiciones específicas asociadas con cada imagen.
                    </p>

                    <hr className="my-4" />

                    {/* OUTGOING LINKS – FIX Ahrefs */}
                    <div className="mt-4 mb-4">
                        <h2 className="h2-categories mb-3">Enlaces relacionados</h2>
                        <ul>
                            <li><Link to="/politica-privacidad">Política de Privacidad</Link></li>
                            <li><Link to="/politica-cookies">Política de Cookies</Link></li>
                            <li><Link to="/cambios-politica-cookies">Cambios en Política de Cookies</Link></li>
                            <li><Link to="/contact">Contacto</Link></li>
                        </ul>
                    </div>

                    <div className="cart_extra">
                        <Link to="/" className="btn btn-light btn-radius">
                            <div className="add-to-cart">Atrás</div>
                        </Link>
                    </div>
                </div>
            </div>
        </>
    );
};

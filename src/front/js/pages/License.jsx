import React from "react";
import { Helmet } from "react-helmet";

export const License = () => {
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
              <strong>Modificación:</strong> No está permitido modificar las imágenes de ninguna manera sin el permiso explícito.
            </li>
            <li>
              <strong>Atribución:</strong> Se requiere la atribución adecuada cuando se utiliza la imagen en cualquier contexto.
            </li>
          </ul>

          <p>
            Para obtener una licencia comercial, por favor{" "}
            <a href="/contact">
              <u>contáctanos</u>
            </a>.
          </p>

          <p>
            Recuerda siempre revisar y respetar las condiciones específicas asociadas con cada imagen.
          </p>

          <div className="cart_extra">
            <a href="/" className="btn btn-light btn-radius">
              <div className="add-to-cart">Atrás</div>
            </a>
          </div>
        </div>
      </div>
    </>
  );
};

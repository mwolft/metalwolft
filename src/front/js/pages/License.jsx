import React from "react";
import { Helmet } from "react-helmet";

export const License = () => {
  return (
    <>
      <Helmet>
        <meta name="robots" content="noindex, nofollow" />
        <meta name="theme-color" content="#ff324d" />
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

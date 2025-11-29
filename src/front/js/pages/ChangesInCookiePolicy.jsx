import React from 'react';
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../component/Breadcrumb.jsx';
import { Helmet } from "react-helmet";

export const ChangesInCookiePolicy = () => {
    return (
        <>
            <Helmet>
                <title>Cambios en la Política de Cookies | MetalWolft</title>
                <meta
                    name="description"
                    content="Consulta las actualizaciones y cambios realizados en la Política de Cookies de MetalWolft. Mantenemos esta información al día para garantizar transparencia y claridad en el uso de tecnologías de seguimiento."
                />
                <meta name="theme-color" content="#ff324d" />
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

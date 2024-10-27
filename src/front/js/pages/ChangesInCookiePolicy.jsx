import React from 'react';
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../component/Breadcrumb.jsx';

export const ChangesInCookiePolicy = () => {
    return (
        <>
            <Breadcrumb />
            <div className="container">
                <h2>Cambios en nuestra Política de Cookies</h2>
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

import React from 'react';
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../component/Breadcrumb.jsx';
import { Helmet } from "react-helmet";

export const PrivacyCookiesHome = () => {
    return (
        <>
            <Helmet>
                <meta name="robots" content="noindex, nofollow" />
                <meta name="theme-color" content="#ff324d" />
            </Helmet>
            <div className="container" style={{ marginTop: '65px' }}>
                <h1 className='h1-categories'>Políticas de Privacidad y Cookies</h1>
                <p>En Metal Wolft, tu privacidad es nuestra prioridad. Aquí te explicamos cómo manejamos tu información personal y el uso de cookies en nuestro sitio.</p>
                <h2 className="h2-categories mb-3">Gestión de la Información</h2>
                <p>Recopilamos, utilizamos y protegemos tu información personal con el objetivo de mejorar tu experiencia de usuario. Puedes revisar cada una de nuestras políticas y ajustar tus preferencias según tus necesidades.</p>
                <div className="policy-links mt-4">
                    <h3 className="h3-categories">Explora nuestras Políticas</h3>
                    <ul>
                        <li><Link to="/politica-privacidad">Política de Privacidad</Link></li>
                        <li><Link to="/politica-cookies">Política de Cookies</Link></li>
                        <li><Link to="/cookies-esenciales">Gestión de Preferencias de Cookies</Link></li>
                    </ul>
                </div>
                <p>Te recomendamos leer cada una de nuestras políticas para comprender cómo manejamos tus datos y cómo puedes controlar tus preferencias de privacidad en nuestro sitio.</p>
            </div>
        </>
    );
};

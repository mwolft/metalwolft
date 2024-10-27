import React from 'react';
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../component/Breadcrumb.jsx';

export const PrivacyCookiesHome = () => {
    return (
        <>
            <Breadcrumb />
            <div className="container py-5">
                <h1>Políticas de Privacidad y Cookies</h1>
                <p>En Metal Wolft, tu privacidad es nuestra prioridad. Aquí te explicamos cómo manejamos tu información personal y el uso de cookies en nuestro sitio.</p>
                <h2>Gestión de la Información</h2>
                <p>Recopilamos, utilizamos y protegemos tu información personal con el objetivo de mejorar tu experiencia de usuario. Puedes revisar cada una de nuestras políticas y ajustar tus preferencias según tus necesidades.</p>
                <div className="policy-links mt-4">
                    <h3>Explora nuestras Políticas</h3>
                    <ul>
                        <li><Link to="/politica-de-privacidad">Política de Privacidad</Link></li>
                        <li><Link to="/politica-de-cookies">Política de Cookies</Link></li>
                        <li><Link to="/preferencias-de-cookies">Gestión de Preferencias de Cookies</Link></li>
                        <li><Link to="/faq-privacidad-cookies">Preguntas Frecuentes</Link></li>
                    </ul>
                </div>
                <p>Te recomendamos leer cada una de nuestras políticas para comprender cómo manejamos tus datos y cómo puedes controlar tus preferencias de privacidad en nuestro sitio.</p>
            </div>
        </>
    );
};

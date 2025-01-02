import React from 'react';
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../component/Breadcrumb.jsx';

export const CookiesPolicy = () => {
    return (
        <>
            <div className="container" style={{ marginTop: '65px' }}>
                <h1 className='h1-categories'>Política de Cookies</h1>
                <p>Este sitio web utiliza cookies para mejorar la experiencia del usuario. Al utilizar nuestro sitio web, aceptas el uso de cookies conforme a esta política.</p>

                <h2 className="h2-categories mb-3">¿Qué son las Cookies?</h2>
                <p>Las cookies son pequeños archivos de texto que se almacenan en tu dispositivo cuando visitas ciertos sitios web. Permiten que el sitio recuerde tus acciones y preferencias para mejorar tu experiencia de navegación.</p>

                <h2 className="h2-categories mb-3">Tipos de Cookies que Utilizamos</h2>
                <ul>
                    <li><strong>Cookies esenciales:</strong> Son necesarias para el funcionamiento básico del sitio, permitiéndote iniciar sesión y usar funciones esenciales.</li>
                    <li><strong>Cookies de rendimiento:</strong> Nos ayudan a entender cómo los visitantes interactúan con nuestro sitio, recopilando información de forma anónima.</li>
                    <li><strong>Cookies de funcionalidad:</strong> Recuerdan tus preferencias para ofrecer una experiencia personalizada.</li>
                    <li><strong>Cookies de publicidad:</strong> Utilizamos cookies para mostrar anuncios relevantes en nuestro sitio y en sitios de terceros.</li>
                </ul>

                <h2 className="h2-categories mb-3">Control de Cookies</h2>
                <p>Puedes gestionar tus preferencias de cookies desde la configuración de tu navegador. Sin embargo, desactivar ciertas cookies puede afectar la funcionalidad del sitio.</p>

                <h2 className="h2-categories mb-3">Cambios en nuestra Política de Cookies</h2>
                <p>Nos reservamos el derecho de realizar cambios en esta política en cualquier momento. Publicaremos las actualizaciones en esta página.</p>

                <p>Si tienes preguntas sobre nuestra política de cookies, contáctanos a través de nuestros canales de atención al cliente.</p>
            </div>
        </>
    );
};
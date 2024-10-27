import React from 'react';
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../component/Breadcrumb.jsx';

export const PrivacyPolicy = () => {
    return (
        <>
            <Breadcrumb />
            <div className="container py-5">
                <h1>Política de Privacidad</h1>
                <p>Tu privacidad es importante para nosotros. Esta política describe cómo recopilamos, utilizamos y protegemos tu información personal.</p>

                <h2>Información que Recopilamos</h2>
                <p>Recopilamos información personal cuando te registras en nuestro sitio, realizas una compra o navegas en nuestra web. La información puede incluir tu nombre, correo electrónico, dirección postal y número de teléfono.</p>

                <h2>Uso de la Información</h2>
                <p>Utilizamos la información para procesar pedidos, enviar notificaciones importantes y mejorar tu experiencia en nuestro sitio web. También podemos usarla para responder a tus consultas.</p>

                <h2>Protección de Datos Personales</h2>
                <p>Implementamos medidas de seguridad, como cifrado y protocolos de protección de datos, para garantizar la seguridad de tu información personal. No compartiremos tus datos con terceros sin tu consentimiento, salvo en situaciones necesarias para cumplir con servicios solicitados por ti.</p>

                <h2>Derechos del Usuario</h2>
                <p>Tienes derecho a acceder, corregir y eliminar tus datos personales en cualquier momento. Además, puedes optar por no recibir comunicaciones de marketing.</p>

                <h2>Cambios en la Política de Privacidad</h2>
                <p>Nos reservamos el derecho de actualizar esta política en cualquier momento. Te notificaremos sobre cualquier cambio significativo.</p>

                <p>Para obtener más detalles o hacer preguntas sobre nuestra política de privacidad, contáctanos a través de nuestro servicio de atención al cliente.</p>
            </div>
        </>
    );
};

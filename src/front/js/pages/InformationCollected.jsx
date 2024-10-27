import React from 'react';
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../component/Breadcrumb.jsx';

export const InformationCollected = () => {
    return (
        <>
            <Breadcrumb />
            <div className="container py-5">
            <h1>Información que Recopilamos</h1>
            <p>En Metal Wolft, recopilamos información para mejorar tu experiencia de usuario y para gestionar correctamente los pedidos y servicios que ofrecemos.</p>

            <h2>Tipos de Información Recopilada</h2>
            <ul>
                <li><strong>Información no personal:</strong> Recopilamos datos de navegación, direcciones IP y cookies de los visitantes de nuestro sitio web. Estos datos se utilizan para analizar el tráfico y mejorar nuestra plataforma.</li>
                <li><strong>Información personal:</strong> Al registrarte o realizar una compra, recopilamos datos como tu nombre, correo electrónico, dirección postal y número de teléfono, que son necesarios para procesar tu pedido y comunicarte cualquier actualización relevante.</li>
            </ul>

            <h2>Uso de la Información</h2>
            <p>Utilizamos la información recopilada para:</p>
            <ul>
                <li>Procesar tus pedidos de manera eficaz.</li>
                <li>Ofrecerte una experiencia personalizada en nuestra página web.</li>
                <li>Enviar notificaciones sobre el estado de tus pedidos y cualquier novedad relevante.</li>
            </ul>

            <h2>Consentimiento y Derechos del Usuario</h2>
            <p>Al proporcionar tus datos personales, consientes que usemos esta información conforme a lo establecido en esta política. Tienes derecho a solicitar acceso, corrección o eliminación de tus datos en cualquier momento.</p>

            <h2>Actualización de la Información</h2>
            <p>Esta política puede ser actualizada para reflejar cambios en nuestras prácticas de manejo de datos. Te recomendamos revisar esta página periódicamente para estar informado.</p>
        </div>
        </>
    );
};

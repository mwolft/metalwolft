import React, { useEffect, useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import '../../styles/breadcrumb.css';

export const Breadcrumb = () => {
    const location = useLocation();
    const [breadcrumbs, setBreadcrumbs] = useState([]);

    useEffect(() => {
        const pathnames = location.pathname.split('/').filter((x) => x);
        const breadcrumbsArray = pathnames.map((value, index) => {
            const to = `/${pathnames.slice(0, index + 1).join('/')}`;
            return { name: value, path: to };
        });

        setBreadcrumbs(breadcrumbsArray);
    }, [location]);


    const breadcrumbNameMap = {
        'rejas-para-ventanas': 'Rejas para Ventanas',
        'vallados-metalicos-exteriores': 'Vallados Metálicos Exteriores',
        'puertas-peatonales-metalicas' : 'Puertas Peatonales Metálicas',
        'puertas-correderas-exteriores' : 'Puertas Correderas Exteriores',
        'cerramientos-de-cocina-con-cristal' : 'Cerramientos de Cocina con Cristal',
        'puertas-correderas-interiores' : 'Puertas Correderas Interiores',
        'blogs': 'Blog de Carpintería Metálica',
        'medir-hueco-rejas-para-ventanas': 'Cómo Medir el Hueco para Rejas de Ventanas',
        'instalation-rejas-para-ventanas': 'Instalación de Rejas para Ventanas con Tornillos Inviolables',
        'cookies-esenciales': 'Cookies',
        'politica-privacidad': 'Política de Privacidad',
        'politica-cookies': 'Política de Cookies',
        'informacion-recogida': 'Información Recogida',
        'cambios-politica-cookies': 'Cambios de Política de Cookies',
        'contact': 'Comunícate con Nuestro Equipo'
    };
    

    // Función para obtener el nombre amigable
    const getDisplayName = (breadcrumb) => {
        return breadcrumbNameMap[breadcrumb.name] || breadcrumb.name;
    };

    // título para el h1 segun el último breadcrumb)
    const pageTitle = breadcrumbs.length > 0 ? getDisplayName(breadcrumbs[breadcrumbs.length - 1]) : 'Inicio';

    return (
        <div className="breadcrumb">
            <h1 className='h1-breadcrumb'>{pageTitle}</h1>
            <p className='p-breadcrumb'>
                <Link className="a-breadcrumb" to="/">Inicio</Link>
                {breadcrumbs.map((breadcrumb, index) => {
                    const isLast = index === breadcrumbs.length - 1;
                    const name = getDisplayName(breadcrumb);
                    return isLast ? (
                        <span className="span-bradcrumb" key={breadcrumb.path}> / {name}</span>
                    ) : (
                        <span className="span-bradcrumb" key={breadcrumb.path}>
                            {' '}
                            / <Link to={breadcrumb.path}>{name}</Link>
                        </span>
                    );
                })}
            </p>
        </div>
    );
};

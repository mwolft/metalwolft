import React, { useEffect, useState } from "react";
import { useLocation, Link } from "react-router-dom";

const DeliveryEstimateBanner = () => {
    const [estimate, setEstimate] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const location = useLocation();
    const isInPlazosPage = location.pathname === '/plazos-entrega-rejas-a-medida';

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/delivery-estimate`)
            .then((response) => {
                if (!response.ok) throw new Error('Error fetching delivery estimate');
                return response.json();
            })
            .then((data) => setEstimate(data))
            .catch((error) => console.error(error))
            .finally(() => setIsLoading(false));
    }, []);

    const formatDeliveryRange = (startDateStr, endDateStr) => {
        const startDate = new Date(startDateStr);
        const endDate = new Date(endDateStr);

        const startDay = startDate.getDate();
        const endDay = endDate.getDate();

        const startMonth = startDate.toLocaleDateString('es-ES', { month: 'long' });
        const endMonth = endDate.toLocaleDateString('es-ES', { month: 'long' });

        if (startMonth === endMonth) {
            return `entre el ${startDay} y el ${endDay} de ${startMonth}`;
        } else {
            return `entre el ${startDay} de ${startMonth} y el ${endDay} de ${endMonth}`;
        }
    };

    const today = new Date().toLocaleDateString('es-ES');

    if (isLoading) {
        return (
            <div style={skeletonStyles.container}>
                <div style={skeletonStyles.icon}></div>
                <div style={skeletonStyles.textLineContainer}>
                    <div style={skeletonStyles.textLine}></div>
                    <div style={{ ...skeletonStyles.textLine, width: '60%' }}></div>
                </div>
            </div>
        );
    }

    if (!estimate || !estimate.is_active) return null;

    return (
        <div style={bannerStyles.container}>
            <i className="fas fa-circle-info" style={bannerStyles.icon}></i>
            <span>
                La previsión de entrega a día de hoy ({today}): <b>{formatDeliveryRange(estimate.start_date, estimate.end_date)}</b>.
                {!isInPlazosPage && (
                    <Link
                        to="/plazos-entrega-rejas-a-medida"
                        style={bannerStyles.link}
                    >
                        Leer más
                    </Link>
                )}
            </span>
        </div>
    );
};

// Skeleton Styles
const skeletonStyles = {
    container: {
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        padding: '15px 20px',
        backgroundColor: '#e0e0e0',
        borderRadius: '10px',
        animation: 'pulse 1.5s infinite'
    },
    icon: {
        width: '24px',
        height: '24px',
        borderRadius: '50%',
        backgroundColor: '#d0d0d0',
        flexShrink: 0
    },
    textLineContainer: {
        flex: 1
    },
    textLine: {
        height: '12px',
        backgroundColor: '#d0d0d0',
        borderRadius: '6px'
    }
};

// Banner Styles
const bannerStyles = {
    container: {
        backgroundColor: '#CFE2FF',
        border: '1px solid #052C65',
        padding: '15px 20px',
        borderRadius: '10px',
        color: '#052C65',
        fontSize: '16px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
    },
    icon: {
        fontSize: '1.5rem',
        color: '#052C65'
    },
    link: {
        color: '#0d6efd',
        textDecoration: 'underline',
        marginLeft: '5px'
    }
};

export default DeliveryEstimateBanner;

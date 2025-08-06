import React, { useState, useEffect } from 'react';
import CookieConsent from 'react-cookie-consent';

export const CookieBanner = () => {
    const [cookiesAccepted, setCookiesAccepted] = useState(false);
    const [onlyEssentialCookies, setOnlyEssentialCookies] = useState(false);

    useEffect(() => {
        const consentStatus = localStorage.getItem('cookiesConsent');
        if (consentStatus === 'all') {
            setCookiesAccepted(true);
            updateGoogleConsent('granted');
        } else if (consentStatus === 'essential') {
            setOnlyEssentialCookies(true);
            updateGoogleConsent('denied');
        }
    }, []);

    const updateGoogleConsent = (status) => {
        if (window.gtag) {
            window.gtag('consent', 'update', {
                'ad_storage': status,
                'analytics_storage': status,
                'ad_user_data': status,
                'ad_personalization': status
            });
        }
    };

    const handleAcceptAll = () => {
        localStorage.setItem('cookiesConsent', 'all');
        setCookiesAccepted(true);
        setOnlyEssentialCookies(false);
        updateGoogleConsent('granted');
    };

    const handleAcceptEssential = () => {
        localStorage.setItem('cookiesConsent', 'essential');
        setOnlyEssentialCookies(true);
        setCookiesAccepted(false);
        updateGoogleConsent('denied');
    };

    return (
        <CookieConsent
            buttonText="Aceptar todas"
            enableDeclineButton
            declineButtonText="Solo esenciales"
            onAccept={handleAcceptAll}
            onDecline={handleAcceptEssential}
            style={{ background: "#2B373B" }}
            buttonStyle={{ color: "#4e503b", fontSize: "13px" }}
            declineButtonStyle={{ color: "#ffffff", backgroundColor: "#ff324d", fontSize: "13px" }}
        >
            Usamos cookies para mejorar tu experiencia. Puedes aceptar todas las cookies o solo las esenciales.
        </CookieConsent>
    );
};

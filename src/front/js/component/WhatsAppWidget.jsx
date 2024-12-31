import React, { useState, useEffect } from "react";
import "../../styles/whatsapp-bot.css";

export const WhatsAppWidget = ({ whatsappNumber, placeholderText = "Escribenos por WhatsApp", widgetText = "¿Le podemos ayudar?", botImage }) => {
    const [showWidget, setShowWidget] = useState(false);
    const [userMessage, setUserMessage] = useState("");
    const [isMinimized, setIsMinimized] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setShowWidget(true);
        }, 10000); // El widget aparece tras 10 segundos
        return () => clearTimeout(timer);
    }, []);

    const closeWidget = () => {
        setShowWidget(false);
        setIsMinimized(true); // Minimiza el widget
    };

    const openWidget = () => {
        setShowWidget(true);
        setIsMinimized(false); // Restaura el widget completo
    };

    const whatsappUrl = whatsappNumber ? `https://wa.me/${whatsappNumber}` : null;

    return (
        <>
            {isMinimized && (
                <div className="minimized-widget" onClick={openWidget}>
                    <i className="fa fa-whatsapp" aria-hidden="true"></i>
                </div>
            )}

            {showWidget && (
                <div className="whatsapp-widget">
                    <div className="widget-header">
                        <img
                            src={botImage || "https://res.cloudinary.com/dewanllxn/image/upload/v1735631180/welder-bot_tqxadc.png"}
                            alt="Bot Soldador"
                            className="widget-image"
                        />
                        <span>{widgetText}</span>
                        <button onClick={closeWidget} className="close-widget">✖</button>
                    </div>
                    <div className="widget-message">
                        <div className="widget-input-container">
                            <input
                                type="text"
                                placeholder={placeholderText}
                                className="widget-input"
                                value={userMessage}
                                onChange={(e) => setUserMessage(e.target.value)}
                            />
                            <button
                                className="widget-send-button"
                                onClick={() => {
                                    if (whatsappUrl) {
                                        window.open(
                                            `${whatsappUrl}?text=${encodeURIComponent(userMessage)}`,
                                            "_blank"
                                        );
                                    } else {
                                        console.error("Número de WhatsApp no definido o inválido.");
                                        alert("El número de WhatsApp no está configurado correctamente.");
                                    }
                                }}
                            >
                                <i className="fa fa-paper-plane" aria-hidden="true"></i>
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

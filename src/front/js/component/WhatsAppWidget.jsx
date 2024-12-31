import React, { useState, useEffect } from "react";
import "../../styles/whatsapp-bot.css"; 

export const WhatsAppWidget = ({ whatsappNumber, placeholderText = "Escribenos por WhatsApp", widgetText = "¿Le podemos ayudar?", botImage }) => {
    const [showWidget, setShowWidget] = useState(false);
    const [userMessage, setUserMessage] = useState("");
    const [isMinimized, setIsMinimized] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setShowWidget(true);
        }, 10000);
        return () => clearTimeout(timer);
    }, []);

    const closeWidget = () => {
        setShowWidget(false);
        setIsMinimized(true);
    };

    const openWidget = () => {
        setShowWidget(true);
        setIsMinimized(false);
    };

    const whatsappUrl = `https://wa.me/${whatsappNumber}`;

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
                            src="https://res.cloudinary.com/dewanllxn/image/upload/v1735631180/welder-bot_tqxadc.png"
                            alt="Bot Soldador"
                            className="widget-image"
                        />
                        <span>¿Le podemos ayudar?</span>
                        <button onClick={closeWidget} className="close-widget">✖</button>
                    </div>
                    <div className="widget-message">
                        <div className="widget-input-container">
                            <input
                                type="text"
                                placeholder="Escribenos por WhatsApp"
                                className="widget-input"
                                value={userMessage}
                                onChange={(e) => setUserMessage(e.target.value)}
                            />
                            <button
                                className="widget-send-button"
                                onClick={() =>
                                    window.open(
                                        `${whatsappUrl}?text=${encodeURIComponent(userMessage)}`,
                                        "_blank"
                                    )
                                }
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


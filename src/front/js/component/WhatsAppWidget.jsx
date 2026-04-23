import React, { useState, useEffect, useRef } from "react";
import "../../styles/whatsapp-bot.css";

const SESSION_AUTO_SHOWN_KEY = "mw_whatsapp_auto_shown";
const SESSION_MINIMIZED_KEY = "mw_whatsapp_minimized";
const AUTO_OPEN_DELAY_MS = 10000;
const AUTO_MINIMIZE_DELAY_MS = 5000;

export const WhatsAppWidget = ({ whatsappNumber, placeholderText = "Escribenos por WhatsApp", widgetText = "¿Le podemos ayudar?", botImage }) => {
    const [showWidget, setShowWidget] = useState(false);
    const [userMessage, setUserMessage] = useState("");
    const [isMinimized, setIsMinimized] = useState(false);
    const autoOpenTimerRef = useRef(null);
    const autoMinimizeTimerRef = useRef(null);
    const hasUserInteractedRef = useRef(false);

    const persistSessionFlag = (key, value) => {
        if (typeof window === "undefined") return;
        window.sessionStorage.setItem(key, value);
    };

    const readSessionFlag = (key) => {
        if (typeof window === "undefined") return false;
        return window.sessionStorage.getItem(key) === "1";
    };

    const clearAutoMinimizeTimer = () => {
        if (autoMinimizeTimerRef.current) {
            clearTimeout(autoMinimizeTimerRef.current);
            autoMinimizeTimerRef.current = null;
        }
    };

    const minimizeWidget = () => {
        clearAutoMinimizeTimer();
        setShowWidget(false);
        setIsMinimized(true);
        persistSessionFlag(SESSION_MINIMIZED_KEY, "1");
    };

    const registerInteraction = () => {
        hasUserInteractedRef.current = true;
        clearAutoMinimizeTimer();
    };

    useEffect(() => {
        const hasAutoShownInSession = readSessionFlag(SESSION_AUTO_SHOWN_KEY);
        const isMinimizedInSession = readSessionFlag(SESSION_MINIMIZED_KEY);

        if (hasAutoShownInSession || isMinimizedInSession) {
            setShowWidget(false);
            setIsMinimized(true);
            return undefined;
        }

        autoOpenTimerRef.current = setTimeout(() => {
            hasUserInteractedRef.current = false;
            persistSessionFlag(SESSION_AUTO_SHOWN_KEY, "1");
            setShowWidget(true);
            setIsMinimized(false);

            autoMinimizeTimerRef.current = setTimeout(() => {
                if (!hasUserInteractedRef.current) {
                    minimizeWidget();
                }
            }, AUTO_MINIMIZE_DELAY_MS);
        }, AUTO_OPEN_DELAY_MS);

        return () => {
            if (autoOpenTimerRef.current) {
                clearTimeout(autoOpenTimerRef.current);
                autoOpenTimerRef.current = null;
            }
            clearAutoMinimizeTimer();
        };
    }, []);

    const closeWidget = () => {
        registerInteraction();
        minimizeWidget();
    };

    const openWidget = () => {
        registerInteraction();
        persistSessionFlag(SESSION_AUTO_SHOWN_KEY, "1");
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
                <div
                    className="whatsapp-widget"
                    onMouseEnter={registerInteraction}
                    onClick={registerInteraction}
                    onFocusCapture={registerInteraction}
                >
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
                                onChange={(e) => {
                                    registerInteraction();
                                    setUserMessage(e.target.value);
                                }}
                            />
                            <button
                                className="widget-send-button"
                                onClick={() => {
                                    registerInteraction();
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

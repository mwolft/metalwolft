import React, { useEffect, useState } from "react";
import "../../styles/notification.css";

export const Notification = ({ message, duration, onClose }) => {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        // Configurar el temporizador para ocultar la notificación
        const timer = setTimeout(() => {
            setVisible(false);
            if (onClose) {
                onClose();
            }
        }, duration || 3000); // Por defecto, el mensaje dura 3 segundos

        // Limpiar el temporizador si el componente se desmonta antes de tiempo
        return () => clearTimeout(timer);
    }, [duration, onClose]);

    if (!visible) return null;

    return (
        <div className="notification">
            {message}
        </div>
    );
};


import React, { useEffect, useState } from "react";

const MaintenancePopup = () => {
  const [isVisible, setIsVisible] = useState(true);
  const [timeLeft, setTimeLeft] = useState("");

  useEffect(() => {
    const targetDate = new Date("2025-07-15T23:59:59");

    const updateCountdown = () => {
      const now = new Date();
      const diff = targetDate - now;

      if (diff <= 0) {
        setTimeLeft("¡Últimas horas!");
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const minutes = Math.floor((diff / (1000 * 60)) % 60);
      const seconds = Math.floor((diff / 1000) % 60);

      setTimeLeft(`${days} d ${hours} h ${minutes} min ${seconds} s`);
    };

    updateCountdown(); // primera ejecución inmediata
    const timer = setInterval(updateCountdown, 1000); // cada segundo

    return () => clearInterval(timer);
  }, []);

  if (!isVisible) return null;

  return (
    <div style={styles.overlay}>
      <div style={styles.popup}>
        <button style={styles.closeButton} onClick={() => setIsVisible(false)}>
          ✖
        </button>
        <i className="fas fa-tags" style={{color: "#f44336", fontSize: '5rem' }}></i>
        <h2 style={styles.title}>🚨 ¡Rebajas en todas las Rejas!</h2>
        <p style={styles.message}>
          Hasta el <strong>15 de julio</strong>
        </p>
        <p style={styles.timer}>
          ⏳ Tiempo restante: {timeLeft}
        </p>
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: "fixed",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    zIndex: 9999,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  popup: {
    backgroundColor: "#fff",
    padding: "25px",
    borderRadius: "12px",
    textAlign: "center",
    boxShadow: "0 8px 16px rgba(0,0,0,0.2)",
    width: "90%",
    maxWidth: "420px",
    position: "relative",
  },
  closeButton: {
    position: "absolute",
    top: "12px",
    right: "12px",
    backgroundColor: "transparent",
    border: "none",
    fontSize: "18px",
    cursor: "pointer",
    color: "#888",
  },
  title: {
    fontSize: "22px",
    color: "#f44336",
    marginBottom: "12px",
    marginTop: "30px",
  },
  message: {
    fontSize: "16px",
    color: "#444",
    marginBottom: "10px"
  },
  timer: {
    fontSize: "15px",
    color: "#666",
    fontStyle: "italic"
  }
};

export default MaintenancePopup;

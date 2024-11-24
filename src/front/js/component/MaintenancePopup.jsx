import React, { useState } from "react";

const MaintenancePopup = () => {
  const [isVisible, setIsVisible] = useState(true); 

  if (!isVisible) return null;

  return (
    <div style={styles.overlay}>
      <div style={styles.popup}>
        <button style={styles.closeButton} onClick={() => setIsVisible(false)}>
          ✖
        </button>
        <h2 style={styles.title}>Sitio web en mantenimiento</h2>
        <p style={styles.message}>
          Disculpe las molestias. Estamos trabajando para mejorar su experiencia.
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
    backgroundColor: "rgba(0, 0, 0, 0.6)", 
    zIndex: 9999,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  popup: {
    backgroundColor: "#ffffff", 
    padding: "20px",
    borderRadius: "8px",
    textAlign: "center",
    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
    width: "80%",
    maxWidth: "400px",
    position: "relative",
  },
  closeButton: {
    position: "absolute",
    top: "10px",
    right: "10px",
    backgroundColor: "transparent",
    border: "none",
    fontSize: "16px",
    cursor: "pointer",
    color: "#999",
  },
  title: {
    fontSize: "20px",
    color: "#f44336", 
    marginBottom: "10px",
    marginTop: "30px",
  },
  message: {
    fontSize: "16px",
    color: "#333333", 
  },
};

export default MaintenancePopup;

import React, { useEffect, useState } from "react";

const MaintenancePopup = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [estimate, setEstimate] = useState(null);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 6000);

    fetch('https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/api/delivery-estimate')
      .then((response) => {
        if (!response.ok) throw new Error(`Error: ${response.status} ${response.statusText}`);
        return response.json();
      })
      .then((data) => setEstimate(data))
      .catch((error) => console.error("Error fetching delivery estimate:", error));

    return () => clearTimeout(timer);
  }, []);

  const handleClose = () => setIsVisible(false);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  };

  const formatDeliveryRange = (startDateStr, endDateStr) => {
    const startDate = new Date(startDateStr);
    const endDate = new Date(endDateStr);

    const startDay = startDate.getDate();
    const endDay = endDate.getDate();

    const startMonth = startDate.toLocaleDateString('es-ES', { month: 'long' });
    const endMonth = endDate.toLocaleDateString('es-ES', { month: 'long' });

    if (startMonth === endMonth) {
      return `Entre el ${startDay} y el ${endDay} de ${startMonth}`;
    } else {
      return `Entre el ${startDay} de ${startMonth} y el ${endDay} de ${endMonth}`;
    }
  };

  const today = new Date().toLocaleDateString('es-ES');

  if (!isVisible || !estimate || !estimate.is_active) return null;

  return (
    <div style={styles.overlay} onClick={handleOverlayClick}>
      <div style={styles.popup}>
        <button style={styles.closeButton} onClick={handleClose}>
          ✖
        </button>

        <div style={styles.dateHeader}>
          <i className="fas fa-calendar-alt" style={styles.calendarIcon}></i>
          <span style={styles.currentDate}>{today}</span>
        </div>

        <h2 style={styles.title}>
          <span style={styles.titleHighlight}>
            <b>Previsión de fecha de entrega:</b>
          </span>
        </h2>

        <div style={styles.message}>
          <div style={styles.deliveryRangeBadge}>
            {formatDeliveryRange(estimate.start_date, estimate.end_date)}
          </div>
        </div>

        <div style={styles.trustMessage}>
          Procesamos y actualizamos cada pedido a diario para ofrecerte siempre la previsión más precisa.<br />
          Si necesitas recibir tu pedido en una fecha concreta, no dudes en contactarnos.
        </div>

        <img
          src="https://res.cloudinary.com/dewanllxn/image/upload/v1754155736/estado-de-envio_uglnqu.jpg"
          alt="Entrega"
          style={styles.image}
        />
        <div
          style={{
            ...styles.deliveryRangeBadge,
            backgroundColor: isHovered ? '#d32f2f' : '#ff324d',
            cursor: 'pointer'
          }}
          onClick={handleClose}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          Cerrar
        </div>
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
    maxWidth: "720px",
    position: "relative",
  },
  closeButton: {
    position: "absolute",
    top: "12px",
    right: "12px",
    backgroundColor: "transparent",
    border: "1px solid #ccc",
    borderRadius: "6px",
    padding: "4px 8px",
    fontSize: "16px",
    cursor: "pointer",
    color: "#555",
    transition: "all 0.2s ease-in-out",
  },
  closeButtonBottom: {
    marginTop: '15px',
    padding: '10px 20px',
    fontSize: '16px',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer'
  },
  dateHeader: {
    display: 'flex',
    alignItems: 'end',
    justifyContent: 'center',
    gap: '12px',
    marginBottom: '20px'
  },
  calendarIcon: {
    color: "#ff324d",
    fontSize: '5rem'
  },
  currentDate: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#333'
  },
  title: {
    fontSize: "20px",
    color: "#333",
    textTransform: "uppercase",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: "12px",
    marginTop: "30px",
  },
  titleHighlight: {
    borderLeft: '4px solid #f44336',
    paddingLeft: '10px'
  },
  message: {
    fontSize: "16px",
    color: "#444",
    marginBottom: "10px"
  },
  deliveryRangeBadge: {
    display: 'inline-block',
    backgroundColor: '#ff324d',
    color: '#fff',
    padding: '6px 14px',
    borderRadius: '20px',
    fontWeight: 'bold',
    fontSize: '16px',
    margin: '10px 0'
  },
  trustMessage: {
    maxWidth: '100%',
    margin: '15px 1px 25px 1px',
    fontSize: '14px',
    color: '#777',
    textAlign: 'center',
    lineHeight: '1.4'
  },
  image: {
    width: '100%',
    height: 'auto',
    maxWidth: '750px',
    marginBottom: '20px',
    objectFit: 'contain',
    borderRadius: '12px',
    backgroundColor: '#f5f5f5'
  }
};

export default MaintenancePopup;

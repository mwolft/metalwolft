import React, { useEffect, useState } from "react";

export const SeasonalBanner = () => {
    const [visible, setVisible] = useState(false);
    const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

    useEffect(() => {
        const timeout = setTimeout(() => setVisible(true), 50);
        return () => clearTimeout(timeout);
    }, []);


    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth < 1202);
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);


    // --- ESTILOS ---

    const containerStyle = {
        backgroundColor: "#ff324d", // Rojo intenso de la foto
        color: "white",
        padding: "20px 20px 50px 20px",
        borderRadius: "0", // Los banners de rebajas suelen ser full-width o rectangulares
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        position: "relative", // Necesario para los elementos absolutos (fondo)
        overflow: "hidden", // Para que el texto de fondo no se salga
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(10px)",
        transition: "opacity 0.6s ease-out, transform 0.6s ease-out",
        boxShadow: "0 4px 15px rgba(0,0,0,0.3)",
        fontFamily: "'Segoe UI', Roboto, Helvetica, Arial, sans-serif", // Fuente robusta
        minHeight: "250px", // Altura suficiente para el diseño
        marginBottom: "20px"
    };

    const topTextStyle = {
        fontSize: "1rem",
        fontWeight: "700",
        letterSpacing: "1px",
        textTransform: "uppercase",
        marginBottom: "-10px", // Acercarlo al texto grande
        zIndex: 2,
        position: "relative"
    };

    const mainTitleContainerStyle = {
        position: "relative",
        zIndex: 2,
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
    };

    const mainTextStyle = {
        fontSize: "clamp(3rem, 8vw, 6rem)", // Responsive: grande pero adaptable
        fontWeight: "900", // Extra bold
        margin: "15px",
        textTransform: "uppercase",
        lineHeight: "1",
        textShadow: "0 2px 10px rgba(0,0,0,0.2)"
    };

    // Estilo para simular el texto borroso del fondo (Efecto Watermark)
    const backgroundWatermarkStyle = {
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        fontSize: "8rem",
        fontWeight: "900",
        color: "rgba(0, 0, 0, 0.1)",
        zIndex: 0,
        whiteSpace: "nowrap",
        pointerEvents: "none",
        userSelect: "none"
    };

    // Estilo para la imagen del carrito (Overlay)
    const cartImageStyle = {
        height: "140px",
        width: "auto",
        position: "absolute",
        zIndex: 3,
        bottom: "10px",
        right: "12%",
        filter: "drop-shadow(0 5px 10px rgba(0,0,0,0.3))",
        transform: visible ? "scale(1) rotate(-10deg)" : "scale(0.8) rotate(0deg)",
        transition: "transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)"
    };
    const cartImageMobile = {
        height: "100px",
        width: "auto",
        position: "absolute",
        zIndex: 3,
        bottom: "0px",
        right: "15%",
        transform: visible
            ? "translateX(50%) scale(1) rotate(-5deg)"
            : "translateX(50%) scale(0.8) rotate(0deg)",
        filter: "drop-shadow(0 3px 6px rgba(0,0,0,0.25))",
        transition: "transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)"
    };
    const stylishSubTextStyle = {
        fontSize: ".9rem",
        fontWeight: 300,
        fontFamily: "Georgia, 'Times New Roman', serif",
        fontStyle: "italic",
        opacity: 0.9,
        marginTop: "0px",
        letterSpacing: "0.3px",
        maxWidth: "900px",
        lineHeight: "1.35",
        zIndex: 2,
    };
    const snowImageStyle = {
        height: "150px",
        width: "auto",
        position: "absolute",
        zIndex: 3,
        bottom: "0",
        left: "13%",
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(20px)",
        transition: "opacity 0.8s ease, transform 0.8s ease",
        filter: "drop-shadow(0 5px 10px rgba(0,0,0,0.25))"
    };
    const snowImageMobile = {
        height: "80px",
        width: "auto",
        position: "absolute",
        zIndex: 3,
        bottom: "5px",
        left: "30%", // centrado visualmente
        transform: visible
            ? "translateX(-120%) translateY(0)"
            : "translateX(-120%) translateY(20px)",
        opacity: visible ? 0.9 : 0,
        transition: "opacity 0.8s ease, transform 0.8s ease",
    };



    return (
        <div style={containerStyle}>
            {/* Texto de fondo decorativo (Watermark) */}
            <div style={backgroundWatermarkStyle}>
                REBAJAS REBAJAS
            </div>

            {/* Contenido Principal */}
            <p style={topTextStyle}>Solo disponible durante la campaña de invierno 2025</p>

            <div style={mainTitleContainerStyle}>
                <p style={mainTextStyle}>REBAJAS</p>
            </div>
            <p style={stylishSubTextStyle}>Aprovecha la temporada baja en rejas para ventanas...lo agradecerás en primavera.</p>
            <img
                src="https://res.cloudinary.com/dewanllxn/image/upload/v1764142951/snow-ofer_qdj6xk.png"
                alt="Copos de nieve"
                style={isMobile ? snowImageMobile : snowImageStyle}
            />

            <img
                src="https://res.cloudinary.com/dewanllxn/image/upload/v1764137819/cart-season_wh3lpv.png"
                alt="Carrito de compras"
                style={isMobile ? cartImageMobile : cartImageStyle}
            />

        </div>
    );
};
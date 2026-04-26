import React from "react";
import { Link } from "react-router-dom";

export const BodyHomeTertiary = ({ variant = "contact-header" }) => {
    if (variant === "conversion") {
        return (
            <div className="container home-conversion-support">
                <div className="home-buying-help">
                    <div className="home-buying-help-header">
                        <p className="home-section-eyebrow">Antes de comprar</p>
                        <h2 className="h1-home home-help-title">Todo lo que necesitas para medir, instalar y decidir</h2>
                        <p className="home-help-copy">
                            Si quieres ir a lo seguro, apóyate en nuestras guías prácticas antes de configurar tu reja.
                        </p>
                    </div>
                    <div className="row g-3">
                        <div className="col-12 col-md-4">
                            <div className="home-help-card">
                                <h3 className="home-help-card-title">Cómo medir tu ventana</h3>
                                <p className="home-help-card-copy">
                                    Aprende a tomar alto y ancho correctamente para calcular el precio sin errores.
                                </p>
                                <Link to="/medir-hueco-rejas-para-ventanas" className="home-help-card-link">
                                    Ver guía de medición
                                </Link>
                            </div>
                        </div>
                        <div className="col-12 col-md-4">
                            <div className="home-help-card">
                                <h3 className="home-help-card-title">Guía de instalación</h3>
                                <p className="home-help-card-copy">
                                    Revisa las opciones de anclaje y qué instalación conviene más en cada caso.
                                </p>
                                <Link to="/instalation-rejas-para-ventanas" className="home-help-card-link">
                                    Ver guía de instalación
                                </Link>
                            </div>
                        </div>
                        <div className="col-12 col-md-4">
                            <div className="home-help-card">
                                <h3 className="home-help-card-title">Plazos de fabricación y entrega</h3>
                                <p className="home-help-card-copy">
                                    Consulta tiempos orientativos para planificar tu compra con más tranquilidad.
                                </p>
                                <Link to="/plazos-entrega-rejas-a-medida" className="home-help-card-link">
                                    Consultar plazos
                                </Link>
                            </div>
                        </div>
                    </div>
                    <p className="home-help-footer">
                        También puedes visitar nuestro <Link to="/blogs">blog</Link> o escribirnos desde <Link to="/contact">contacto</Link> si necesitas más ayuda.
                    </p>
                </div>

                <div className="row g-3 home-trust-grid">
                    <div className="col-12 col-sm-6 col-xl-3">
                        <div className="home-trust-item">
                            <strong>Fabricación a medida</strong>
                            <span>Cada reja se adapta a tus medidas reales.</span>
                        </div>
                    </div>
                    <div className="col-12 col-sm-6 col-xl-3">
                        <div className="home-trust-item">
                            <strong>Envío a toda España</strong>
                            <span>Compra online y recibe tu pedido donde lo necesites.</span>
                        </div>
                    </div>
                    <div className="col-12 col-sm-6 col-xl-3">
                        <div className="home-trust-item">
                            <strong>IVA incluido</strong>
                            <span>Precios claros desde el primer momento.</span>
                        </div>
                    </div>
                    <div className="col-12 col-sm-6 col-xl-3">
                        <div className="home-trust-item">
                            <strong>Atención por WhatsApp</strong>
                            <span>Te ayudamos si tienes dudas antes de comprar.</span>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (variant === "home-contact-cta") {
        return (
            <div className="container home-contact-cta">
                <div className="home-contact-cta-box">
                    <p className="home-section-eyebrow">Ayuda rápida</p>
                    <h2 className="h1-home home-contact-cta-title">¿Tienes dudas antes de comprar?</h2>
                    <p className="home-contact-cta-copy">
                        Te ayudamos a elegir medidas, instalación o cualquier detalle antes de hacer tu pedido.
                    </p>
                    <div className="home-contact-cta-actions">
                        <a
                            href="https://wa.me/34634112604"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-style-background-color"
                        >
                            Escríbenos por WhatsApp
                        </a>
                        <Link to="/contact" className="home-hero-secondary">
                            Ir a contacto
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="container home-info">
            <div className="row d-flex justify-content-center">
                <h2 className="h1-home">CONTÁCTANOS</h2>
                <hr className="hr-cart"></hr>
            </div>
        </div>
    );
};

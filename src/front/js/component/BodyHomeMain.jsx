import React from "react";
import { Link } from "react-router-dom";

export const BodyHomeMain = () => {
    return (
        <div className="container home-commercial-hero">
            <div className="row align-items-center g-4">
                <div className="col-12 col-lg-7">
                    <p className="home-section-eyebrow">METAL WOLFT</p>
                    <h1 className="h1-home home-hero-title">Rejas para ventanas a medida</h1>
                    <p className="home-hero-subtitle">
                        Fabricadas en metal, personalizadas por medidas y enviadas a toda España.
                    </p>
                    <div className="home-hero-cta-group">
                        <Link to="/rejas-para-ventanas" className="btn btn-style-background-color home-hero-primary">
                            Ver rejas para ventanas
                        </Link>
                        <Link to="/medir-hueco-rejas-para-ventanas" className="home-hero-secondary">
                            Cómo medir tu ventana
                        </Link>
                    </div>
                </div>
                <div className="col-12 col-lg-5">
                    <div className="home-hero-route-card">
                        <p className="home-hero-route-label">Tu ruta más rápida para comprar</p>
                        <ol className="home-hero-route-list">
                            <li>Elige tu modelo de reja</li>
                            <li>Mide la ventana correctamente</li>
                            <li>Configura medidas y anclaje</li>
                            <li>Calcula el precio y añade al carrito</li>
                        </ol>
                        <Link to="/contact" className="home-hero-route-link">
                            Resolver dudas antes de comprar
                        </Link>
                    </div>
                </div>
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
        </div>
    );
};

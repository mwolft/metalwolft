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
        </div>
    );
};

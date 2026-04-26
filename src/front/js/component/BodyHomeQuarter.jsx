import React from "react";
import { Link } from "react-router-dom";
import herreroHome from "../../img/home/body-home/herrero-ciudad-real.avif";

export const BodyHomeQuarter = () => {
    return (
        <section className="container home-about-us-container">
            <div className="row align-items-center g-5">
                {/* Lado izquierdo */}
                <div className="col-12 col-lg-6">
                    <span className="home-section-eyebrow">Confianza</span>
                    <h2 className="h1-home home-about-title">Sobre nosotros</h2>
                    
                    <div className="home-about-content">
                        <p className="home-about-copy">
                            Fabricamos <Link to="/rejas-para-ventanas" className="highlight-link">rejas metálicas a medida</Link> en España. 
                            Cada pedido se produce bajo demanda, fusionando artesanía técnica con precisión industrial.
                        </p>
                        <p className="home-about-copy">
                            Si buscas seguridad, estamos aquí para facilitarlo. Revisa nuestra <Link to="/medir-hueco-rejas-para-ventanas" className="highlight-link">guía de medición</Link> o contacta con nuestro equipo.
                        </p>
                    </div>
                </div>

                {/* Lado derecho: Estilo Industrial Glass */}
                <div className="col-12 col-lg-6">
                    <div className="about-image-wrapper">
                        <img
                            src={herreroHome}
                            alt="Proceso de soldadura artesanal"
                            className="about-image"
                        />
                        <div className="about-image-overlay">
                            <p>Arte y acero se unen bajo la experta mano de nuestro equipo.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};
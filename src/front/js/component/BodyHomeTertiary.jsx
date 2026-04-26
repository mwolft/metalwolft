import React from "react";
import { Link } from "react-router-dom";
import { 
  Ruler, 
  Wrench, 
  Truck, 
  MessageCircle, 
  Factory, 
  Globe, 
  ReceiptText 
} from "lucide-react";

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
                    <div className="row g-4">
                        {/* CARD 1: Medición */}
                        <div className="col-12 col-md-4">
                            <div className="home-help-card">
                                <div className="icon-box variant-red">
                                    <Ruler size={32} strokeWidth={1.5} />
                                </div>
                                <h3 className="home-help-card-title">Cómo medir tu ventana</h3>
                                <p className="home-help-card-copy">
                                    Aprende a tomar alto y ancho correctamente para calcular el precio sin errores.
                                </p>
                                <Link to="/medir-hueco-rejas-para-ventanas" className="home-help-card-link">
                                    Ver guía de medición <span>→</span>
                                </Link>
                            </div>
                        </div>

                        {/* CARD 2: Instalación */}
                        <div className="col-12 col-md-4">
                            <div className="home-help-card">
                                <div className="icon-box variant-red">
                                    <Wrench size={32} strokeWidth={1.5} />
                                </div>
                                <h3 className="home-help-card-title">Guía de instalación</h3>
                                <p className="home-help-card-copy">
                                    Revisa las opciones de anclaje y qué instalación conviene más en cada caso.
                                </p>
                                <Link to="/instalation-rejas-para-ventanas" className="home-help-card-link">
                                    Ver guía de instalación <span>→</span>
                                </Link>
                            </div>
                        </div>

                        {/* CARD 3: Plazos */}
                        <div className="col-12 col-md-4">
                            <div className="home-help-card">
                                <div className="icon-box variant-red">
                                    <Truck size={32} strokeWidth={1.5} />
                                </div>
                                <h3 className="home-help-card-title">Plazos de fabricación</h3>
                                <p className="home-help-card-copy">
                                    Consulta tiempos orientativos para planificar tu compra con más tranquilidad.
                                </p>
                                <Link to="/plazos-entrega-rejas-a-medida" className="home-help-card-link">
                                    Consultar plazos <span>→</span>
                                </Link>
                            </div>
                        </div>
                    </div>

                    <p className="home-help-footer">
                        También puedes visitar nuestro <Link to="/blogs">blog</Link> o escribirnos desde <Link to="/contact">contacto</Link> si necesitas más ayuda.
                    </p>
                </div>

                {/* TRUST BAR (Inferior) */}
                <div className="row g-3 home-trust-grid">
                    <TrustItem 
                        icon={<Factory size={20} />} 
                        title="Fabricación a medida" 
                        text="Cada reja se adapta a tus medidas reales." 
                    />
                    <TrustItem 
                        icon={<Globe size={20} />} 
                        title="Envío a toda España" 
                        text="Compra online y recibe donde lo necesites." 
                    />
                    <TrustItem 
                        icon={<ReceiptText size={20} />} 
                        title="IVA incluido" 
                        text="Precios claros desde el primer momento." 
                    />
                    <TrustItem 
                        icon={<MessageCircle size={20} className="text-whatsapp" />} 
                        title="Atención por WhatsApp" 
                        text="Te ayudamos si tienes dudas antes de comprar." 
                    />
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

// Sub-componente para limpiar el código de la barra de confianza
const TrustItem = ({ icon, title, text }) => (
    <div className="col-12 col-sm-6 col-xl-3">
        <div className="home-trust-item">
            <div className="trust-icon-mini">{icon}</div>
            <div className="trust-content">
                <strong>{title}</strong>
                <span>{text}</span>
            </div>
        </div>
    </div>
);
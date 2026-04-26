import React from "react";
import Card from 'react-bootstrap/Card';
import Figure from 'react-bootstrap/Figure';
import "../../styles/home.css";
import herreroHome from "../../img/home/body-home/herrero-ciudad-real.avif";
import { Link } from "react-router-dom";

export const BodyHomeQuarter = () => {
    return (
        <div className="container home-about-us">
            <div className="row d-flex justify-content-center align-items-center g-4">
                <div className="col-12 col-lg-6">
                    <p className="home-section-eyebrow">Confianza</p>
                    <h2 className="h1-home home-about-title">Sobre nosotros</h2>
                    <p className="home-about-copy">
                        Fabricamos <Link to="/rejas-para-ventanas">rejas metálicas a medida</Link> en España. Cada pedido se produce según tus dimensiones, con envío a toda España.
                    </p>
                    <p className="home-about-copy">
                        Si quieres avanzar con seguridad, puedes revisar nuestra <Link to="/medir-hueco-rejas-para-ventanas">guía de medición</Link> o pedir ayuda desde <Link to="/contact">contacto</Link>.
                    </p>
                </div>
                <div className="col-12 col-lg-5">
                    <Card className="home-about-card">
                        <Figure className="mb-0">
                            <img
                                src={herreroHome}
                                alt="carpinteria metálica online"
                                style={{ width: '100%', height: '300px', objectFit: 'cover' }}
                            />
                            <Figure.Caption className="mt-2 home-about-caption">
                                Arte y acero se unen bajo la experta mano de nuestro soldador.
                            </Figure.Caption>
                        </Figure>
                    </Card>
                </div>
            </div>
        </div>
    );
};

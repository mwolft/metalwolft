import React from "react";
import Card from 'react-bootstrap/Card';
import Figure from 'react-bootstrap/Figure';
import "../../styles/home.css";
import herreroHome from "../../img/home/body-home/herrero-ciudad-real.avif";
import { useNavigate, Link } from "react-router-dom";

export const BodyHomeQuarter = () => {
    const navigate = useNavigate();
    const handleSignUp = () => {
        navigate("/login");
    };

    return (
        <div className="container home-about-us">
            <div className="row d-flex justify-content-center align-items-center">
                <div className="d-flex flex-column justify-content-center align-items-center col-12 col-sm-12 col-md-6 col-lg-7 col-xl-5">
                    <h2>QUIÉNES SOMOS <i className="fa-solid fa-question fa-xl" style={{color: '#ff324d'}}></i></h2>
                    <hr className="hr-cart"></hr>
                    <p className="info-p mt-3 mb-2">
                        <Link to="/rejas-para-ventanas" style={{ color: '#ff324d', textDecoration: 'underline' }}>Metal Wolft</Link> se dedica al sector de la <b>Carpintería Metálica</b>, representando un referente de calidad y confianza. Nuestra trayectoria se inicia con humildes comienzos, evolucionando hasta convertirnos en un referente a nivel nacional para nuestra comunidad, gracias a <b>nuestra dedicación, maestría y pasión por la transformación del metal</b>.
                    </p>
                    <p className="info-p pb-3">
                        A lo largo de los años, nuestra experiencia nos ha posicionado para superar consistentemente las expectativas en la industria. Orgullosos de nuestra evolución, nos dedicamos a la <strong>fabricación de productos de alta calidad en acero y aluminio</strong>, caracterizados por su durabilidad, funcionalidad y diseño. Nuestra presencia en Online nos facilita el servir a un amplio espectro de clientes, entregando soluciones metálicas que destacan en el mercado.
                    </p>
                </div>
                <div className="col-12 col-sm-12 col-md-6 col-lg-5 col-xl-5 mt-2">
                    <Card style={{ height: '100%' }}>
                        <Figure>
                            <img
                                src={herreroHome}
                                alt="soldador en ciudad real"
                                style={{
                                    width: '100%',
                                    height: '400px',
                                    objectFit: 'cover'
                                }} />
                            <Figure.Caption className="mt-2" style={{ fontSize: '10px', fontStyle: 'italic' }}>
                                Arte y acero se unen bajo la experta mano de nuestro soldador.
                            </Figure.Caption>
                        </Figure>
                    </Card>
                </div>
            </div>
        </div>
    );
};

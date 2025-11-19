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
                <h2 className="h1-home">SOBRE NOSOTROS</h2>
                <hr className="hr-cart"></hr>
                <div className="d-flex flex-column justify-content-center align-items-center col-12 col-sm-12 col-md-6 col-lg-7 col-xl-5">
                    <p className="info-p mt-3 mb-2">
                        <Link to="/rejas-para-ventanas" style={{ color: '#ff324d', textDecoration: 'none', fontWeight: 'bolder' }}>Metal Wolft</Link> se dedica a la fabricación y distribución de <b>productos metálicos</b>, que combinan <b>calidad y funcionalidad</b>.
                    </p>
                    <p className="info-p">
                        Con más de <strong>10 años de experiencia</strong>, ofrecemos soluciones metálicas como <b>rejas, vallados y puertas</b>, diseñadas para satisfacer tanto a empresas como a clientes particulares.
                    </p>
                    <p className="info-p pb-3">
                        Nuestros diseños no solo destacan por su durabilidad, sino que también están pensados para facilitar su instalación. <br />¡Además contámos con <b style={{ color: '#ff324d' }}>ENVÍOS GRATUÍTOS</b> a toda <b>España</b>!
                    </p>
                </div>
                <div className="col-12 col-sm-12 col-md-6 col-lg-5 col-xl-5 mt-2">
                    <Card style={{ height: '100%' }}>
                        <Figure>
                            <img
                                src={herreroHome}
                                alt="carpinteria metálica online"
                                style={{ width: '100%', height: '300px', objectFit: 'cover' }} />
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

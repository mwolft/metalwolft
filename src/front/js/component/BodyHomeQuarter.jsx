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
                <h2>Sobre nosotros</h2>
                <hr className="hr-cart"></hr>
                <div className="d-flex flex-column justify-content-center align-items-center col-12 col-sm-12 col-md-6 col-lg-7 col-xl-5">
                    <p className="info-p mt-3 mb-2">
                        <Link to="/rejas-para-ventanas" style={{ color: '#ff324d', textDecoration: 'underline' }}>Metal Wolft</Link> se dedica al sector de la <b>Carpintería Metálica</b>, representando un referente de calidad y confianza.
                    </p>
                    <p className="info-p pb-3">
                        Con más de <strong>10 años de experiencia</strong>, destacamos en la fabricación de productos metálicos en acero. Diseños duraderos y funcionales, <b>disponibles en toda España</b>.
                    </p>
                </div>
                <div className="col-12 col-sm-12 col-md-6 col-lg-5 col-xl-5 mt-2">
                    <Card style={{ height: '100%' }}>
                        <Figure>
                            <img
                                src={herreroHome}
                                alt="soldador en ciudad real"
                                style={{ width: '100%', height: '400px', objectFit: 'cover' }} />
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

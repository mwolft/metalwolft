import React from "react";
import Card from 'react-bootstrap/Card';
import Figure from 'react-bootstrap/Figure';
import "../../styles/home.css";
import herreroHome from "../../img/home/body-home/herrero-ciudad-real.avif";
import { useNavigate } from "react-router-dom";

export const BodyHomeQuarter = () => {
    const navigate = useNavigate();
    const handleSignUp = () => {
        navigate("/login");
    };

    return (
        <div className="container home-about-us">
            <div className="row d-flex justify-content-center align-items-center">
                <div className="d-flex flex-column justify-content-center align-items-center col-12 col-sm-12 col-md-6 col-lg-7 col-xl-5">
                    <h3>Sobre nosotros</h3>
                    <p className="info-p mt-3 mb-2">
                        Metal Wolft Ciudad Real destaca en el sector de la Carpintería Metálica, representando un referente de calidad y confianza. Nuestra trayectoria se inicia con humildes comienzos, evolucionando hasta convertirnos en una entidad fundamental para nuestra comunidad, gracias a nuestra inquebrantable dedicación, maestría y pasión por la transformación del metal.
                    </p>
                    <p className="info-p pb-3">
                        A lo largo de los años, nuestra experiencia nos ha posicionado para superar consistentemente las expectativas en la industria. Orgullosos de nuestra evolución, nos dedicamos a la fabricación de productos de alta calidad en acero y aluminio, caracterizados por su durabilidad, funcionalidad y diseño. Nuestra presencia en Ciudad Real nos facilita el servir a un amplio espectro de clientes, entregando soluciones metálicas que destacan en el mercado.
                    </p>
                </div>
                <div className="col-12 col-sm-12 col-md-6 col-lg-5 col-xl-5" mt-2>
                    <Card className="bg-light" style={{ height: '100%' }}>
                        <Figure>
                            <div style={{ backgroundImage: `url(${herreroHome})`, backgroundSize: 'cover', backgroundPosition: 'center', height: '400px' }}></div>
                            <Figure.Caption className="mt-2">
                                Arte y acero se unen bajo la experta mano de nuestro soldador.
                            </Figure.Caption>
                        </Figure>
                    </Card>
                </div>
            </div>
        </div>
    );

};


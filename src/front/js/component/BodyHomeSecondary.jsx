import React from "react";
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import "../../styles/home.css";
import rejasHome from "../../img/home/body-home/rejas-para-ventanas-sencillas-y-bonitas-sin-obra.avif";
import correderasHome from "../../img/home/body-home/puertas-correderas-automaticas-en-ciudad-real.avif";
import valladosHome from "../../img/home/body-home/vallados-metalicos-exteriores-en-ciudad-real.avif";
import peatonalesHome from "../../img/home/body-home/puertas-peatonales-en-ciudad-real.avif";
import { useNavigate } from "react-router-dom";

export const BodyHomeSecondary = () => {
    const navigate = useNavigate();
    const handleSignUp = () => {
        navigate("/login");
    };

    return (
        <div className="container my-5">
            <div className="row">
                <div className="col-12 col-sm-12 col-md-5 col-lg-5 col-xl-5" mt-2>
                    <Card className="text-white" style={{ height: '300px' }}>
                        <div
                            style={{
                                backgroundImage: `url(${rejasHome})`,
                                backgroundSize: 'cover',
                                backgroundPosition: 'center',
                                height: '100%'
                            }}
                        >
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Rejas para Ventanas</h2>
                                <p className="p-home">Diseño Moderno</p>
                                <div className="my-5">
                                    <Button className="btn-style-background-color">Explorar</Button>{' '}
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
                <div className="col-12 col-sm-12 col-md-7 col-lg-7 col-xl-7 mt-2">
                    <Card className="text-white" style={{ height: '300px' }}>
                        <div
                            style={{
                                backgroundImage: `url(${correderasHome})`,
                                backgroundSize: 'cover',
                                backgroundPosition: 'center',
                                height: '100%'
                            }}
                        >
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Correderas Exteriores</h2>
                                <p className="p-home">Automáticas</p>
                                <div className="my-5">
                                    <Button className="btn-style-background-color">Explorar</Button>{' '}
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
                <div className="col-12 col-sm-12 col-md-7 col-lg-7 col-xl-7 mt-2">
                    <Card className="text-white" style={{ height: '300px' }}>
                        <div
                            style={{
                                backgroundImage: `url(${valladosHome})`,
                                backgroundSize: 'cover',
                                backgroundPosition: 'center',
                                height: '100%'
                            }}
                        >
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Vallados Metálicos</h2>
                                <p className="p-home">Diseño innovador</p>
                                <div className="my-5">
                                    <Button className="btn-style-background-color">Explorar</Button>{' '}
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
                <div className="col-12 col-sm-12 col-md-5 col-lg-5 col-xl-5 mt-2">
                    <Card className="text-white" style={{ height: '300px' }}>
                        <div
                            style={{
                                backgroundImage: `url(${peatonalesHome})`,
                                backgroundSize: 'cover',
                                backgroundPosition: 'center',
                                height: '100%'
                            }}
                        >
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Puertas Peatonales</h2>
                                <p className="p-home">A la Vanguardia</p>
                                <div className="my-5">
                                    <Button className="btn-style-background-color">Explorar</Button>{' '}
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );

};


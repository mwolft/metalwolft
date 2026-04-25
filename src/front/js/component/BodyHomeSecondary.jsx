import React from "react";
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import "../../styles/home.css";
import rejasHome from "../../img/home/body-home/rejas-para-ventanas-sencillas-y-bonitas-sin-obra.avif";
import correderasHome from "../../img/home/body-home/puertas-correderas-automaticas-en-ciudad-real.avif";
import valladosHome from "../../img/home/body-home/vallados-metalicos-exteriores-en-ciudad-real.avif";
import peatonalesHome from "../../img/home/body-home/puertas-peatonales-en-ciudad-real.avif";
import correderasInterioresHome from "../../img/home/body-home/puertas-correderas-interiores.avif";
import cerramientoCocinaHome from "../../img/home/body-home/cerramiento-de-cocina-con-cristal.jpg";
import { Link } from "react-router-dom";

export const BodyHomeSecondary = () => {
    return (
        <div className="container my-5">
            <div className="home-category-header">
                <p className="home-section-eyebrow">Catálogo principal</p>
                <h2 className="h1-home home-category-title">Empieza por nuestras rejas para ventanas</h2>
                <p className="home-category-copy">
                    Es la categoría más solicitada y el camino más directo para medir, configurar y comprar online.
                </p>
            </div>
            <div className="row">
                <div className="col-12 col-sm-12 col-md-5 col-lg-5 col-xl-5 mt-2">
                    <Card className="text-white home-category-card home-category-card--featured" style={{ height: '300px' }}>
                        <div style={{ position: 'relative', height: '100%' }}>
                            <img
                                src={rejasHome}
                                alt="rejas para ventanas"
                                style={{
                                    objectFit: 'cover',
                                    width: '100%',
                                    height: '100%',
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                }}
                            />
                            <Card.ImgOverlay className="m-3">
                                <span className="home-category-badge">Más vendido</span>
                                <h2 className="h2-home">Rejas para Ventanas</h2>
                                <p className="p-home">A medida y listas para calcular online</p>
                                <div className="my-5">
                                    <Button
                                        as={Link}
                                        to="/rejas-para-ventanas"
                                        className="btn-style-background-color"
                                    >
                                        Ver rejas para ventanas
                                    </Button>
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
                <div className="col-12 col-sm-12 col-md-7 col-lg-7 col-xl-7 mt-2">
                    <Card className="text-white" style={{ height: '300px' }}>
                        <div style={{ position: 'relative', height: '100%' }}>
                            <img
                                src={correderasHome}
                                alt="puertas correderas exteriores"
                                style={{
                                    objectFit: 'cover',
                                    width: '100%',
                                    height: '100%',
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                }}
                            />
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Correderas Exteriores</h2>
                                <p className="p-home">Automáticas</p>
                                <div className="my-5">
                                    <Button
                                        as={Link}
                                        to="/puertas-correderas-exteriores"
                                        className="btn-style-background-color"
                                    >
                                        Ver puertas correderas exteriores
                                    </Button>
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
                <div className="col-12 col-sm-12 col-md-7 col-lg-7 col-xl-7 mt-2">
                    <Card className="text-white" style={{ height: '300px' }}>
                        <div style={{ position: 'relative', height: '100%' }}>
                            <img
                                src={valladosHome}
                                alt="vallados metalicos"
                                style={{
                                    objectFit: 'cover',
                                    width: '100%',
                                    height: '100%',
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                }}
                            />
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Vallados Metálicos</h2>
                                <p className="p-home">Diseño innovador</p>
                                <div className="my-5">
                                    <Button
                                        as={Link}
                                        to="/vallados-metalicos-exteriores"
                                        className="btn-style-background-color"
                                    >
                                        Ver vallados metálicos
                                    </Button>
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
                <div className="col-12 col-sm-12 col-md-5 col-lg-5 col-xl-5 mt-2">
                    <Card className="text-white" style={{ height: '300px' }}>
                        <div style={{ position: 'relative', height: '100%' }}>
                            <img
                                src={peatonalesHome}
                                alt="puertas peatonales"
                                style={{
                                    objectFit: 'cover',
                                    width: '100%',
                                    height: '100%',
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                }}
                            />
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Puertas Peatonales</h2>
                                <p className="p-home">A la vanguardia</p>
                                <div className="my-5">
                                    <Button
                                        as={Link}
                                        to="/puertas-peatonales-metalicas"
                                        className="btn-style-background-color"
                                    >
                                        Ver puertas peatonales
                                    </Button>
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
                <div className="col-12 col-sm-12 col-md-5 col-lg-5 col-xl-5 mt-2">
                    <Card className="text-white" style={{ height: '300px' }}>
                        <div style={{ position: 'relative', height: '100%' }}>
                            <img
                                src={correderasInterioresHome}
                                alt="puertas correderas interiores"
                                style={{
                                    objectFit: 'cover',
                                    width: '100%',
                                    height: '100%',
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                }}
                            />
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Puertas Interiores</h2>
                                <p className="p-home">Con estilo</p>
                                <div className="my-5">
                                    <Button
                                        as={Link}
                                        to="/puertas-correderas-interiores"
                                        className="btn-style-background-color"
                                    >
                                        Ver puertas interiores
                                    </Button>
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
                <div className="col-12 col-sm-12 col-md-7 col-lg-7 col-xl-7 mt-2">
                    <Card className="text-white" style={{ height: '300px' }}>
                        <div style={{ position: 'relative', height: '100%' }}>
                            <img
                                src={cerramientoCocinaHome}
                                alt="cerramiento de cocina con cristal"
                                style={{
                                    objectFit: 'cover',
                                    width: '100%',
                                    height: '100%',
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                }}
                            />
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Cerramientos de Cocina</h2>
                                <p className="p-home">Tendencias</p>
                                <div className="my-5">
                                    <Button
                                        as={Link}
                                        to="/cerramientos-de-cocina-con-cristal"
                                        className="btn-style-background-color"
                                    >
                                        Ver cerramientos
                                    </Button>
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
};

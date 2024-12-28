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
import { useNavigate } from "react-router-dom";

export const BodyHomeSecondary = () => {
    const navigate = useNavigate();

    // Función para manejar la navegación a diferentes rutas
    const handleNavigate = (path) => {
        navigate(path);
    };

    return (
        <div className="container my-5">
            <div className="row">
                <div className="col-12 col-sm-12 col-md-5 col-lg-5 col-xl-5 mt-2">
                    <Card className="text-white" style={{ height: '300px' }}>
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
                                    left: 0, }}/>
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Rejas para Ventanas</h2>
                                <p className="p-home">Diseño Moderno</p>
                                <div className="my-5">
                                    <Button
                                        className="btn-style-background-color"
                                        onClick={() => handleNavigate('/rejas-para-ventanas')}>Ver más</Button>
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
                                    left: 0, }}/>
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Correderas Exteriores</h2>
                                <p className="p-home">Automáticas</p>
                                <div className="my-5">
                                    <Button
                                        className="btn-style-background-color"
                                        onClick={() => handleNavigate('/puertas-correderas-exteriores')}>Ver más</Button>
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
                                    left: 0, }}/>
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Vallados Metálicos</h2>
                                <p className="p-home">Diseño Innovador</p>
                                <div className="my-5">
                                    <Button
                                        className="btn-style-background-color"
                                        onClick={() => handleNavigate('/vallados-metalicos-exteriores')}>Ver más</Button>
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
                                    left: 0, }}/>
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Puertas Peatonales</h2>
                                <p className="p-home">A la Vanguardia</p>
                                <div className="my-5">
                                    <Button
                                        className="btn-style-background-color"
                                        onClick={() => handleNavigate('/puertas-peatonales-metalicas')}>Ver más</Button>
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
                                    left: 0, }}/>
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Puertas Interiores</h2>
                                <p className="p-home">Con Estilo</p>
                                <div className="my-5">
                                    <Button
                                        className="btn-style-background-color"
                                        onClick={() => handleNavigate('/puertas-correderas-interiores')}>Ver más</Button>
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
                                    left: 0, }}/>
                            <Card.ImgOverlay className="m-3">
                                <h2 className="h2-home">Cerramientos de Cocina</h2>
                                <p className="p-home">Tendencias</p>
                                <div className="my-5">
                                    <Button
                                        className="btn-style-background-color"
                                        onClick={() => handleNavigate('/cerramientos-de-cocina-con-cristal')}>Ver más</Button>
                                </div>
                            </Card.ImgOverlay>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
};

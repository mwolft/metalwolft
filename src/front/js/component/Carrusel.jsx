import React from "react";
import valladosCarrusel from "../../img/home/carrusel/vallados-metalicos-en-ciudad-real.avif";
import rejasCarrusel from "../../img/home/carrusel/rejas-para-ventanas-en-ciudad-real.avif";
import correderasCarrusel from "../../img/home/carrusel/puertas-correderas-en-ciudad-real.avif";
import { useNavigate } from "react-router-dom";
import Carousel from 'react-bootstrap/Carousel';
import Button from 'react-bootstrap/Button';

export const Carrusel = () => {
    const navigate = useNavigate();

    const handleNavigate = (path) => {
        navigate(path);
    };

    return (
        <Carousel data-bs-theme="dark" style={{ marginTop: '65px' }}>
            <Carousel.Item>
                <div className="carrusel-background" style={{ backgroundImage: `url(${valladosCarrusel})` }} />
                <Carousel.Caption>
                    <p className="p-carrusel">Nuevos diseños</p>
                    <h6 className="h6-carrusel">Vallados Metálicos</h6>
                    <p className="p-carrusel">Explora nuestra selección de vallas metálicas diseñadas para combinar seguridad y elegancia en tu hogar. Encuentra el estilo perfecto para ti.</p>
                    <div className="my-5">
                        <Button className="btn-style-background-color" onClick={() => handleNavigate('/vallados-metalicos-exteriores')}>
                            Explorar diseños
                        </Button>
                    </div>
                </Carousel.Caption>
            </Carousel.Item>
            <Carousel.Item>
                <div className="carrusel-background" style={{ backgroundImage: `url(${rejasCarrusel})` }} />
                <Carousel.Caption>
                    <p className="p-carrusel">Diseños exclusivos</p>
                    <h6 className="h6-carrusel">Rejas para Ventanas</h6>
                    <p className="p-carrusel">Descubre nuestras rejas para ventanas fabricadas con calidad y diseño a medida. Envíos rápidos a toda España. ¡Consulta nuestro catálogo hoy!</p>
                    <div className="my-5">
                        <Button className="btn-style-background-color" onClick={() => handleNavigate('/rejas-para-ventanas')}>
                            Diseños
                        </Button>
                    </div>
                </Carousel.Caption>
            </Carousel.Item>
            <Carousel.Item>
                <div className="carrusel-background" style={{ backgroundImage: `url(${correderasCarrusel})` }} />
                <Carousel.Caption>
                    <p className="p-carrusel">Ofertas especiales</p>
                    <h6 className="h6-carrusel">Puertas Correderas</h6>
                    <p className="p-carrusel">Diseño moderno y funcionalidad excepcional. Descubre nuestras puertas correderas exteriores con envío a toda España. ¡Consúltanos para más detalles!</p>
                    <div className="my-5">
                        <Button className="btn-style-background-color" onClick={() => handleNavigate('/puertas-correderas-exteriores')}>
                            Ofertas
                        </Button>
                    </div>
                </Carousel.Caption>
            </Carousel.Item>
        </Carousel>
    );
};

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
        <Carousel data-bs-theme="dark"  style={{ marginTop: '65px' }}>
            <Carousel.Item>
                <div className="carrusel-background" style={{ backgroundImage: `url(${valladosCarrusel})` }}/>
                <Carousel.Caption>
                    <h5>First slide label</h5>
                    <p>Nulla vitae elit libero, a pharetra augue mollis interdum.</p>
                    <div className="my-3">
                        <Button className="btn-style">Explorar</Button>{' '}
                    </div>
                </Carousel.Caption>
            </Carousel.Item>
            <Carousel.Item>
                <div className="carrusel-background" style={{ backgroundImage: `url(${rejasCarrusel})` }}/>
                <Carousel.Caption>
                    <h5>Second slide label</h5>
                    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
                    <div className="my-3">
                        <Button className="btn-style">Ir a categoria</Button>{' '}
                    </div>
                </Carousel.Caption>
            </Carousel.Item>
            <Carousel.Item>
                <div className="carrusel-background" style={{ backgroundImage: `url(${correderasCarrusel})` }}/>
                <Carousel.Caption>
                    <h5>Third slide label</h5>
                    <p>Praesent commodo cursus magna, vel scelerisque nisl consectetur.</p>
                    <div className="my-3">
                        <Button className="btn-style">Ver catálogo</Button>{' '}
                    </div>
                </Carousel.Caption>
            </Carousel.Item>
        </Carousel>
    );
};


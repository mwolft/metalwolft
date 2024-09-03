import React from "react";
import Card from 'react-bootstrap/Card';
import nutritionImage from "../../img/home-nutrition.jpg";
import exerciseImage from "../../img/home-exercise.jpg";
import equipmentImage from "../../img/home-equipment.jpg";

export const BodyHomeMain = () => {

    return (
        <div className="container my-5">
            <hr className="text-write"></hr>
            <div className="row">
                <div className="mt-5 col-card col-12 col-md-6 col-lg-4">
                    <Card>
                        <Card.Img src={equipmentImage} alt="Card image" />
                        <Card.ImgOverlay className="img-fluid">
                            <div data-hover-content="Obtén los mejores ejercicios" className="cover-card">
                                <Card.Title>TrAIner</Card.Title>
                                <Card.Text>
                                EJERCICIOS
                                </Card.Text>
                            </div>
                        </Card.ImgOverlay>
                    </Card>
                </div>
                <div className="mt-5 col-card col-12 col-md-6 col-lg-4">
                    <Card>
                        <Card.Img src={nutritionImage} alt="Card image" />
                        <Card.ImgOverlay className="img-fluid">
                            <div data-hover-content="Obtén planes de nutrición" className="cover-card">
                                <Card.Title>trAIner</Card.Title>
                                <Card.Text>
                                 NUTRICIÓN
                                </Card.Text>
                            </div>
                        </Card.ImgOverlay>
                    </Card>
                </div>
                <div className="mt-5 col-card col-12 col-md-6 col-lg-4">
                    <Card>
                        <Card.Img src={exerciseImage} alt="Card image" />
                        <Card.ImgOverlay className="img-fluid">
                            <div data-hover-content="Obtén contactos con profesionales" className="cover-card">
                                <Card.Title>Contacto</Card.Title>
                                <Card.Text>
                                 ENTRENADORES 
                                </Card.Text>
                            </div>
                        </Card.ImgOverlay>
                    </Card>
                </div>
            </div>
        </div>

    )
}

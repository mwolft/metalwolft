import React from 'react';
import Button from 'react-bootstrap/Button';
import Card from 'react-bootstrap/Card';
import albanyImage from "../../img/cards-carrusel/rejas-para-ventanas.avif";

export const Product = () => {


    return (
        <div className="row my-5">
            <div className="col-12 col-md-6 col-lg-4 col-xl-4">
                <Card className="px-2" style={{ width: 'auto'}}>
                    <Card.Img variant="top" src={albanyImage} />
                    <Card.Body>
                        <Card.Title>Card Title</Card.Title>
                        <Card.Text>
                            Some quick example text to build on the card title and make up the
                            bulk of the card's content.
                        </Card.Text>
                    </Card.Body>
                </Card>
            </div>
            <div className="col-12 col-md-6 col-lg-4 col-xl-4">
                <Card className="px-2" style={{ width: 'auto'}}>
                    <Card.Img variant="top" src={albanyImage} />
                    <Card.Body>
                        <Card.Title>Card Title</Card.Title>
                        <Card.Text>
                            Some quick example text to build on the card title and make up the
                            bulk of the card's content.
                        </Card.Text>
                    </Card.Body>
                </Card>
            </div>
            <div className="col-12 col-md-6 col-lg-4 col-xl-4">
                <Card className="px-2" style={{ width: 'auto'}}>
                    <Card.Img variant="top" src={albanyImage} />
                    <Card.Body>
                        <Card.Title>Card Title</Card.Title>
                        <Card.Text>
                            Some quick example text to build on the card title and make up the
                            bulk of the card's content.
                        </Card.Text>
                    </Card.Body>
                </Card>
            </div>
        </div>
    );
};


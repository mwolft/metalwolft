import React from "react";
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { Breadcrumb } from '../component/Breadcrumb.jsx';
import { BodyHomeTertiary } from "../component/BodyHomeTertiary.jsx";

export const Contact = () => {
    return (
        <>
            <Breadcrumb />
            <BodyHomeTertiary />
            <div className="container">
                <div className="row" style={{ marginBottom: '50px' }}>
                    <div className="col-12 col-lg-6">
                        <h2>Contáctanos</h2>
                        <p>Estamos listos para resolver tus dudas y atender tus necesidades. Si buscas más información sobre nuestros productos metálicos, deseas un presupuesto o simplemente quieres saludarnos, utiliza nuestro formulario de contacto.</p>
                        <p>Te responderemos rápidamente para ofrecerte la mejor solución en productos metálicos personalizados.</p>
                        <Form>
                            <div className="row">
                                <div className="col-md-6">
                                    <Form.Group className="mb-3" controlId="formBasicName">
                                        <Form.Control type="text" placeholder="Nombre:" />
                                    </Form.Group>
                                </div>
                                <div className="col-md-6">
                                    <Form.Group className="mb-3" controlId="formBasicFirstname">
                                        <Form.Control type="text" placeholder="Apellidos:" />
                                    </Form.Group>
                                </div>
                            </div>
                            <div className="row">
                                <div className="col-md-6">
                                    <Form.Group className="mb-3" controlId="phone">
                                        <Form.Control type="text" placeholder="Teléfono:" />
                                    </Form.Group>
                                </div>
                                <div className="col-md-6">
                                    <Form.Group className="mb-3" controlId="email">
                                        <Form.Control type="email" placeholder="Correo:" />
                                    </Form.Group>
                                </div>
                            </div>
                            <div className="row">
                                <div className="col-md-12">
                                    <Form.Group className="mb-3" controlId="message">
                                        <Form.Control as="textarea" rows={3} placeholder="Mensaje:" />
                                    </Form.Group>
                                </div>
                            </div>
                            <Button className="stylebtn" variant="primary" type="submit">
                                Enviar
                            </Button>
                        </Form>
                    </div>
                    <div className="col-12 col-lg-6 mt-5 mt-lg-0">
                        <iframe
                            src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3101.0997967559592!2d-3.9339100875221473!3d38.990218671586376!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xd6bc3694e58cfc3%3A0xd92dfe7e129cd7b5!2sC.%20de%20Pedrera%20Alta%2C%2011%2C%2013003%20Ciudad%20Real!5e0!3m2!1ses!2ses!4v1707690312958!5m2!1ses!2ses"
                            width="100%"
                            height="350"
                            style={{ border: 0 }}
                            allowFullScreen
                            loading="lazy"
                            referrerPolicy="no-referrer-when-downgrade"
                        ></iframe>
                    </div>
                </div>
            </div>
        </>
    );
};

import React, { useState } from "react";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import { BodyHomeTertiary } from "../component/BodyHomeTertiary.jsx";

export const Contact = () => {
    const [formData, setFormData] = useState({
        name: "",
        firstname: "",
        phone: "",
        email: "",
        message: "",
    });

    const handleChange = (e) => {
        const { id, value } = e.target;
        setFormData({ ...formData, [id]: value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(
                `${process.env.REACT_APP_BACKEND_URL}/api/email/contact`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(formData),
                }
            );

            if (response.ok) {
                alert("Mensaje enviado correctamente.");
                setFormData({
                    name: "",
                    firstname: "",
                    phone: "",
                    email: "",
                    message: "",
                });
            } else {
                alert("Error al enviar el mensaje. Inténtalo nuevamente.");
            }
        } catch (error) {
            console.error("Error al enviar el formulario:", error);
            alert("Error al enviar el mensaje. Intenta nuevamente.");
        }
    };

    return (
        <div style={{ marginTop: "80px" }}>
            <BodyHomeTertiary />

            <div className="container">
                <div className="row text-center" style={{ marginBottom: "50px" }}>
                    <p>Estamos listos para resolver tus dudas y atender tus necesidades.</p>
                    <p style={{ marginBottom: "30px" }}>
                        Te responderemos rápidamente para ofrecerte la mejor solución.
                    </p>

                    <div className="col-12 col-lg-6 m-auto">
                        <Form onSubmit={handleSubmit}>
                            <div className="row">
                                <div className="col-md-6">
                                    <Form.Group className="mb-3" controlId="name">
                                        <Form.Control
                                            type="text"
                                            placeholder="Nombre:"
                                            value={formData.name}
                                            onChange={handleChange}
                                            required
                                        />
                                    </Form.Group>
                                </div>

                                <div className="col-md-6">
                                    <Form.Group className="mb-3" controlId="firstname">
                                        <Form.Control
                                            type="text"
                                            placeholder="Apellidos:"
                                            value={formData.firstname}
                                            onChange={handleChange}
                                            required
                                        />
                                    </Form.Group>
                                </div>
                            </div>

                            <div className="row">
                                <div className="col-md-6">
                                    <Form.Group className="mb-3" controlId="phone">
                                        <Form.Control
                                            type="text"
                                            placeholder="Teléfono:"
                                            value={formData.phone}
                                            onChange={handleChange}
                                            required
                                        />
                                    </Form.Group>
                                </div>

                                <div className="col-md-6">
                                    <Form.Group className="mb-3" controlId="email">
                                        <Form.Control
                                            type="email"
                                            placeholder="Correo:"
                                            value={formData.email}
                                            onChange={handleChange}
                                            required
                                        />
                                    </Form.Group>
                                </div>
                            </div>

                            <Form.Group className="mb-3" controlId="message">
                                <Form.Control
                                    as="textarea"
                                    rows={3}
                                    placeholder="Mensaje:"
                                    value={formData.message}
                                    onChange={handleChange}
                                    required
                                />
                            </Form.Group>

                            <Button className="stylebtn" variant="primary" type="submit">
                                Enviar
                            </Button>
                        </Form>
                    </div>
                </div>
            </div>
        </div>
    );
};

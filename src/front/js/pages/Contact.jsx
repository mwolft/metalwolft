import React, { useState, useEffect } from "react";
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { BodyHomeTertiary } from "../component/BodyHomeTertiary.jsx";
import { Helmet } from "react-helmet-async";

export const Contact = () => {
    const [formData, setFormData] = useState({
        name: "",
        firstname: "",
        phone: "",
        email: "",
        message: "",
    });

    const [metaData, setMetaData] = useState({});

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/contact`)
            .then((res) => res.json())
            .then((data) => setMetaData(data))
            .catch((err) => console.error("Error SEO /contact:", err));
    }, []);


    const handleChange = (e) => {
        const { id, value } = e.target;
        setFormData({ ...formData, [id]: value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/email/contact`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                alert("Mensaje enviado correctamente.");
                setFormData({ name: "", firstname: "", phone: "", email: "", message: "" });
            } else {
                alert("Error al enviar el mensaje. Inténtalo nuevamente.");
            }
        } catch (error) {
            console.error("Error al enviar el formulario:", error);
            alert("Error al enviar el mensaje. Intenta nuevamente.");
        }
    };

    return (
        <>
            <Helmet htmlAttributes={{ lang: metaData.lang || "es" }}>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ff324d"} />

                {/* Canonical */}
                <link rel="canonical" href={metaData.canonical} />

                {/* OpenGraph */}
                <meta property="og:type" content={metaData.og_type} />
                <meta property="og:title" content={metaData.og_title} />
                <meta property="og:description" content={metaData.og_description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />

                {/* Twitter */}
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:title" content={metaData.twitter_title} />
                <meta name="twitter:description" content={metaData.twitter_description} />
                <meta name="twitter:image" content={metaData.twitter_image} />

                {/* JSON-LD */}
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            <div style={{ marginTop: '80px' }}>
                <BodyHomeTertiary />
                <div className="container">
                    <div className="row text-center" style={{ marginBottom: '50px' }}>
                        <p>Estamos listos para resolver tus dudas y atender tus necesidades.</p>
                        <p style={{ marginBottom: '30px' }}>Te responderemos rápidamente para ofrecerte la mejor solución.</p>
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
                                            />
                                        </Form.Group>
                                    </div>
                                </div>
                                <div className="row">
                                    <div className="col-md-12">
                                        <Form.Group className="mb-3" controlId="message">
                                            <Form.Control
                                                as="textarea"
                                                rows={3}
                                                placeholder="Mensaje:"
                                                value={formData.message}
                                                onChange={handleChange}
                                            />
                                        </Form.Group>
                                    </div>
                                </div>
                                <Button className="stylebtn" variant="primary" type="submit">
                                    Enviar
                                </Button>
                            </Form>
                        </div>
                        {/*                    <div className="col-12 col-lg-6 mt-5 mt-lg-0">
                            <iframe
                                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3101.0997967559592!2d-3.9339100875221473!3d38.990218671586376!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xd6bc3694e58cfc3%3A0xd92dfe7e129cd7b5!2sC.%20de%20Pedrera%20Alta%2C%2011%2C%2013003%20Ciudad%20Real!5e0!3m2!1ses!2ses!4v1707690312958!5m2!1ses!2ses"
                                width="100%"
                                height="350"
                                style={{ border: 0 }}
                                allowFullScreen
                                loading="lazy"
                                referrerPolicy="no-referrer-when-downgrade"
                            ></iframe>
                        </div>*/}
                    </div>
                </div>
            </div>
        </>
    );
};

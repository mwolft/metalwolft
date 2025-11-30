import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { Helmet } from "react-helmet-async";

export const FormularioIncidencias = () => {

    const [metaData, setMetaData] = useState({});
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        order_number: '',
        issue_type: '',
        message: ''
    });

    const [images, setImages] = useState([]);
    const [sending, setSending] = useState(false);
    const [responseMessage, setResponseMessage] = useState(null);
    const [error, setError] = useState(null);
    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/formulario-incidencias`)
            .then(res => res.json())
            .then(data => setMetaData(data))
            .catch(err => console.error("SEO error:", err));
    }, []);


    return (
        <>
            <Helmet htmlAttributes={{ lang: metaData.lang || "es" }}>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />

                <meta name="robots" content="noindex, nofollow" />
                <meta name="theme-color" content={metaData.theme_color || "#ff324d"} />

                {/* OG */}
                <meta property="og:type" content={metaData.og_type} />
                <meta property="og:title" content={metaData.og_title} />
                <meta property="og:description" content={metaData.og_description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name} />
                <meta property="og:locale" content={metaData.og_locale} />

                {/* Twitter */}
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:title" content={metaData.twitter_title} />
                <meta name="twitter:description" content={metaData.twitter_description} />
                <meta name="twitter:image" content={metaData.twitter_image} />

                {/* Canonical */}
                {metaData.canonical && (
                    <link rel="canonical" href={metaData.canonical} />
                )}

                {/* JSON-LD */}
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            <Container style={{ marginTop: '70px', maxWidth: '700px' }}>
                <h1 className="h1-categories mb-4">Formulario de Incidencias</h1>
                <p>Por favor, rellena los campos para reportar un problema con tu pedido. Puedes adjuntar hasta 3 imágenes para ayudarnos a valorar el caso.</p>

                {responseMessage && <Alert variant="success">{responseMessage}</Alert>}
                {error && <Alert variant="danger">{error}</Alert>}

                <Form onSubmit={handleSubmit} encType="multipart/form-data">
                    <Form.Group className="mb-3">
                        <Form.Label>Nombre completo *</Form.Label>
                        <Form.Control
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            required
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Correo electrónico *</Form.Label>
                        <Form.Control
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            required
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Número de pedido *</Form.Label>
                        <Form.Control
                            type="text"
                            name="order_number"
                            value={formData.order_number}
                            onChange={handleChange}
                            placeholder="Ejemplo: MW1234"
                            required
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Tipo de incidencia *</Form.Label>
                        <Form.Select
                            name="issue_type"
                            value={formData.issue_type}
                            onChange={handleChange}
                            required
                        >
                            <option value="">Selecciona una opción...</option>
                            <option value="Pintura o acabado">Pintura o acabado</option>
                            <option value="Medidas o encaje">Medidas o encaje</option>
                            <option value="Transporte o embalaje">Transporte o embalaje</option>
                            <option value="Otro">Otro</option>
                        </Form.Select>
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Descripción del problema</Form.Label>
                        <Form.Control
                            as="textarea"
                            rows={4}
                            name="message"
                            value={formData.message}
                            onChange={handleChange}
                            placeholder="Describe brevemente la incidencia..."
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label>Imágenes (máx. 3)</Form.Label>
                        <Form.Control
                            type="file"
                            name="images"
                            multiple
                            accept="image/*"
                            onChange={handleImageChange}
                        />
                    </Form.Group>

                    {images.length > 0 && (
                        <div className="mb-3">
                            <p><strong>Imágenes seleccionadas:</strong></p>
                            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                {images.map((img, i) => (
                                    <img
                                        key={i}
                                        src={URL.createObjectURL(img)}
                                        alt={`preview-${i}`}
                                        style={{ width: '100px', height: '100px', objectFit: 'cover', borderRadius: '8px', border: '1px solid #ddd' }}
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="m-4">
                        <Button
                            type="submit"
                            variant="dark"
                            disabled={sending}
                            className="w-100"
                        >
                            {sending ? (
                                <>
                                    <Spinner animation="border" size="sm" /> Enviando...
                                </>
                            ) : (
                                "Enviar incidencia"
                            )}
                        </Button>
                    </div>
                </Form>
            </Container>
        </>
    );
};

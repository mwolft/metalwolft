import React, { useState } from 'react';
import { Container, Row, Col, Form, Button, Alert, Spinner } from 'react-bootstrap';

export const FormularioIncidencias = () => {
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

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleImageChange = (e) => {
        const selectedFiles = Array.from(e.target.files);
        if (selectedFiles.length > 3) {
            setError('Solo se permiten hasta 3 imágenes.');
        } else {
            setImages(selectedFiles);
            setError(null);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSending(true);
        setResponseMessage(null);
        setError(null);

        try {
            const data = new FormData();
            Object.entries(formData).forEach(([key, value]) => data.append(key, value));
            images.forEach((file, index) => data.append(`image${index + 1}`, file));

            const backendUrl =
                process.env.NODE_ENV === 'development'
                    ? 'https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/'
                    : 'https://api.metalwolft.com';

            const resp = await fetch(`${backendUrl}/api/email/report-issue`, {
                method: 'POST',
                body: data
            });


            const result = await resp.json();

            if (resp.ok) {
                setResponseMessage('✅ Incidencia enviada correctamente. Te contactaremos en breve.');
                setFormData({ name: '', email: '', order_number: '', issue_type: '', message: '' });
                setImages([]);
            } else {
                throw new Error(result.error || 'Error al enviar la incidencia.');
            }
        } catch (err) {
            setError('❌ Hubo un problema al enviar la incidencia. Inténtalo de nuevo.');
        } finally {
            setSending(false);
        }
    };

    return (
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
    );
};

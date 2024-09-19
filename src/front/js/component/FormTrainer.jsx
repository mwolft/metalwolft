import React, { useState } from 'react';
import { Form, Button, Container } from 'react-bootstrap';

export const FormTrainer = () => {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        location: '',
        specialty: '',
        certificate: null,
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const handleFileChange = (e) => {
        setFormData({ ...formData, certificate: e.target.files[0] });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        // Form submission logic here
        console.log(formData);
        alert('¡Formulario enviado con éxito!');
    };

    return (
        <div style={{ backgroundColor: '#d3d3d3', minHeight: '100vh', paddingTop: '150px' }}>
            <Container>
                <h2 className="text-center mb-4" style={{ color: 'black' }}>CONVIERTETE EN ENTRENADOR</h2>
                <Form onSubmit={handleSubmit} style={{ backgroundColor: '#FFFACD', padding: '20px', borderRadius: '10px' }}>
                    <Form.Group className="mb-3">
                        <Form.Label style={{ color: 'black' }}>Nombre Completo</Form.Label>
                        <Form.Control 
                            type="text" 
                            placeholder="Ingresa tu nombre completo" 
                            name="name" 
                            value={formData.name} 
                            onChange={handleChange} 
                            required 
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label style={{ color: 'black' }}>Correo Electrónico</Form.Label>
                        <Form.Control 
                            type="email" 
                            placeholder="Ingresa tu correo electrónico" 
                            name="email" 
                            value={formData.email} 
                            onChange={handleChange} 
                            required 
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label style={{ color: 'black' }}>Ubicación</Form.Label>
                        <Form.Control 
                            type="text" 
                            placeholder="Ingresa tu ubicación (Ciudad, País)" 
                            name="location" 
                            value={formData.location} 
                            onChange={handleChange} 
                            required 
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label style={{ color: 'black' }}>Especialidad</Form.Label>
                        <Form.Control 
                            as="select" 
                            name="specialty" 
                            value={formData.specialty} 
                            onChange={handleChange} 
                            required
                        >
                            <option value="">Selecciona tu especialidad</option>
                            <option value="Nutritionist">Nutricionista</option>
                            <option value="Trainer">Entrenador</option>
                            <option value="Nutritionist - Trainer">Nutricionista - Entrenador</option>
                        </Form.Control>
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label style={{ color: 'black' }}>Adjuntar Certificado</Form.Label>
                        <Form.Control 
                            type="file" 
                            accept=".pdf, .jpg, .png" 
                            onChange={handleFileChange} 
                            required 
                        />
                        <Form.Text className="text-muted">
                            Adjunta tu certificado (PDF, JPG, PNG)
                        </Form.Text>
                    </Form.Group>

                    <div className="d-grid">
                        <Button variant="warning" type="submit" style={{ color: 'black' }}>
                            Enviar Solicitud
                        </Button>
                    </div>
                </Form>
            </Container>
        </div>
    );
};
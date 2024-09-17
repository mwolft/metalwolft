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
        alert('Form submitted successfully!');
    };

    return (
        <div style={{ backgroundColor: '#d3d3d3', minHeight: '100vh', paddingTop: '150px' }}>
            <Container>
                <h2 className="text-center mb-4" style={{ color: 'black' }}>Become a Trainer</h2>
                <Form onSubmit={handleSubmit} style={{ backgroundColor: '#FFFACD', padding: '20px', borderRadius: '10px' }}>
                    <Form.Group className="mb-3">
                        <Form.Label style={{ color: 'black' }}>Full Name</Form.Label>
                        <Form.Control 
                            type="text" 
                            placeholder="Enter your full name" 
                            name="name" 
                            value={formData.name} 
                            onChange={handleChange} 
                            required 
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label style={{ color: 'black' }}>Email</Form.Label>
                        <Form.Control 
                            type="email" 
                            placeholder="Enter your email" 
                            name="email" 
                            value={formData.email} 
                            onChange={handleChange} 
                            required 
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label style={{ color: 'black' }}>Location</Form.Label>
                        <Form.Control 
                            type="text" 
                            placeholder="Enter your location (City, Country)" 
                            name="location" 
                            value={formData.location} 
                            onChange={handleChange} 
                            required 
                        />
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label style={{ color: 'black' }}>Specialty</Form.Label>
                        <Form.Control 
                            as="select" 
                            name="specialty" 
                            value={formData.specialty} 
                            onChange={handleChange} 
                            required
                        >
                            <option value="">Select your specialty</option>
                            <option value="Nutritionist">Nutritionist</option>
                            <option value="Trainer">Trainer</option>
                            <option value="Nutritionist - Trainer">Nutritionist - Trainer</option>
                        </Form.Control>
                    </Form.Group>

                    <Form.Group className="mb-3">
                        <Form.Label style={{ color: 'black' }}>Attach Certificate</Form.Label>
                        <Form.Control 
                            type="file" 
                            accept=".pdf, .jpg, .png" 
                            onChange={handleFileChange} 
                            required 
                        />
                        <Form.Text className="text-muted">
                            Attach your certification file (PDF, JPG, PNG)
                        </Form.Text>
                    </Form.Group>

                    <div className="d-grid">
                        <Button variant="warning" type="submit" style={{ color: 'black' }}>
                            Submit Application
                        </Button>
                    </div>
                </Form>
            </Container>
        </div>
    );
};
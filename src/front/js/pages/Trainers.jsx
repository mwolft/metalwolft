import React from 'react';
import { Card, Button, Container, Row, Col } from 'react-bootstrap';

const trainers = [
    {
        id: 1,
        name: 'Juan Pérez',
        location: 'Madrid, España',
        specialty: 'Nutricionista',
        image: 'https://randomuser.me/api/portraits/men/30.jpg',
    },
    {
        id: 2,
        name: 'Ana Martínez',
        location: 'Barcelona, España',
        specialty: 'Especialista en Ejercicio',
        image: 'https://randomuser.me/api/portraits/women/17.jpg',
    },
    {
        id: 3,
        name: 'Miguel Sánchez',
        location: 'Valencia, España',
        specialty: 'Nutricionista - Entrenador de Fuerza y Acondicionamiento',
        image: 'https://randomuser.me/api/portraits/men/22.jpg',
    },
    {
        id: 4,
        name: 'Sara López',
        location: 'Sevilla, España',
        specialty: 'Nutricionista',
        image: 'https://randomuser.me/api/portraits/women/31.jpg',
    },
    {
        id: 5,
        name: 'Cristóbal Gómez',
        location: 'Bilbao, España',
        specialty: 'Especialista en Glúteos',
        image: 'https://randomuser.me/api/portraits/men/39.jpg',
    },
    {
        id: 6,
        name: 'Emilia Rodríguez',
        location: 'Málaga, España',
        specialty: 'Nutricionista - Instructor de Yoga',
        image: 'https://randomuser.me/api/portraits/women/91.jpg',
    },
    {
        id: 7,
        name: 'Miguel Hernández',
        location: 'Zaragoza, España',
        specialty: 'Nutricionista',
        image: 'https://randomuser.me/api/portraits/men/64.jpg',
    },
    {
        id: 8,
        name: 'Olivia García',
        location: 'Granada, España',
        specialty: 'Instructora de Pilates',
        image: 'https://randomuser.me/api/portraits/women/4.jpg',
    },
    {
        id: 9,
        name: 'David Fernández',
        email: 'david.fernandez@example.com',
        location: 'Alicante, España',
        specialty: 'Nutricionista - Instructor de Kickboxing',
        image: 'https://randomuser.me/api/portraits/men/5.jpg',
    },
    {
        id: 10,
        name: 'Sofía Blanco',
        location: 'Vigo, España',
        specialty: 'Nutricionista',
        image: 'https://randomuser.me/api/portraits/women/69.jpg',
    },
    {
        id: 11,
        name: 'Liam Martínez',
        location: 'Madrid, España',
        specialty: 'Director de Fitness',
        image: 'https://randomuser.me/api/portraits/men/45.jpg',
    },
    {
        id: 12,
        name: 'Isabela Verde',
        location: 'Sevilla, España',
        specialty: 'Nutricionista - Instructor de Transformación Física',
        image: 'https://randomuser.me/api/portraits/women/55.jpg',
    }
];

export const Trainers = () => {
    return (
        <div style={{ backgroundColor: '#d3d3d3', minHeight: '100vh' }}>
            <div className='container mt-5'>
            </div>
            <Container className="py-5">
                <h2 className="text-center mb-4" style={{ color: 'black' }}>Nuestros Entrenadores</h2>
                <Row>
                    {trainers.map((trainer) => (
                        <Col xs={12} md={6} lg={4} key={trainer.id} className="mb-4">
                            <Card className="h-100 d-flex flex-column" style={{ backgroundColor: '#FFFACD', color: 'black' }}>
                                <Card.Img variant="top" src={trainer.image} alt={trainer.name} />
                                <Card.Body className="d-flex flex-column">
                                    <Card.Title className="text-center" style={{ fontSize: '1.5rem' }}>{trainer.name}</Card.Title>
                                        <br></br>
                                    <ul className="list-unstyled" style={{ fontSize: '1.25rem' }}>
                                        <li><strong>Ubicación:</strong> {trainer.location}</li>
                                        <li><strong>Especialidad:</strong> {trainer.specialty}</li>
                                    </ul>
                                    <div className="mt-auto d-grid">
                                        <Button variant="warning" href={`mailto:${trainer.email || 'info@example.com'}`} style={{ color: 'black', fontSize: '1.25rem' }}>
                                            Contactar a {trainer.name}
                                        </Button>
                                    </div>
                                </Card.Body>
                            </Card>
                        </Col>
                    ))}
                </Row>
            </Container>
        </div>
    );
};
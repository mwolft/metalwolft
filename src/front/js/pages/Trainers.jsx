import React from 'react';
import { Card, Button, Container, Row, Col } from 'react-bootstrap';
import Trainer01 from '../../img/trainers_img/Trainer-01.webp';
import Trainer02 from '../../img/trainers_img/Trainer-02.webp';
import Trainer03 from '../../img/trainers_img/Trainer-03.webp';
import Trainer04 from '../../img/trainers_img/Trainer-04.webp';
import Trainer05 from '../../img/trainers_img/Trainer-05.webp';
import Trainer06 from '../../img/trainers_img/Trainer-06.webp';
import Trainer07 from '../../img/trainers_img/Trainer-07.webp';
import Trainer08 from '../../img/trainers_img/Trainer-08.webp';
import Trainer09 from '../../img/trainers_img/Trainer-09.webp';
import Trainer10 from '../../img/trainers_img/Trainer-10.webp';
import Trainer11 from '../../img/trainers_img/Trainer-11.webp';
import Trainer12 from '../../img/trainers_img/Trainer-12.webp';

const trainers = [
    {
        id: 1,
        name: 'David Pérez Pérez',
        location: 'Madrid, España',
        specialty: 'Nutricionista',
        image: Trainer01,
    },
    {
        id: 2,
        name: 'Ana Martínez Rodríguez',
        location: 'Barcelona, España',
        specialty: 'Especialista en Ejercicio',
        image: Trainer02,
    },
    {
        id: 3,
        name: 'Alejandro Sánchez Castillo',
        location: 'Valencia, España',
        specialty: 'Nutricionista - Entrenador de Fuerza y Acondicionamiento',
        image: Trainer03,
    },
    {
        id: 4,
        name: 'Sara López García',
        location: 'Sevilla, España',
        specialty: 'Nutricionista',
        image: Trainer04,
    },
    {
        id: 5,
        name: 'Cristóbal Gómez Gil',
        location: 'Bilbao, España',
        specialty: 'Especialista en Glúteos',
        image: Trainer06,
    },
    {
        id: 6,
        name: 'Emilia Rodríguez Fuentes',
        location: 'Málaga, España',
        specialty: 'Nutricionista - Instructor de Yoga',
        image: Trainer05,
    },
    {
        id: 7,
        name: 'Miguel Hernández Hernández',
        location: 'Zaragoza, España',
        specialty: 'Nutricionista',
        image: Trainer07,
    },
    {
        id: 8,
        name: 'Olivia García Clemente',
        location: 'Granada, España',
        specialty: 'Instructora de Pilates',
        image: Trainer09,
    },
    {
        id: 9,
        name: 'Laura Fernández Sanchez',
        email: 'david.fernandez@example.com',
        location: 'Alicante, España',
        specialty: 'Nutricionista - Instructor de Kickboxing',
        image: Trainer08,
    },
    {
        id: 10,
        name: 'Sofía Blanco Hurtado',
        location: 'Vigo, España',
        specialty: 'Nutricionista',
        image: Trainer11,
    },
    {
        id: 11,
        name: 'Liam Martínez Mendez',
        location: 'Madrid, España',
        specialty: 'Director de Fitness',
        image: Trainer10,
    },
    {
        id: 12,
        name: 'Isabela Verde Oliveira',
        location: 'Sevilla, España',
        specialty: 'Nutricionista - Instructor de Transformación Física',
        image: Trainer12,
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
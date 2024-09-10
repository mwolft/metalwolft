import React from 'react';
import { Card, Button, Container, Row, Col } from 'react-bootstrap';

// Sample trainer data
const trainers = [
    {
        id: 1,
        name: 'John Doe',
        email: 'john.doe@example.com',
        location: 'Madrid, Spain',
        specialty: 'Nutritionist',
        image: 'https://randomuser.me/api/portraits/men/30.jpg',
    },
    {
        id: 2,
        name: 'Jane Smith',
        email: 'jane.smith@example.com',
        location: 'Barcelona, Spain',
        specialty: 'Trainer',
        image: 'https://randomuser.me/api/portraits/women/17.jpg',
    },
    {
        id: 3,
        name: 'Mike Johnson',
        email: 'mike.johnson@example.com',
        location: 'Valencia, Spain',
        specialty: 'Nutritionist - Trainer',
        image: 'https://randomuser.me/api/portraits/men/22.jpg',
    },
    {
        id: 4,
        name: 'Sara Lee',
        email: 'sara.lee@example.com',
        location: 'Seville, Spain',
        specialty: 'Nutritionist',
        image: 'https://randomuser.me/api/portraits/women/31.jpg',
    },
    {
        id: 5,
        name: 'Chris Brown',
        email: 'chris.brown@example.com',
        location: 'Bilbao, Spain',
        specialty: 'Trainer',
        image: 'https://randomuser.me/api/portraits/men/39.jpg',
    },
    {
        id: 6,
        name: 'Emily Davis',
        email: 'emily.davis@example.com',
        location: 'Malaga, Spain',
        specialty: 'Nutritionist - Trainer',
        image: 'https://randomuser.me/api/portraits/women/91.jpg',
    },
    {
        id: 7,
        name: 'Michael Harris',
        email: 'michael.harris@example.com',
        location: 'Zaragoza, Spain',
        specialty: 'Nutritionist',
        image: 'https://randomuser.me/api/portraits/men/64.jpg',
    },
    {
        id: 8,
        name: 'Olivia Martin',
        email: 'olivia.martin@example.com',
        location: 'Granada, Spain',
        specialty: 'Trainer',
        image: 'https://randomuser.me/api/portraits/women/4.jpg',
    },
    {
        id: 9,
        name: 'David Wilson',
        email: 'david.wilson@example.com',
        location: 'Alicante, Spain',
        specialty: 'Nutritionist - Trainer',
        image: 'https://randomuser.me/api/portraits/men/5.jpg',
    },
    {
        id: 10,
        name: 'Sophia White',
        email: 'sophia.white@example.com',
        location: 'Vigo, Spain',
        specialty: 'Nutritionist',
        image: 'https://randomuser.me/api/portraits/women/69.jpg',
    },
    {
        id: 11,
        name: 'Liam Carter',
        email: 'liam.carter@example.com',
        location: 'Madrid, Spain',
        specialty: 'Trainer',
        image: 'https://randomuser.me/api/portraits/men/45.jpg',
    },
    {
        id: 12,
        name: 'Isabella Green',
        email: 'isabella.green@example.com',
        location: 'Seville, Spain',
        specialty: 'Nutritionist - Trainer',
        image: 'https://randomuser.me/api/portraits/women/55.jpg',
    }
];

export const Trainers = () => {
    return (
        <div style={{ backgroundColor: '#d3d3d3', minHeight: '100vh' }}>
            <div className='container mt-5'>
            </div>
            <Container className="py-5">
                <h2 className="text-center mb-4" style={{ color: 'black' }}>Our Trainers</h2>
                <Row>
                    {trainers.map((trainer) => (
                        <Col md={4} key={trainer.id} className="mb-4">
                            <Card className="h-100" style={{ backgroundColor: '#FFFACD', color: 'black' }}>
                                <Card.Img variant="top" src={trainer.image} alt={trainer.name} />
                                <Card.Body>
                                    <Card.Title className="text-center">{trainer.name}</Card.Title>
                                    <ul className="list-unstyled">
                                        <li><strong>Email:</strong> {trainer.email}</li>
                                        <li><strong>Location:</strong> {trainer.location}</li>
                                        <li><strong>Specialty:</strong> {trainer.specialty}</li>
                                    </ul>
                                    <div className="d-grid">
                                        <Button variant="warning" href={`mailto:${trainer.email}`} style={{ color: 'black' }}>
                                            Contact {trainer.name}
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
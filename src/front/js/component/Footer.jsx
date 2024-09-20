import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import '../../styles/footer.css'; 

export const Footer = () => {
  return (
    <footer className="footer-custom mt-auto">
      <Container fluid>
        <Row className="text-center py-4">
          <Col>
            <h5 className="footer-title">DIRECCIÓN</h5>
            <p>4GEEKS ACADEMY</p>
          </Col>
          <Col>
            <h5 className="footer-title">CORREO</h5>
            <p>admin@appfit.com</p>
          </Col>
          <Col>
            <h5 className="footer-title">equipo 2</h5>
            <p>ALI, SERGIO, STEFANO</p>
          </Col>
        </Row>
      </Container>
    </footer>
  );
};


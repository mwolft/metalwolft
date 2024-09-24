import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import '../../styles/footer.css';

export const Footer = () => {
  return (
    <footer className="footer-style mt-auto bg-dark text-white">
      <div className="row footer-row">
        <div className="footer-box col-12 col-md-6 col-lg-6 col-xl-6">
          <h5 className="footer-h5 mb-4 text-uppercase">Localización</h5>
          <p className="footer-p">
            <i className="fa-solid fa-location-dot"></i> Ofic. Calle Pedrera Alta 11. Ciudad Real, Castilla La Mancha, España
          </p>
          <p className="footer-p">
            <i className="fa-regular fa-envelope-open"></i> admin@metalwolft.com
          </p>
          <p className="footer-p">
            <i className="fa-solid fa-phone"></i> +34 634 11 26 04
          </p>
        </div>
        <div className="footer-box col-12 col-md-3 col-lg-3 col-xl-3">
          <h5 className="footer-h5 mb-4 text-uppercase">Contácto</h5>
          <p className="footer-p">Contácto</p>
          <p className="footer-p">Sobre nosotros</p>
          <p className="footer-p">Preguntas frecuentes</p>
        </div>
        <div className="footer-box col-12 col-md-3 col-lg-3 col-xl-3">
          <h5 className="footer-h5 mb-4 text-uppercase">Área legal</h5>
          <p className="footer-p">Términos y condiciones</p>
          <p className="footer-p">Descuentos</p>
          <p className="footer-p">Devoluciones</p>
          <p className="footer-p">Cookies</p>
          <p className="footer-p">Política de privacidad</p>
        </div>
      </div>
    </footer>
  );
};


import React from 'react';
import { Link } from 'react-router-dom';
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
          <p className="footer-p"><Link to="/contacto" className="footer-p">Contácto</Link></p>
          <p className="footer-p"><Link to="/sobre-nosotros" className="footer-p">Sobre nosotros</Link></p>
          <p className="footer-p"><Link to="/preguntas-frecuentes" className="footer-p">Preguntas frecuentes</Link></p>
          <p className="footer-p"><Link to="/cookies-esenciales" className="footer-p">Cookies esenciales</Link></p>
          <p className="footer-p"><Link to="/politica-cookies" className="footer-p">Política de cookies</Link></p>
        </div>
        <div className="footer-box col-12 col-md-3 col-lg-3 col-xl-3">
          <h5 className="footer-h5 mb-4 text-uppercase">Área legal</h5>
          <p className="footer-p"><Link to="/terminos-condiciones" className="footer-p">Términos y condiciones</Link></p>
          <p className="footer-p"><Link to="/descuentos" className="footer-p">Descuentos</Link></p>
          <p className="footer-p"><Link to="/devoluciones" className="footer-p">Devoluciones</Link></p>
          <p className="footer-p"><Link to="/informacion-recogida" className="footer-p">Información recogida</Link></p>
          <p className="footer-p"><Link to="/cambios-politica-cookies" className="footer-p">Cambios en la política de cookies</Link></p>
          <p className="footer-p"><Link to="/politica-privacidad" className="footer-p">Política de privacidad</Link></p>
        </div>
      </div>
    </footer>
  );
};

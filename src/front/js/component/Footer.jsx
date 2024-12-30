import React from 'react';
import { Link } from 'react-router-dom';
import '../../styles/footer.css';

export const Footer = () => {
  return (
    <footer className="footer-style mt-auto bg-dark text-white py-3">
      <div className="container text-center">
        <div className="row">
          <div className="col-12">
            <p className="footer-p d-flex justify-content-center align-items-center mt-3">
              {/*<Link to="/contact" className="footer-p mx-3">Contacto</Link>*/}
              <Link to="/informacion-recogida" className="footer-p">Información recogida</Link>
              <Link to="/politica-cookies" className="footer-p mx-3">Política de cookies</Link>
              <Link to="/politica-privacidad" className="footer-p mx-3">Política de privacidad</Link>
              <Link to="/cookies-esenciales" className="footer-p">Cookies esenciales</Link>
              <Link to="/cambios-politica-cookies" className="footer-p">Cambios en la política de cookies</Link>
            </p>
          </div>
        </div>
        <div className="row">
          <div className="col-12 mt-3">
            <p className="footer-p d-flex justify-content-center align-items-center">
              © 2025 Metal Wolft. Todos los derechos reservados.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

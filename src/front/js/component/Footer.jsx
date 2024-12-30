import React from 'react';
import { Link } from 'react-router-dom';
import '../../styles/footer.css';

export const Footer = () => {
  return (
    <footer className="mt-auto bg-dark text-white py-3">
      <div className="container text-center">
        <p style={{marginTop:'20px', marginBottom:'30px'}}>© 2025 Metal Wolft. Todos los derechos reservados.</p>
        <hr />
        <ul className="footer-list d-flex flex-wrap justify-content-center mb-0">
          <li className="footer-item mx-3 my-2">
            <Link to="/informacion-recogida" className="footer-link">Información recogida</Link>
          </li>
          <li className="footer-item mx-3 my-2">
            <Link to="/politica-cookies" className="footer-link">Política de cookies</Link>
          </li>
          <li className="footer-item mx-3 my-2">
            <Link to="/politica-privacidad" className="footer-link">Política de privacidad</Link>
          </li>
          <li className="footer-item mx-3 my-2">
            <Link to="/cookies-esenciales" className="footer-link">Cookies esenciales</Link>
          </li>
          <li className="footer-item mx-3 my-2">
            <Link to="/cambios-politica-cookies" className="footer-link">Cambios en la política de cookies</Link>
          </li>
        </ul>
      </div>
    </footer>
  );
};

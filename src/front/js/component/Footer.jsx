import React from 'react';
import { Link } from 'react-router-dom';
import '../../styles/footer.css';

export const Footer = () => {
  return (
    <footer className="mt-auto bg-dark text-white py-3 px-5">
      <div className="container text-center">
        <p style={{marginTop: '6px', marginBottom: '17px'}}>© 2025 Metal Wolft. Todos los derechos reservados.</p>
        <hr />
        <ul className="footer-list">
          <li className="footer-item">
            <Link to="/informacion-recogida" className="footer-link">Información recogida</Link>
          </li>
          <li className="footer-item">
            <Link to="/politica-cookies" className="footer-link">Política de cookies</Link>
          </li>
          <li className="footer-item">
            <Link to="/politica-privacidad" className="footer-link">Política de privacidad</Link>
          </li>
          <li className="footer-item">
            <Link to="/cookies-esenciales" className="footer-link">Cookies esenciales</Link>
          </li>
          <li className="footer-item">
            <Link to="/cambios-politica-cookies" className="footer-link">Cambios en la política de cookies</Link>
          </li>
          <li className="footer-item">
            <Link to="/politica-devolucion" className="footer-link">Política de devolución</Link>
          </li>
        </ul>
      </div>
    </footer>
  );
};

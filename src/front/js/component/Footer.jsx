import React from 'react';
import { Link } from 'react-router-dom';
import '../../styles/footer.css';

export const Footer = () => {
  return (
    <footer className="footer-style mt-auto bg-dark text-white">
      <div className="row footer-row">
        <div className="footer-box col-12 col-md-6 col-lg-6 col-xl-6">
          <h2 className="footer-h5 mb-4 text-uppercase">Localización</h2>
          <p className="footer-p">
            <i className="fa-solid fa-location-dot"></i> Ofic. Calle Pedrera Alta 11. Ciudad Real, Castilla La Mancha, España
          </p>
          <div className="alert alert-warning d-flex align-items-center" role="alert">
            <svg
              className="bi flex-shrink-0 me-2"
              role="img"
              aria-label="Warning:"
              viewBox="0 0 16 16"
              width="12"
              height="12"
              fill="currentColor"
            >
              <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z" />
            </svg>
            <div style={{ fontSize: "0.7rem" }}>
              Actualmente esta oficina no está abierta al público.
            </div>
          </div>
          <p className="footer-p">
            <i className="fa-regular fa-envelope-open"></i> admin@metalwolft.com
          </p>
          <p className="footer-p">
            <i className="fa-solid fa-phone"></i> +34 634 11 26 04
          </p>
        </div>
        <div className="footer-box col-12 col-md-3 col-lg-3 col-xl-3">
          <h2 className="footer-h5 mb-4 text-uppercase">Contacto</h2>
          <p className="footer-p"><Link to="/contact" className="footer-p">Contacto</Link></p>
          <p className="footer-p"><Link to="/cookies-esenciales" className="footer-p">Cookies esenciales</Link></p>
          <p className="footer-p"><Link to="/politica-cookies" className="footer-p">Política de cookies</Link></p>
        </div>
        <div className="footer-box col-12 col-md-3 col-lg-3 col-xl-3">
          <h2 className="footer-h5 mb-4 text-uppercase">Área legal</h2>
          <p className="footer-p"><Link to="/informacion-recogida" className="footer-p">Información recogida</Link></p>
          <p className="footer-p"><Link to="/cambios-politica-cookies" className="footer-p">Cambios en la política de cookies</Link></p>
          <p className="footer-p"><Link to="/politica-privacidad" className="footer-p">Política de privacidad</Link></p>
        </div>
      </div>
    </footer>
  );
};

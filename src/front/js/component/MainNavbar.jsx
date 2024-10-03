import React, { useContext, useState } from "react";
import logoweb from "../../img/herrero-soldador-en-ciudad-real.png";
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import { useNavigate } from "react-router-dom";
import { Context } from "../store/appContext";
import { Link } from "react-router-dom";
import '../../styles/navbar.css';

export const MainNavbar = () => {
    const { store, actions } = useContext(Context);
    const [expanded, setExpanded] = useState(false);
    const navigate = useNavigate();

    const handleLogout = () => {
        actions.setIsLoged(false);
        setExpanded(false);
        navigate("/"); // Redirige a la home después del logout
    };

    const handleToggle = () => setExpanded(!expanded);
    const handleSelect = () => setExpanded(false);

    const handleFavoritesClick = () => {
        if (store.isLoged) {
            navigate('/favoritos');
        } else {
            alert('Debe registrarse para ver los favoritos');
        }
    };

    return (
        <Navbar expand="lg" className="estilo-navbar fixed-top text-uppercase" data-bs-theme="light" expanded={expanded}>
            <Container fluid>
                <Navbar.Brand as={Link} to="/" onClick={handleSelect}>
                    <img src={logoweb} alt="Logo" className="d-inline-block align-top" />
                </Navbar.Brand>
                <Navbar.Toggle aria-controls="basic-navbar-nav" onClick={handleToggle} />
                <Navbar.Collapse id="basic-navbar-nav">
                    <Nav className="me-auto" onSelect={handleSelect}>
                        <Nav.Link as={Link} to="/" onClick={handleSelect}>Inicio</Nav.Link>
                        <NavDropdown title="Productos" id="trainer-nav-dropdown">
                            <NavDropdown.Item as={Link} to="/rejas-para-ventanas" onClick={handleSelect}>Rejas para ventanas</NavDropdown.Item>
                            <NavDropdown.Item as={Link} to="/generate-routines" onClick={handleSelect}>Generar Rutina</NavDropdown.Item>
                        </NavDropdown>
                        <Nav.Link as={Link} to="/bmr-calculator" onClick={handleSelect}>Blog</Nav.Link>
                        <Nav.Link as={Link} to="/exercises" onClick={handleSelect}>Contácto</Nav.Link>
                        <Nav.Link as={Link} to="/bmr-calculator" onClick={handleSelect}>Sobre nosotros</Nav.Link>
                    </Nav>
                    <Nav className="ms-auto" onSelect={handleSelect}>
                        <Nav.Link onClick={handleFavoritesClick} className="d-flex align-items-center position-relative">
                            <i className="fa-regular fa-heart fa-lg me-2"></i>
                            <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                                {store.favorites ? store.favorites.length : 0}
                                <span className="visually-hidden">favoritos</span>
                            </span>
                        </Nav.Link>
                        {store.isLoged ? (
                            <>
                                {store.currentUser?.is_admin && (
                                    <Nav.Link as={Link} to="/admin" onClick={handleSelect}>
                                        Administración
                                    </Nav.Link>
                                )}
                                <Nav.Link onClick={handleLogout} className="d-flex align-items-center">
                                    <i className="fa-solid fa-right-to-bracket fa-lg me-2"></i>
                                    <p className="small mb-0">Salir</p>
                                </Nav.Link>
                            </>
                        ) : (
                            <Nav.Link onClick={() => { setExpanded(false); navigate("/login"); }} className="d-flex align-items-center">
                                <i className="fa-solid fa-user-plus fa-lg me-2"></i>
                                <p className="small mb-0">Iniciar sesión</p>
                            </Nav.Link>
                        )}
                    </Nav>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
};

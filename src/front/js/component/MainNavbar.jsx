import React, { useContext, useState } from "react";
import logoweb from "../../img/LogoWeb.png";
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import { Button } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { Context } from "../store/appContext";
import { Link } from "react-router-dom";
import '../../styles/navbar.css';

export const MainNavbar = () => {
    const { store, actions } = useContext(Context);
    const [expanded, setExpanded] = useState(false); // controla el estado del nav
    const navigate = useNavigate();

    const handleLogout = () => {
        actions.setIsLoged(false);
        setExpanded(false); // cierra el nav al salir
        navigate("/"); // y redirige a la home
    };

    const handleToggle = () => setExpanded(!expanded); // interructor de abrir y cerrar el menu

    const handleSelect = () => setExpanded(false); // cierra el menu al hacer clickç

    return (
        <Navbar expand="lg" className="estilo-navbar fixed-top text-uppercase" data-bs-theme="light" expanded={expanded}>
            <Container fluid>
                <Navbar.Brand as={Link} to="/" onClick={handleSelect}>
                    <img src={logoweb} alt="Logo" className="d-inline-block align-top" />
                </Navbar.Brand>
                <Navbar.Toggle aria-controls="basic-navbar-nav" onClick={handleToggle} />
                <Navbar.Collapse id="basic-navbar-nav">
                    <Nav className="me-auto" onSelect={handleSelect}>
                        <Nav.Link as={Link} to="/trainers" onClick={handleSelect}>Trainers</Nav.Link>
                        <Nav.Link as={Link} to="/bmr-calculator" onClick={handleSelect}>BMR Calculator</Nav.Link>
                        <NavDropdown title="TrAIner" id="trainer-nav-dropdown">
                            <NavDropdown.Item as={Link} to="/generate-recipes" onClick={handleSelect}>Generar Receta</NavDropdown.Item>
                            <NavDropdown.Item as={Link} to="/generate-routines" onClick={handleSelect}>Generar Rutina</NavDropdown.Item>
                        </NavDropdown>
                        <Nav.Link as={Link} to="/exercises" onClick={handleSelect}>Ejercicios</Nav.Link>
                    </Nav>
                    <Nav className="ms-auto" onSelect={handleSelect}>
                        {store.isLoged ? (
                            <NavDropdown title={<i className="fa-solid fa-user"></i>} id="user-nav-dropdown" align="end">
                                <NavDropdown.Item as={Link} to="/profile" onClick={handleSelect}>Perfil</NavDropdown.Item>
                                <NavDropdown.Divider />
                                <NavDropdown.Item onClick={handleLogout}>Cerrar sesión</NavDropdown.Item>
                            </NavDropdown>
                        ) : (
                            <Button variant="outline-dark mx-1" onClick={() => { setExpanded(false); navigate("/login"); }}>
                                <i className="fa-solid fa-user-plus"></i>
                            </Button>
                        )}
                    </Nav>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
};

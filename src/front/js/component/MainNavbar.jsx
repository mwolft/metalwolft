import React, { useContext } from "react";
import { useState } from "react";
import logoweb from "../../img/LogoWeb.png";
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import { Button } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { Context } from "../store/appContext";
import { Link } from "react-router-dom";
import '../../styles/MainNavbar.css';


export const MainNavbar = () => {
    const { store, actions } = useContext(Context);
    const { isLoggedIn, setIsLoggedIn } = useState(false);
    const navigate = useNavigate();

    const handleLogout = () => {
        actions.setIsLoged(false);
    };

    return (
        <Navbar expand="lg" className="estilo-navbar fixed-top" data-bs-theme="light">
            <Container fluid>
                <Navbar.Brand as={Link} to="/"> 
                    <img src={logoweb} alt="Logo" width="100" height="30" className="d-inline-block align-top" />
                </Navbar.Brand>
                <Navbar.Toggle aria-controls="basic-navbar-nav" />
                <Navbar.Collapse id="basic-navbar-nav">
                    <Nav className="me-auto">
                        <Nav.Link as={Link} to="/trainers">Trainers</Nav.Link>
                        <Nav.Link as={Link} to="/bmr-calculator">BMR Calculator</Nav.Link>
                        <NavDropdown title="TrAIner" id="trainer-nav-dropdown">
                            <NavDropdown.Item as={Link} to="/generate-recipes">Generate Recipes</NavDropdown.Item>
                            <NavDropdown.Item as={Link} to="/generate-routines">Generate Routines</NavDropdown.Item>
                        </NavDropdown>
                        <Nav.Link as={Link} to="/category">Ejercicios</Nav.Link>
                        <Nav.Link as={Link} to="/category">Nutrición</Nav.Link>
                    </Nav>
                    <Nav className="ms-auto">
                        {store.isLoged ? (
                            <NavDropdown title={<i className="fa-solid fa-user"></i>} id="user-nav-dropdown" align="end">
                                <NavDropdown.Item href="#perfil">Perfil</NavDropdown.Item>
                                <NavDropdown.Divider />
                                <NavDropdown.Item onClick={handleLogout}>Cerrar sesión</NavDropdown.Item>
                            </NavDropdown>
                        ) : (
                            <>
                                <Button variant="outline-dark mx-1" onClick={() => navigate("/sign-up")}><i className="fa-solid fa-user-plus"></i></Button>
                                <Button variant="outline-dark mx-1" onClick={() => navigate("/login")}><i className="fa-solid fa-right-to-bracket"></i></Button>
                            </>
                        )}
                    </Nav>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
}
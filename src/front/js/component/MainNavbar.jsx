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



export const MainNavbar = () => {
    const {store, actions} = useContext(Context)
    const { isLoggedIn, setIsLoggedIn } = useState(false);
    const navigate = useNavigate()
    const handleLogout = () => {
        actions.setIsLoged(false);
    };
    return (
        <div className="main-navbar mb-auto p-2">
            <Navbar className="navbar-expand-l">
                <Container>
                    <Navbar.Brand>
                        <img src={logoweb} alt="Logo" width="100" height="30" className="d-inline-block align-top" />
                    </Navbar.Brand>
                    <Navbar.Toggle aria-controls="basic-navbar-nav" />
                    <Navbar.Collapse id="basic-navbar-nav">
                        <Nav className="mx-auto">
                            <Nav.Link href="#trainer">Trainer</Nav.Link>
                            <Nav.Link href="#ejercicios">Ejercicios</Nav.Link>
                            <Nav.Link href="#nutricion">Nutrición</Nav.Link>
                        </Nav>
                        <Nav className="ms-auto">
                            {store.isLoged ? (
                                <NavDropdown title={<i className="fa-solid fa-user"></i>} id="basic-nav-dropdown" align="end">
                                    <NavDropdown.Item href="#perfil">Perfil</NavDropdown.Item>
                                    <NavDropdown.Divider />
                                    <NavDropdown.Item onClick={handleLogout}>Cerrar sesión</NavDropdown.Item>
                                </NavDropdown>
                            ) : (
                                <>
                                    <Button variant="outline-dark" onClick={() => navigate("/login")}><i className="fa-solid fa-user"></i></Button>
                                </>
                            )}
                        </Nav>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
        </div>
    );
};

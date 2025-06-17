import React, { useContext, useState } from "react";
{/* import logoweb from "../../img/logo.png"; */}
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
        navigate("/");
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
        <>
            <div className="top-banner text-center py-2">
                <i className="fa-solid fa-truck-fast"></i> Envíos gratuítos a partir de 350€
            </div>
            <Navbar expand="lg" className="estilo-navbar fixed-top text-uppercase" data-bs-theme="light" expanded={expanded}>
                <Container fluid>
                    <Navbar.Brand as={Link} to="/" onClick={handleSelect}>
                    {/* <img src={logoweb} alt="Logo" className="d-inline-block align-top" />*/}
                        <img
                            src="https://res.cloudinary.com/dewanllxn/image/upload/v1750127736/logo-metal-wolft_zlbzng.avif"
                            alt="rejas para ventanas logo"
                            className="navbar-logo"
                            width="182" 
                            height="47" 
                            loading="eager" 
                        />
                    </Navbar.Brand>
                    <div className="d-flex align-items-center justify-content-center">
                        <Nav.Link onClick={handleFavoritesClick} className="d-flex align-items-center position-relative d-lg-none">
                            <i className="fa-regular fa-heart fa-lg"></i>
                            {store.isLoged && (
                                <span className="position-absolute badge rounded-pill bg-danger favorites-badge">
                                    {store.favorites.length}
                                    <span className="visually-hidden">favoritos</span>
                                </span>
                            )}
                        </Nav.Link>
                        <Nav.Link as={Link} to="/cart" className="d-flex align-items-center position-relative d-lg-none">
                            <i className="fa-solid fa-cart-shopping fa-lg"></i>
                            {store.isLoged && (
                                <span className="position-absolute badge rounded-pill bg-danger cart-badge">
                                    {store.cart.length}
                                    <span className="visually-hidden">productos en el carrito</span>
                                </span>
                            )}
                        </Nav.Link>
                        {store.isLoged ? (
                            <Nav.Link onClick={handleLogout} className="d-flex align-items-center d-lg-none">
                                <i className="fa-solid fa-right-to-bracket fa-lg me-2"></i>
                                <p className="small mb-0"></p>
                            </Nav.Link>
                        ) : (
                            <Nav.Link onClick={() => { setExpanded(false); navigate("/login"); }} className="d-flex align-items-center d-lg-none">
                                <i className="fa-regular fa-user fa-lg me-2"></i>
                                <p className="small mb-0"></p>
                            </Nav.Link>
                        )}
                        <Navbar.Toggle aria-controls="basic-navbar-nav" onClick={handleToggle} />
                    </div>
                    <Navbar.Collapse id="basic-navbar-nav">
                        <Nav className="m-auto" onSelect={handleSelect}>
                            <Nav.Link as={Link} to="/" onClick={handleSelect}>Inicio</Nav.Link>
                            <NavDropdown title="Productos" id="trainer-nav-dropdown">
                                <NavDropdown.Item as={Link} to="/rejas-para-ventanas" onClick={handleSelect}>Rejas para Ventanas</NavDropdown.Item>
                                <NavDropdown.Item as={Link} to="/vallados-metalicos-exteriores" onClick={handleSelect}>Vallados Metálicos Exteriores</NavDropdown.Item>
                                <NavDropdown.Item as={Link} to="/puertas-peatonales-metalicas" onClick={handleSelect}>Puertas Peatonales Metálicas</NavDropdown.Item>
                                <NavDropdown.Item as={Link} to="/puertas-correderas-exteriores" onClick={handleSelect}>Puertas Correderas Exteriores</NavDropdown.Item>
                                <NavDropdown.Item as={Link} to="/cerramientos-de-cocina-con-cristal" onClick={handleSelect}>Cerramientos de Cocina con Cristal</NavDropdown.Item>
                                <NavDropdown.Item as={Link} to="/puertas-correderas-interiores" onClick={handleSelect}>Puertas Correderas Interiores</NavDropdown.Item>
                            </NavDropdown>
                            <Nav.Link as={Link} to="/blogs" onClick={handleSelect}>Blog</Nav.Link>
                            {store.isLoged && store.currentUser?.is_admin && (
                                <Nav.Link as={Link} to="/admin" onClick={handleSelect} className="d-lg-none" style={{ marginLeft: '1.3rem', border: 'solid 2px #ff324d', borderRadius: '10px' }}>
                                    <i className="fa-solid fa-toolbox"></i> Admin
                                </Nav.Link>
                            )}
                        </Nav>
                        <Nav className="ms-auto d-none d-lg-flex" onSelect={handleSelect}>
                            <Nav.Link onClick={handleFavoritesClick} className="d-flex align-items-center position-relative">
                                <i className="fa-regular fa-heart fa-lg"></i>
                                {store.isLoged && (
                                    <span className="position-absolute badge rounded-pill favorites-badge">
                                        {store.favorites.length}
                                        <span className="visually-hidden">favoritos</span>
                                    </span>
                                )}
                            </Nav.Link>
                            <Nav.Link as={Link} to="/cart" className="d-flex align-items-center position-relative">
                                <i className="fa-solid fa-cart-shopping fa-lg"></i>
                                {store.isLoged && (
                                    <span className="position-absolute badge rounded-pill favorites-badge">
                                        {store.cart.length}
                                        <span className="visually-hidden">productos en el carrito</span>
                                    </span>
                                )}
                            </Nav.Link>
                            {store.isLoged ? (
                                <>
                                    {store.currentUser?.is_admin && (
                                        <Nav.Link as={Link} to="/admin" onClick={handleSelect} style={{ marginLeft: '1.3rem', border: 'solid 2px #ff324d', borderRadius: '10px' }}>
                                            <i className="fa-solid fa-toolbox"></i> Admin
                                        </Nav.Link>
                                    )}
                                    <Nav.Link onClick={handleLogout} className="button-navbar d-flex align-items-center">
                                        <i className="fa-solid fa-right-to-bracket fa-lg me-2"></i>
                                        <p className="small mb-0">Salir</p>
                                    </Nav.Link>
                                </>
                            ) : (
                                <Nav.Link onClick={() => { setExpanded(false); navigate("/login"); }} className="button-navbar d-flex align-items-center">
                                    <i className="fa-regular fa-user fa-lg me-2"></i>
                                    <p className="small mb-0">Iniciar sesión</p>
                                </Nav.Link>
                            )}
                        </Nav>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
        </>
    );
};

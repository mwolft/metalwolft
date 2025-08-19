import React, { useContext, useState } from "react";
/* import logoweb from "../../img/logo.png"; */
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import { useNavigate, Link } from "react-router-dom";
import { Context } from "../store/appContext";
import '../../styles/navbar.css';

export const MainNavbar = () => {
    const { store, actions } = useContext(Context);
    const [expanded, setExpanded] = useState(false);
    const navigate = useNavigate();

    const displayName = (() => {
        const fn = store.currentUser?.firstname?.trim();
        if (fn) return fn;
        const emailUser = store.currentUser?.email?.split('@')?.[0];
        return emailUser || 'Usuario';
    })();


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
                🚚 Envío gratis a partir de 150€{" "}
                <span
                    style={{ cursor: 'pointer' }}
                    title="Haz clic para más info"
                    onClick={() =>
                        alert(
                            `No se aplica a productos que superen las dimensiones máximas estándar.\n\n` +
                            `Se consideran grandes si la suma de largo + ancho + alto excede los 300 cm.\n\n` +
                            `Estos productos tienen tarifa especial de envío.`
                        )
                    }
                >
                    ℹ️
                </span>
            </div>

            <Navbar
                expand="lg"
                className="estilo-navbar fixed-top text-uppercase"
                data-bs-theme="light"
                expanded={expanded}
            >
                <Container fluid>
                    <Navbar.Brand as={Link} to="/" onClick={handleSelect}>
                        {/* <img src={logoweb} alt="Logo" className="d-inline-block align-top" /> */}
                        <img
                            src="https://res.cloudinary.com/dewanllxn/image/upload/v1750127736/logo-metal-wolft_zlbzng.avif"
                            alt="rejas para ventanas logo"
                            className="navbar-logo"
                            width="182"
                            height="47"
                            loading="eager"
                        />
                    </Navbar.Brand>

                    {/* Iconos visibles SOLO en móvil */}
                    <div className="d-flex align-items-center justify-content-center">

                        {/* Favoritos */}
                        <Nav.Link
                            onClick={handleFavoritesClick}
                            className="d-flex align-items-center position-relative d-lg-none"
                            aria-label="Favoritos"
                        >
                            <i className="fa-regular fa-heart fa-lg"></i>
                            {store.isLoged && (
                                <span className="position-absolute badge rounded-pill bg-danger favorites-badge">
                                    {store.favorites.length}
                                    <span className="visually-hidden">favoritos</span>
                                </span>
                            )}
                        </Nav.Link>

                        {/* Carrito */}
                        <Nav.Link
                            as={Link}
                            to="/cart"
                            className="d-flex align-items-center position-relative d-lg-none"
                            aria-label="Carrito"
                            onClick={handleSelect}
                            id="carrito"
                        >
                            <i className="fa-solid fa-cart-shopping fa-lg"></i>
                            {store.isLoged && (
                                <span className="position-absolute badge rounded-pill bg-danger cart-badge">
                                    {store.cart.length}
                                    <span className="visually-hidden">productos en el carrito</span>
                                </span>
                            )}
                        </Nav.Link>

                        {/* Usuario solo si NO está logado */}
                        {!store.isLoged && (
                            <Nav.Link
                                onClick={() => { setExpanded(false); navigate("/login"); }}
                                className="d-flex align-items-center d-lg-none iniciar-sesion"
                                aria-label="Iniciar sesión"
                            >
                                <i className="fa-regular fa-user fa-lg"></i>
                            </Nav.Link>
                        )}

                        <Navbar.Toggle aria-controls="basic-navbar-nav" onClick={handleToggle} />
                    </div>



                    <Navbar.Collapse id="basic-navbar-nav">
                        <Nav className="m-auto" onSelect={handleSelect}>
                            <Nav.Link as={Link} to="/" onClick={handleSelect}>
                                <span className="d-lg-none">
                                    <i className="fa-solid fa-house me-2"></i> Inicio
                                </span>
                                <span className="d-none d-lg-inline">Inicio</span>
                            </Nav.Link>


                            <NavDropdown
                                title={
                                    <>
                                        <span className="d-lg-none">
                                            <i className="fa-solid fa-box me-2"></i> Productos
                                        </span>
                                        <span className="d-none d-lg-inline">Productos</span>
                                    </>
                                }
                                id="trainer-nav-dropdown"
                            >
                                <NavDropdown.Item as={Link} to="/rejas-para-ventanas" onClick={handleSelect}>
                                    Rejas para Ventanas
                                </NavDropdown.Item>
                                <NavDropdown.Item as={Link} to="/vallados-metalicos-exteriores" onClick={handleSelect}>
                                    Vallados Metálicos Exteriores
                                </NavDropdown.Item>
                                <NavDropdown.Item as={Link} to="/puertas-peatonales-metalicas" onClick={handleSelect}>
                                    Puertas Peatonales Metálicas
                                </NavDropdown.Item>
                                <NavDropdown.Item as={Link} to="/puertas-correderas-exteriores" onClick={handleSelect}>
                                    Puertas Correderas Exteriores
                                </NavDropdown.Item>
                                <NavDropdown.Item as={Link} to="/cerramientos-de-cocina-con-cristal" onClick={handleSelect}>
                                    Cerramientos de Cocina con Cristal
                                </NavDropdown.Item>
                                <NavDropdown.Item as={Link} to="/puertas-correderas-interiores" onClick={handleSelect}>
                                    Puertas Correderas Interiores
                                </NavDropdown.Item>
                            </NavDropdown>

                            <Nav.Link as={Link} to="/blogs" onClick={handleSelect}>
                                <span className="d-lg-none">
                                    <i className="fa-regular fa-newspaper me-2"></i> Blog
                                </span>
                                <span className="d-none d-lg-inline">Blog</span>
                            </Nav.Link>


                            {/* En MÓVIL añadimos opciones de cuenta dentro del menú colapsado */}
                            <div className="d-lg-none">
                                <hr className="my-2" />
                                {store.isLoged ? (
                                    <>
                                        <Nav.Link as={Link} to="/mi-cuenta" onClick={handleSelect}>
                                            <i className="fa-regular fa-id-card me-2"></i> Mi cuenta
                                        </Nav.Link>

                                        {store.currentUser?.is_admin && (
                                            <Nav.Link
                                                as={Link}
                                                to="/admin"
                                                onClick={handleSelect}
                                            >
                                                <i className="fa-solid fa-toolbox" style={{ marginRight: '9px' }}></i> Admin
                                            </Nav.Link>
                                        )}

                                        <Nav.Link onClick={handleLogout}>
                                            <i className="fa-solid fa-arrow-right-from-bracket me-2"></i> Cerrar sesión
                                        </Nav.Link>
                                    </>
                                ) : (
                                    <Nav.Link onClick={() => { setExpanded(false); navigate("/login"); }} className="iniciar-sesion">
                                        <i className="fa-regular fa-user me-2"></i> Iniciar sesión
                                    </Nav.Link>
                                )}
                            </div>
                        </Nav>

                        {/* Zona derecha SOLO escritorio */}
                        <Nav className="ms-auto d-none d-lg-flex" onSelect={handleSelect}>
                            <Nav.Link
                                onClick={handleFavoritesClick}
                                className="d-flex align-items-center position-relative"
                                aria-label="Favoritos"
                            >
                                <i className="fa-regular fa-heart fa-lg"></i>
                                {store.isLoged && (
                                    <span className="position-absolute badge rounded-pill favorites-badge">
                                        {store.favorites.length}
                                        <span className="visually-hidden">favoritos</span>
                                    </span>
                                )}
                            </Nav.Link>

                            <Nav.Link
                                as={Link}
                                to="/cart"
                                className="d-flex align-items-center position-relative"
                                aria-label="Carrito"
                            >
                                <i className="fa-solid fa-cart-shopping fa-lg"></i>
                                {store.isLoged && (
                                    <span className="position-absolute badge rounded-pill favorites-badge">
                                        {store.cart.length}
                                        <span className="visually-hidden">productos en el carrito</span>
                                    </span>
                                )}
                            </Nav.Link>

                            {store.isLoged ? (
                                <NavDropdown
                                    title={
                                        <span>
                                            <i className="fa-regular fa-user fa-lg me-2"></i>
                                            <span className="d-none d-lg-inline">Hola, {displayName}</span>
                                        </span>
                                    }
                                    id="account-dropdown-desktop"
                                    align="end"
                                >

                                    <NavDropdown.Item as={Link} to="/mi-cuenta" onClick={handleSelect}>
                                        <i className="fa-regular fa-id-card me-2"></i> Mi cuenta
                                    </NavDropdown.Item>

                                    {store.currentUser?.is_admin && (
                                        <>
                                            <NavDropdown.Divider />
                                            <NavDropdown.Item as={Link} to="/admin" onClick={handleSelect}>
                                                <i className="fa-solid fa-toolbox me-2"></i> Panel de administración
                                            </NavDropdown.Item>
                                        </>
                                    )}

                                    <NavDropdown.Divider />
                                    <NavDropdown.Item onClick={handleLogout}>
                                        <i className="fa-solid fa-arrow-right-from-bracket me-2"></i> Cerrar sesión
                                    </NavDropdown.Item>
                                </NavDropdown>
                            ) : (
                                <Nav.Link
                                    onClick={() => { setExpanded(false); navigate("/login"); }}
                                    className="button-navbar d-flex align-items-center"
                                >
                                    <i className="fa-regular fa-user fa-lg me-2"></i>
                                    <p className="small mb-0 sin-margin-right">Iniciar sesión</p>
                                </Nav.Link>
                            )}
                        </Nav>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
        </>
    );
};

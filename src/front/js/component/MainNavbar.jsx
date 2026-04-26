import React, { useContext, useState } from "react";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import NavDropdown from "react-bootstrap/NavDropdown";
import { useNavigate, Link } from "react-router-dom";
import { Context } from "../store/appContext";
import "../../styles/navbar.css";

export const MainNavbar = () => {
    const { store, actions } = useContext(Context);
    const [expanded, setExpanded] = useState(false);
    const navigate = useNavigate();
    const isAdminUser = Boolean(store.isAdmin || store.currentUser?.is_admin);

    const displayName = (() => {
        const fn = store.currentUser?.firstname?.trim();
        if (fn) return fn;
        const emailUser = store.currentUser?.email?.split("@")?.[0];
        return emailUser || "Usuario";
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
            navigate("/favoritos");
        } else {
            alert("Debe registrarse para ver los favoritos");
        }
    };

    const handleLoginClick = () => {
        setExpanded(false);
        navigate("/login");
    };

    const handleMobileFavoritesClick = () => {
        handleFavoritesClick();
        setExpanded(false);
    };

    const productMenuGroups = [
        {
            title: "Rejas",
            items: [
                { to: "/rejas-para-ventanas", label: "Rejas para ventanas" }
            ]
        },
        {
            title: "Exterior",
            items: [
                { to: "/vallados-metalicos-exteriores", label: "Vallados metálicos" },
                { to: "/puertas-peatonales-metalicas", label: "Puertas peatonales" },
                { to: "/puertas-correderas-exteriores", label: "Puertas correderas exteriores" }
            ]
        },
        {
            title: "Interior",
            items: [
                { to: "/puertas-correderas-interiores", label: "Puertas correderas interiores" },
                { to: "/cerramientos-de-cocina-con-cristal", label: "Cerramientos con cristal" }
            ]
        }
    ];

    return (
        <>
            <div className="top-banner">
                <span className="top-banner-copy">Envío gratis a partir de 150€</span>
                <button
                    type="button"
                    className="top-banner-info"
                    title="Haz clic para más info"
                    aria-label="Más información sobre envíos"
                    onClick={() =>
                        alert(
                            `Información sobre envíos especiales.\n\n` +
                            `Se aplica una tarifa especial cuando:\n` +
                            `- El lado más largo supera los 175 cm, o\n` +
                            `- La suma de las dimensiones (alto + ancho + fondo) supera los 300 cm.\n\n` +
                            `Los productos que cumplen estas condiciones tendrán un coste de envío especial.`
                        )
                    }
                >
                    <i className="fa-solid fa-circle-info" aria-hidden="true"></i>
                </button>
            </div>

            <Navbar
                expand="lg"
                className="estilo-navbar fixed-top text-uppercase"
                data-bs-theme="light"
                expanded={expanded}
            >
                <Container fluid className="navbar-shell">
                    <Navbar.Brand as={Link} to="/" onClick={handleSelect}>
                        <img
                            src="https://res.cloudinary.com/dewanllxn/image/upload/v1750127736/logo-metal-wolft_zlbzng.avif"
                            alt="rejas para ventanas logo"
                            className="navbar-logo"
                            width="182"
                            height="47"
                            loading="eager"
                        />
                    </Navbar.Brand>

                    <div className="navbar-mobile-actions d-flex d-lg-none">
                        <Nav.Link
                            as={Link}
                            to="/cart"
                            className="navbar-icon-link position-relative"
                            aria-label="Carrito"
                            onClick={handleSelect}
                            id="carrito"
                        >
                            <i className="fa-solid fa-cart-shopping"></i>
                            {store.isLoged && (
                                <span className="position-absolute badge rounded-pill bg-danger cart-badge">
                                    {store.cart.length}
                                    <span className="visually-hidden">productos en el carrito</span>
                                </span>
                            )}
                        </Nav.Link>

                        <Navbar.Toggle
                            aria-controls="basic-navbar-nav"
                            onClick={handleToggle}
                            className="navbar-mobile-toggle"
                        />
                    </div>

                    <Navbar.Collapse id="basic-navbar-nav" className="navbar-collapse-shell">
                        <Nav className="navbar-primary-nav mx-auto" onSelect={handleSelect}>
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
                                            <i className="fa-solid fa-box me-2"></i> Catálogo
                                        </span>
                                        <span className="d-none d-lg-inline">Catálogo</span>
                                    </>
                                }
                                id="trainer-nav-dropdown"
                                className="products-dropdown-menu"
                            >
                                <div className="products-mega-menu-grid d-none d-lg-grid">
                                    {productMenuGroups.map((group) => (
                                        <div className="products-mega-group" key={group.title}>
                                            <div className="products-mega-group-title">{group.title}</div>
                                            <div className="products-mega-links">
                                                {group.items.map((item) => (
                                                    <NavDropdown.Item
                                                        as={Link}
                                                        to={item.to}
                                                        onClick={handleSelect}
                                                        className="products-mega-link"
                                                        key={item.to}
                                                    >
                                                        {item.label}
                                                    </NavDropdown.Item>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div className="d-lg-none">
                                    {productMenuGroups.flatMap((group) => group.items).map((item) => (
                                        <NavDropdown.Item
                                            as={Link}
                                            to={item.to}
                                            onClick={handleSelect}
                                            className="products-mobile-link"
                                            key={item.to}
                                        >
                                            {item.label}
                                        </NavDropdown.Item>
                                    ))}
                                </div>
                            </NavDropdown>

                            <Nav.Link as={Link} to="/blogs" onClick={handleSelect}>
                                <span className="d-lg-none">
                                    <i className="fa-regular fa-newspaper me-2"></i> Blog
                                </span>
                                <span className="d-none d-lg-inline">Blog</span>
                            </Nav.Link>
                        </Nav>

                        <Nav className="navbar-mobile-menu d-lg-none">
                            <Nav.Link
                                onClick={handleMobileFavoritesClick}
                                className="navbar-mobile-menu-link"
                                aria-label="Favoritos"
                            >
                                <span className="navbar-mobile-menu-label">
                                    <i className="fa-regular fa-heart"></i>
                                    Favoritos
                                </span>
                                {store.isLoged && (
                                    <span className="navbar-inline-badge">{store.favorites.length}</span>
                                )}
                            </Nav.Link>

                            {store.isLoged ? (
                                <>
                                    <Nav.Link
                                        as={Link}
                                        to="/mi-cuenta"
                                        onClick={handleSelect}
                                        className="navbar-mobile-menu-link"
                                    >
                                        <span className="navbar-mobile-menu-label">
                                            <i className="fa-regular fa-id-card"></i>
                                            Mi cuenta
                                        </span>
                                    </Nav.Link>

                                    {isAdminUser && (
                                        <Nav.Link
                                            as={Link}
                                            to="/admin"
                                            onClick={handleSelect}
                                            className="navbar-mobile-menu-link"
                                        >
                                            <span className="navbar-mobile-menu-label">
                                                <i className="fa-solid fa-toolbox"></i>
                                                Admin
                                            </span>
                                        </Nav.Link>
                                    )}

                                    <Nav.Link onClick={handleLogout} className="navbar-mobile-menu-link">
                                        <span className="navbar-mobile-menu-label">
                                            <i className="fa-solid fa-arrow-right-from-bracket"></i>
                                            Cerrar sesión
                                        </span>
                                    </Nav.Link>
                                </>
                            ) : (
                                <Nav.Link onClick={handleLoginClick} className="navbar-mobile-menu-link">
                                    <span className="navbar-mobile-menu-label">
                                        <i className="fa-regular fa-user"></i>
                                        Iniciar sesión
                                    </span>
                                </Nav.Link>
                            )}

                            <div className="navbar-mobile-support">
                                <div className="navbar-mobile-support-title">Ayuda rápida</div>

                                <div className="navbar-mobile-support-links">
                                    <Nav.Link
                                        href="https://wa.me/34634112604"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        onClick={handleSelect}
                                        className="navbar-mobile-support-link"
                                    >
                                        <span className="navbar-mobile-support-label">
                                            <i className="fa-brands fa-whatsapp"></i>
                                            WhatsApp
                                        </span>
                                    </Nav.Link>

                                    <Nav.Link
                                        href="tel:+34634112604"
                                        onClick={handleSelect}
                                        className="navbar-mobile-support-link"
                                    >
                                        <span className="navbar-mobile-support-label">
                                            <i className="fa-solid fa-phone"></i>
                                            Llamar
                                        </span>
                                    </Nav.Link>

                                    <Nav.Link
                                        as={Link}
                                        to="/contact"
                                        onClick={handleSelect}
                                        className="navbar-mobile-support-link"
                                    >
                                        <span className="navbar-mobile-support-label">
                                            <i className="fa-regular fa-envelope"></i>
                                            Contacto
                                        </span>
                                    </Nav.Link>
                                </div>
                            </div>
                        </Nav>

                        <Nav className="navbar-secondary-nav ms-auto d-none d-lg-flex" onSelect={handleSelect}>
                            <Nav.Link
                                onClick={handleFavoritesClick}
                                className="navbar-icon-link position-relative"
                                aria-label="Favoritos"
                            >
                                <i className="fa-regular fa-heart"></i>
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
                                className="navbar-icon-link position-relative"
                                aria-label="Carrito"
                                onClick={handleSelect}
                            >
                                <i className="fa-solid fa-cart-shopping"></i>
                                {store.isLoged && (
                                    <span className="position-absolute badge rounded-pill cart-badge">
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

                                    {isAdminUser && (
                                        <>
                                            <NavDropdown.Divider />
                                            <NavDropdown.Item as={Link} to="/admin" onClick={handleSelect}>
                                                <i className="fa-solid fa-toolbox me-2"></i> Panel de administracion
                                            </NavDropdown.Item>
                                        </>
                                    )}

                                    <NavDropdown.Divider />
                                    <NavDropdown.Item onClick={handleLogout}>
                                        <i className="fa-solid fa-arrow-right-from-bracket me-2"></i> Cerrar sesión
                                    </NavDropdown.Item>
                                </NavDropdown>
                            ) : (
                                <Nav.Link onClick={handleLoginClick} className="button-navbar d-flex align-items-center">
                                    <i className="fa-regular fa-user fa-lg me-2"></i>
                                    <span className="navbar-login-copy">Iniciar sesión</span>
                                </Nav.Link>
                            )}
                        </Nav>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
        </>
    );
};

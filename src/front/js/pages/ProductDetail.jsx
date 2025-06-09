import React, { useContext, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Context } from '../store/appContext';
import {
    Button,
    Container,
    Row,
    Col,
    Carousel,
    Form,
    OverlayTrigger,
    Popover
} from 'react-bootstrap';
import { Notification } from '../component/Notification.jsx';
import { Helmet } from 'react-helmet-async';
import '../../styles/cards-carrusel.css';
import { WhatsAppWidget } from "../component/WhatsAppWidget.jsx";

export const ProductDetail = () => {
    const { store, actions } = useContext(Context);
    const { category_slug, product_slug } = useParams();
    const navigate = useNavigate();
    const [product, setProduct] = useState(null);
    const [loading, setLoading] = useState(true);
    const [notification, setNotification] = useState(null);
    // --- NUEVO ESTADO PARA LOS METADATOS SEO ---
    const [seoData, setSeoData] = useState(null);

    // Estados “modal-like”
    const [currentIndex, setCurrentIndex] = useState(0);
    const [height, setHeight] = useState('');
    const [width, setWidth] = useState('');
    const [mounting, setMounting] = useState('Sin obra: con pletinas');
    const [color, setColor] = useState('blanco');
    const [calculatedPrice, setCalculatedPrice] = useState(null);
    const [calculatedArea, setCalculatedArea] = useState(null);
    const [calcError, setCalcError] = useState('');

    useEffect(() => {
        const fetchProductAndSeoData = async () => {
            setLoading(true);
            setNotification(null);
            try {
                // Fetch de los datos del producto
                const productRes = await fetch(
                    `${process.env.REACT_APP_BACKEND_URL}/api/${category_slug}/${product_slug}`
                );
                if (!productRes.ok) {
                    const errorData = await productRes.json();
                    throw new Error(errorData.message || 'Producto no encontrado');
                }
                const productData = await productRes.json();
                setProduct(productData);

                // --- NUEVO FETCH PARA LOS METADATOS SEO ---
                const seoRes = await fetch(
                    `${process.env.REACT_APP_BACKEND_URL}/api/seo/${category_slug}/${product_slug}`
                );
                if (seoRes.ok) {
                    const seoJson = await seoRes.json();
                    setSeoData(seoJson);
                } else {
                    console.warn("No se pudieron cargar los metadatos SEO. Usando valores por defecto o los del producto.");
                    // Opcional: Generar un SEOData básico si el fetch falla
                    setSeoData({
                        lang: "es",
                        title: `${productData.nombre} | Metal Wolft`,
                        description: productData.descripcion.substring(0, 150),
                        og_image: productData.imagen,
                        canonical: `${window.location.origin}/${category_slug}/${product_slug}`,
                        json_ld: null // O un JSON-LD básico
                    });
                }

            } catch (err) {
                console.error("Error al cargar el producto o SEO data:", err);
                setNotification(err.message || 'Error al cargar los detalles del producto.');
                navigate('/');
            } finally {
                setLoading(false);
            }
        };

        if (category_slug && product_slug) {
            fetchProductAndSeoData();
        }
    }, [category_slug, product_slug, navigate, actions.apiFetch]);

    const handleSelect = (selectedIndex) => setCurrentIndex(selectedIndex);


    const handleFavorite = async () => {
        if (!store.isLoged) {
            setNotification('Debe iniciar sesión para favoritos');
            return;
        }
        if (actions.isFavorite(product)) {
            await actions.removeFavorite(product.id);
            setNotification('Producto eliminado de favoritos');
        } else {
            await actions.addFavorite(product);
            setNotification('Producto añadido a favoritos');
        }
    };

    const handleCalculatePrice = () => {
        setCalcError('');
        const h = parseFloat(height),
            w = parseFloat(width);
        if (isNaN(h) || isNaN(w)) {
            setCalcError('Debe ingresar dimensiones válidas');
            return;
        }
        if (h < 30 || w < 30 || h > 200 || w > 200 || h + w > 300) {
            setCalcError(
                'Dimensiones fuera de rango (30–200 cm, suma ≤ 300 cm)'
            );
            return;
        }
        const base = product.precio_rebajado || product.precio;
        const area = (h * w) / 10000;
        setCalculatedArea(area);
        let price = area * base;
        const basePrice = 80;
        let multiplier =
            area >= 0.9
                ? 1
                : area >= 0.8
                    ? 1.1
                    : area >= 0.7
                        ? 1.15
                        : area >= 0.6
                            ? 1.2
                            : area >= 0.5
                                ? 1.3
                                : area >= 0.4
                                    ? 1.55
                                    : area >= 0.3
                                        ? 1.9
                                        : area >= 0.2
                                            ? 2.5
                                            : 3.0;
        price = Math.max(price * multiplier, basePrice);
        setCalculatedPrice(price.toFixed(2));
    };

    const handleAddToCart = async () => {
        if (!store.isLoged) {
            setNotification('Debe iniciar sesión para carrito');
            return;
        }
        if (!calculatedPrice) {
            setNotification('Primero calcule el precio');
            return;
        }
        await actions.addToCart({
            product_id: product.id,
            alto: parseFloat(height),
            ancho: parseFloat(width),
            anclaje: mounting,
            color,
            precio_total: calculatedPrice
        });
        setNotification('Producto añadido al carrito');
        // reset
        setHeight('');
        setWidth('');
        setMounting('Sin obra: con pletinas');
        setColor('blanco');
        setCalculatedPrice(null);
        setCalculatedArea(null);
    };

    const determinePlacement = () =>
        window.innerWidth > 768 ? 'right' : 'top';

    if (loading)
        return (
            <div className="text-center mt-5">Cargando producto...</div>
        );
    if (!product) return null;

    const allImages = [
        { image_url: product.imagen },
        ...(product.images || []).filter(img => img.image_url !== product.imagen)
    ];

    return (
        <Container style={{ marginTop: '150px', marginBottom: '100px' }}>
            {seoData && ( 
                <Helmet htmlAttributes={{ lang: seoData.lang || "es" }}>
                    <title>{seoData.title}</title>
                    <meta name="description" content={seoData.description} />
                    <meta name="keywords" content={seoData.keywords} />
                    <meta name="robots" content={seoData.robots || "index, follow"} />
                    <meta name="theme-color" content={seoData.theme_color || "#ffffff"} />

                    {/* Open Graph Tags */}
                    <meta property="og:type" content={seoData.og_type || "product"} />
                    <meta property="og:title" content={seoData.og_title || seoData.title} />
                    <meta property="og:description" content={seoData.og_description || seoData.description} />
                    <meta property="og:image" content={seoData.og_image} />
                    <meta property="og:image:width" content={seoData.og_image_width || "1200"} />
                    <meta property="og:image:height" content={seoData.og_image_height || "630"} />
                    <meta property="og:image:alt" content={seoData.og_image_alt || seoData.title} />
                    <meta property="og:image:type" content={seoData.og_image_type || "image/jpeg"} />
                    <meta property="og:url" content={seoData.og_url} />
                    <meta property="og:site_name" content={seoData.og_site_name || "Metal Wolft"} />
                    <meta property="og:locale" content={seoData.og_locale || "es_ES"} />
                    {seoData.og_updated_time && <meta property="og:updated_time" content={seoData.og_updated_time} />}

                    {/* Twitter Card Tags */}
                    <meta name="twitter:card" content={seoData.twitter_card_type || "summary_large_image"} />
                    <meta name="twitter:site" content={seoData.twitter_site} />
                    <meta name="twitter:creator" content={seoData.twitter_creator} />
                    <meta name="twitter:title" content={seoData.twitter_title || seoData.title} />
                    <meta name="twitter:description" content={seoData.twitter_description || seoData.description} />
                    <meta name="twitter:image" content={seoData.twitter_image} />
                    <meta name="twitter:image:alt" content={seoData.twitter_image_alt || seoData.title} />

                    {/* Canonical URL */}
                    <link rel="canonical" href={seoData.canonical} />

                    {/* JSON-LD Schema */}
                    {seoData.json_ld && (
                        <script type="application/ld+json">
                            {JSON.stringify(seoData.json_ld)}
                        </script>
                    )}
                </Helmet>
            )}

            <Row className="justify-content-center">
                {/* Columna de imágenes: 12 en xs, 5 en lg, centrada */}
                <Col xs={12} lg={5} className="d-flex flex-column align-items-center">
                    <Carousel activeIndex={currentIndex} onSelect={handleSelect} className="w-100">
                        {allImages.map((img, i) => (
                            <Carousel.Item key={i}>
                                <img
                                    src={img.image_url}
                                    alt={product.nombre}
                                    className="d-block w-100 img-fluid"
                                    style={{ borderRadius: '5px' }}
                                />
                            </Carousel.Item>
                        ))}
                    </Carousel>
                    <div className="thumbnail-gallery d-flex justify-content-center mt-3">
                        {allImages.map((img, i) => (
                            <img
                                key={i}
                                src={img.image_url}
                                alt={product.nombre}
                                className={`img-thumbnail mx-1 ${currentIndex === i ? 'active-thumbnail' : ''}`}
                                style={{ width: '72px', height: '80px', cursor: 'pointer' }}
                                onClick={() => setCurrentIndex(i)}
                            />
                        ))}
                    </div>
                </Col>

                {/* Columna de detalles: 12 en xs, 5 en lg, con margen top solo en xs */}
                <Col xs={12} lg={5} className="mt-4 mt-lg-0">
                    <div className="pr_detail">
                        <h1>{product.nombre}</h1>
                        <hr />
                        <h5>
                            Precio:
                            {product.precio_rebajado ? (
                                <>
                                    <span className="price-original" style={{ textDecoration: 'line-through', color: '#999' }}> {product.precio}€/m²</span>
                                    <span className="price-discounted" style={{ color: '#e63946', fontWeight: 'bold', marginLeft: '8px' }}> {product.precio_rebajado}€/m²</span>
                                    <span className="discount-percentage" style={{ color: '#28a745', padding: '2px 6px', marginLeft: '2px' }}> -{product.porcentaje_rebaja}%</span>
                                </>
                            ) : (
                                <span className="current-price ms-2"> {product.precio} €/m²</span>
                            )}
                        </h5>
                        <p>{product.descripcion}</p>

                        <Form>
                            {/* Dimensiones */}
                            <Row>
                                <Col>
                                    <Form.Group>
                                        <Form.Label>Alto (cm)</Form.Label>
                                        <Form.Control
                                            type="number"
                                            value={height}
                                            onChange={e => setHeight(e.target.value)}
                                        />
                                    </Form.Group>
                                </Col>
                                <Col>
                                    <Form.Group>
                                        <Form.Label>Ancho (cm)</Form.Label>
                                        <Form.Control
                                            type="number"
                                            value={width}
                                            onChange={e => setWidth(e.target.value)}
                                        />
                                    </Form.Group>
                                </Col>
                            </Row>
                            {calcError && <p className="text-danger mt-2">{calcError}</p>}

                            {/* Instalación & Color */}
                            <Row className="mt-3">
                                <Col>
                                    <Form.Group>
                                        <OverlayTrigger
                                            trigger={['hover', 'focus']}
                                            placement={determinePlacement()}
                                            overlay={
                                                <Popover id="popover-install">
                                                    <Popover.Header as="h3">Instalación</Popover.Header>
                                                    <Popover.Body style={{ maxWidth: '300px', overflowX: 'hidden' }}>
                                                        <p><b>Sin obra:</b> con pletinas.</p>
                                                        <img
                                                            src="https://res.cloudinary.com/dewanllxn/image/upload/v1738176285/agujeros-en-pletinas_tlosu0.png"
                                                            alt="pletinas"
                                                            // --- CAMBIO 2: Asegurar max-width: 100% y height: auto ---
                                                            style={{ width: '100%', height: 'auto', marginBottom: '10px', display: 'block' }}
                                                        />
                                                        <p><b>Sin obra:</b> con agujeros interiores.</p>
                                                        <img
                                                            src="https://res.cloudinary.com/dewanllxn/image/upload/v1738176285/agujeros-interiores_xa0onj.png"
                                                            alt="interiores"
                                                            // --- CAMBIO 2: Asegurar max-width: 100% y height: auto ---
                                                            style={{ width: '100%', height: 'auto', marginBottom: '10px', display: 'block' }}
                                                        />
                                                        <p><b>Sin obra:</b> con agujeros frontales.</p>
                                                        <img
                                                            src="https://res.cloudinary.com/dewanllxn/image/upload/v1738176286/agujeros-frontales_low9pi.png"
                                                            alt="frontales"
                                                            // --- CAMBIO 2: Asegurar max-width: 100% y height: auto ---
                                                            style={{ width: '100%', height: 'auto', marginBottom: '10px', display: 'block' }}
                                                        />
                                                        <p><b>Con obra:</b> con garras metálicas.</p>
                                                        <img
                                                            src="https://res.cloudinary.com/dewanllxn/image/upload/v1734888241/rejas-para-ventanas-sin-obra_wukdzi.png"
                                                            alt="garras"
                                                            // --- CAMBIO 2: Asegurar max-width: 100% y height: auto ---
                                                            style={{ width: '100%', height: 'auto', display: 'block' }}
                                                        />
                                                    </Popover.Body>
                                                </Popover>
                                            }
                                        >
                                            <Form.Label>
                                                Instalación <i className="fa-solid fa-info-circle ms-2 text-primary" />
                                            </Form.Label>
                                        </OverlayTrigger>
                                        <Form.Select
                                            value={mounting}
                                            onChange={e => setMounting(e.target.value)}
                                        >
                                            <option>Sin obra: con agujeros interiores</option>
                                            <option>Sin obra: con agujeros frontales</option>
                                            <option>Sin obra: con pletinas</option>
                                            <option>Con obra: con garras metálicas</option>
                                        </Form.Select>
                                    </Form.Group>
                                </Col>
                                <Col>
                                    <Form.Group>
                                        <Form.Label>Color</Form.Label>
                                        <Form.Select
                                            value={color}
                                            onChange={e => setColor(e.target.value)}
                                        >
                                            <option>blanco</option>
                                            <option>negro</option>
                                            <option>gris</option>
                                            <option>verde</option>
                                            <option>marrón</option>
                                        </Form.Select>
                                    </Form.Group>
                                </Col>
                            </Row>

                            {/* Botón Calcular */}
                            <Button className="btn-style-background-color mt-3" onClick={handleCalculatePrice}>
                                <i className="fa-solid fa-calculator me-2" /> Calcular precio
                            </Button>

                            {/* Resultado de cálculo */}
                            {calculatedPrice && (
                                <div className="mt-3">
                                    <h5>Precio calculado: {calculatedPrice} €</h5>
                                    {calculatedArea < 1 && <p className="text-warning">Área &lt; 1 m² incrementa coste.</p>}
                                </div>
                            )}

                            <hr />
                            <div className="d-flex justify-content-end align-items-center mt-4">
                                <i
                                    className={`fa-regular fa-heart ${actions.isFavorite(product) ? 'fa-solid' : ''}`}
                                    onClick={handleFavorite}
                                    style={{ cursor: 'pointer', color: '#ff324d', fontSize: '1.5rem', marginRight: '8px' }}
                                />
                                <Button className="btn-style-background-color" onClick={handleAddToCart}>
                                    <i className="fa-solid fa-cart-shopping me-2" /> Añadir al carrito
                                </Button>
                            </div>
                        </Form>
                    </div>
                </Col>
            </Row>
            <WhatsAppWidget
                whatsappNumber="34634112604"
                placeholderText="Escribenos por WhatsApp"
                widgetText="¿Le podemos ayudar?"
                botImage="https://res.cloudinary.com/dewanllxn/image/upload/v1735631180/welder-bot_tqxadc.png"
            />

            {/* Notificación */}
            {notification && (
                <Notification
                    message={notification}
                    duration={3000}
                    onClose={() => setNotification(null)}
                />
            )}
        </Container>
    );
};
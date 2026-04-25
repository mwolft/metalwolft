import React, { useContext, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { RelatedProductsCarousel } from "../component/RelatedProductsCarousel.jsx";
import { Context } from '../store/appContext';
import { Heart, HeartOff, Share2, ShoppingCart } from 'lucide-react';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import {
    Button,
    Container,
    Row,
    Col,
    Carousel,
    Form,
    OverlayTrigger,
    Overlay,
    Popover
} from 'react-bootstrap';
import { Notification } from '../component/Notification.jsx';
import { Helmet } from 'react-helmet-async';
import '../../styles/cards-carrusel.css';
import { WhatsAppWidget } from "../component/WhatsAppWidget.jsx";
import DeliveryEstimate from "../component/DeliveryEstimate.jsx"
import { Breadcrumb } from "../component/Breadcrumb.jsx";

const PENDING_PRODUCT_CONFIG_STORAGE_KEY = "mw_pending_product_config";
const PENDING_PRODUCT_CONFIG_MAX_AGE_MS = 30 * 60 * 1000;
const DEFAULT_MOUNTING = 'Sin obra: con agujeros interiores';
const DEFAULT_COLOR = 'satinado_blanco';

const readPendingProductConfig = () => {
    if (typeof window === "undefined") return null;

    const rawPendingConfig = window.sessionStorage.getItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
    if (!rawPendingConfig) return null;

    try {
        return JSON.parse(rawPendingConfig);
    } catch (error) {
        window.sessionStorage.removeItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
        return null;
    }
};

const clearPendingProductConfig = () => {
    if (typeof window === "undefined") return;
    window.sessionStorage.removeItem(PENDING_PRODUCT_CONFIG_STORAGE_KEY);
};

const getDimensionValidationError = (rawHeight, rawWidth) => {
    const h = parseFloat(rawHeight);
    const w = parseFloat(rawWidth);

    if (isNaN(h) || isNaN(w)) {
        return 'Debe ingresar dimensiones válidas';
    }

    if (h < 30 || w < 30 || h > 250 || w > 250 || h + w > 400) {
        return 'Dimensiones fuera de rango (30–250 cm, suma ≤ 400 cm)';
    }

    return '';
};

const buildPriceQuote = ({ rawHeight, rawWidth, product }) => {
    const dimensionError = getDimensionValidationError(rawHeight, rawWidth);
    if (dimensionError) {
        return { error: dimensionError };
    }

    const h = parseFloat(rawHeight);
    const w = parseFloat(rawWidth);

    const base = product.precio_rebajado || product.precio;
    const area = (h * w) / 10000;
    const basePrice = 80;
    let price = area * base;
    const multiplier =
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

    return {
        h,
        w,
        area,
        formattedPrice: price.toFixed(2)
    };
};

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
    const [mounting, setMounting] = useState(DEFAULT_MOUNTING);
    const [color, setColor] = useState(DEFAULT_COLOR);
    const [calculatedPrice, setCalculatedPrice] = useState(null);
    const [calculatedArea, setCalculatedArea] = useState(null);
    const [calcError, setCalcError] = useState('');
    const [priceNeedsRecalculation, setPriceNeedsRecalculation] = useState(false);
    const [showRestoredPriceReady, setShowRestoredPriceReady] = useState(false);
    const [previewColor, setPreviewColor] = useState(null);
    const priceFeedbackRef = useRef(null);
    const COLOR_MAP = {
        satinado_blanco: { hex: "#ffffff", type: "satinado" },
        satinado_negro: { hex: "#000000", type: "satinado" },
        satinado_gris: { hex: "#494949", type: "satinado" },
        satinado_verde: { hex: "#183022", type: "satinado" },

        forja_negro: { hex: "#1a1a1a", type: "forja" },
        forja_gris: { hex: "#7a7d80", type: "forja" },
        forja_marron: { hex: "#5a3a2a", type: "forja" },
        forja_azul: { hex: "#2e4579", type: "forja" },
        forja_verde: { hex: "#506c39", type: "forja" },
        forja_dorado: { hex: "#947d30", type: "forja" }
    };

    // Estados “overlay”
    const [showHint, setShowHint] = useState(false);
    const [altoEl, setAltoEl] = useState(null);

    const closeHintIfVisible = () => {
        if (showHint) {
            setShowHint(false);
        }
    };

    const toggleHint = () => {
        setShowHint((prevShowHint) => !prevShowHint);
    };

    const applyPriceQuote = (quote) => {
        if (!quote || quote.error) {
            setCalcError(quote?.error || 'No se pudo calcular el precio');
            setCalculatedArea(null);
            setCalculatedPrice(null);
            return null;
        }

        setCalcError('');
        setCalculatedArea(quote.area);
        setCalculatedPrice(quote.formattedPrice);
        return quote;
    };

    const savePendingProductConfig = () => {
        if (typeof window === "undefined") return;

        const pendingConfig = {
            category_slug,
            product_slug,
            height,
            width,
            mounting,
            color,
            saved_at: Date.now(),
            return_to: `/${category_slug}/${product_slug}`
        };

        window.sessionStorage.setItem(
            PENDING_PRODUCT_CONFIG_STORAGE_KEY,
            JSON.stringify(pendingConfig)
        );
    };

    const clearRestoredPriceReady = () => {
        if (showRestoredPriceReady) {
            setShowRestoredPriceReady(false);
        }
    };

    const invalidateCalculatedPrice = () => {
        clearRestoredPriceReady();

        if (calculatedPrice || calculatedArea) {
            setCalculatedPrice(null);
            setCalculatedArea(null);
            setPriceNeedsRecalculation(true);
        }
    };



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

                        // 🟢 PRIORIDAD: titulo_seo → fallback automático
                        title: productData.titulo_seo
                            ? productData.titulo_seo
                            : `${productData.nombre} | ${productData.categoria_nombre}`,

                        // 🟢 Descripción: descripcion_seo → descripcion → fallback truncado
                        description: productData.descripcion_seo
                            ? productData.descripcion_seo
                            : (productData.descripcion || "").substring(0, 160),

                        og_image: productData.imagen,

                        canonical: `${window.location.origin}/${category_slug}/${product_slug}`,

                        json_ld: null
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
        setShowRestoredPriceReady(false);
        setPriceNeedsRecalculation(false);
        const quote = applyPriceQuote(
            buildPriceQuote({
                rawHeight: height,
                rawWidth: width,
                product
            })
        );

        if (!quote) {
            return;
        }

        if (window.dataLayer) {
            window.dataLayer.push({
                event: "calcular_precio",
                product_name: product?.nombre,
                product_slug: product?.slug,
                height_cm: quote.h,
                width_cm: quote.w,
                area_m2: quote.area,
                final_price: quote.formattedPrice
            });
        }
    };

    const handleAddToCart = async () => {
        if (!calculatedPrice) {
            setNotification('Primero calcula el precio con tus medidas.');
            return;
        }

        if (!store.isLoged) {
            savePendingProductConfig();
            navigate("/login");
            return;
        }

        if (mounting.includes("garras")) {
            setNotification("Esta opción no está disponible temporalmente");
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
        setMounting(DEFAULT_MOUNTING);
        setColor(DEFAULT_COLOR);
        setCalculatedPrice(null);
        setCalculatedArea(null);
        setPriceNeedsRecalculation(false);
        setShowRestoredPriceReady(false);
    };

    const determinePlacement = () =>
        window.innerWidth > 768 ? 'right' : 'top';

    useEffect(() => {
        if (!calculatedPrice || !priceFeedbackRef.current) return;

        window.requestAnimationFrame(() => {
            priceFeedbackRef.current?.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest'
            });
        });
    }, [calculatedPrice]);

    useEffect(() => {
        if (!product) return;

        const pendingConfig = readPendingProductConfig();
        if (!pendingConfig) return;

        const savedAt = Number(pendingConfig.saved_at);
        const isFresh = Number.isFinite(savedAt) && Date.now() - savedAt <= PENDING_PRODUCT_CONFIG_MAX_AGE_MS;

        if (!isFresh) {
            clearPendingProductConfig();
            return;
        }

        if (
            pendingConfig.category_slug !== category_slug ||
            pendingConfig.product_slug !== product_slug
        ) {
            clearPendingProductConfig();
            return;
        }

        const restoredHeight = pendingConfig.height ?? '';
        const restoredWidth = pendingConfig.width ?? '';
        const restoredMounting = pendingConfig.mounting || DEFAULT_MOUNTING;
        const restoredColor = COLOR_MAP[pendingConfig.color] ? pendingConfig.color : DEFAULT_COLOR;

        setHeight(restoredHeight);
        setWidth(restoredWidth);
        setMounting(restoredMounting);
        setColor(restoredColor);

        if (restoredHeight && restoredWidth) {
            applyPriceQuote(
                buildPriceQuote({
                    rawHeight: restoredHeight,
                    rawWidth: restoredWidth,
                    product
                })
            );
            setPriceNeedsRecalculation(false);
            setShowRestoredPriceReady(true);
        }

        clearPendingProductConfig();
        setNotification('Hemos restaurado tu configuración.');
    }, [product, category_slug, product_slug]);



    if (loading) {
        return (
            <Container style={{ marginTop: '100px', marginBottom: '100px' }}>
                <Row>
                    <Col md={6}>
                        <Skeleton height={400} borderRadius={10} />
                        <div className="mt-3">
                            <Skeleton height={20} width={`80%`} />
                            <Skeleton height={20} width={`60%`} className="mt-2" />
                        </div>
                    </Col>
                    <Col md={6}>
                        <Skeleton height={30} width={250} />
                        <Skeleton height={20} width={180} className="mt-2" />
                        <Skeleton height={20} width={220} className="mt-2" />
                        <div className="mt-4">
                            <Skeleton height={40} width={200} />
                            <Skeleton height={40} width={200} className="mt-2" />
                            <Skeleton height={40} width={200} className="mt-2" />
                        </div>
                        <div className="mt-5 d-flex gap-3">
                            <Skeleton circle height={36} width={36} />
                            <Skeleton height={36} width={150} />
                        </div>
                    </Col>
                </Row>
            </Container>
        );
    }

    const handleShare = async () => {
        const url = window.location.href;
        try {
            if (navigator.share) {
                await navigator.share({
                    title: document.title,
                    url
                });
            } else {
                await navigator.clipboard.writeText(url);
                alert("Enlace copiado al portapapeles");
            }
        } catch (err) {
            console.error("Error al compartir:", err);
        }
    };


    const categoryName = product?.categoria_nombre || category_slug.replaceAll("-", " ");

    const allImages = [
        { image_url: product.imagen },
        ...(product.images || []).filter(img => img.image_url !== product.imagen)
    ];

    const activeColor = previewColor || {
        name: color,
        ...COLOR_MAP[color]
    };

    const dimensionsReadyForQuote = !getDimensionValidationError(height, width);
    const pricePromptMessage = priceNeedsRecalculation
        ? (
            dimensionsReadyForQuote
                ? 'Has cambiado la configuración. Vuelve a calcular el precio.'
                : 'Has cambiado la configuración. Revisa las medidas y vuelve a calcular el precio.'
        )
        : (
            dimensionsReadyForQuote
                ? 'Medidas listas. Calcula el precio para continuar.'
                : 'Introduce tus medidas y calcula el precio para ver el coste final de tu reja a medida.'
        );
    const pricePromptClassName = `product-price-prompt mt-3${priceNeedsRecalculation ? ' product-price-prompt--warning' : dimensionsReadyForQuote ? ' product-price-prompt--ready' : ''}`;

    return (
        <div className="product-page-wrapper">
            <Container style={{ marginTop: '120px', marginBottom: '0' }}>
                <Breadcrumb
                    items={[
                        { label: "Inicio", to: "/" },
                        { label: "Catálogo" },
                        { label: categoryName, to: `/${category_slug}` },
                        { label: product?.nombre || product_slug.replaceAll("-", " ") }
                    ]}
                />
                {seoData && (
                    <Helmet htmlAttributes={{ lang: seoData.lang || "es" }}>
                        {/* TITLE */}
                        <title>
                            {seoData.title ||
                                product.titulo_seo ||
                                `${product.nombre} | ${product.categoria_nombre}`}
                        </title>

                        {/* DESCRIPTION */}
                        <meta
                            name="description"
                            content={
                                seoData.description ||
                                product.descripcion_seo ||
                                product.descripcion?.substring(0, 160)
                            }
                        />

                        {/* KEYWORDS */}
                        <meta
                            name="keywords"
                            content={
                                seoData.keywords ||
                                `${product.nombre}, ${product.categoria_nombre}, rejas para ventanas`
                            }
                        />

                        {/* Robots / Canonical */}
                        <meta name="robots" content={seoData.robots || "index, follow"} />
                        <meta name="theme-color" content={seoData.theme_color || "#ff324d"} />
                        <link rel="canonical" href={seoData.canonical} />

                        {/* OPEN GRAPH */}
                        <meta property="og:type" content={seoData.og_type || "product"} />
                        <meta property="og:title" content={seoData.og_title || seoData.title} />
                        <meta
                            property="og:description"
                            content={
                                seoData.og_description ||
                                seoData.description ||
                                product.descripcion_seo
                            }
                        />
                        <meta property="og:image" content={seoData.og_image} />
                        <meta property="og:image:width" content={seoData.og_image_width || "1200"} />
                        <meta property="og:image:height" content={seoData.og_image_height || "630"} />
                        <meta
                            property="og:image:alt"
                            content={seoData.og_image_alt || seoData.title}
                        />
                        <meta property="og:image:type" content={seoData.og_image_type || "image/jpeg"} />
                        <meta property="og:url" content={seoData.og_url} />
                        <meta property="og:site_name" content={seoData.og_site_name || "Metal Wolft"} />
                        <meta property="og:locale" content={seoData.og_locale || "es_ES"} />
                        {seoData.og_updated_time && (
                            <meta property="og:updated_time" content={seoData.og_updated_time} />
                        )}

                        {/* TWITTER */}
                        <meta
                            name="twitter:card"
                            content={seoData.twitter_card_type || "summary_large_image"}
                        />
                        <meta name="twitter:site" content={seoData.twitter_site} />
                        <meta name="twitter:creator" content={seoData.twitter_creator} />
                        <meta
                            name="twitter:title"
                            content={seoData.twitter_title || seoData.title}
                        />
                        <meta
                            name="twitter:description"
                            content={
                                seoData.twitter_description ||
                                seoData.description ||
                                product.descripcion_seo
                            }
                        />
                        <meta name="twitter:image" content={seoData.twitter_image} />
                        <meta
                            name="twitter:image:alt"
                            content={seoData.twitter_image_alt || seoData.title}
                        />

                        {/* JSON-LD */}
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
                                        width="540"
                                        height="600"
                                        className="d-block img-fluid product-detail-main-image"
                                        style={{ borderRadius: '5px', objectFit: 'cover' }}
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
                                    width="72"
                                    height="80"
                                    className={`img-thumbnail mx-1 ${currentIndex === i ? 'active-thumbnail' : ''}`}
                                    style={{ cursor: 'pointer', objectFit: 'cover' }}
                                    onClick={() => setCurrentIndex(i)}
                                />
                            ))}
                        </div>
                    </Col>

                    {/* Columna de detalles: 12 en xs, 5 en lg, con margen top solo en xs */}
                    <Col xs={12} lg={5} className="mt-4 mt-lg-0">
                        <div className="pr_detail">
                            <h1>{product.h1_seo || product.nombre}</h1>
                            <hr />
                            <div className="product-price" style={{ fontSize: '1.1rem', fontWeight: '500', marginBottom: '1rem' }}>
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
                            </div>
                            {/* Descripción SEO (texto comercial corto) */}
                            {product.descripcion_seo && (
                                <p style={{ marginBottom: "1rem" }}>
                                    {product.descripcion_seo}
                                </p>
                            )}

                            {/* Descripción técnica (siempre visible debajo) */}
                            {product.descripcion && (
                                <p>
                                    Especificaciones: <br />{product.descripcion}
                                </p>
                            )}

                            <div className="product-purchase-guide" aria-label="Cómo comprar esta reja">
                                <p className="product-purchase-guide-label">Cómo comprar</p>
                                <div className="product-purchase-steps">
                                    <span className="product-purchase-step">
                                        <span className="product-step-number">1</span>
                                        Introduce medidas
                                    </span>
                                    <span className="product-purchase-step">
                                        <span className="product-step-number">2</span>
                                        Calcula el precio
                                    </span>
                                    <span className="product-purchase-step">
                                        <span className="product-step-number">3</span>
                                        Añade al carrito
                                    </span>
                                </div>
                                <div className="product-trust-badges" aria-label="Señales de confianza">
                                    <span className="product-trust-badge">IVA incluido</span>
                                    <span className="product-trust-badge">Fabricación a medida</span>
                                    <span className="product-trust-badge">Ayuda por WhatsApp si la necesitas</span>
                                </div>
                            </div>

                            <Form>
                                {/* Dimensiones */}
                                <Row>
                                    <Col>
                                        <Form.Group className="position-relative">
                                            <div className="product-input-label">
                                                <Form.Label className="mb-0">Alto (cm)</Form.Label>
                                                <button
                                                    type="button"
                                                    className="product-inline-help-button"
                                                    onClick={toggleHint}
                                                    aria-label={showHint ? "Ocultar ayuda sobre las medidas" : "Mostrar ayuda sobre las medidas"}
                                                    aria-expanded={showHint}
                                                >
                                                    <i className="fa-solid fa-circle-info" />
                                                </button>
                                            </div>
                                            <Form.Control
                                                type="number"
                                                value={height}
                                                ref={setAltoEl}
                                                onFocus={closeHintIfVisible}
                                                onChange={(e) => {
                                                    closeHintIfVisible();
                                                    invalidateCalculatedPrice();
                                                    setHeight(e.target.value.replace(',', '.'));
                                                }}
                                                placeholder="Ej.: 120.1"
                                                min="0"
                                                step="0.1"
                                                inputMode="decimal"
                                                onWheel={(e) => e.currentTarget.blur()}
                                            />

                                            <Overlay
                                                target={altoEl}
                                                show={showHint && !!altoEl}
                                                placement="bottom"
                                                container={typeof document !== 'undefined' ? document.body : undefined}
                                                popperConfig={{
                                                    strategy: "fixed",
                                                    modifiers: [
                                                        { name: "offset", options: { offset: [0, 8] } },
                                                        { name: "preventOverflow", options: { boundary: "viewport" } },
                                                        { name: "computeStyles", options: { adaptive: false } },
                                                    ],
                                                }}
                                            >
                                                {(props) => (
                                                    <Popover {...props} id="popover-alto" className="popover-hint">
                                                        <Popover.Body style={{ position: "relative", paddingRight: "2rem" }}>
                                                            <button
                                                                type="button"
                                                                onClick={() => setShowHint(false)}
                                                                aria-label="Cerrar"
                                                                style={{ position: "absolute", top: 6, right: 8, border: "none", background: "transparent", cursor: "pointer" }}
                                                            >
                                                                ✕
                                                            </button>
                                                            Introduce <b>las medidas</b> para calcular <strong>el precio</strong>.
                                                        </Popover.Body>
                                                    </Popover>
                                                )}
                                            </Overlay>
                                        </Form.Group>
                                    </Col>
                                    <Col>
                                        <Form.Group>
                                            <Form.Label>Ancho (cm)</Form.Label>
                                            <Form.Control
                                                type="number"
                                                value={width}
                                                onFocus={closeHintIfVisible}
                                                onChange={(e) => {
                                                    closeHintIfVisible();
                                                    invalidateCalculatedPrice();
                                                    setWidth(e.target.value.replace(',', '.'));
                                                }}
                                                min="0"
                                                step="0.1"
                                                inputMode="decimal"
                                                onWheel={(e) => e.currentTarget.blur()}
                                            />
                                        </Form.Group>
                                    </Col>
                                </Row>
                                {calcError && <p className="text-danger mt-2">{calcError}</p>}
                                <p className="product-form-helper">
                                    Introduce alto y ancho en centímetros para calcular el precio exacto de tu reja.
                                </p>

                                {/* Instalación & Color */}
                                <Row className="mt-3">
                                    <Col>
                                        <Form.Group>
                                            <OverlayTrigger
                                                trigger={['hover', 'focus']}
                                                placement={determinePlacement()}
                                                container={typeof document !== 'undefined' ? document.body : undefined}
                                                popperConfig={{
                                                    strategy: "fixed",
                                                    modifiers: [
                                                        { name: "offset", options: { offset: [0, 12] } },
                                                        { name: "flip", options: { fallbackPlacements: ["left", "top", "bottom"] } },
                                                        { name: "preventOverflow", options: { boundary: "viewport", padding: 16 } },
                                                        { name: "computeStyles", options: { adaptive: false } }
                                                    ]
                                                }}
                                                overlay={
                                                    <Popover id="popover-install" className="installation-popover">
                                                        <Popover.Header as="h3">Instalación</Popover.Header>
                                                        <Popover.Body>
                                                            <p><b>Sin obra:</b> con pletinas.</p>
                                                            <img
                                                                src="https://res.cloudinary.com/dewanllxn/image/upload/v1738176285/agujeros-en-pletinas_tlosu0.png"
                                                                alt="pletinas"
                                                                width="1140"
                                                                height="536"
                                                                className="installation-popover-image"
                                                            />
                                                            <p><b>Sin obra:</b> con agujeros interiores.</p>
                                                            <img
                                                                src="https://res.cloudinary.com/dewanllxn/image/upload/v1738176285/agujeros-interiores_xa0onj.png"
                                                                alt="interiores"
                                                                width="1140"
                                                                height="536"
                                                                className="installation-popover-image"
                                                            />
                                                            <p><b>Sin obra:</b> con agujeros frontales.</p>
                                                            <img
                                                                src="https://res.cloudinary.com/dewanllxn/image/upload/v1738176286/agujeros-frontales_low9pi.png"
                                                                alt="frontales"
                                                                width="1140"
                                                                height="536"
                                                                className="installation-popover-image"
                                                            />
                                                            <p><b>Con obra:</b> con garras metálicas.</p>
                                                            <img
                                                                src="https://res.cloudinary.com/dewanllxn/image/upload/v1734888241/rejas-para-ventanas-sin-obra_wukdzi.png"
                                                                alt="garras"
                                                                width="1140"
                                                                height="536"
                                                                className="installation-popover-image"
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
                                                onChange={e => {
                                                    invalidateCalculatedPrice();
                                                    setMounting(e.target.value);
                                                }}
                                            >
                                                <option>Sin obra: con agujeros interiores</option>
                                                <option>Sin obra: con agujeros frontales</option>
                                                <option>Sin obra: con pletinas</option>
                                                <option disabled>
                                                    Con obra: con garras metálicas (no disponible)
                                                </option>
                                            </Form.Select>
                                            {activeColor && (
                                                <div
                                                    style={{
                                                        marginTop: "10px",
                                                        height: "80px",
                                                        borderRadius: "8px",
                                                        border: "1px solid #ccc",
                                                        background: activeColor.name.includes("forja")
                                                            ? `linear-gradient(135deg, ${activeColor.hex}, #111),url('https://www.transparenttextures.com/patterns/asfalt-light.png')`
                                                            : activeColor.hex,
                                                        backgroundBlendMode: activeColor.name.includes("forja")
                                                            ? "overlay"
                                                            : "normal",
                                                        transition: "all 0.2s ease"
                                                    }}
                                                />
                                            )}
                                            <div className="mt-1" style={{ fontSize: "0.9rem", color: "#555" }}>
                                                Seleccionado: <strong>
                                                    {{
                                                        satinado_blanco: "Blanco liso",
                                                        satinado_negro: "Negro liso",
                                                        satinado_gris: "Gris medio liso",
                                                        satinado_verde: "Verde carruajes liso",

                                                        forja_negro: "Negro forja",
                                                        forja_gris: "Gris acero forja",
                                                        forja_marron: "Marrón castaño forja",
                                                        forja_azul: "Azul forja",
                                                        forja_verde: "Verde bronce forja",
                                                        forja_dorado: "Dorado forja"
                                                    }[color]}
                                                </strong>
                                            </div>
                                        </Form.Group>
                                    </Col>
                                    <Col>
                                        <Form.Group>
                                            <Form.Label>Color</Form.Label>

                                            {/* SATINADO */}
                                            <div style={{ fontSize: "0.85rem", marginBottom: "4px", fontWeight: "500" }}>
                                                Satinado liso
                                            </div>

                                            <div className="color-swatch-container">
                                                {[
                                                    { name: "satinado_blanco", label: "Blanco liso", hex: "#ffffff" },
                                                    { name: "satinado_negro", label: "Negro liso", hex: "#000000" },
                                                    { name: "satinado_gris", label: "Gris medio liso", hex: "#494949" },
                                                    { name: "satinado_verde", label: "Verde carruajes liso", hex: "#183022" }
                                                ].map((c) => (
                                                    <div
                                                        key={c.name}
                                                        className={`color-swatch ${color === c.name ? "selected" : ""}`}
                                                        onMouseEnter={() => setPreviewColor(c)}
                                                        onMouseLeave={() => setPreviewColor(null)}
                                                        onTouchStart={() => setPreviewColor(c)}
                                                        style={{ backgroundColor: c.hex }}
                                                        onClick={() => {
                                                            invalidateCalculatedPrice();
                                                            setColor(c.name);
                                                        }}
                                                        title={c.label}
                                                    ></div>
                                                ))}
                                            </div>

                                            {/* EFECTO FORJA */}
                                            <div style={{ fontSize: "0.85rem", marginTop: "10px", marginBottom: "4px", fontWeight: "500" }}>
                                                Efecto forja
                                            </div>

                                            <div className="color-swatch-container">
                                                {[
                                                    { name: "forja_negro", label: "Negro forja", hex: "#1a1a1a" },
                                                    { name: "forja_gris", label: "Gris acero forja", hex: "#7a7d80" },
                                                    { name: "forja_marron", label: "Marrón castaño forja", hex: "#5a3a2a" },
                                                    { name: "forja_azul", label: "Azul forja", hex: "#2e4579" },
                                                    { name: "forja_verde", label: "Verde bronce forja", hex: "#506c39" },
                                                    { name: "forja_dorado", label: "Dorado forja", hex: "#947d30" }
                                                ].map((c) => (
                                                    <div
                                                        key={c.name}
                                                        className={`color-swatch ${color === c.name ? "selected" : ""}`}
                                                        onMouseEnter={() => setPreviewColor(c)}
                                                        onMouseLeave={() => setPreviewColor(null)}
                                                        onTouchStart={() => setPreviewColor(c)}
                                                        style={{
                                                            backgroundColor: c.hex,
                                                            backgroundImage: "url('https://www.transparenttextures.com/patterns/dark-matter.png')",
                                                            backgroundBlendMode: 'multiply'
                                                        }}
                                                        onClick={() => {
                                                            invalidateCalculatedPrice();
                                                            setColor(c.name);
                                                        }}
                                                        title={c.label}
                                                    ></div>
                                                ))}
                                            </div>
                                        </Form.Group>
                                    </Col>
                                </Row>

                                {/* Botón Calcular */}
                                <div className="product-calculate-section">
                                    <Button className="btn-style-background-color product-calculate-button mt-3" onClick={handleCalculatePrice}>
                                        <i className="fa-solid fa-calculator me-2" /> Calcular precio ahora
                                    </Button>

                                    {/* Resultado de cálculo */}
                                    {calculatedPrice ? (
                                        <div className="product-price-result mt-3" ref={priceFeedbackRef}>
                                            <span className="product-price-result-label">Precio calculado para tus medidas</span>
                                            {showRestoredPriceReady && (
                                                <p className="product-restored-price-ready mb-2">
                                                    <i className="fa-solid fa-circle-check me-2" />
                                                    Precio calculado con tus medidas
                                                </p>
                                            )}
                                            <h5 className="product-price-result-value">{calculatedPrice} €</h5>
                                            <p className="mb-0">IVA incluido para esta configuración.</p>
                                            {calculatedArea < 1 && <p className="text-warning mb-0 mt-2">Área &lt; 1 m² incrementa coste.</p>}
                                        </div>
                                    ) : (
                                        <div className={pricePromptClassName} ref={priceFeedbackRef}>
                                            <p className="mb-0">{pricePromptMessage}</p>
                                        </div>
                                    )}
                                </div>
                                <div className="product-delivery-estimate">
                                    <DeliveryEstimate />
                                </div>
                                <div className="product-cta-guidance">
                                    <p>
                                        {calculatedPrice
                                            ? "Ya tienes el precio calculado. Revisa la configuración y añádela al carrito."
                                            : "Primero introduce tus medidas y calcula el precio para preparar la compra."}
                                    </p>
                                    {!store.isLoged && (
                                        <p>
                                            Para añadir esta reja al carrito necesitas <Link to="/login">iniciar sesión</Link>.
                                        </p>
                                    )}
                                    <p>
                                        Si tienes dudas antes de comprar, escríbenos por <a href="https://wa.me/34634112604" target="_blank" rel="noopener noreferrer">WhatsApp</a> o usa nuestro <Link to="/contact">formulario de contacto</Link>.
                                    </p>
                                </div>
                                <hr />
                                <div className="product-action-row d-flex flex-column flex-sm-row justify-content-between align-items-stretch align-items-sm-center mt-4 gap-3">
                                    <div className="product-secondary-actions d-flex justify-content-end align-items-center gap-3">
                                        <Share2
                                            onClick={handleShare}
                                            size={24}
                                            color="#ff324d"
                                            style={{ cursor: 'pointer' }}
                                        />
                                        <i
                                            className={`fa-regular fa-heart ${actions.isFavorite(product) ? 'fa-solid' : ''}`}
                                            onClick={handleFavorite}
                                            style={{ cursor: 'pointer', color: '#ff324d', fontSize: '1.5rem', marginRight: '8px' }}
                                        />
                                    </div>

                                    <div className="product-primary-action">
                                        {calculatedPrice && (
                                            <p className={`product-cart-ready-note${showRestoredPriceReady ? ' product-cart-ready-note--restored' : ''}`}>
                                                {showRestoredPriceReady ? 'Ya puedes añadir tu reja restaurada al carrito.' : 'Ya puedes añadir tu reja al carrito.'}
                                            </p>
                                        )}
                                        <Button className="btn-style-background-color product-add-to-cart-button" onClick={handleAddToCart}>
                                            <ShoppingCart size={18} className="me-2" />
                                            Añadir al carrito
                                        </Button>
                                    </div>
                                </div>
                            </Form>
                        </div>
                    </Col>
                    <div className="custom-accordion product-detail-accordion my-5">
                        {/* Acordeón 4 */}
                        <div className="accordion-item">
                            <input type="checkbox" id="accordion-4" />
                            <label htmlFor="accordion-4" className="accordion-header product-accordion-header with-arrow d-flex justify-content-between align-items-center">
                                <span className="product-accordion-heading">
                                    <i className="fa-solid fa-toolbox me-2"></i>
                                    Herramientas Recomendadas
                                </span>
                                <i className="fa-solid fa-chevron-down arrow-icon"></i>
                            </label>
                            <h2 className="visually-hidden">Herramientas recomendadas</h2>
                            <div className="accordion-content product-accordion-body">
                                <div className="container product-tools-wrap mt-5">
                                    <div className="row product-tools-grid text-center d-flex flex-column flex-lg-row justify-content-center align-items-stretch gap-3">

                                        {/* Herramienta 1 */}
                                        <div className="col-12 col-lg-3 mb-4 product-tool-card-column">
                                            <div className="product-tool-card">
                                                <img
                                                    src="https://m.media-amazon.com/images/I/710L8PQsrkL._AC_SX569_.jpg"
                                                    alt="Taladro Bosch Professional"
                                                    className="img-fluid rounded product-tool-image"
                                                />
                                                <h6 className="product-tool-title mt-2">Einhell Taladro Percutor sin cable</h6>
                                                <p className="product-tool-copy">Compacto y potente para perforar materiales como piedra o ladrillo.</p>
                                                <a
                                                    href="https://amzn.to/3TWBpNO"
                                                    target="_blank"
                                                    rel="sponsored noopener noreferrer"
                                                    className="product-tool-cta btn btn-sm btn-warning mt-2"
                                                >
                                                    Ver en Amazon
                                                </a>
                                            </div>
                                        </div>

                                        {/* Herramienta 2 */}
                                        <div className="col-12 col-lg-3 mb-4 product-tool-card-column">
                                            <div className="product-tool-card">
                                                <img
                                                src="https://m.media-amazon.com/images/I/31Izs0l3NcS._AC_SY879_.jpg"
                                                alt="Brocas para pared"
                                                className="img-fluid rounded product-tool-image"
                                            />
                                            <h6 className="mt-2">Brocas para mampostería de 12</h6>
                                            <p>Brocas de alto rendimiento resistente a la percusión.</p>
                                            <a
                                                href="https://amzn.to/46l6bYb"
                                                target="_blank"
                                                rel="sponsored noopener noreferrer"
                                                className="product-tool-cta btn btn-sm btn-warning mt-2"
                                            >
                                                Ver en Amazon
                                            </a>
                                            </div>
                                        </div>

                                        {/* Herramienta 3 */}
                                        <div className="col-12 col-lg-3 mb-4 product-tool-card-column">
                                            <div className="product-tool-card">
                                                <img
                                                src="https://m.media-amazon.com/images/I/71-iVl4GBSL._AC_SX569_.jpg"
                                                alt="Juego de llaves Torx"
                                                className="img-fluid rounded product-tool-image"
                                            />
                                            <h6 className="mt-2"> Juego de Llave Torx Profesional T10</h6>
                                            <p>Ideal para fijaciones con tornillos de seguridad Torx.</p>
                                            <a
                                                href="https://amzn.to/44nC6Vq"
                                                target="_blank"
                                                rel="sponsored noopener noreferrer"
                                                className="product-tool-cta btn btn-sm btn-warning mt-2"
                                            >
                                                Ver en Amazon
                                            </a>
                                            </div>
                                        </div>

                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Acordeón 1 */}
                        <div className="accordion-item">
                            <input type="checkbox" id="accordion-1" />
                            <label htmlFor="accordion-1" className="accordion-header product-accordion-header with-arrow d-flex justify-content-between align-items-center">
                                <span className="product-accordion-heading">
                                    <i className="fa-solid fa-screwdriver-wrench me-2"></i>
                                    Instalación y consejos prácticos
                                </span>
                                <i className="fa-solid fa-chevron-down arrow-icon"></i>
                            </label>
                            <h2 className="visually-hidden">Instalación y consejos prácticos</h2>
                            <div className="accordion-content product-accordion-body">
                                <h3 className="h3-categories">¿Cómo elegir la reja perfecta para tu ventana?</h3>
                                <p>En cuanto a estética y estilo es cuestión de <b>gustos</b> porque todas cumplen con la premisa fundamental de la <strong>seguridad</strong>.</p>
                                <p>Para elegir la reja perfecta hay que fijarse en que la instalación sea lo más favorable para cada caso.</p>
                                <p>Se recomienda <b>con garras</b> en el caso de que la ubicación se encuentre <b>en fase de obra y esté en bruto la fachada</b>, simplemente porque coge <b>más fuerza el anclaje</b>. Para todos los demás casos, el <b>anclaje con tornillos especiales</b> es suficiente, siendo más <b>limpio y económico</b>.</p>

                                <h3 className="h3-categories mt-4">¿Cómo Medir el Hueco para Rejas de Ventanas?</h3>
                                <ul>
                                    <li><strong>Mide el ancho:</strong> Mide de un lado al otro del marco de la ventana, asegurándote de tomar la medida en varios puntos (arriba, en el centro y abajo). La <b>medida más pequeña</b> es la que debes tomar. Resta medio centímetro para asegurar el encaje.</li>
                                    <li><strong>Mide la altura:</strong> Desde la base hasta la parte superior del marco. Resta 2-3 cm para permitir limpieza del vierteaguas y evitar acumulación de suciedad.</li>
                                </ul>
                                <p>Si tienes dudas, <Link to="/contact" className="link-categories">consúltanos</Link> para evitar errores.</p>
                                <p>Consulta nuestra <Link to="/medir-hueco-rejas-para-ventanas" className="link-categories">guía para medir el hueco</Link> en el blog.</p>
                                <p>Tomar medidas precisas es esencial para garantizar que las rejas se ajusten correctamente.</p>

                                <h3 className="h3-categories mt-4">¿Cómo instalar rejas para ventanas?</h3>
                                <p>La <strong>instalación de rejas para ventanas</strong> no solo garantiza la <strong>seguridad</strong> de tu hogar, sino que también puede mejorar su estética.</p>
                                <p>Dependiendo del <b>tipo de instalación</b> (con obra o sin obra), se requerirán herramientas diferentes.</p>
                                <p>La instalación con obra suele realizarla un albañil. La sin obra es más accesible y cualquier persona con pocas herramientas puede hacerla.</p>
                                <p>Consulta nuestra <Link to="/instalation-rejas-para-ventanas" className="link-categories">guía de instalación sin obra</Link> con todos los pasos.</p>
                            </div>
                        </div>

                        {/* Acordeón 2 */}
                        <div className="accordion-item">
                            <input type="checkbox" id="accordion-2" />
                            <label htmlFor="accordion-2" className="accordion-header product-accordion-header with-arrow d-flex justify-content-between align-items-center">
                                <span className="product-accordion-heading">
                                    <i className="fa-regular fa-circle-question me-2"></i>
                                    Preguntas frecuentes
                                </span>
                                <i className="fa-solid fa-chevron-down arrow-icon"></i>
                            </label>
                            <h2 className="visually-hidden">Preguntas frecuentes</h2>
                            <div className="accordion-content product-accordion-body">
                                <ul>
                                    <li><b>¿Los precios incluyen IVA?</b> Sí, todos nuestros precios incluyen IVA.</li>
                                    <li>
                                        <b>¿Cuál es el tiempo de fabricación y entrega?</b> Nuestro tiempo estimado de fabricación y entrega es de <b>20 días hábiles</b>. Sin embargo, este plazo puede variar dependiendo de nuestra carga de trabajo.
                                        En caso de que haya un aumento en los tiempos, te lo notificaremos con anticipación para que estés informado.
                                        Puedes consultar más detalles en nuestra sección de
                                        <Link to="/plazos-entrega-rejas-a-medida" className="product-accordion-inline-link">
                                            Plazos de Entrega.
                                        </Link>
                                    </li>
                                    <li>
                                        <b>¿Qué sucede después de realizar mi compra?</b> Tras completar tu compra, recibirás un correo de confirmación con todos los detalles. Además, nos pondremos en contacto contigo para orientarte en la instalación y ofrecerte asistencia personalizada, asegurándonos de que tengas una experiencia satisfactoria con tu compra.
                                    </li>
                                    <li>
                                        <b>¿Cómo puedo ponerme en contacto?</b> Puedes hacerlo a través de nuestro <Link to="/contact">formulario de contacto</Link>, enviándonos un mensaje por <a href="https://wa.me/34634112604" target="_blank" rel="noopener noreferrer">WhatsApp</a> o llamándonos al <a href="tel:634112604">634112604</a>.
                                    </li>
                                </ul>
                            </div>
                        </div>

                        {/* Acordeón 3 */}
                        <div className="accordion-item">
                            <input type="checkbox" id="accordion-3" />
                            <label htmlFor="accordion-3" className="accordion-header product-accordion-header with-arrow d-flex justify-content-between align-items-center">
                                <span className="product-accordion-heading">
                                    <i className="fa-solid fa-th-large me-2"></i>
                                    Tipos de rejas para ventanas
                                </span>
                                <i className="fa-solid fa-chevron-down arrow-icon"></i>
                            </label>
                            <h2 className="visually-hidden">Tipos de rejas para ventanas</h2>
                            <div className="accordion-content product-accordion-body">
                                <h4 className="h3-categories">Rejas para ventanas modernas</h4>
                                <p>Las <strong>rejas para ventanas modernas</strong> han experimentado una transformación en su estilo y materiales, siguiendo líneas más <strong>sencillas</strong> siendo igual de <strong>bonitas</strong>, ofreciendo un equilibrio perfecto entre <b>seguridad y estética</b>.</p>
                                <p>Aunque el hierro sigue siendo el material predominante, se han incorporado otros materiales, como el acero inoxidable, para satisfacer las necesidades cambiantes de los propietarios.</p>
                                <p>En <Link to="/" className="link-categories">Metal Wolf</Link>, nos enorgullece presentar una selección de <strong>rejas para ventanas modernas</strong> que destacan tanto por su estilo como por su capacidad de brindar <b>protección efectiva</b>.</p>
                                <p>Nuestra filosofía se centra en la creación de <b>diseños</b> que no solo cumplen con su propósito principal, sino que también <b>realzan la estética de su hogar</b>.</p>
                                <p>Si quieres ideas y acabados actuales, puedes consultar nuestra guÃ­a de <Link to="/rejas-para-ventanas-modernas" className="link-categories">rejas para ventanas modernas</Link>.</p>
                                {/* ------------------------------------------ */}
                                <h4 className="h3-categories">Rejas para ventanas sin obra</h4>

                                <p>
                                    <strong>Las rejas para ventanas sin obra</strong> se fijan directamente en el marco de la ventana con
                                    <a href="https://todoanclajes.com/producto/tornillo-inviolable-torx-7-x-30/?gad_source=1&gclid=CjwKCAiAjp-7BhBZEiwAmh9rBX_pS1jYu9WcRXkLhOVUreLYelh3cFK1xX7rnxMQv4ru8xcZ-6YLmRoCnEsQAvD_BwE" className="link-categories" target="_blank" rel="nofollow noopener noreferrer">
                                        tornillos especiales inviolables
                                    </a>, diseñados para ofrecer una sujeción segura y resistente. Al no requerir intervención en los muros, el resultado es más <b>limpio</b>.
                                </p>
                                <p>
                                    La <Link to="/instalation-rejas-para-ventanas" className="link-categories">guía de instalación sin obra</Link> muestra cómo reducir tanto los tiempos como los costes asociados.
                                </p>
                                <p>Este tipo de reja las convierte en una opción ideal para quienes desean mantener intacto el acabado de la fachada.</p>
                                <p>
                                    Si deseas proteger tu hogar sin alterar la fachada, las <strong>rejas sin obra</strong> son la alternativa perfecta. Combina <b>seguridad y funcionalidad</b> y un diseño que se adapta a cualquier estilo de ventana.
                                </p>
                                <p>TambiÃ©n puedes comparar modelos y acabados en nuestra secciÃ³n de <Link to="/rejas-para-ventanas-sin-obra" className="link-categories">rejas para ventanas sin obra</Link>.</p>
                                <div className="container">
                                    <div className="row text-center mt-4 d-flex flex-column flex-lg-row">
                                        {[
                                            {
                                                src: "https://res.cloudinary.com/dewanllxn/image/upload/v1738176285/agujeros-en-pletinas_tlosu0.png",
                                                alt: "Rejas con pletinas",
                                                title: "Con pletinas",
                                                description: "Fijación rápida y segura sin necesidad de obra."
                                            },
                                            {
                                                src: "https://res.cloudinary.com/dewanllxn/image/upload/v1738176285/agujeros-interiores_xa0onj.png",
                                                alt: "Rejas con agujeros interiores",
                                                title: "Con agujeros interiores",
                                                description: "Ideal para marcos con profundidad reducida."
                                            },
                                            {
                                                src: "https://res.cloudinary.com/dewanllxn/image/upload/v1738176286/agujeros-frontales_low9pi.png",
                                                alt: "Rejas con agujeros frontales",
                                                title: "Con agujeros frontales",
                                                description: "Fijación directamente en la parte frontal de la pared."
                                            }
                                        ].map((item, index) => (
                                            <div key={index} className="col-12 col-lg-12 mb-4 text-center">
                                                <img
                                                    src={item.src}
                                                    alt={item.alt}
                                                    className="img-fluid img-large"
                                                    style={{ cursor: 'zoom-in' }}
                                                />
                                                <h6 className="mt-2">{item.title}</h6>
                                                <p>{item.description}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* ------------------------------------------ */}
                                <h4 className="h3-categories">Rejas para ventanas con obra</h4>
                                <p>
                                    Las <strong>rejas para ventanas con obra</strong> son una opción perfecta para proyectos en los que <b>la fachada aún no tiene su acabado final</b>, como durante reformas o construcciones en curso.
                                </p>
                                <p>
                                    A diferencia de las rejas sin obra, estas <b>no utilizan tornillos especiales</b>. En su lugar, están diseñadas con <b>garras de hierro soldadas</b> al lateral del bastidor de la reja.
                                </p>
                                <p>
                                    Estas garras <b>se fijan directamente al muro</b> de la fachada mediante una mezcla de cemento, creando una unión resistente y permanente.
                                </p>

                                <div className="container">
                                    <div className="row text-center mt-4 d-flex flex-column flex-lg-row">
                                        {[
                                            {
                                                src: "https://res.cloudinary.com/dewanllxn/image/upload/v1734888241/rejas-para-ventanas-sin-obra_wukdzi.png",
                                                alt: "Rejas con obra",
                                                title: "Con garras metálicas",
                                                description: "Fijación resistente con cemento en el muro."
                                            }
                                        ].map((item, index) => (
                                            <div key={index} className="col-12 col-lg-12 mb-4 text-center">
                                                <img
                                                    src={item.src}
                                                    alt={item.alt}
                                                    className="img-fluid img-large"
                                                    style={{ cursor: 'zoom-in' }}
                                                />
                                                <p className="fw-bold mt-2">{item.title}</p>
                                                <p>{item.description}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="comparison-table">
                                    <table>
                                        <thead>
                                            <tr>
                                                <th></th>
                                                <th>INSTALACIÓN CON OBRA</th>
                                                <th>INSTALACIÓN SIN OBRA</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <strong>Descripción</strong>
                                                </td>
                                                <td>
                                                    Las rejas se fijan directamente a los muros mediante garras de hierro
                                                    y cemento, proporcionando una unión resistente y permanente.
                                                </td>
                                                <td>
                                                    Las rejas se fijan al marco de la ventana con tornillos especiales,
                                                    evitando la necesidad de modificar los muros.
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    <strong>Ventajas</strong>
                                                </td>
                                                <td>
                                                    <ul>
                                                        <li>Mayor resistencia.</li>
                                                        <li>Adecuado para proyectos en construcción o reforma.</li>
                                                    </ul>
                                                </td>
                                                <td>
                                                    <ul>
                                                        <li>Rápida instalación.</li>
                                                        <li>No afecta la estética de la fachada.</li>
                                                        <li>Más económico.</li>
                                                    </ul>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    <strong>Desventajas</strong>
                                                </td>
                                                <td>
                                                    <ul>
                                                        <li>Requiere albañilería.</li>
                                                        <li>Proceso más costoso.</li>
                                                    </ul>
                                                </td>
                                                <td>
                                                    <ul>
                                                        <li>Menor resistencia a impactos fuertes.</li>
                                                        <li>No adecuado para fachadas en construcción.</li>
                                                    </ul>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    <strong>Tiempo de Instalación</strong>
                                                </td>
                                                <td>1-2 días (dependiendo de la obra).</td>
                                                <td>1-2 horas (sin necesidad de obra).</td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    <strong>Precio Aproximado</strong>
                                                </td>
                                                <td>Más elevado por el coste de mano de obra y materiales.</td>
                                                <td>Más económico, solo se necesitan los tornillos y herramientas básicas.</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                                {/* ------------------------------------------ */}
                                <h4 className="h3-categories">Rejas abatibles para ventanas</h4>
                                <p>Las <strong>rejas abatibles para ventanas</strong> son la solución perfecta para quienes buscan <b>seguridad y comodidad en su hogar</b>.</p>
                                <p>Gracias a su sistema de apertura y cierre, estas rejas permiten un acceso sencillo para limpiar las ventanas o disfrutar de una ventilación sin restricciones.</p>
                                {/* ------------------------------------------ */}
                                <h4 className="h3-categories">Rejas para gatos y mascotas</h4>
                                <p>Las <strong>rejas para gatos y mascotas</strong> son una solución perfecta para proteger a tus animales de compañía, asegurando su bienestar sin comprometer la ventilación o la estética de tu hogar.</p>
                                <p>Este tipo de reja está diseñado especialmente para <b>evitar accidentes</b>, como caídas desde ventanas abiertas o balcones, sin limitar la libertad de movimiento de tus mascotas.</p>
                                <p>A diferencia de las rejas convencionales, las rejas para mascotas cuentan con un <b>diseño especial</b> que reduce el espacio entre los barrotes. </p>
                                <p>Esta característica evita que gatos, perros pequeños u otros animales puedan atravesarlas, ofreciendo una protección efectiva sin limitar su libertad de movimiento.</p>
                                {/* ------------------------------------------ */}
                                <h4 className="h3-categories">Rejas rústicas</h4>
                                <p>Las <strong>rejas rústicas</strong> son ideales para quienes buscan un <b>estilo tradicional</b> en la decoración de sus ventanas. Inspiradas en la arquitectura <b>clásica</b>, estas rejas destacan por sus <b>detalles ornamentales</b> y su robustez.</p>
                                <p>Aportan un encanto histórico y una elegancia atemporal a cualquier edificación. Estas piezas, a menudo elaboradas en <b>hierro forjado</b>, reflejan la artesanía de épocas pasadas y son ideales para quienes buscan un estilo clásico en sus ventanas o puertas.</p>

                                {/* ------------------------------------------------------------------------------------------------------------------------ */}
                                <hr className="hr-categories mt-5" />
                                <h2 className="h2-categories my-3">Precios de rejas para ventanas</h2>
                                <p>El <strong>precio de las rejas para ventanas</strong> puede variar considerablemente dependiendo de diversos factores, como el <b>material utilizado, el tipo de diseño, las dimensiones de la ventana y el método de instalación</b> requerido.</p>
                                <p>Los materiales más comunes, como el hierro, el aluminio y el acero inoxidable, tienen precios diferentes. El <b>hierro suele ser la opción más económica</b>, mientras que el acero inoxidable es una de las más costosas debido a su alta resistencia y durabilidad.</p>
                                <p>También influye el <b>nivel de personalización</b>. Las rejas estándar suelen ser más económicas, mientras que las rejas con <b>diseños ornamentales o personalizados tienden a incrementar su coste</b>.</p>
                                <p>En cuanto a la instalación, las rejas que requieren <b>obra suelen tener un precio más alto</b> debido al tiempo y materiales adicionales necesarios, mientras que las <strong>rejas sin obra son más rápidas y económicas</strong> de colocar.</p>
                                <p>Además, algunos proveedores ofrecen servicios adicionales, como acabados especiales o tratamientos anticorrosión, que pueden agregar valor y durabilidad a las rejas, aunque con un coste extra.</p>
                                <p>En nuestra página web, puedes <b>calcular al instante el precio de cada reja</b>, lo que te permitirá explorar diferentes opciones y encontrar la que mejor se ajuste a tu presupuesto y necesidades. </p>
                                <p>Consulta nuestro <strong>catálogo</strong> para obtener más detalles y solicita un presupuesto personalizado si necesitas asesoramiento adicional.</p>
                                {/* ------------------------------------------ */}
                                <h3 className="h3-categories">¿Cuánto vale poner una reja en una ventana?</h3>
                                <p>El coste de <strong>instalar una reja en una ventana</strong> puede variar significativamente en función del tipo de instalación. </p>
                                <p>Si la instalación requiere obra de albañilería el coste es mayor con respecto a la instalación de rejas para ventana sin obra que su instalación es mucho más simple.</p>
                                {/* ------------------------------------------ */}
                                <h3 className="h3-categories">Consejos para ahorrar en la instalación</h3>
                                <p>Las <strong>rejas sin obra</strong> son una opción <b>económica y práctica</b>, ya que su instalación es <b>rápida</b>, requiere menos mano de obra y <b>reduce significativamente el coste total</b>. </p>
                                <p>Además, están diseñadas para que <b>reduce significativamente el coste total</b>x, sin necesidad de conocimientos especializados.</p>
                                <p>Nuestras <strong>rejas para ventanas sin obra</strong> incluyen todos los elementos necesarios para una <strong>instalación sencilla</strong>: tacos y tornillos especialmente diseñados. </p>
                                <p>Con solo un <b>taladro</b>, puedes perforar los agujeros, fijar la reja y ajustar los tornillos para que quede perfectamente instalada. </p>
                                {/* ------------------------------------------ */}
                                <h3 className="h3-categories">Consigue el precio exacto</h3>
                                <p>Para obtener un <strong>precio</strong> exacto de las rejas para tus ventanas...</p>
                                <p>Te recomendamos que, si tiene dudas, <Link to="/contact" className="link-categories">contáctenos</Link> para que podamos asesorarle y ofrecerle toda la información necesaria.</p>
                            </div>
                        </div>
                    </div>
                    <RelatedProductsCarousel
                        categorySlug={category_slug}
                        categoryName={categoryName}
                        currentProductId={product.id}
                        productName={product.nombre}
                    />
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
        </div>
    );
};

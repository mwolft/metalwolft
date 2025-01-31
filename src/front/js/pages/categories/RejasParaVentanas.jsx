import React, { useEffect, useContext, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet";
import { Breadcrumb } from "../../component/Breadcrumb.jsx";
import { Product } from "../../component/Product.jsx";
import { AsideCategories } from "../../component/AsideCategories.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import { AsidePost } from "../../component/AsidePost.jsx";
import { Context } from "../../store/appContext.js";
import "../../../styles/categories-pages.css";
import MetalStructureViewer from '../../component/MetalStructureViewer.jsx';
import LazyLoad from "react-lazyload";
import { WhatsAppWidget } from "../../component/WhatsAppWidget.jsx";

export const RejasParaVentanas = ({ onSelectCategory, onSelectSubcategory, categoryId }) => {
    const { store, actions } = useContext(Context);
    const navigate = useNavigate();
    const rejasCategoryId = 1;
    const [selectedCategoryId, setSelectedCategoryId] = useState(rejasCategoryId);
    const [selectedSubcategoryId, setSelectedSubcategoryId] = useState(null);
    const [metaData, setMetaData] = useState({});
    const [recentPosts, setRecentPosts] = useState([]);
    const [otherCategories, setOtherCategories] = useState([]);


    useEffect(() => {
        const fetchRecentPosts = async () => {
            const posts = await actions.getRecentPosts();
            setRecentPosts(posts);
        };
        fetchRecentPosts();

        const fetchOtherCategories = async () => {
            const categories = await actions.getOtherCategories(rejasCategoryId);
            setOtherCategories(categories);
        };
        fetchOtherCategories();
    }, []);


    const handlePostNavigation = (postSlug) => {
        navigate(`/${postSlug}`);
    };


    const handleCategoryNavigation = (categorySlug) => {
        navigate(`/${categorySlug}`);
    };


    useEffect(() => {
        actions.fetchProducts(selectedCategoryId, selectedSubcategoryId);
    }, [selectedCategoryId, selectedSubcategoryId]);


    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://scaling-umbrella-976gwrg7664j3grx-3001.app.github.dev";

        fetch(`${apiBaseUrl}/api/seo/rejas-para-ventanas`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then((data) => setMetaData(data))
            .catch((error) => console.error("Error fetching SEO data:", error));
    }, []);


    const handleCategorySelect = (categoryId) => {
        setSelectedCategoryId(categoryId);
        setSelectedSubcategoryId(null);
    };


    const handleSubcategorySelect = (subcategoryId) => {
        setSelectedSubcategoryId(subcategoryId);
    };


    return (
        <>
            <Helmet>
                {/* Título y Descripción */}
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="keywords" content={metaData.keywords} />

                {/* Robots */}
                <meta name="robots" content={metaData.robots || "index, follow"} />

                {/* Theme Color */}
                <meta name="theme-color" content={metaData.theme_color || "#ffffff"} />

                {/* Open Graph Meta Tags */}
                <meta property="og:type" content={metaData.og_type || "website"} />
                <meta property="og:title" content={metaData.title} />
                <meta property="og:description" content={metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:image:width" content={metaData.og_image_width || "1200"} />
                <meta property="og:image:height" content={metaData.og_image_height || "630"} />
                <meta property="og:image:alt" content={metaData.og_image_alt || "Carpintería metálica"} />
                <meta property="og:image:type" content={metaData.og_image_type || "image/jpeg"} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta property="og:updated_time" content={metaData.og_updated_time || "2024-12-10T12:00:00"} />

                {/* Canonical */}
                <link rel="canonical" href={metaData.canonical} />

                {store.products && store.products.length > 0 && (
                    <link
                        rel="preload"
                        as="image"
                        href={store.products[0].imagen}
                    />
                )}


                {/* JSON-LD Schema */}
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            {/*<Breadcrumb />*/}
            <div className="container" style={{ marginTop: "100px" }}>
                <div className="row">
                    <h1 className="h2-categories mb-4">Rejas para ventanas</h1>
                    <p>Las <strong>rejas para ventanas</strong> son elementos esenciales para la protección en cualquier hogar. En este sitio encontrarás información completa sobre los diferentes <b>tipos, estilos y precios</b> de rejas para ventanas. Nuestro objetivo es ayudarte a elegir la opción más adecuada, teniendo en cuenta tanto la <b>funcionalidad</b> como la <b>estética</b>.</p>
                    <p>Consigue el precio al instante y ¡Aprovécha de los <strong>ENVÍOS GRATUÍTOS</strong> directos de fábrica!</p>
                    <div className="col-12 col-lg-3 col-xl-3 order-1">
                        <div className="col-12 d-block order-1">
                            <AsideCategories
                                onSelectCategory={handleCategorySelect}
                                onSelectSubcategory={handleSubcategorySelect}
                                categoryId={rejasCategoryId}
                            />
                        </div>
                        <div className="d-none d-lg-block">
                            <AsidePost />
                            <AsideOthersCategories currentCategoryId={rejasCategoryId} />
                        </div>
                    </div>
                    <div className="col-12 col-lg-9 col-xl-9 order-2 p-3">
                        {/* ------------------------------------------------------------------------------------------------------------------------ */}
                        {/*<MetalStructureViewer />*/}
                        <h2 className="h2-categories">Catálogo de rejas para ventanas</h2>
                        <div className="row">
                            {store.products && store.products.length > 0 ? (
                                store.products.map((product, index) => (
                                    <div key={index} className="col-6 col-sm-6 col-md-4 col-lg-4 col-xl-4 mb-4 d-flex">
                                        <Product product={product} className="w-100" />
                                    </div>
                                ))
                            ) : (
                                <p>Cargando productos o no hay productos disponibles para esta categoría.</p>
                            )}
                        </div>
                    </div>
                    <div className="col-12 d-block d-lg-none order-3 p-3" aria-hidden="true">
                        <aside className="widget mb-5">
                            <p className="widget_title"><b>Posts Recientes</b></p>
                            <hr className="hr-home" />
                            {recentPosts.length > 0 ? (
                                <ul className="widget_categories">
                                    {recentPosts.map((post, index) => (
                                        <li key={index} className="others-categories">
                                            <img className="img-other-categories" src={post.image_url} alt={post.title} />
                                            <p className="p-other-categories">
                                                {post.title}<br />
                                                <span className="other-categories-span">{post.date}</span>
                                                <button
                                                    className="buton-other-categories"
                                                    onClick={() => handlePostNavigation(post.slug)}
                                                    aria-label={`Leer más sobre ${post.title}`}
                                                >
                                                    Leer más
                                                </button>
                                            </p>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p>Cargando posts recientes...</p>
                            )}
                        </aside>
                        <aside className="widget my-2">
                            <p className="widget_title"><b>Otras Categorías</b></p>
                            <hr className="hr-home" />
                            {otherCategories.length > 0 ? (
                                <ul className="widget_categories">
                                    {otherCategories.map((category, index) => (
                                        <li key={index} className="others-categories">
                                            <img
                                                className="img-other-categories"
                                                src={category.image_url || "/path/to/default/image.jpg"}
                                                alt={category.nombre}
                                                style={{
                                                    width: "80px",
                                                    height: "100%",
                                                    objectFit: "cover"
                                                }}
                                            />
                                            <p className="p-other-categories">
                                                {category.nombre}<br />
                                                <button
                                                    className="buton-other-categories"
                                                    onClick={() => handleCategoryNavigation(category.slug)}
                                                    aria-label={`Ir a categoría ${category.nombre}`}
                                                >
                                                    Ir a categoría
                                                </button>
                                            </p>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p>Cargando otras categorías...</p>
                            )}
                        </aside>
                    </div>
                </div>
                <div className="row">
                    <div className="col-12 col-lg-3 col-xl-3 order-1">
                    </div>
                    <div className="col-12 col-lg-9 col-xl-9 order-2 my-4 p-3">
                        <div className="alert alert-primary" role="alert">
                            <p><b><i className="fa-regular fa-circle-question"></i> PREGUNTAS FRECUENTES</b></p>
                            <ul>
                                <li><b>¿Los precios incluyen IVA?</b> Sí, todos nuestros precios incluyen IVA.</li>
                                <li>
                                    <b>¿Cuál es el tiempo de fabricación y entrega?</b> Nuestro tiempo estimado de fabricación y entrega es de <b>20 días hábiles</b>. Sin embargo, este plazo puede variar dependiendo de nuestra carga de trabajo. En caso de que haya un aumento en los tiempos, te lo notificaremos con anticipación para que estés informado.
                                </li>
                                <li>
                                    <b>¿Qué sucede después de realizar mi compra?</b> Tras completar tu compra, recibirás un correo de confirmación con todos los detalles. Además, nos pondremos en contacto contigo para orientarte en la instalación y ofrecerte asistencia personalizada, asegurándonos de que tengas una experiencia satisfactoria con tu compra.
                                </li>
                                <li>
                                    <b>¿Cómo puedo ponerme en contacto después de la compra?</b> Puedes hacerlo a través de nuestro <a href="/contact" target="_blank" rel="noopener noreferrer">formulario de contacto</a>, enviándonos un mensaje por <a href="https://wa.me/634112604" target="_blank" rel="noopener noreferrer">WhatsApp</a> o llamándonos al <a href="tel:634112604">634112604</a>.
                                </li>
                            </ul>
                        </div>
                        {/* ------------------------------------------------------------------------------------------------------------------------ */}
                        <h2 className="h2-categories">Tipos de rejas para ventanas</h2>
                        {/* ------------------------------------------ */}
                        <h3 className="h3-categories">Rejas para ventanas modernas</h3>
                        <p>Las <strong>rejas para ventanas modernas</strong> han experimentado una transformación en su estilo y materiales, siguiendo líneas más <strong>sencillas</strong> siendo igual de <strong>bonitas</strong>, ofreciendo un equilibrio perfecto entre <b>seguridad y estética</b>.</p>
                        <p>Aunque el hierro sigue siendo el material predominante, se han incorporado otros materiales, como el acero inoxidable, para satisfacer las necesidades cambiantes de los propietarios.</p>
                        <p>En <Link to="/" className="link-categories">Metal Wolf</Link>, nos enorgullece presentar una selección de <strong>rejas para ventanas modernas</strong> que destacan tanto por su estilo como por su capacidad de brindar <b>protección efectiva</b>.</p>
                        <p>Nuestra filosofía se centra en la creación de <b>diseños</b> que no solo cumplen con su propósito principal, sino que también <b>realzan la estética de su hogar</b>.</p>
                        {/* ------------------------------------------ */}
                        <h3 className="h3-categories">Rejas para ventanas sin obra</h3>

                        <p>
                            <strong>Las rejas para ventanas sin obra</strong> se fijan directamente en el marco de la ventana con
                            <Link to="https://todoanclajes.com/producto/tornillo-inviolable-torx-7-x-30/?gad_source=1&gclid=CjwKCAiAjp-7BhBZEiwAmh9rBX_pS1jYu9WcRXkLhOVUreLYelh3cFK1xX7rnxMQv4ru8xcZ-6YLmRoCnEsQAvD_BwE" className="link-categories">
                                tornillos especiales inviolables
                            </Link>, diseñados para ofrecer una sujeción segura y resistente. Al no requerir intervención en los muros, el resultado es más <b>limpio</b>.
                        </p>
                        <p>
                            La <Link to="https://www.metalwolft.com/instalation-rejas-para-ventanas" className="link-categories">instalación de las rejas sin obra</Link> es rápida y sencilla, lo que permite reducir tanto los tiempos como los costes asociados.
                        </p>
                        <p>Este tipo de reja las convierte en una opción ideal para quienes desean mantener intacto el acabado de la fachada.</p>
                        <p>
                            Si deseas proteger tu hogar sin alterar la fachada, las <strong>rejas sin obra</strong> son la alternativa perfecta. Combina <b>seguridad y funcionalidad</b> y un diseño que se adapta a cualquier estilo de ventana.
                        </p>
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
                        <h3 className="h3-categories">Rejas para ventanas con obra</h3>
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
                                        <h6 className="mt-2">{item.title}</h6>
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
                        <h3 className="h3-categories">Rejas abatibles para ventanas</h3>
                        <p>Las <strong>rejas abatibles para ventanas</strong> son la solución perfecta para quienes buscan <b>seguridad y comodidad en su hogar</b>.</p>
                        <p>Gracias a su sistema de apertura y cierre, estas rejas permiten un acceso sencillo para limpiar las ventanas o disfrutar de una ventilación sin restricciones.</p>
                        {/* ------------------------------------------ */}
                        <h3 className="h3-categories">Rejas para gatos y mascotas</h3>
                        <p>Las <strong>rejas para gatos y mascotas</strong> son una solución perfecta para proteger a tus animales de compañía, asegurando su bienestar sin comprometer la ventilación o la estética de tu hogar.</p>
                        <p>Este tipo de reja está diseñado especialmente para <b>evitar accidentes</b>, como caídas desde ventanas abiertas o balcones, sin limitar la libertad de movimiento de tus mascotas.</p>
                        <p>A diferencia de las rejas convencionales, las rejas para mascotas cuentan con un <b>diseño especial</b> que reduce el espacio entre los barrotes. </p>
                        <p>Esta característica evita que gatos, perros pequeños u otros animales puedan atravesarlas, ofreciendo una protección efectiva sin limitar su libertad de movimiento.</p>
                        {/* ------------------------------------------ */}
                        <h3 className="h3-categories">Rejas rústicas</h3>
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
                        <p>Para obtener un <strong>precio</strong> exacto de las rejas para tus ventanas, es importante proporcionar <b>medidas precisas</b> y detallar el tipo de <strong>instalación</strong> que necesitas. </p>
                        <p>En nuestro <strong>catálogo</strong> encontrará diversos diseños de reja donde podrá insertar las medidas, el tipo de instalación y el color y se calculará el <strong>precio</strong> <b>al instante</b>.</p>
                        <p>Te recomendamos que, si tiene dudas, <Link to="https://www.metalwolft.com/contact" className="link-categories">contáctenos</Link> para que podamos asesorarle y ofrecerle toda la información necesaria.</p>
                        {/* ------------------------------------------------------------------------------------------------------------------------ */}
                        <hr className="hr-categories mt-5" />
                        <h2 className="h2-categories my-3">Instalación y consejos prácticos</h2>
                        {/* ------------------------------------------ */}
                        <h3 className="h3-categories">¿Cómo elegir la reja perfecta para tu ventana?</h3>
                        <p>En cuanto a estética y estilo es cuestión de <b>gustos</b> porque todas cumplen con la premisa fundamental de la <strong>seguridad</strong>.</p>
                        <p>Para elegir la reja perfecta hay que fijarse en que la instalación que sea lo más favorable para cada caso. </p>
                        <p>Se recomienda <b>con garras en el caso que la ubicación</b> se encuentre <b>en fase de obra y esté en bruto la fachada</b> faltándole el acabado a la fachada, simplemente porque coge <b>más fuerza el anclaje</b>, para todos los demás casos el <b>anclaje con tornillos especiales</b> es suficiente, siendo más <b>limpio y económico</b>.</p>
                        {/* ------------------------------------------ */}
                        <h3 className="h3-categories">¿Cómo Medir el Hueco para Rejas de Ventanas?</h3>
                        <ul>
                            <li><strong>Mide el ancho:</strong> Mide de un lado al otro del marco de la ventana, asegurándote de tomar la medida en varios puntos (arriba, en el centro y abajo). La <b>medida mas pequeña</b> es la que debes de coger para que encaje la reja. Además, como puede haber ligeras variaciones de milímetros, es muy aconsejable restarle medio centímetro para repartir en los laterales y asegurar que la reja va a encajar.</li>
                            <li><strong>Mide la altura:</strong> Desde la base hasta la parte superior del marco de la ventana. Repite la medición en ambos lados. A esta altura a nosotros nos gusta restarle 2/3 centímetros para que quede hueco en la parte inferior para poder limpiar el vierteaguas y no se acumulen restos de polvo, hojas, etc. </li></ul>
                        <p>Asegúrate de anotar todas las medidas y, si es posible, <Link to="https://www.metalwolft.com/contact" className="link-categories">consultárnos</Link> para evitar errores.</p>
                        <p>Puede consultar un <Link to="https://www.metalwolft.com/medir-hueco-rejas-para-ventanas" className="link-categories">artículo dedicado</Link> en nuestro blog</p>
                        <p>
                            Tomar medidas precisas es esencial para garantizar que las rejas se ajusten correctamente.
                        </p>
                        {/* ------------------------------------------ */}
                        <h3 className="h3-categories">¿Cómo instalar rejas para ventanas?</h3>
                        <p>La <strong>instalación de rejas para ventanas</strong> no solo garantiza la <strong>seguridad</strong> de tu hogar, sino que también puede mejorar su estética. </p>
                        <p>Dependiendo del <b>tipo de instalación</b>, que nosotros diferenciamos en con obra o sin obra, se requerirá diferentes herramientas.</p>
                        <p>Como la instalación con obra la suele realizar un albañil con mucha facilidad, nos centramos en la instalación sin obra en la que cualquiera lo puede hacer con pocas herramientas.</p>
                        <p>Tenemos un artículo dedicado donde especificamos con más detalle este proceso pinchando en el siguiente enlace: <Link to="https://www.metalwolft.com/instalation-rejas-para-ventanas" className="link-categories">Instalación de rejas para ventanas sin obra</Link>.</p>
                    </div>
                </div>
            </div>
            <WhatsAppWidget
                whatsappNumber="34634112604"
                placeholderText="Escribenos por WhatsApp"
                widgetText="¿Le podemos ayudar?"
                botImage="https://res.cloudinary.com/dewanllxn/image/upload/v1735631180/welder-bot_tqxadc.png"
            />
        </>
    );
};

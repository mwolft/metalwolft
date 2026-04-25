import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext.js';
import { Breadcrumb } from "../../component/Breadcrumb.jsx";
import { AsidePost } from "../../component/AsidePost.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import { Link } from "react-router-dom";
import { RelatedProductsCarousel } from "../../component/RelatedProductsCarousel.jsx";

export const RejasParaVentanasSinObra = () => {
    const { store, actions } = useContext(Context);
    const [metaData, setMetaData] = useState({});
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const { currentPost, currentComments } = store;
    const postId = 6;

    const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
        ? process.env.REACT_APP_BACKEND_URL
        : process.env.NODE_ENV === "production"
            ? "https://api.metalwolft.com"
            : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

    useEffect(() => {
        fetch(`${apiBaseUrl}/api/seo/rejas-para-ventanas-sin-obra`)
            .then((r) => {
                if (!r.ok) throw new Error(`Error: ${r.status} ${r.statusText}`);
                return r.json();
            })
            .then((data) => setMetaData(data))
            .catch((err) => console.error("Error fetching SEO data:", err));
    }, []);


    useEffect(() => {
        if (!currentPost || currentPost.id !== postId) {
            actions.fetchPost(postId);
        }
    }, [actions, currentPost, postId]);


    useEffect(() => {
        if (currentPost && currentPost.id === postId && !store.commentsLoaded) {
            actions.fetchComments(postId);
        }
    }, [actions, currentPost, postId, store.commentsLoaded]);

    const handleCommentSubmit = async (e) => {
        e.preventDefault();
        const token = localStorage.getItem('token');
        if (!token) {
            alert("Debes estar logeado para comentar.");
            return;
        }
        if (!commentContent.trim()) return;

        try {
            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts/${postId}/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ content: commentContent })
            });
            if (!response.ok) throw new Error("Error al enviar comentario");
            await response.json();
            actions.fetchComments(postId);
            setCommentContent("");
            setSuccessMessage("Comentario publicado con éxito!");
            setTimeout(() => setSuccessMessage(""), 3000);
        } catch (error) {
            console.error('Error:', error);
        }
    };


    return (
        <>
            <Helmet htmlAttributes={{ lang: metaData.lang || "es" }}>
                {/* 🏷️ SEO básico */}
                <title>{metaData.title || "Rejas para ventanas sin obra | Metal Wolft"}</title>
                <meta
                    name="description"
                    content={metaData.description || "Descubre cómo funcionan las rejas sin obra: seguras, fáciles de colocar y hechas a medida por Metal Wolft."}
                />
                <meta
                    name="keywords"
                    content={metaData.keywords || "rejas para ventanas sin obra, rejas fáciles de instalar, rejas metálicas sin taladro, Metal Wolft"}
                />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <link rel="canonical" href={metaData.canonical || window.location.href} />
                <meta name="theme-color" content={metaData.theme_color || "#ff324d"} />

                {/* 🐦 Twitter Card */}
                <meta name="twitter:card" content={metaData.twitter_card_type || "summary_large_image"} />
                <meta name="twitter:site" content={metaData.twitter_site || "@MetalWolft"} />
                <meta name="twitter:creator" content={metaData.twitter_creator || "@MetalWolft"} />
                <meta name="twitter:title" content={metaData.twitter_title || metaData.title} />
                <meta name="twitter:description" content={metaData.twitter_description || metaData.description} />
                <meta name="twitter:image" content={metaData.twitter_image || metaData.og_image} />
                <meta
                    name="twitter:image:alt"
                    content={metaData.twitter_image_alt || metaData.og_image_alt || "Rejas para ventanas sin obra Metal Wolft"}
                />

                {/* 📘 Open Graph (Facebook / LinkedIn) */}
                <meta property="og:type" content={metaData.og_type || "article"} />
                <meta property="og:title" content={metaData.title} />
                <meta property="og:description" content={metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:image:width" content={metaData.og_image_width || "825"} />
                <meta property="og:image:height" content={metaData.og_image_height || "550"} />
                <meta property="og:image:type" content={metaData.og_image_type || "image/png"} />
                <meta property="og:image:alt" content={metaData.og_image_alt || "Rejas sin obra Metal Wolft"} />
                <meta property="og:url" content={metaData.og_url || window.location.href} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta property="og:locale:alternate" content={metaData.og_locale_alternate || "en_US"} />

                {/* 🔧 JSON-LD estructurado */}
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            <Container className='post-page' style={{ marginTop: '60px' }}>
                <Breadcrumb
                    items={[
                        { label: "Inicio", to: "/" },
                        { label: "Blog", to: "/blogs" },
                        { label: currentPost?.title || "Artículo" }
                    ]}
                />
                <Row>
                    <Col xl={9}>
                        {currentPost && (
                            <div className="single_post">
                                <h1 className="h1-categories">{currentPost.title}</h1>
                                <p className="p-coments-single-post">
                                    <i className="fa-regular fa-calendar mx-1" style={{ color: '#ff324d' }}></i> {new Date(currentPost.created_at).toLocaleDateString()}
                                    <i className="fa-regular fa-comments mx-1" style={{ color: '#ff324d', paddingLeft: '10px' }}></i> {currentComments?.length || 0} Comentarios
                                </p>
                                <img
                                    src="https://res.cloudinary.com/dewanllxn/image/upload/v1760282424/rejas-para-ventanas-sin-obra_s8mzho.avif"
                                    alt="rejas para venanas sin obra"
                                    className="img-fluid my-3 post-hero-image"
                                />
                            </div>
                        )}
                        <div className="blog-text">
                            <p>Para acertar a la primera, te vendrÃ¡ bien revisar <Link to="/medir-hueco-rejas-para-ventanas" style={{ color: "#ff324d", textDecoration: "underline" }}>cÃ³mo medir el hueco</Link> y seguir nuestra <Link to="/instalation-rejas-para-ventanas" style={{ color: "#ff324d", textDecoration: "underline" }}>guÃ­a de instalaciÃ³n sin obra</Link>.</p>
                            <h2 className="h2-categories">¿Qué son las rejas para ventanas sin obra?</h2>
                            <p>
                                Las <strong>rejas para ventanas sin obra</strong> son una solución sencilla y moderna para proteger tus ventanas
                                sin tener que hacer rozas ni obras de albañilería.
                            </p>
                            <p>
                                Son rejas que ya vienen preparadas para atornillar directamente
                                al muro de la fachada, sin necesidad de cemento ni soldadura.
                            </p>
                            <p>
                                Este tipo de rejas se instalan fácilmente porque incluyen <strong>agujeros interiores</strong> o pequeñas
                                <strong> pletinas metálicas</strong> (también llamadas “orejetas”) que salen del propio marco.
                            </p>
                            <blockquote className="blockquote_style3">
                                Son la forma más práctica de proteger tus ventanas sin tener que hacer ningún tipo de reforma.
                            </blockquote>
                            <p>
                                En ellas se colocan tornillos especiales de seguridad que garantizan una fijación firme sin dañar la fachada.
                            </p>
                            <p>
                                En <strong>MetalWolft</strong> fabricamos cada reja a medida, adaptándola exactamente al hueco de tu ventana.
                            </p>
                            <p>
                                Así queda perfectamente encajada, sin holguras y con un acabado limpio que no altera la estética de la vivienda.
                                Todo el sistema está pensado para que puedas reforzar tus ventanas sin complicaciones ni obras.
                            </p>

                            <RelatedProductsCarousel
                                categorySlug="rejas-para-ventanas"
                                categoryName="Rejas para ventanas"
                                currentProductId={null}  
                                productName="rejas sin obra"
                            />

                            <h2 className="h2-categories">Ventajas frente a las rejas con obra</h2>
                            <p>
                                Las <strong>rejas para ventanas sin obra</strong> tienen varias ventajas claras frente a las rejas tradicionales que van empotradas o soldadas al muro.
                                Aquí te resumimos las principales:
                            </p>
                            <ul className="m-4">
                                <li>
                                    <strong>Instalación limpia y rápida:</strong> no hace falta abrir huecos ni hacer rozas.
                                    En menos de una hora puedes tener tu reja colocada, sin polvo ni ruidos.
                                </li>
                                <li>
                                    <strong>Sin albañilería:</strong> todo se fija con tornillos de seguridad, evitando cemento, soldadura o herramientas pesadas.
                                </li>
                                <li>
                                    <strong>Reversibles:</strong> si algún día quieres desmontarlas para pintar o mudarte, se retiran (con herramientas especiales) sin dejar marcas en la pared.
                                </li>
                                <li>
                                    <strong>Mismo resultado visual:</strong> una vez instalada, la reja sin obra ofrece el mismo acabado que una reja empotrada.
                                </li>
                                <li>
                                    <strong>Más cómodas:</strong> puedes instalarlas tú mismo con un taladro y una llave, sin depender de un albañil ni esperar días de obra.
                                </li>
                            </ul>

                            <h2 className="h2-categories">¿Cómo se fijan las rejas sin obra?</h2>
                            <p>
                                Las <strong>rejas para ventanas sin obra</strong> se fijan con <strong>tornillos de seguridad inviolables</strong>,
                                diseñados para que una vez colocados no puedan desatornillarse desde fuera. Son los mismos que se utilizan
                                en cerramientos metálicos profesionales.
                            </p>
                            <p>
                                Este tipo de tornillos lleva una tapa metálica que se incrusta despues de apretarse, cubriendo la cabeza del tornillo.
                                De esta forma, el sistema queda totalmente protegido y no se puede manipular ni extraer sin herramientas especializadas.
                            </p>
                            <blockquote className="blockquote_style3">
                                Se fijan con tornillos de seguridad inviolables, creando una sujeción firme y protegida.
                            </blockquote>

                            <p>
                                En <strong>MetalWolft</strong> utilizamos la tornillería más robusta del mercado, con materiales galvanizados
                                y tratamiento anticorrosión, para garantizar una sujeción firme incluso con los años y la exposición al exterior.
                            </p>
                            <p>
                                Todo el conjunto —marco, anclajes y tornillos— forma una estructura sólida y discreta que proporciona seguridad real
                                sin afectar al aspecto del edificio.
                            </p>

                            <h2 className="h2-categories">¿Cuándo conviene elegir una reja sin obra?</h2>
                            <p>
                                Las <strong>rejas sin obra</strong> son perfectas cuando el muro o el interior de la ventana ya está terminado,
                                por ejemplo, con yeso, piedra o azulejos, y no quieres hacer una roza o dañar el acabado.
                            </p>
                            <p>
                                También son una opción ideal si vives de alquiler o en una vivienda donde no puedes modificar la fachada.
                                Su instalación es rápida, limpia y no requiere permisos ni trabajos de albañilería.
                            </p>
                            <blockquote className="blockquote_style3">
                                Son una solución económica, limpia y duradera.
                            </blockquote>

                            <p>
                                Otra situación muy común es cuando quieres reforzar una segunda residencia o una casa de campo,
                                pero sin meterte en obras ni dejar la vivienda abierta varios días.
                                Con una reja sin obra puedes instalarla en una mañana y olvidarte.
                            </p>
                            <p>
                                En resumen, las <strong>rejas para ventanas sin obra</strong> son una solución económica, limpia y duradera.
                                Protegen igual que una reja empotrada, pero con la ventaja de poder instalarse de forma sencilla,
                                sin afectar la estética ni el muro de la casa.
                            </p>

                            <p className="mt-4">
                                Si quieres ver modelos reales y calcular el precio al instante, visita nuestra sección de{" "}
                                <Link to="/rejas-para-ventanas" style={{ color: "#ff324d" }}>
                                    rejas para ventanas a medida
                                </Link>.
                                Encontrarás diferentes estilos, colores y tipos de instalación, todos fabricados en hierro con pintura al horno
                                y envío a toda España.
                            </p>
                        </div>

                        <hr style={{ marginTop: '30px' }} />

                        <div className="comment-area" style={{ marginTop: '50px', marginBottom: '50px' }}>
                            <div className="content_title">
                                <p>Comentarios ({currentComments?.length || 0})</p>
                            </div>
                            {currentComments && currentComments.length > 0 ? (
                                <ul className="list_none comment_list">
                                    {currentComments.map(comment => (
                                        <li className="comment_info" key={comment.id}>
                                            <div className="d-flex">
                                                <div className="comment_user">
                                                    <img src="https://res.cloudinary.com/dewanllxn/image/upload/v1733563800/user_tnrkmx.png" alt="user avatar" style={{ width: '3rem' }} />
                                                </div>
                                                <div className="comment_content">
                                                    <div className="meta_data">
                                                        <h6>{comment.user_id}</h6>
                                                        <div className="comment-time">{new Date(comment.created_at).toLocaleString()}</div>
                                                    </div>
                                                    <p>{comment.content}</p>
                                                </div>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p>Sin comentarios todavía. ¡Sé el primero en escribir uno!</p>
                            )}
                            {successMessage && <Alert variant="success">{successMessage}</Alert>}
                            <Form onSubmit={handleCommentSubmit}>
                                <Form.Group>
                                    <Form.Control
                                        as="textarea"
                                        value={commentContent}
                                        onChange={(e) => setCommentContent(e.target.value)}
                                        placeholder="Escribir un comentario"
                                        rows="4"
                                    />
                                </Form.Group>
                                <Button type="submit" className="btn btn-style-background-color mt-2">Enviar comentario</Button>
                            </Form>
                        </div>
                    </Col>
                    <Col xl={3}>
                        <AsidePost currentPostId={postId} />
                        <AsideOthersCategories currentCategoryId={null} />
                    </Col>
                </Row>
            </Container>
        </>
    );
};

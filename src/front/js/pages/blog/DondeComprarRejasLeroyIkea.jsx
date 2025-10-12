import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Container, Row, Col, Form, Button, Alert } from "react-bootstrap";
import { Context } from "../../store/appContext.js";
import { AsidePost } from "../../component/AsidePost.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import { Link } from "react-router-dom";
import { RelatedProductsCarousel } from "../../component/RelatedProductsCarousel.jsx";

export const DondeComprarRejasLeroyIkea = () => {
    const { store, actions } = useContext(Context);
    const [metaData, setMetaData] = useState({});
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const { currentPost, currentComments } = store;

    const postId = 5;

    // Base URL API (igual que en tus otros posts)
    const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
        ? process.env.REACT_APP_BACKEND_URL
        : process.env.NODE_ENV === "production"
            ? "https://api.metalwolft.com"
            : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

    // Cargar metadata SEO específica de este post
    useEffect(() => {
        fetch(`${apiBaseUrl}/api/seo/donde-comprar-rejas-leroy-ikea`)
            .then((r) => {
                if (!r.ok) throw new Error(`Error: ${r.status} ${r.statusText}`);
                return r.json();
            })
            .then((data) => setMetaData(data))
            .catch((err) => console.error("Error fetching SEO data:", err));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Cargar contenido del post
    useEffect(() => {
        if (!currentPost || currentPost.id !== postId) actions.fetchPost(postId);
    }, [actions, currentPost]);

    // Cargar comentarios
    useEffect(() => {
        if (currentPost && currentPost.id === postId && !store.commentsLoaded) {
            actions.fetchComments(postId);
        }
    }, [actions, currentPost, store.commentsLoaded]);

    // Enviar comentario
    const handleCommentSubmit = async (e) => {
        e.preventDefault();
        const token = localStorage.getItem("token");
        if (!token) {
            alert("Debes estar logeado para comentar.");
            return;
        }
        if (!commentContent.trim()) return;

        try {
            const response = await fetch(
                `${apiBaseUrl}/api/posts/${postId}/comments`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({ content: commentContent }),
                }
            );
            if (!response.ok) throw new Error("Error al enviar comentario");
            await response.json();
            actions.fetchComments(postId);
            setCommentContent("");
            setSuccessMessage("Comentario publicado con éxito!");
            setTimeout(() => setSuccessMessage(""), 3000);
        } catch (error) {
            console.error("Error:", error);
        }
    };

    return (
        <>
            <Helmet htmlAttributes={{ lang: metaData.lang || "es" }}>
                <title>{metaData.title || "¿Dónde comprar rejas para ventanas?"}</title>
                <meta
                    name="description"
                    content={
                        metaData.description ||
                        "Comparamos Ikea, Leroy Merlin y la opción a medida para comprar rejas para ventanas: precios, calidades, plazos y cuándo elegir cada una."
                    }
                />
                <meta
                    name="keywords"
                    content={
                        metaData.keywords ||
                        "rejas para ventanas Leroy Merlin,rejas para ventanas Ikea,rejas a medida,comparativa rejas"
                    }
                />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ffffff"} />
                <link
                    rel="canonical"
                    href={
                        metaData.canonical ||
                        "https://www.metalwolft.com/donde-comprar-rejas-leroy-ikea"
                    }
                />

                {/* Twitter */}
                <meta name="twitter:card" content={metaData.twitter_card_type || "summary_large_image"} />
                <meta name="twitter:site" content={metaData.twitter_site || "@metalwolft"} />
                <meta name="twitter:creator" content={metaData.twitter_creator || "@metalwolft"} />
                <meta name="twitter:title" content={metaData.twitter_title || "Ikea, Leroy Merlin o a medida: ¿dónde comprar rejas para ventanas?"} />
                <meta name="twitter:description" content={metaData.twitter_description || "Pros y contras de Ikea, Leroy Merlin y las rejas a medida."} />
                <meta name="twitter:image" content={metaData.twitter_image || "https://res.cloudinary.com/dewanllxn/image/upload/v1760079525/donde-comprar-rejas-leroy-ikea_-_copia_ztsabu.png"} />
                <meta name="twitter:image:alt" content={metaData.twitter_image_alt || "Comparativa Ikea vs Leroy Merlin vs a medida"} />

                {/* Open Graph */}
                <meta property="og:type" content={metaData.og_type || "article"} />
                <meta property="og:title" content={metaData.title || "¿Dónde comprar rejas para ventanas?"} />
                <meta property="og:description" content={metaData.description || "Comparamos Ikea, Leroy Merlin y rejas a medida."} />
                <meta property="og:image" content={metaData.og_image || "https://res.cloudinary.com/dewanllxn/image/upload/v1760079525/donde-comprar-rejas-leroy-ikea_-_copia_ztsabu.png"} />
                <meta property="og:image:width" content={metaData.og_image_width || "400"} />
                <meta property="og:image:height" content={metaData.og_image_height || "300"} />
                <meta property="og:image:type" content={metaData.og_image_type || "image/png"} />
                <meta property="og:image:alt" content={metaData.og_image_alt || "Comparativa de opciones para comprar rejas"} />
                <meta property="og:url" content={metaData.og_url || "https://www.metalwolft.com/donde-comprar-rejas-leroy-ikea"} />
                <meta property="og:site_name" content={metaData.og_site_name || "MetalWolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />

                {/* JSON-LD opcional */}
                {metaData.json_ld && (
                    <script
                        type="application/ld+json"
                        dangerouslySetInnerHTML={{ __html: JSON.stringify(metaData.json_ld) }}
                    />
                )}
            </Helmet>

            <Container className="post-page" style={{ marginTop: "20px", marginBottom: "50px" }}>
                <Row>
                    <Col xl={9}>
                        {currentPost ? (
                            <div className="single_post">
                                <h1 className="h1-categories">{currentPost.title}</h1>
                                <p className="p-coments-single-post">
                                    <i className="fa-regular fa-calendar mx-1" style={{ color: "#ff324d" }}></i>{" "}
                                    {new Date(currentPost.created_at).toLocaleDateString()}
                                    <i className="fa-regular fa-comments mx-1" style={{ color: "#ff324d", paddingLeft: "10px" }}></i>{" "}
                                    {currentComments?.length || 0} Comentarios
                                </p>
                                <img
                                    src="https://res.cloudinary.com/dewanllxn/image/upload/v1760079525/donde-comprar-rejas-leroy-ikea_rsquhp.avif"
                                    alt="¿Dónde comprar rejas? Ikea, Leroy Merlin o a medida"
                                    className="img-fluid my-3"
                                    width="825"
                                    height="550"
                                />
                            </div>
                        ) : (
                            <p>Cargando...</p>
                        )}
                        <div className="blog-text">
                            <h2 className="h2-categories">Comparativa de rejas para ventanas: Ikea, Leroy Merlin o a medida</h2>
                            <p>
                                Si estás buscando <strong>rejas para ventanas</strong> y no sabes por dónde empezar,
                                lo normal es pensar primero en tiendas como <strong>Ikea</strong> o <strong>Leroy Merlin</strong>.
                                Son conocidas, rápidas y tienen precios competitivos.
                            </p>
                            <p>Pero ojo, no todas las viviendas ni
                                todos los huecos son iguales.
                            </p>
                            <p>Si lo que necesitas es una <strong>reja a medida</strong>,
                                con un nivel extra de seguridad o un diseño más cuidado, lo mejor es apostar por una
                                <strong> fabricación personalizada</strong>.
                            </p>

                            <p>
                                En pocas palabras: Ikea y Leroy Merlin te sacan del apuro si tienes una medida estándar,
                                pero si buscas algo más duradero, bonito y que encaje justo en tu ventana, el camino es otro.
                            </p>

                            <h2 className="h2-categories">Comparativa rápida de rejas para ventanas</h2>
                            <ul className="m-4">
                                <li>
                                    <strong>Ikea:</strong> precios muy bajos y entrega rápida. Ideal si buscas algo
                                    decorativo o temporal. Eso sí, sus <em>rejas para ventanas</em> no suelen estar
                                    pensadas para seguridad real ni fabricadas en hierro soldado.
                                </li>
                                <li>
                                    <strong>Leroy Merlin:</strong> más variedad que Ikea, con modelos de hierro o aluminio
                                    y la opción de recoger en tienda. Sin embargo, la mayoría de sus rejas son de
                                    <strong> medidas estándar</strong>, y la calidad depende mucho del proveedor y del
                                    grosor del material.
                                </li>
                                <li>
                                    <strong>A medida:</strong> aquí la cosa cambia. Se diseñan <em>rejas a medida </em>
                                    que se adaptan exactamente a tu hueco, con <strong>soldadura profesional</strong>,
                                    <strong> pintura al horno</strong> y opciones como <em>rejas abatibles</em>, con
                                    <em> cerradura o llave</em> y diferentes acabados según el estilo de tu vivienda.
                                </li>
                            </ul>

                            <h2 className="h2-categories">¿Cuándo elegir Ikea, Leroy Merlin o una reja a medida?</h2>
                            <p>
                                No hay una única respuesta: depende de lo que busques. Te dejamos algunas pistas sencillas:
                            </p>
                            <ul className="m-4">
                                <li>
                                    <strong>Quieres algo rápido y económico:</strong> Ikea o Leroy Merlin te lo solucionan.
                                </li>
                                <li>
                                    <strong>Tus ventanas no encajan en medidas estándar y quieres una reja más segura:</strong> encarga una reja a medida.
                                </li>
                                <li>
                                    <strong>Buscas estilo, color o diseño personalizados:</strong> las rejas fabricadas a medida
                                    te permiten elegir el tipo de perfil, el color, el grosor e incluso el sistema de apertura.
                                </li>
                            </ul>

                            <RelatedProductsCarousel
                                categorySlug="rejas-para-ventanas"
                                categoryName="Rejas para ventanas"
                                currentProductId={null}  
                                productName="rejas Leroy Merlin"
                            />

                            <h2 className="h2-categories">Precio, calidad y durabilidad</h2>
                            <p>
                                En tiendas como <strong>Ikea</strong> o <strong>Leroy Merlin</strong> encontrarás <strong>rejas económicas</strong>,
                                fabricadas en serie y con un acabado visual atractivo.
                            </p>

                            <p>
                                Están pensadas para soluciones rápidas,
                                pero su <strong>tratamiento anticorrosión</strong> y los <strong>sistemas de anclaje</strong> suelen ser básicos,
                                suficientes para interiores o zonas de poco uso, pero no para una exposición exterior prolongada.
                            </p>

                            <p>
                                En <strong>MetalWolft</strong> cuidamos cada detalle. Utilizamos la <strong>tornillería más resistente del mercado </strong>
                                y fijaciones reforzadas que garantizan una sujeción sólida y duradera.
                            </p>
                            <p>
                                Nuestras <strong>rejas a medida</strong> pueden
                                costar un poco más, pero están diseñadas para durar décadas, adaptarse a cualquier entorno y mantener su
                                pintura y estructura intactas frente al tiempo y la intemperie.
                            </p>


                            <h2 className="h2-categories">Conclusión: ¿qué rejas para ventanas merecen más la pena?</h2>
                            <p>
                                Si tienes una casa o piso con huecos estándar, Ikea y Leroy Merlin te sacarán del paso.
                                Pero si valoras la seguridad, el acabado y el diseño, merece la pena apostar por una
                                <strong> reja a medida</strong>.
                            </p>
                            <p>
                                En <strong>MetalWolft</strong> fabricamos rejas adaptadas a tu ventana, soldadas y pintadas
                                con los mismos materiales que usamos en las instalaciones profesionales.
                            </p>

                            <p className="mt-4">
                                ¿No sabes qué reja encaja mejor en tu ventana? Primero puedes revisar <strong>nuestra guía</strong> de <Link to="/instalation-rejas-para-ventanas" style={{ color: "#ff324d" }}> instalación sin obra
                                </Link> para aprender cómo medir correctamente.
                            </p>
                            <p>
                                Después visita nuestra sección de <Link to="/rejas-para-ventanas" style={{ color: "#ff324d" }}> rejas para ventanas
                                </Link> y <strong>calcula al instante el precio</strong> de cada modelo según tus medidas, color y tipo de anclaje. Así sabrás en segundos cuánto cuesta tu reja a medida, sin esperas ni formularios.
                            </p>


                        </div>


                        <hr style={{ marginTop: "30px" }} />

                        {/* ===== Comentarios ===== */}
                        <div className="comment-area" style={{ marginTop: "50px", marginBottom: "50px" }}>
                            <div className="content_title">
                                <p>Comentarios ({currentComments?.length || 0})</p>
                            </div>

                            {currentComments && currentComments.length > 0 ? (
                                <ul className="list_none comment_list">
                                    {currentComments.map((comment) => (
                                        <li className="comment_info" key={comment.id}>
                                            <div className="d-flex">
                                                <div className="comment_user">
                                                    <img
                                                        src="https://res.cloudinary.com/dewanllxn/image/upload/v1733563800/user_tnrkmx.png"
                                                        alt="user avatar"
                                                        style={{ width: "3rem" }}
                                                    />
                                                </div>
                                                <div className="comment_content">
                                                    <div className="meta_data">
                                                        <h6>{String(comment.user_id)}</h6>
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
                                <Button type="submit" className="btn btn-style-background-color mt-2">
                                    Enviar comentario
                                </Button>
                            </Form>
                        </div>
                    </Col>

                    <Col xl={3}>
                        <AsidePost currentPostId={postId} />
                        <AsideOthersCategories currentCategoryId={postId} />
                    </Col>
                </Row>
            </Container>
        </>
    );
};

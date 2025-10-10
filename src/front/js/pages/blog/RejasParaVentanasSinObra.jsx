import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext.js';
import { AsidePost } from "../../component/AsidePost.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import { Link } from "react-router-dom";

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
            <Container className='post-page' style={{ marginTop: '20px' }}>
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
                                    src="https://res.cloudinary.com/dewanllxn/image/upload/v1760109829/rejas-para-ventanas-sin-obra_dzoea9.avif"
                                    alt="plazos de entrega de rejas para ventanas"
                                    className="img-fluid my-3"
                                />
                            </div>
                        )}
                        <div className="blog-text">
                            <h2 className="h2-categories">¿Qué son las rejas para ventanas sin obra?</h2>
                            <p>
                                Las <strong>rejas para ventanas sin obra</strong> son una solución moderna y práctica para reforzar
                                la seguridad de tu hogar sin necesidad de hacer agujeros ni modificar la fachada.
                                Se instalan mediante <strong>anclajes interiores o sistemas de presión</strong> que se fijan al marco
                                o al hueco de la ventana, sin cemento ni albañilería.
                            </p>

                            <p>
                                Este tipo de rejas se han vuelto muy populares porque combinan seguridad, estética y facilidad de montaje.
                                Son ideales para viviendas en alquiler, segundas residencias o para quien quiere proteger sin meterse en obras.
                                En MetalWolft fabricamos cada modelo a medida, para que quede ajustado al milímetro y mantenga una sujeción firme.
                            </p>

                            <h2 className="h2-categories">Ventajas frente a las rejas tradicionales</h2>
                            <ul className="m-4">
                                <li><strong>Instalación limpia y rápida:</strong> no requiere perforar paredes ni manchar la fachada.</li>
                                <li><strong>Desmontables:</strong> se pueden retirar fácilmente si cambias de vivienda o quieres pintar.</li>
                                <li><strong>Seguras:</strong> aunque no van “empotradas”, los anclajes internos de acero y los tornillos de seguridad
                                    ofrecen una resistencia muy superior a las rejas decorativas de gran superficie.</li>
                                <li><strong>Estéticas:</strong> disponibles en varios estilos y colores, sin perder armonía con el diseño de la casa.</li>
                            </ul>

                            <h2 className="h2-categories">¿Cómo se fijan las rejas sin obra?</h2>
                            <p>
                                Las rejas sin obra se apoyan directamente sobre el hueco de la ventana.
                                Se ajustan con <strong>tornillería interior y tacos de presión</strong> invisibles desde el exterior.
                                En MetalWolft utilizamos <strong>tornillos galvanizados de alta resistencia</strong>, los mismos que se emplean
                                en carpintería metálica profesional, para garantizar una fijación sólida incluso con el paso de los años.
                            </p>

                            <p>
                                A diferencia de las rejas prefabricadas de grandes superficies, nuestras rejas a medida se diseñan según tu hueco,
                                asegurando que no queden holguras ni puntos débiles. Cada pieza se pinta con pintura al horno para resistir
                                la intemperie y mantener su aspecto durante años.
                            </p>

                            <h2 className="h2-categories">¿Cuándo conviene elegir una reja sin obra?</h2>
                            <ul className="m-4">
                                <li>Si vives de alquiler y no puedes modificar la fachada.</li>
                                <li>Si quieres reforzar ventanas sin obras ni permisos.</li>
                                <li>Si buscas una opción segura y estética para segundas viviendas.</li>
                                <li>O si simplemente prefieres un sistema que puedas quitar o trasladar fácilmente.</li>
                            </ul>

                            <p className="mt-4">
                                Puedes ver todos nuestros modelos de <Link to="/rejas-para-ventanas" style={{ color: "#ff324d" }}>rejas a medida</Link>,
                                comparar estilos y precios al instante según tus medidas.
                                Fabricamos en hierro, con pintura profesional y envío a toda España.
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
                        <AsideOthersCategories currentCategoryId={postId} />
                    </Col>
                </Row>
            </Container>
        </>
    );
};

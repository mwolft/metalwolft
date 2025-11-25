import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext.js';
import { AsidePost } from "../../component/AsidePost.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import { Link } from "react-router-dom";

export const RecepcionPedidosRevisarAntesFirmar = () => {
    const { store, actions } = useContext(Context);
    const [metaData, setMetaData] = useState({});
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const { currentPost, currentComments } = store;
    const postId = 4;

    // Log del estado global para depurar
    useEffect(() => {
        console.log("Store:", store);
        console.log("currentPost:", currentPost);
        console.log("currentComments:", currentComments);
    }, [store, currentPost, currentComments]);

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

        fetch(`${apiBaseUrl}/api/seo/recepcion-pedidos-revisar-antes-firmar`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then((data) => {
                console.log("SEO MetaData:", data);
                setMetaData(data);
            })
            .catch((error) => console.error("Error fetching SEO data:", error));
    }, []);

    useEffect(() => {
        if (!currentPost || currentPost.id !== postId) {
            console.log("Fetching post", postId);
            actions.fetchPost(postId);
        }
    }, [actions, currentPost, postId]);

    useEffect(() => {
        if (currentPost && currentPost.id === postId && !store.commentsLoaded) {
            console.log("Fetching comments for post", postId);
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
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="keywords" content={metaData.keywords} />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ff324d"} />
                <link rel="canonical" href={metaData.canonical} />

                {/* Twitter */}
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:site" content={metaData.twitter_site} />
                <meta name="twitter:creator" content={metaData.twitter_creator} />
                <meta name="twitter:title" content={metaData.twitter_title || metaData.title} />
                <meta name="twitter:description" content={metaData.twitter_description || metaData.description} />
                <meta name="twitter:image" content={metaData.twitter_image || metaData.og_image} />
                <meta name="twitter:image:alt" content={metaData.twitter_image_alt || metaData.og_image_alt} />

                {/* Open Graph */}
                <meta property="og:type" content={metaData.og_type || "article"} />
                <meta property="og:title" content={metaData.title} />
                <meta property="og:description" content={metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:image:width" content={metaData.og_image_width || "400"} />
                <meta property="og:image:height" content={metaData.og_image_height || "300"} />
                <meta property="og:image:type" content={metaData.og_image_type || "image/avif"} />
                <meta property="og:image:alt" content={metaData.og_image_alt || "Recepción de pedidos Metal WolfT"} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta property="og:locale:alternate" content={metaData.og_locale_alternate || "en_US"} />

                {/* JSON-LD */}
                {metaData.json_ld && (
                    <script
                        type="application/ld+json"
                        dangerouslySetInnerHTML={{ __html: JSON.stringify(metaData.json_ld) }}
                    />
                )}
            </Helmet>

            <Container className='post-page' style={{ marginTop: '20px', marginBottom: '50px' }}>
                <Row>
                    <Col xl={9}>
                        {currentPost ? (
                            <div className="single_post">
                                <h1 className="h1-categories">{currentPost.title}</h1>
                                <p className="p-coments-single-post">
                                    <i className="fa-regular fa-calendar mx-1" style={{ color: '#ff324d' }}></i>{" "}
                                    {new Date(currentPost.created_at).toLocaleDateString()}
                                    <i className="fa-regular fa-comments mx-1" style={{ color: '#ff324d', paddingLeft: '10px' }}></i>{" "}
                                    {currentComments?.length || 0} Comentarios
                                </p>
                                <img
                                    src="https://res.cloudinary.com/dewanllxn/image/upload/v1757832270/recepcion-pedidos-revisar-antes-firmar-open_yu5oqv.avif"
                                    alt="Recepción de pedidos y revisión de daños"
                                    className="img-fluid my-3"
                                />
                            </div>
                        ) : (
                            <p>Cargando...</p>
                        )}

                        <div className="blog-text">
                            <h2 className="h2-categories">¿POR QUÉ REVISAR ANTES DE FIRMAR?</h2>
                            <p>
                                Piensa que tu pedido ha pasado por fábricas, almacenes y furgonetas antes de llegar a tu puerta.
                                Nosotros lo embalamos con cuidado y trabajamos con <strong>SEUR España</strong>, pero a veces los baches, los traslados rápidos o simplemente el azar pueden jugar una mala pasada.
                                <br /><br />
                                Si revisas el paquete <strong>en el momento de la entrega</strong>, todo es mucho más fácil:
                                si ves un golpe o una rotura y lo dejas reflejado, SEUR y nosotros podemos reclamar y reponer sin problemas.
                                Si no lo revisas y firmas sin mirar, reclamar después es casi imposible.
                            </p>

                            <h2 className="h2-categories">QUÉ REVISAR</h2>
                            <p>
                                Tómate dos minutos antes de abrirlo. No hace falta desmontar el embalaje ahí mismo,
                                pero sí asegurarte de que por fuera está todo bien. Mira:
                            </p>
                            <ul className="m-4">
                                <li><strong>Estado exterior:</strong> ¿Tiene golpes, agujeros, humedad o parece que se ha abierto?</li>
                                <li><strong>Ruidos extraños:</strong> Si al moverlo escuchas piezas sueltas, mejor anotarlo.</li>
                                <li><strong>Precintos y etiquetas:</strong> Comprueba que no falten ni estén arrancadas.</li>
                            </ul>

                            <h2 className="h2-categories">PASOS PARA RECLAMAR SI HAY PROBLEMAS</h2>
                            <p>
                                Si ves algo raro, no te preocupes: sigue estos pasos sencillos para que podamos ayudarte:
                            </p>
                            <ol className="m-4">
                                <li><strong>Haz fotos</strong> al paquete tal y como te lo entregan, antes de abrirlo.</li>
                                <li>Pide al repartidor que deje constancia: escribe <em>"pendiente de revisión"</em> o <em>"paquete dañado"</em> en su PDA o en el albarán.</li>
                                <li>Avísanos el mismo día. Envíanos fotos y detalles a través del <Link to="/contact" style={{ color: '#ff324d', textDecoration: 'underline' }}>formulario</Link> o por <a href="https://wa.me/34634112604" style={{ color: '#ff324d', textDecoration: 'underline' }}>WhatsApp</a>.</li>
                                <li><strong>No tires el embalaje</strong> hasta que resolvamos la incidencia, porque nos sirve como prueba.</li>
                            </ol>

                            <h2 className="h2-categories">NUESTRO COMPROMISO</h2>
                            <p>
                                Sabemos que comprar online requiere confianza. Por eso te pedimos estos pasos:
                                no es para complicarte, es para <strong>proteger tu compra</strong> y que, si pasa algo en el transporte,
                                podamos responder rápido y sin pegas.
                                <br /><br />
                                Nosotros estamos de tu lado y queremos que todo llegue perfecto.
                                Si no es así, juntos haremos que se solucione cuanto antes.
                            </p>
                        </div>


                        <hr style={{ marginTop: '30px' }} />

                        <div className="comment-area" style={{ marginTop: '50px', marginBottom: '50px' }}>
                            <div className="content_title">
                                <p>Comentarios ({currentComments?.length || 0})</p>
                            </div>
                            {currentComments && currentComments.length > 0 ? (
                                <ul className="list_none comment_list">
                                    {currentComments.map(comment => {
                                        console.log("Comment:", comment);
                                        return (
                                            <li className="comment_info" key={comment.id}>
                                                <div className="d-flex">
                                                    <div className="comment_user">
                                                        <img src="https://res.cloudinary.com/dewanllxn/image/upload/v1733563800/user_tnrkmx.png" alt="user avatar" style={{ width: '3rem' }} />
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
                                        );
                                    })}
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

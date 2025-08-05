import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext.js';
import { AsidePost } from "../../component/AsidePost.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import { Link } from "react-router-dom";
import DeliveryEstimateBanner from "../../component/DeliveryEstimateBanner.jsx";

export const PlazosEntregaRejasAMedida = () => {
    const { store, actions } = useContext(Context);
    const [metaData, setMetaData] = useState({});
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const { currentPost, currentComments } = store;
    const postId = 3;

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
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="keywords" content={metaData.keywords} />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ffffff"} />
                <meta name="twitter:card" content={metaData.twitter_card_type} />
                <meta name="twitter:site" content={metaData.twitter_site} />
                <meta name="twitter:creator" content={metaData.twitter_creator} />
                <meta name="twitter:title" content={metaData.twitter_title || metaData.title} />
                <meta name="twitter:description" content={metaData.twitter_description || metaData.description} />
                <meta name="twitter:image" content={metaData.twitter_image || metaData.og_image} />
                <meta name="twitter:image:alt" content={metaData.twitter_image_alt || metaData.og_image_alt} />
                <meta property="og:type" content={metaData.og_type || "article"} />
                <meta property="og:title" content={metaData.title} />
                <meta property="og:description" content={metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:image:width" content={metaData.og_image_width || "400"} />
                <meta property="og:image:height" content={metaData.og_image_height || "300"} />
                <meta property="og:image:type" content={metaData.og_image_type || "image/avif"} />
                <meta property="og:image:alt" content={metaData.og_image_alt || "plazos de entrega rejas a medida"} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta property="og:locale:alternate" content={metaData.og_locale_alternate || "en_US"} />
                <link rel="canonical" href={metaData.canonical} />
                {metaData.json_ld && (
                    <script type="application/ld+json">{JSON.stringify(metaData.json_ld)}</script>
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
                                    src="https://res.cloudinary.com/dewanllxn/image/upload/v1753776840/plazos-de-entrega-rejas-para-ventanas_v48rm7.avif"
                                    alt="plazos de entrega de rejas para ventanas"
                                    className="img-fluid my-3"
                                />
                            </div>
                        )}
                        <div className="blog-text">
                            <h2 className="h2-categories">¿CUÁL ES EL PLAZO DE ENTREGA?</h2>
                            <p>
                                Hemos desarrollado un sistema de <strong>estimación automática</strong> que te muestra, en tiempo real, un rango de <strong>fechas</strong> ajustado a nuestra <strong>carga de trabajo actual</strong>.
                            </p>
                            <DeliveryEstimateBanner />
                            <p style={{ marginTop: '20px' }}>
                                Esto te permitirá tener una previsión <strong>más fiable</strong>, incluso en periodos donde la demanda puede incrementarse de forma puntual.
                            </p>
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                minHeight: '150px'
                            }}>
                                <img
                                    src="https://res.cloudinary.com/dewanllxn/image/upload/v1754155736/estado-de-envio_uglnqu.jpg"
                                    alt="Entrega"
                                    style={{
                                        width: '100%',
                                        height: 'auto',
                                        maxWidth: '750px',
                                        objectFit: 'contain',
                                        borderRadius: '12px'
                                    }}
                                />
                            </div>
                            <p>
                                Todas nuestras rejas se fabrican a medida, desde cero, según las dimensiones que introduces.
                                Por eso, el plazo de entrega puede variar ligeramente en función de la carga de trabajo y el modelo seleccionado.
                            </p>
                            <p>
                                La estimación de entrega se actualiza diariamente y podrás consultarla en todo momento durante tu proceso de compra.
                                De forma general, solemos entregar en un plazo de <strong>20 días naturales</strong>.
                                Sin embargo, en periodos de alta demanda (como primavera u otoño) este rango puede ajustarse.
                            </p>
                            <p>
                                Nuestro compromiso es mantenerte informado y ofrecerte la previsión más precisa desde el primer momento.
                            </p>


                            <h2 className="h2-categories">¿QUÉ FACTORES AFECTAN AL PLAZO?</h2>
                            <ul className="m-4">
                                <li><strong>Volumen de pedidos:</strong> Los meses con más solicitudes suelen tener más tiempo de espera.</li>
                                <li><strong>Tipo de reja:</strong> Modelos especiales, acabados o estructuras complejas pueden requerir más días.</li>
                                <li><strong>Ubicación de entrega:</strong> Algunas zonas geográficas pueden requerir más tiempo logístico.</li>
                            </ul>

                            <h2 className="h2-categories">¿PUEDO CONSULTAR EL ESTADO DE MI PEDIDO?</h2>
                            <p>
                                Sí, por supuesto. Si necesitas información adicional sobre tu pedido o deseas coordinar la entrega para una fecha concreta, puedes escribirnos a través del
                                <Link to="/contact" style={{ color: '#ff324d', textDecoration: 'underline' }}> formulario de contacto</Link> o directamente a nuestro
                                <a href="https://wa.me/34634112604" target="_blank" rel="noopener noreferrer" style={{ color: '#ff324d', textDecoration: 'underline' }}> WhatsApp</a>.
                            </p>
                            <p>
                                También puedes ver ejemplos de trabajos anteriores y tiempos reales de entrega en nuestra sección de
                                <Link to="/rejas-para-ventanas" style={{ color: '#ff324d', textDecoration: 'underline' }}> Rejas para Ventanas</Link>.
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

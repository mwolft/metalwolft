import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext.js';
import { AsidePost } from "../../component/AsidePost.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import { Link } from "react-router-dom";
import MetalStructureViewer from '../../component/MetalStructureViewer.jsx';
import { RelatedProductsCarousel } from "../../component/RelatedProductsCarousel.jsx";

export const RejasParaVentanasModernas = () => {
    const { store, actions } = useContext(Context);
    const [metaData, setMetaData] = useState({});
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const { currentPost, currentComments } = store;
    const postId = 7;

    const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
        ? process.env.REACT_APP_BACKEND_URL
        : process.env.NODE_ENV === "production"
            ? "https://api.metalwolft.com"
            : "https://fuzzy-space-eureka-7v7jw6jv7v5jhp945-3001.app.github.dev/";

    useEffect(() => {
        fetch(`${apiBaseUrl}/api/seo/rejas-para-ventanas-modernas`)
            .then((response) => {
                if (!response.ok) throw new Error(`Error: ${response.status} ${response.statusText}`);
                return response.json();
            })
            .then((data) => setMetaData(data))
            .catch((error) => console.error("Error fetching SEO data:", error));
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
                <title>{metaData.title || "Metal Wolft | Rejas a medida"}</title>
                <meta name="description" content={metaData.description || "Fabricamos rejas a medida seguras, modernas y sin obra."} />
                <meta name="keywords" content={metaData.keywords || "rejas para ventanas, rejas modernas, rejas sin obra, metal wolft"} />
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
                <meta name="twitter:image:alt" content={metaData.twitter_image_alt || metaData.og_image_alt || "Rejas para ventanas Metal Wolft"} />

                {/* 📘 Open Graph (Facebook / LinkedIn) */}
                <meta property="og:type" content={metaData.og_type || "article"} />
                <meta property="og:title" content={metaData.title} />
                <meta property="og:description" content={metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:image:width" content={metaData.og_image_width || "825"} />
                <meta property="og:image:height" content={metaData.og_image_height || "550"} />
                <meta property="og:image:type" content={metaData.og_image_type || "image/png"} />
                <meta property="og:image:alt" content={metaData.og_image_alt || "Rejas a medida Metal Wolft"} />
                <meta property="og:url" content={metaData.og_url || window.location.href} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta property="og:locale:alternate" content={metaData.og_locale_alternate || "en_US"} />

                {/* 🔧 JSON-LD estructurado (SEO técnico) */}
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
                                    src="https://res.cloudinary.com/dewanllxn/image/upload/v1760282425/rejas-para-ventanas-modernas_rdp46a.avif"
                                    alt="rejas para ventanas modernas"
                                    className="img-fluid my-3"
                                />
                            </div>
                        )}
                        <div className="blog-text">
                            <h2 className="h2-categories">Rejas modernas: seguridad con estilo</h2>
                            <p>
                                Las <strong>rejas para ventanas modernas</strong> han dejado atrás la idea de hierro pesado y clásico.
                            </p>
                            <p>
                                Hoy en día, se pueden fabricar con diseños minimalistas, líneas rectas y acabados limpios que
                                se adaptan a cualquier tipo de fachada.
                            </p>
                            <p>
                                En <strong>MetalWolft</strong> fabricamos rejas de diseño a medida, combinando seguridad, estética y durabilidad.
                            </p>
                            <blockquote className="blockquote_style3">
                                Estas rejas no solo cumplen una función de protección; también aportan un toque decorativo.
                            </blockquote>
                            <p>
                                Gracias al corte preciso, la pintura profesional y los perfiles de acero seleccionados,
                                conseguimos un acabado elegante y contemporáneo, ideal para viviendas modernas o rehabilitaciones con estilo.
                            </p>
                            <MetalStructureViewer />
                            <h2 className="h2-categories">Diseños más populares</h2>
                            <ul className="m-4">
                                <li><strong>Rejas minimalistas:</strong> líneas rectas, sin adornos, perfectas para fachadas modernas y limpias.</li>
                                <li><strong>Rejas horizontales:</strong> aportan sensación de amplitud y se integran muy bien con ventanales grandes.</li>
                                <li><strong>Rejas con marco interior:</strong> más robustas, ofrecen una estética de carpintería metálica profesional.</li>
                                <li><strong>Rejas decorativas modernas:</strong> combinan seguridad con formas geométricas o paneles personalizados por láser.</li>
                            </ul>

                            <RelatedProductsCarousel
                                categorySlug="rejas-para-ventanas"
                                categoryName="Rejas para ventanas"
                                currentProductId={null}  
                                productName="rejas modernas"
                            />

                            <h2 className="h2-categories">Materiales y acabados</h2>
                            <p>
                                Todas nuestras <strong>rejas modernas</strong> se fabrican en hierro, con soldadura reforzada y pintura profesional.
                            </p>
                            <p>
                                Puedes elegir entre acabados en negro mate, blanco, grafito o incluso colores personalizados
                                según tu fachada o carpintería.
                            </p>
                            <p>
                                También ofrecemos la opción de <strong>rejas abatibles con cerradura</strong> para mantener la estética moderna sin renunciar
                                a la funcionalidad.
                            </p>
                            <blockquote className="blockquote_style3">
                                Todos los sistemas incluyen <strong>tornillería y anclajes de seguridad</strong> para un acabado limpio y discreto.
                            </blockquote>

                            <h2 className="h2-categories">¿Por qué elegir rejas modernas a medida?</h2>
                            <ul className="m-4">
                                <li>Porque se adaptan a tus medidas exactas, sin huecos ni ajustes improvisados.</li>
                                <li>Porque permiten combinar <strong>diseño y seguridad</strong> sin comprometer la estética de tu vivienda.</li>
                                <li>Porque la fabricación a medida asegura una estructura sólida y duradera, sin piezas endebles ni uniones flojas.</li>
                            </ul>

                            <p className="mt-4">
                                Inspírate con nuestros diseños de <Link to="/rejas-para-ventanas" style={{ color: "#ff324d" }}>rejas para ventanas a medida</Link>.
                                Calcula el precio al instante según tus medidas y elige el estilo que mejor encaje con tu hogar.
                            </p>
                            <p>
                                Fabricamos en España y enviamos a todo el país con garantía profesional.
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

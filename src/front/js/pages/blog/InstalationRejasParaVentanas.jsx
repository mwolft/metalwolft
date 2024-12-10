import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet";
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext';
import { Breadcrumb } from '../../component/Breadcrumb.jsx';
import "../../../styles/blog.css";
import { AsidePost } from "../../component/AsidePost.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";

export const InstalationRejasParaVentanas = () => {
    const { store, actions } = useContext(Context);
    const [metaData, setMetaData] = useState({});
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    const { currentPost, currentComments, error } = store;
    const postId = 2;

    useEffect(() => {
        if (!currentPost || currentPost.id !== postId) {
            actions.fetchPost(postId);
        }
    }, [actions, currentPost, postId]);

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://scaling-umbrella-976gwrg7664j3grx-3001.app.github.dev";

        fetch(`${apiBaseUrl}/api/seo/instalation-rejas-para-ventanas`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then((data) => setMetaData(data))
            .catch((error) => console.error("Error fetching SEO data:", error));
    }, []);

    useEffect(() => {
        if (currentPost && currentPost.id === postId && (!currentComments || currentComments[0]?.post_id !== postId)) {
            actions.fetchComments(postId);
        }
    }, [actions, currentPost, currentComments, postId]);

    const handleCommentSubmit = async (e) => {
        e.preventDefault();
        const token = localStorage.getItem('token');
        if (!token) {
            alert("Debes estar logeado para comentar.");
            return;
        }
        if (!commentContent || commentContent.trim() === "") {
            console.error("El contenido del comentario no puede estar vacío");
            return;
        }
        try {
            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts/${postId}/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ content: commentContent })
            });
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`Error posting comment: ${response.status} - ${errorText}`);
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            const newComment = await response.json();
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
            <Helmet>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="keywords" content={metaData.keywords} />
                <meta name="robots" content={metaData.robots || "index, follow"} />
                <meta name="theme-color" content={metaData.theme_color || "#ffffff"} />
                {/* Open Graph Meta Tags */}
                <meta property="og:type" content={metaData.og_type || "article"} />
                <meta property="og:title" content={metaData.title} />
                <meta property="og:description" content={metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:image:width" content={metaData.og_image_width || "400"} />
                <meta property="og:image:height" content={metaData.og_image_height || "300"} />
                <meta property="og:image:type" content={metaData.og_image_type || "image/png"} />
                <meta property="og:image:alt" content={metaData.og_image_alt || "Instalación de rejas para ventanas"} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta property="og:locale:alternate" content={metaData.og_locale_alternate || "en_US"} />
                {/* Canonical Link */}
                <link rel="canonical" href={metaData.canonical} />
                {/* JSON-LD Schema */}
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            <Breadcrumb />
            <Container className='post-page'>
                <Row>
                    <Col xl={9}>
                        {currentPost && (
                            <div className="single_post">
                                <h1 className="blog_title">{currentPost.title}</h1>
                                <p className="p-coments-single-post">
                                    <i className="fa-regular fa-calendar mx-1" style={{ color: '#ff324d' }}></i> {new Date(currentPost.created_at).toLocaleDateString()}
                                    <i className="fa-regular fa-comments mx-1" style={{ color: '#ff324d', paddingLeft: '10px' }}></i> {currentComments?.length || 0} Comentarios
                                </p>
                                <img src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562840/rejas-de-seguridad-para-ventanas_buzhg0.avif" alt="instalacion de rejas para ventanas" className="img-fluid my-3" />
                            </div>
                        )}
                        <div className="blog-text">
                            <h3>PREPARACIÓN Y HERRAMIENTAS NECESARIAS</h3>
                            <p>Después de haber medido cuidadosamente los huecos de las ventanas, como se detalló en nuestro <u><b>artículo anterior,</b></u>
                                y tras haber elegido el <u>estilo de rejas para ventanas</u> que mejor se adapte a tus necesidades, estás listo para recibir tus rejas. </p>

                            <p>Asegúrate de tener a mano las siguientes herramientas esenciales:</p>
                            <ul class="m-4">
                                <li class="m-3"><b>Taladro manual:</b> Para perforar agujeros en la pared de forma precisa.</li>
                                <li class="m-3"><b>Broca de pared de calibre 10:</b> Necesaria para crear los agujeros de anclaje en la pared.</li>
                                <li class="m-3"><b>Llave con punta para tornillos TORX:</b> Para apretar los tornillos de forma segura.</li>
                                <li class="m-3"><b>Un nivel:</b> Garantizar que la reja se instale perfectamente nivelada tanto horizontal como verticalmente.</li>
                                <li class="m-3"><b>Un rotulador:</b> Utilizado para marcar los puntos de anclaje en la pared.</li>
                                <li class="m-3"><b>Opcionales</b> - Listones de madera o martillo: Estos listones de madera o un martillo pueden ser útiles para ajustar la reja en su lugar y nivelarla correctamente haciendo palanca.</li>
                            </ul>
                            <h3>PASOS PARA LA INSTALACIÓN EXITOSA</h3>
                            <ol class="m-4" start="1">
                                <li><b>Posiciona la reja</b> en su lugar: Comienza por colocar la reja en el hueco de la ventana, asegurándote de que esté <b>al mismo nivel</b> que la
                                    superficie frontal de la pared. Utiliza las cuñas de madera o el martillo si es necesario para ajustarla adecuadamente en su lugar.</li>
                                <li><b>Marca los puntos de anclaje:</b> Usando un nivel, asegúrate de que la reja esté <b>nivelada</b> tanto horizontal como verticalmente.
                                    Marca los puntos de anclaje a través de los agujeros preperforados en la reja. Esto te indicará <b>dónde deben ir</b> los agujeros en la pared.</li>
                                <li><b>Retira la reja y realiza los agujeros:</b> Con los puntos de anclaje marcados, retira la reja para que puedas perforar los agujeros de
                                    anclaje de manera cómoda en los lugares marcados. Asegúrate de que los agujeros estén alineados con precisión.</li>
                                <li><b>Limpia la zona:</b> Antes de instalar la reja, asegúrate de que la zona esté limpia y libre de polvo y escombros.</li>
                                <li><b>Instala los tacos</b> de anclaje: Inserta los tacos de anclaje en los agujeros que has perforado en la pared.</li>
                                <li><b>Coloca la reja y atornilla:</b> Con los tacos de anclaje en su lugar, vuelve a colocar la reja en la posición correcta
                                    y utiliza los tornillos TORX para fijarla de manera segura.</li>
                                <li><b>Añade tapas inviolables:</b> Para una mayor seguridad, asegúrate de colocar las tapas inviolables en los tornillos.
                                    Estas tapas no solo proporcionan un aspecto limpio, sino que también evitan que se quiten fácilmente.</li>
                                <li><b>Ajustes finales:</b> Si la pared no es completamente rectangular y presenta algunas variaciones en su ancho,
                                    puedes rellenar cualquier espacio adicional <b>con silicona</b> para obtener un aspecto estético uniforme.</li>
                            </ol>
                            <div class="row">
                                <div class="col-sm-6">
                                    <div class="single_img">
                                        <img class="w-100 mb-4" src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562842/rejas-para-ventanas-modernas-2023_mambli.avif" alt="rejas para ventanas modernas" />
                                    </div>
                                </div>
                                <div class="col-sm-6">
                                    <div class="single_img">
                                        <img class="w-100 mb-4" src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562850/rejas-para-ventanas-sin-obra-precio_bps3ec.avif" alt="rejas para ventanas sin obra" />
                                    </div>
                                </div>
                            </div>
                            <blockquote class="blockquote_style3">
                                <p>La instalación de rejas para ventanas a veces necesita asistencia adicional, especialmente al manipular y ajustar la reja en su lugar.</p>
                            </blockquote>
                            <h3>RECOMENDACIONES</h3>
                            <ul class="m-4">
                                <li class="m-3"><b>Solicita ayuda:</b> La instalación de rejas para ventanas requiere la ayuda de otra persona,
                                    especialmente al manipular y ajustar la reja en su lugar.</li>
                                <li class="m-3">El tipo de material de la pared en la que se instalarán las rejas puede afectar
                                    la <b>facilidad de perforación.</b> Por ejemplo, las paredes de hormigón armado pueden requerir un taladro más robusto.</li>
                                <li class="m-3">Ubicación de la reja: Coloca la reja en el lugar que mediste anteriormente, es decir, si mediste al borde de
                                    la esquina o más adentro en la pared. Generalmente, se instalan al <b>mismo nivel</b> que la superficie frontal de la vivienda.</li>
                                <li class="m-3">Uso de taladros eléctricos:
                                    Utilizar taladros eléctricos para <b>apretar los tornillos</b> facilita la instalación y garantiza un ajuste seguro.</li>
                            </ul>
                            <h3>CONSEJOS DE MANTENIMIENTO DE LAS REJAS PARA VENTANAS</h3>
                            <ul class="m-4">
                                <li class="m-3"><b>El mantenimiento</b> de tus rejas para ventanas es esencial para prolongar su <b>vida útil</b> y preservar su atractivo estético.
                                    Dependiendo del acabado en pintura que hayas elegido, el mantenimiento variará:</li>
                                <li class="m-3"><b>Revestimiento termolacado:</b> Si has optado por un revestimiento termolacado, puedes disfrutar de la ventaja de una pintura
                                    de alta durabilidad. No tendrás que volver a <b>pintar las rejas</b> durante muchos años, ya que este tipo de pintura <b>protege</b> contra la corrosión y el desgaste.</li>
                                <li><b>Pintura no lacada:</b> Si la pintura no es lacada, su durabilidad dependerá de factores como la <b>ubicación geográfica.</b> En áreas cercanas al mar,
                                    la salinidad del ambiente puede <b>afectar la pintura</b> con el tiempo. Es aconsejable cubrir cualquier <b>arañazo o desgaste</b> en la pintura para evitar un deterioro acelerado del material.</li>
                            </ul>
                            <p><b>Mantener</b> tus rejas para ventanas en buenas condiciones es <b>esencial</b> para garantizar su eficacia y aspecto atractivo <b>con el tiempo.</b></p>
                            <p>No dudes en contactárnos si tienes alguna pregunta o necesitas <b>asesoramiento adicional</b> sobre la instalación o el mantenimiento de tus rejas para ventanas.</p>
                            <p>Esperamos que esta guía haya sido útil en tu proyecto de instalación de rejas para ventanas. Si tienes alguna pregunta o necesitas más información,
                                no dudes en ponerte en <u>contacto con nosotros.</u> ¡Estamos aquí para ayudarte!</p>
                            <video controls width="100%" height="auto">
                                <source src="https://res.cloudinary.com/dewanllxn/video/upload/v1733563618/instalacion-rejas-para-ventanas_kcno5b.webm" type="video/webm" />
                                Your browser does not support the video tag.
                            </video>
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
                                                    <img src="https://res.cloudinary.com/dewanllxn/image/upload/v1733563800/user_tnrkmx.png"
                                                        alt="user avatar"
                                                        style={{ width: '3rem', height: 'auto' }} />
                                                </div>
                                                <div className="comment_content">
                                                    <div className="d-flex">
                                                        <div className="meta_data">
                                                            <h6>{comment.user_id}</h6>
                                                            <div className="comment-time">{new Date(comment.created_at).toLocaleString()}</div>
                                                        </div>
                                                    </div>
                                                    <p>{comment.content}</p>
                                                </div>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p>Sin comentarios todavía. Sé el primero en escribir un comentario!</p>
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

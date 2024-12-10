import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet";
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext';
import { Breadcrumb } from '../../component/Breadcrumb.jsx';
import { AsidePost } from "../../component/AsidePost.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import "../../../styles/blog.css";

export const MedirHuecoRejasParaVentanas = () => {
    const { store, actions } = useContext(Context);
    const [metaData, setMetaData] = useState({});
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    const { currentPost, currentComments, error } = store;
    const postId = 1;

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

        fetch(`${apiBaseUrl}/api/seo/medir-hueco-rejas-para-ventanas`)
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
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
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
                                <img src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562847/rejas-para-ventanas_ttjq3d.avif" alt="rejas para ventanas" className="img-fluid my-3" />
                            </div>
                        )}
                        <div className="blog-text">
                            <p>En numerosas ocasiones, nos enfrentamos a la realidad de que los huecos destinados para la instalación de rejas en ventanas presentan <b>leves variaciones en sus dimensiones.</b></p>
                            <p>Esta divergencia es completamente normal, ya que cada espacio posee sus particularidades.</p>
                            <p>Generalmente esta diferencia <b>es muy leve</b> y no nos tiene que preocupar en exceso estéticamente, pero si hay que <b>ser preciso</b> para el ensamblaje de la misma.</p>
                            <p>En el proceso de instalación de rejas para ventanas, es una práctica común dejar un <b>espacio de aproximadamente 3/4 de centímetros</b> entre la reja y la parte inferior del hueco, sea esta de ladrillo u otro material. </p>
                            <p>Este espacio sirve para <b>evitar la acumulación</b> de suciedad, como polvo y hojas, permitiendo un drenaje eficiente del agua y facilitando la limpieza tanto de la parte inferior del hueco como de la propia reja. </p>
                            <p>Además, contribuye a <b>mantener la integridad</b> de las rejas para ventanas al evitar el contacto directo con la superficie de la pared, <b>previniendo así la corrosión.</b></p>
                            <p>En consecuencia, la <b>medición más crítica</b> se centra en el ancho, que debe realizarse con <b>precisión,</b> como veremos más adelante. </p>
                            <blockquote className="blockquote_style3">
                                <p>Los huecos donde se instalan las rejas para ventanas en muchas ocasiones no son rectángulos perfectos</p>
                            </blockquote>
                            <div className="row">
                                <div className="col-sm-6">
                                    <div className="single_img">
                                        <img className="w-100 mb-4" src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562857/rejas-para-ventanas-modernas_y9ti5y.jpg" alt="rejas para ventanas modernas" />
                                    </div>
                                </div>
                                <div className="col-sm-6">
                                    <div className="single_img">
                                        <img className="w-100 mb-4" src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562856/rejas-para-ventanas-sin-obra_imfqrq.avif" alt="rejas para ventanas sin obra" />
                                    </div>
                                </div>
                            </div>
                            <p>El alto del hueco, por otro lado, suele admitir <b>cierta flexibilidad,</b> dado que se reserva un pequeño margen. </p>
                            <p>Esto significa que, a menudo, es más importante asegurarse de <b>medir el ancho con precisión,</b> ya que cualquier error en esta dimensión podría resultar en la incompatibilidad de las rejas para ventanas con el hueco.</p>
                            <p>La dimensión final del ancho del hueco para las rejas de las ventanas se determina tomando <b>la medida más estrecha</b> entre tres puntos cruciales: la parte inferior, la zona intermedia y la superior. </p>
                            <p>Esto implica que es necesario <b>medir cuidadosamente</b> cada uno de estos puntos para asegurarse de que la reja encaje perfectamente y proporcione una estética deseada.</p>
                            <p>Aunque las rejas para ventanas son rectángulos prácticamente perfectos, con muy pocas variaciones en sus medidas, la <b>albañilería,</b> en contraste, tiende a ser <b>menos precisa.</b></p>
                            <p>Las imperfecciones en las paredes o los cambios en el grosor de los materiales utilizados pueden generar diferencias en las dimensiones del hueco. </p>
                            <p>Por lo tanto, es <b>fundamental</b> no asumir que todas las partes del hueco tienen la <b>misma medida,</b> sino <b>verificar</b> cada punto clave para asegurarse de una instalación exitosa.</p>
                            <blockquote className="blockquote_style3">
                                <p>La dimensión final del ancho la determina la medida más estrecha</p>
                            </blockquote>
                            <p>En situaciones donde las <b>medidas varían</b> algunos milímetros, es posible corregir esta disparidad rellenando el espacio posteriormente. </p>
                            <p>Esto puede lograrse mediante el <b>uso de silicona</b> en casos menores, mientras que para espacios más amplios se recurre al uso de cemento. Estas soluciones permiten <b>ajustar la reja</b> de manera efectiva al hueco y garantizar su estética.</p>
                            <p>Por eso es fundamental que la medición y la instalación se realicen <b>de manera cuidadosa</b> y con seguridad, siempre con alguien que nos ayude en la medición y hacerlo <b>varias veces</b> para estar del todo seguros.</p>
                            <p>En resumen, la medición adecuada del hueco para rejas de ventanas es esencial para garantizar una instalación estéticamente agradable. Dejar un espacio entre la reja y la parte inferior del hueco permite una fácil limpieza y evita la acumulación de suciedad. </p>
                            <p>Asegurarse de medir con <b>precisión el ancho del hueco</b> y considerar las variaciones en la albañilería es fundamental para un resultado exitoso. </p>
                            <p>En caso de discrepancias en las medidas, las soluciones de relleno adecuadas son clave para garantizar un ajuste perfecto y una estética óptima en el hogar.</p>
                            <p>Más abajo <b>os presentamos un video</b> que explica al detalle cómo realizar una medida correcta del hueco de rejas para ventanas.</p>
                            <p>¡Si todavía tiene dudas siempre puede contar con nosotros para resolverle cuantas cuestiones necesite!</p>
                            <video controls width="100%" height="auto">
                                <source src="https://res.cloudinary.com/dewanllxn/video/upload/v1733563614/medicion-rejas-para-ventanas_t2lbbe.webm" type="video/webm" />
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
                        <AsideOthersCategories currentCategoryId={null} />
                    </Col>
                </Row>
            </Container>
        </>
    );
};

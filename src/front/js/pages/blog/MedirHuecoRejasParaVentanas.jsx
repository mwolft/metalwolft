import React, { useEffect, useContext, useState } from 'react';
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext';

export const MedirHuecoRejasParaVentanas = () => {
    const { store, actions } = useContext(Context);
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    const { currentComments, error } = store;
    const postId = 1; 

    useEffect(() => {
        actions.fetchComments(postId);
    }, [actions, postId]);

    const handleCommentSubmit = async (e) => {
        e.preventDefault();
        if (!commentContent) return;

        try {
            const token = localStorage.getItem('jwt');
            const response = await fetch(`${process.env.BACKEND_URL}/api/posts/${postId}/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ content: commentContent })
            });

            if (!response.ok) {
                throw new Error('Error posting comment');
            }

            const newComment = await response.json();
            actions.fetchComments(postId); 
            setCommentContent("");
            setSuccessMessage("Comment posted successfully!");
            setTimeout(() => setSuccessMessage(""), 3000);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    return (
        <Container style={{ marginTop: '150px' }}>
            <Row>
                <Col xl={9}>
                    <div className="single_post">
                        <h2 className="blog_title">MEDICIÓN DEL HUECO PARA REJAS DE VENTANAS: CONSEJOS IMPORTANTES.</h2>
                        <ul className="list_none blog_meta">
                            <li><i className="ti-calendar"></i> 16 de marzo, 2023</li>
                            <li><i className="ti-comments"></i> 2 Comentarios</li>
                        </ul>
                        <div className="blog_img">
                            <img src="https://www.metalwolft.com/assets/images/blog/rejas-para-ventanas.avif" alt="rejas para ventanas" className="img-fluid" />
                        </div>
                        <div className="blog_content">
                            <div className="blog_text">
                                <p>En numerosas ocasiones, nos enfrentamos a la realidad de que los huecos destinados para la instalación de rejas en ventanas presentan <b>leves variaciones en sus dimensiones.</b></p>
                                <p>Esta divergencia es completamente normal, ya que cada espacio posee sus particularidades.</p>
                                <p>Generalmente esta diferencia <b>es muy leve</b> y no nos tiene que preocupar en exceso estéticamente, pero si hay que <b>ser preciso</b> para el ensamblaje de la misma.</p>
                                <blockquote className="blockquote_style3">
                                    <p>Los huecos donde se instalan las rejas para ventanas en muchas ocasiones no son rectángulos perfectos</p>
                                </blockquote>
                                <Row>
                                    <Col sm={6}>
                                        <div className="single_img">
                                            <img className="w-100 mb-4" src="https://www.metalwolft.com/assets/images/blog/rejas-para-ventanas-modernas.avif" alt="rejas para ventanas modernas" />
                                        </div>
                                    </Col>
                                    <Col sm={6}>
                                        <div className="single_img">
                                            <img className="w-100 mb-4" src="https://www.metalwolft.com/assets/images/blog/rejas-para-ventanas-sin-obra.avif" alt="rejas para ventanas sin obra" />
                                        </div>
                                    </Col>
                                </Row>
                                <p>El alto del hueco, por otro lado, suele admitir <b>cierta flexibilidad,</b> dado que se reserva un pequeño margen.</p>
                                <a href="../rejas-para-ventanas" className="btn btn-fill-out btn-radius mb-5">Ver catálogo</a>
                                <video controls preload="none" className="w-100">
                                    <source src="https://www.metalwolft.com/assets/video/medicion-rejas-para-ventanas.webm" type="video/webm" />
                                </video>
                            </div>
                        </div>
                    </div>
                    <div className="comment-area">
                        <div className="content_title">
                            <h5>Comentarios ({currentComments?.length || 0})</h5>
                        </div>
                        {currentComments && currentComments.length > 0 ? (
                            <ul className="list_none comment_list">
                                {currentComments.map(comment => (
                                    <li className="comment_info" key={comment.id}>
                                        <div className="d-flex">
                                            <div className="comment_user">
                                                <img src="https://www.metalwolft.com/assets/images/users/user.png" alt="user avatar" />
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
                            <p>No comments yet. Be the first to comment!</p>
                        )}
                        {successMessage && <Alert variant="success">{successMessage}</Alert>}
                        <Form onSubmit={handleCommentSubmit}>
                            <Form.Group>
                                <Form.Control
                                    as="textarea"
                                    value={commentContent}
                                    onChange={(e) => setCommentContent(e.target.value)}
                                    placeholder="Add a comment"
                                    rows="4"
                                />
                            </Form.Group>
                            <Button type="submit" className="mt-2">Submit Comment</Button>
                        </Form>
                    </div>
                </Col>
                <Col xl={3}>
                    <div className="sidebar">
                        <div className="widget">
                            <div className="shop_banner">
                                <div className="banner_img overlay_bg_20">
                                    <img src="https://www.metalwolft.com/assets/images/banners/rejas_para_ventanas_banner_img.avif" alt="rejas para ventanas rusticas" />
                                </div>
                                <div className="shop_bn_content2 text_white">
                                    <h5 className="text-uppercase shop_subtitle">Hazlo en Casa</h5>
                                    <h3 className="text-uppercase shop_title">Instalación Simple</h3>
                                    <a href="instalation-rejas-para-ventanas" className="btn btn-white rounded-0 btn-sm text-uppercase">Ver video</a>
                                </div>
                            </div>
                        </div>
                    </div>
                </Col>
            </Row>
        </Container>
    );
};

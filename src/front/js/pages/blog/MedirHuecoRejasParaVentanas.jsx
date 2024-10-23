import React, { useEffect, useContext, useState } from 'react';
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext';
import "../../../styles/blog.css";

export const MedirHuecoRejasParaVentanas = () => {
    const { store, actions } = useContext(Context);
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    const { currentPost, currentComments, error } = store;
    const postId = 1; 

    // Cargar el post al montar el componente
    useEffect(() => {
        if (!currentPost || currentPost.id !== postId) {
            actions.fetchPost(postId);
        }
    }, [actions, currentPost, postId]);

    // Cargar comentarios solo si el post ha sido cargado y solo si los comentarios no están ya cargados
    useEffect(() => {
        if (currentPost && currentPost.id === postId && (!currentComments || currentComments[0]?.post_id !== postId)) {
            actions.fetchComments(postId);
        }
    }, [actions, currentPost, currentComments, postId]);

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
                    {currentPost && (
                        <div className="single_post">
                            <h1 className="blog_title">{currentPost.title}</h1>
                            <p className="p-coments">
                                <i className="fa-regular fa-calendar mx-1" style={{color: '#ff324d'}}></i> {new Date(currentPost.created_at).toLocaleDateString()}
                                <i className="fa-regular fa-comments mx-1" style={{color: '#ff324d', paddingLeft: '10px'}}></i> {currentComments?.length || 0} Comentarios
                            </p>
                            <div className="blog_img">
                                <img src="https://www.metalwolft.com/assets/images/blog/rejas-para-ventanas.avif" alt="es" className="img-fluid" />
                            </div>
                        </div>
                    )}
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

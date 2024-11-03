import React, { useEffect, useContext, useState } from 'react';
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext';
import { Breadcrumb } from '../../component/Breadcrumb.jsx';
import "../../../styles/blog.css";
import { AsidePost } from "../../component/AsidePost.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";

export const InstalationRejasParaVentanas = () => {
    const { store, actions } = useContext(Context);
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
            const response = await fetch(`${process.env.BACKEND_URL}/api/posts/${postId}/comments`, {
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
                                <img src="https://www.metalwolft.com/assets/images/blog/rejas-para-ventanas.avif" alt="es" className="img-fluid my-3" />
                            </div>
                        )}
                        <div className="blog-text">
                            {/* Contenido del post aquí */}
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
                                                    <img src="https://www.metalwolft.com/assets/images/users/user.png"
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
                                <p>No comments yet. Be the first to comment!</p>
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

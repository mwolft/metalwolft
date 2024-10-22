import React, { useEffect, useContext, useState } from 'react';
import { Container, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext';

export const MedirHuecoRejasParaVentanas = () => {
    const { store, actions } = useContext(Context);
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    const { currentComments, error } = store;
    const postId = 1; // Asume que este es el ID del post que corresponde a este componente (ajústalo según corresponda)

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
            actions.fetchComments(postId); // Actualizar los comentarios después de añadir uno nuevo
            setCommentContent("");
            setSuccessMessage("Comment posted successfully!");
            setTimeout(() => setSuccessMessage(""), 3000);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    return (
        <Container style={{ marginTop: '350px' }}>
            <h2 className="my-4">Primer Post</h2>
            <p>Contenido del post...</p> {/* Aquí iría el contenido personalizado de este post */}
            
            <hr />
            <h3>Comments</h3>
            {currentComments && currentComments.length > 0 ? (
                <ul>
                    {currentComments.map(comment => (
                        <li key={comment.id}>
                            <p>{comment.content}</p>
                            <small>Posted by user {comment.user_id}</small>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No comments yet. Be the first to comment!</p>
            )}
            
            <hr />
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
        </Container>
    );
};

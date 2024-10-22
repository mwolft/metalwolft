import React, { useEffect, useContext, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Container, Form, Button, Alert } from 'react-bootstrap';
import { Context } from '../../store/appContext';

export const BlogDetailPage = () => {
    const { slug } = useParams();
    const { store, actions } = useContext(Context);
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    const { currentPost, currentComments, error } = store;

    useEffect(() => {
        actions.fetchPost(slug);
    }, [slug, actions]);

    const handleCommentSubmit = async (e) => {
        e.preventDefault();
        if (!commentContent) return;

        try {
            const token = localStorage.getItem('jwt');
            const response = await fetch(`${process.env.BACKEND_URL}/api/posts/${currentPost.id}/comments`, {
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
            actions.fetchComments(currentPost.id); // Actualizar los comentarios después de añadir uno nuevo
            setCommentContent("");
            setSuccessMessage("Comment posted successfully!");
            setTimeout(() => setSuccessMessage(""), 3000);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    if (!currentPost) {
        return <p>Loading...</p>;
    }

    return (
        <Container>
            <h2 className="my-4">{currentPost.title}</h2>
            <p>{currentPost.content}</p>
            {currentPost.image_url && <img src={currentPost.image_url} alt={currentPost.title} className="img-fluid mb-4" />}
            
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

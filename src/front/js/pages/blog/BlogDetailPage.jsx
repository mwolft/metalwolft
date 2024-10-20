import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Container, Form, Button, Alert } from 'react-bootstrap';

export const BlogDetailPage = () => {
    const { slug } = useParams();
    const [post, setPost] = useState(null);
    const [comments, setComments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [commentContent, setCommentContent] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    useEffect(() => {
        const fetchPost = async () => {
            try {
                const response = await fetch(`http://localhost:5000/api/posts/${slug}`);
                if (!response.ok) {
                    throw new Error('Error fetching post');
                }
                const data = await response.json();
                setPost(data);
                fetchComments(data.id);
            } catch (error) {
                console.error('Error:', error);
                setLoading(false);
            }
        };

        const fetchComments = async (postId) => {
            try {
                const response = await fetch(`http://localhost:5000/api/posts/${postId}/comments`);
                if (!response.ok) {
                    throw new Error('Error fetching comments');
                }
                const data = await response.json();
                setComments(data);
                setLoading(false);
            } catch (error) {
                console.error('Error:', error);
                setLoading(false);
            }
        };

        fetchPost();
    }, [slug]);

    const handleCommentSubmit = async (e) => {
        e.preventDefault();
        if (!commentContent) return;

        try {
            const token = localStorage.getItem('jwt');
            const response = await fetch(`http://localhost:5000/api/posts/${post.id}/comments`, {
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
            setComments([...comments, newComment]);
            setCommentContent("");
            setSuccessMessage("Comment posted successfully!");
            setTimeout(() => setSuccessMessage(""), 3000);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    if (loading) {
        return <p>Loading...</p>;
    }

    if (!post) {
        return <p>Post not found</p>;
    }

    return (
        <Container>
            <h2 className="my-4">{post.title}</h2>
            <p>{post.content}</p>
            {post.image_url && <img src={post.image_url} alt={post.title} className="img-fluid mb-4" />}
            
            <hr />
            <h3>Comments</h3>
            {comments.length > 0 ? (
                <ul>
                    {comments.map(comment => (
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


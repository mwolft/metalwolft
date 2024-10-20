import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export const BlogListPage = () => {
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Función para obtener las publicaciones
        const fetchPosts = async () => {
            try {
                const response = await fetch(`${process.env.BACKEND_URL}/api/posts`);
                if (!response.ok) {
                    throw new Error('Error fetching posts');
                }
                const data = await response.json();
                setPosts(data);
                setLoading(false);
            } catch (error) {
                console.error('Error:', error);
                setLoading(false);
            }
        };

        fetchPosts();
    }, []);

    if (loading) {
        return <p>Loading...</p>;
    }

    return (
        <div style={{marginTop: '150px'}}>
            <h2>Blog</h2>
            <ul>
                {posts.map(post => (
                    <li key={post.id}>
                        <h3>{post.title}</h3>
                        <p>{post.content.substring(0, 100)}...</p> {/* Muestra un resumen del contenido */}
                        <Link to={`/blog/${post.slug}`}>Read more</Link>
                    </li>
                ))}
            </ul>
        </div>
    );
};


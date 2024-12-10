import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet";
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../../component/Breadcrumb.jsx';
import "../../../styles/blog.css";
import { Context } from '../../store/appContext';

export const BlogListPage = () => {
    const { store, actions } = useContext(Context);
    const [metaData, setMetaData] = useState({});
    const { posts, error } = store;

    useEffect(() => {
        if (!store.postsLoaded) {
            actions.loadPosts();
        }
    }, [actions, store.postsLoaded]);

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL 
            : process.env.NODE_ENV === "production"
            ? "https://api.metalwolft.com" 
            : "https://scaling-umbrella-976gwrg7664j3grx-3001.app.github.dev";    
    
        fetch(`${apiBaseUrl}/api/seo/blogs`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then((data) => setMetaData(data))
            .catch((error) => console.error("Error fetching SEO data:", error));
    }, []);

    const formatDate = (dateString) => {
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return new Date(dateString).toLocaleDateString(undefined, options);
    };

    const fetchCommentsForPost = async (postId) => {
        await actions.fetchComments(postId);
    };

    if (!store.postsLoaded) {
        return <p>Cargando...</p>;
    }

    if (error) {
        return <p>Error al cargar los posts. Por favor, inténtalo de nuevo más tarde.</p>;
    }

    if (posts.length === 0) {
        return <p>No hay posts disponibles en este momento.</p>;
    }

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
            <div className="container-fluid">
                <div className="row" style={{ margin: '8px 8px', backgroundSize: 'cover' }}>
                    {posts.map(post => (
                        <div
                            className="card-blog col-12 col-sm-12 col-md-4 col-lg-4 col-xl-4 mb-4"
                            key={post.id}
                            onMouseEnter={() => fetchCommentsForPost(post.id)}>
                            <img
                                src={post.image_url}
                                alt={post.title}
                                className="img-blog img-fluid w-100"
                                style={{ objectFit: 'cover', height: '200px' }} />
                            <h2 className='h2-title-blog'>{post.title}</h2>
                            <p className='p-coments'>
                                <div className='p-comments-single'>
                                    <i className="fa-regular fa-calendar" style={{ color: '#ff324d' }}></i> {formatDate(post.created_at)}
                                </div>
                                <div className='p-comments-single'>
                                    <i className="fa-regular fa-comments" style={{ color: '#ff324d' }}></i> {store.currentComments?.filter(comment => comment.post_id === post.id).length || 0} Comentarios
                                </div>
                            </p>
                            <p className='p-content'>{post.content.substring(0, 100)}...</p>
                            <Link className="slug" to={`/${post.slug}`}>Leer más</Link>
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
};

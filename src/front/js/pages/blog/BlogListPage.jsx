import React, { useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { Breadcrumb } from '../../component/Breadcrumb.jsx';
import "../../../styles/blog.css";
import { Context } from '../../store/appContext';

export const BlogListPage = () => {
    const { store, actions } = useContext(Context);
    const { posts, error } = store;

    useEffect(() => {
        if (!store.postsLoaded) {
            actions.loadPosts();
        }
    }, [actions, store.postsLoaded]);

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
            <Breadcrumb />
            <div className="container-fluid">
                <div className="row" style={{ margin: '8px 8px', backgroundSize: 'cover'}}>
                    {posts.map(post => (
                        <div 
                            className="card-blog col-12 col-sm-12 col-md-4 col-lg-4 col-xl-4 mb-4" 
                            key={post.id}
                            onMouseEnter={() => fetchCommentsForPost(post.id)}>
                            <img
                                src={post.image_url}
                                alt={post.title}
                                className="img-blog img-fluid w-100"
                                style={{ objectFit: 'cover', height: '200px' }}/>
                            <h2 className='h2-title-blog'>{post.title}</h2>
                            <p className='p-coments'>
                                <div className='p-comments-single'>
                                    <i className="fa-regular fa-calendar" style={{ color: '#ff324d'}}></i> {formatDate(post.created_at)}
                                </div>
                                <div className='p-comments-single'>
                                    <i className="fa-regular fa-comments" style={{ color: '#ff324d'}}></i> {store.currentComments?.filter(comment => comment.post_id === post.id).length || 0} Comentarios
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

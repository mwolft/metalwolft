import React, { useEffect, useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Context } from "../store/appContext.js";
import "../../styles/categories-pages.css";

export const AsidePost = ({ currentPostId }) => {
    const { store, actions } = useContext(Context);
    const [recentPosts, setRecentPosts] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchRecentPosts = async () => {
            const posts = await actions.getRecentPosts();
            setRecentPosts(posts.filter(post => post.id !== currentPostId)); // Excluir el post actual
        };
        fetchRecentPosts();
    }, [currentPostId]);

    const handlePostNavigation = (postSlug) => {
        navigate(`/${postSlug}`);
    };

    return (
        <aside className="widget my-5">
            <p className="widget_title"><b>Posts Recientes</b></p>
            <hr className="hr-home" />
            {recentPosts.length > 0 ? (
                <ul className="widget_categories">
                    {recentPosts.map((post, index) => (
                        <li key={index} className="others-categories">
                            <img 
                                className="img-other-categories" 
                                src={post.image_url} 
                                alt={post.title} 
                            />
                            <p className="p-other-categories">
                                {post.title}<br />
                                <span className="other-categories-span">{post.date}</span>
                                <button 
                                    className="buton-other-categories" 
                                    onClick={() => handlePostNavigation(post.slug)}
                                    aria-label={`Leer más sobre ${post.title}`}
                                >
                                    Leer más
                                </button>
                            </p>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>Cargando posts recientes...</p>
            )}
        </aside>
    );    
};

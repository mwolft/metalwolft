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
        <div className="widget my-5">
            <h5 className="widget_title">Post Recientes</h5>
            <hr className="hr-home" />
            {recentPosts.length > 0 ? (
                recentPosts.map((post, index) => (
                    <div key={index} className="others-categories">
                        <img className="img-other-categories" src={post.image_url} alt={post.title} />
                        <p className="p-other-categories">
                            {post.title}<br />
                            <span className="other-categories-span">{post.date}</span>
                            <button 
                                className="buton-other-categories" 
                                onClick={() => handlePostNavigation(post.slug)}
                            >
                                Leer más
                            </button>
                        </p>
                    </div>
                ))
            ) : (
                <p>Cargando posts recientes...</p>
            )}
        </div>
    );
};

import React, { useEffect } from "react";
import "../../styles/profile.css";
import { Link } from "react-router-dom";

export const Sidebar = () => {

    useEffect(() => {
        const sidebarToggle = document.getElementById('sidebarCollapse');
        const sidebar = document.getElementById('sidebar');
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
        return () => {
            sidebarToggle.removeEventListener('click', () => {
                sidebar.classList.toggle('active');
            });
        };
    }, []);

    return (
        <>
            <nav id="sidebar" className="pt-5">
                <ul className="list-unstyled components">
                    <li><Link to="/profile"><i className="fa-regular fa-user"></i> Tu perfil</Link></li>
                    <li><Link to="/nutrition-plan"><i className="fa-solid fa-chart-line"></i> Plan de nutrición</Link></li>
                    <li><Link to="/routines"><i className="fa-solid fa-dumbbell"></i> Tus rutinas</Link></li>
                    <li><Link to="/routines"><i className="fa-solid fa-fire-burner"></i> Tus recetas</Link></li>
                </ul>
            </nav>
        </>
    );
};

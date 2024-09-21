import React, { useEffect } from "react";
import fitnessImage from "../../img/fitness.jpg";
import "../../styles/index.css";
import "../../styles/home.css";
import { Carrusel } from "../component/Carrusel.jsx";
import { BodyHomeMain } from "../component/BodyHomeMain.jsx";
import { BodyHomeSecondary } from "../component/BodyHomeSecondary.jsx";
import { useNavigate } from "react-router-dom";

export const Home = () => {
    const navigate = useNavigate();

    useEffect(() => {
        const handleScroll = () => {
            const sections = document.querySelectorAll(".section");
            sections.forEach(section => {
                const sectionTop = section.getBoundingClientRect().top;
                if (sectionTop < window.innerHeight - 40) {
                    section.classList.add("section-visible");
                } else {
                    section.classList.remove("section-visible");
                }
            });
        };
        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    
    const handleSignUp = () => {
        navigate("/login"); 
    };

    return (
        <div>
            <Carrusel />
            <section className="section">
                <BodyHomeMain />
            </section>
            <section className="section">
                <BodyHomeSecondary />
            </section>
        </div>
    );
};



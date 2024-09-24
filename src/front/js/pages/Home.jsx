import React, { useEffect } from "react";
import "../../styles/index.css";
import "../../styles/home.css";
import { Carrusel } from "../component/Carrusel.jsx";
import { BodyHomeMain } from "../component/BodyHomeMain.jsx";
import { BodyHomeSecondary } from "../component/BodyHomeSecondary.jsx";
import { useNavigate } from "react-router-dom";
import { BodyHomeTertiary } from "../component/BodyHomeTertiary.jsx";
import { BodyHomeQuarter } from "../component/BodyHomeQuarter.jsx";
import { CardsCarrusel } from "../component/CardsCarrusel.jsx";

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
            <section className="section">
                <BodyHomeTertiary />
            </section>
            <section className="section">
                <BodyHomeQuarter />
            </section>
            <section className="section">
                <CardsCarrusel />
            </section>
        </div>
    );
};



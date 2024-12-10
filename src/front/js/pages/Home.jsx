import React, { useEffect } from "react";
import "../../styles/index.css";
import "../../styles/home.css";
import { Carrusel } from "../component/Carrusel.jsx";
import { BodyHomeMain } from "../component/BodyHomeMain.jsx";
import { BodyHomeSecondary } from "../component/BodyHomeSecondary.jsx";
import { useNavigate } from "react-router-dom";
import { BodyHomeTertiary } from "../component/BodyHomeTertiary.jsx";
import { BodyHomeQuarter } from "../component/BodyHomeQuarter.jsx";
// import { CardsCarrusel } from "../component/CardsCarrusel.jsx";

export const Home = () => {
    const navigate = useNavigate();

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("section-visible");
                    } else {
                        entry.target.classList.remove("section-visible");
                    }
                });
            },
            { threshold: 0.3 } // Ajusta este valor para definir cuándo se considera visible.
        );

        const sections = document.querySelectorAll(".section");
        sections.forEach(section => observer.observe(section));

        return () => observer.disconnect(); // Limpia el observador cuando el componente se desmonta.
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
            {/*<section className="section">
                <CardsCarrusel />
            </section>*/}
        </div>
    );
};

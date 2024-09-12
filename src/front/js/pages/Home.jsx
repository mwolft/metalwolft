import React, { useEffect } from "react";
import fitnessImage from "../../img/fitness.jpg";
import "../../styles/home.css";
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
                if (sectionTop < window.innerHeight - 150) {
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
            <header className="container-fluid d-flex align-items-end text-center background-image" style={{backgroundImage: `url(${fitnessImage})`}}>
                <div className="row py-5 m-auto">
                    <div className="col-lg-12 col-md-12">
                        <h1 className="h1-home">ES FÁCIL SER FIT</h1>
                        <p>
                            <button className="btn btn-color-yellow btn-lg px-5" onClick={handleSignUp}>
                                Regístrate
                            </button>
                        </p>
                    </div>
                </div>
            </header>
            <section className="section">
                <BodyHomeMain />
            </section>
            <section className="section">
                <BodyHomeSecondary />
            </section>
        </div>
    );
};

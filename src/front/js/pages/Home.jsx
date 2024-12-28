import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet";
import "../../styles/index.css";
import "../../styles/home.css";
import { Carrusel } from "../component/Carrusel.jsx";
import { BodyHomeMain } from "../component/BodyHomeMain.jsx";
import { BodyHomeSecondary } from "../component/BodyHomeSecondary.jsx";
import { useNavigate } from "react-router-dom";
import { BodyHomeTertiary } from "../component/BodyHomeTertiary.jsx";
import { BodyHomeQuarter } from "../component/BodyHomeQuarter.jsx";
import { Contact } from "./Contact.jsx";
// import { CardsCarrusel } from "../component/CardsCarrusel.jsx";

export const Home = () => {
    const navigate = useNavigate();
    const [metaData, setMetaData] = useState({});
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
            { threshold: 0.3 }
        );
        const sections = document.querySelectorAll(".section");
        sections.forEach(section => observer.observe(section));
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        const apiBaseUrl = process.env.REACT_APP_BACKEND_URL
            ? process.env.REACT_APP_BACKEND_URL
            : process.env.NODE_ENV === "production"
                ? "https://api.metalwolft.com"
                : "https://scaling-umbrella-976gwrg7664j3grx-3001.app.github.dev";

        fetch(`${apiBaseUrl}/api/seo/home`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then((data) => setMetaData(data))
            .catch((error) => console.error("Error fetching SEO data:", error));
    }, []);

    const handleSignUp = () => {
        navigate("/login");
    };

    return (
        <div>
            <Helmet>
                {/* Título y Descripción */}
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="keywords" content={metaData.keywords} />

                {/* Robots */}
                <meta name="robots" content={metaData.robots || "index, follow"} />

                {/* Theme Color */}
                <meta name="theme-color" content={metaData.theme_color || "#ffffff"} />

                {/* Open Graph Meta Tags */}
                <meta property="og:type" content={metaData.og_type || "website"} />
                <meta property="og:title" content={metaData.title} />
                <meta property="og:description" content={metaData.description} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:image:width" content={metaData.og_image_width || "1200"} />
                <meta property="og:image:height" content={metaData.og_image_height || "630"} />
                <meta property="og:image:alt" content={metaData.og_image_alt || "Carpintería metálica"} />
                <meta property="og:image:type" content={metaData.og_image_type || "image/jpeg"} />
                <meta property="og:url" content={metaData.og_url} />
                <meta property="og:site_name" content={metaData.og_site_name || "Metal Wolft"} />
                <meta property="og:locale" content={metaData.og_locale || "es_ES"} />
                <meta property="og:updated_time" content={metaData.og_updated_time || "2024-12-10T12:00:00"} />

                {/* Canonical */}
                <link rel="canonical" href={metaData.canonical} />

                {/* JSON-LD Schema */}
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            <Carrusel />
            <section className="section">
                <BodyHomeMain />
            </section>
            <section className="section">
                <BodyHomeSecondary />
            </section>
            <section className="section">
                <BodyHomeQuarter />
            </section>
            <section className="section">
                <Contact />
            </section>
            {/*<section className="section">
                <CardsCarrusel />
            </section>*/}
        </div>
    );
};

import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import injectContext from "./store/appContext.js";
// Custom components
import { Alert } from "./component/Alert.jsx";
import ScrollToTop from "./component/ScrollToTop.jsx";
import { BackendURL } from "./component/BackendURL.jsx";
import { Footer } from "./component/Footer.jsx";
import { MainNavbar } from "./component/MainNavbar.jsx";
import { Sidebar } from "./component/Sidebar.jsx";
import { BodyHomeMain } from "./component/BodyHomeMain.jsx";
import { BodyHomeSecondary } from "./component/BodyHomeSecondary.jsx";
import { BodyHomeTertiary } from "./component/BodyHomeTertiary.jsx";
import { BodyHomeQuarter } from "./component/BodyHomeQuarter.jsx";
import { CardsCarrusel } from "./component/CardsCarrusel.jsx";
import { Carrusel } from "./component/Carrusel.jsx";
// Custom pages
import { Home } from "./pages/Home.jsx";
import { Error404 } from "./pages/Error404.jsx";
import { Login } from "./pages/Login.jsx";
import { Profile } from "./pages/Profile.jsx";

// Create your first component
const Layout = () => {
    // The basename is used when your project is published in a subdirectory and not in the root of the domain
    // you can set the basename on the .env file located at the root of this project, E.g: BASENAME=/react-hello-webapp/
    const basename = process.env.BASENAME || "";
    if(!process.env.BACKEND_URL || process.env.BACKEND_URL == "") return <BackendURL/ >;

    return (
        <div className="d-flex flex-column min-vh-100 bg-light">
            <BrowserRouter basename={basename}>
                <ScrollToTop />
                    <MainNavbar />
                    <Routes>
                        <Route element={<Home />} path="/" />
                        <Route element={<Carrusel />} path='/carrusel' />
                        <Route element={<Error404/>} path='*'/>
                        <Route element={<Login />} path='/login' />
                        <Route element={<BodyHomeMain />} path='/body-home-main' />
                        <Route element={<BodyHomeSecondary />} path='/body-home-secondary' />
                        <Route element={<BodyHomeTertiary />} path='/body-home-tertiary' />
                        <Route element={<BodyHomeQuarter />} path='/body-home-quarter' />
                        <Route element={<CardsCarrusel />} path="/cards-carrusel" />
                        <Route element={<Sidebar />} path='/Sidebar' />
                        <Route element={<Profile />} path='/Profile' />
                    </Routes>
                    <Footer />
            </BrowserRouter>
        </div>
    );
};

export default injectContext(Layout);


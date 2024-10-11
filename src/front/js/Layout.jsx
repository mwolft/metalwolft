import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import injectContext from "./store/appContext.js";

// Custom components
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
import { Breadcrumb } from "./component/Breadcrumb.jsx";
import { Product } from "./component/Product.jsx";
import { Notification } from "./component/Notification.jsx";
import { AsideCategories } from "./component/AsideCategories.jsx";
import CheckoutForm from "./component/CheckoutForm.jsx";
import PayPalButton from "./component/PayPalButton.jsx";

// Custom pages
import { Home } from "./pages/Home.jsx";
import { Error404 } from "./pages/Error404.jsx";
import { Login } from "./pages/Login.jsx";
import { Profile } from "./pages/Profile.jsx";
import AdminPanel from "./pages/AdminPanel.jsx"; 
import { Favoritos } from "./pages/Favoritos.jsx";
import { ProductDetail } from "./pages/ProductDetail.jsx";
import { Cart } from "./pages/Cart.jsx";
import { ThankYou } from "./pages/ThankYou.jsx";
 
// Custom categories
import { RejasParaVentanas } from "./pages/categories/RejasParaVentanas.jsx";

const Layout = () => {
    const basename = process.env.BASENAME || "";
    if (!process.env.BACKEND_URL || process.env.BACKEND_URL === "") return <BackendURL />;

    return (
        <div className="d-flex flex-column min-vh-100 bg-white">
            <BrowserRouter basename={basename}>
                <ScrollToTop />
                <MainNavbar />
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/carrusel" element={<Carrusel />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/admin/*" element={<AdminPanel />} /> 
                    <Route path="/body-home-main" element={<BodyHomeMain />} />
                    <Route path="/body-home-secondary" element={<BodyHomeSecondary />} />
                    <Route path="/body-home-tertiary" element={<BodyHomeTertiary />} />
                    <Route path="/body-home-quarter" element={<BodyHomeQuarter />} />
                    <Route path="/product" element={<Product />} />
                    <Route path="/favoritos" element={<Favoritos />} />
                    <Route path="/product/:id" element={<ProductDetail />} />
                    <Route path="/cart" element={<Cart />} />
                    <Route path="/checkout-form" element={<CheckoutForm />} />
                    <Route path="/thank-you" element={<ThankYou />} />
                    <Route path="/paypal-button" element={<PayPalButton />} />
                    <Route path="/notification" element={<Notification />} />
                    <Route path="/cards-carrusel" element={<CardsCarrusel />} />
                    <Route path="/sidebar" element={<Sidebar />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="/aside-categories" element={<AsideCategories />} />
                    <Route path="/breadcrumb" element={<Breadcrumb />} />
                    <Route path="/rejas-para-ventanas" element={<RejasParaVentanas />} />
                    <Route path="*" element={<Error404 />} />
                </Routes>
                <Footer />
            </BrowserRouter>
        </div>
    );
};

export default injectContext(Layout);

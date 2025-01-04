import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import injectContext from "./store/appContext.js";
import { CookieBanner } from "./component/CookieBanner.jsx";
import { License } from "./pages/License.jsx";

// Custom components
import ScrollToTop from "./component/ScrollToTop.jsx";
import { BackendURL } from "./component/BackendURL.jsx";
import { Footer } from "./component/Footer.jsx";
import { MainNavbar } from "./component/MainNavbar.jsx";
import MaintenancePopup from "./component/MaintenancePopup.jsx"
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
import { AsideOthersCategories } from "./component/AsideOthersCategories.jsx";
import { AsidePost } from "./component/AsidePost.jsx";
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
import { Contact } from "./pages/Contact.jsx";
import { PrivacyCookiesHome } from "./pages/PrivacyCookiesHome.jsx";
import { PrivacyPolicy } from "./pages/PrivacyPolicy.jsx";
import { CookiesPolicy } from "./pages/CookiesPolicy.jsx";
import { InformationCollected } from "./pages/InformationCollected.jsx";
import { ChangesInCookiePolicy } from "./pages/ChangesInCookiePolicy.jsx";
import { ReturnsPolicy } from "./pages/ReturnsPolicy.jsx";
import ResetPassword from "./pages/ResetPassword.jsx"

// Blog
import { BlogListPage } from "./pages/blog/BlogListPage.jsx";
import { MedirHuecoRejasParaVentanas } from "./pages/blog/MedirHuecoRejasParaVentanas.jsx";
import { InstalationRejasParaVentanas } from "./pages/blog/InstalationRejasParaVentanas.jsx";

// Custom categories
import { RejasParaVentanas } from './pages/categories/RejasParaVentanas.jsx';
import { ValladosMetalicosExteriores } from "./pages/categories/ValladosMetalicosExteriores.jsx";
import { PuertasPeatonalesMetalicas } from "./pages/categories/PuertasPeatonalesMetalicas.jsx";
import { PuertasCorrederasInteriores } from "./pages/categories/PuertasCorrederasInteriores.jsx";
import { PuertasCorrederasExteriores } from "./pages/categories/PuertasCorrederasExteriores.jsx";
import { CerramientoDeCocinaConCristal } from "./pages/categories/CerramientoDeCocinaConCristal.jsx";

const Layout = () => {
    const basename = process.env.BASENAME || "";
    if (!process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL === "") return <BackendURL />;

    return (
        <BrowserRouter basename={basename}>
            <ScrollToTop />
            {/*<MaintenancePopup />*/}
            <CookieBanner />
            <MainNavbar />
            <div id="main-content" className="d-flex flex-column bg-white" style={{ margin: '0px', padding: '0px' }}>
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/carrusel" element={<Carrusel />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/reset-password" element={<ResetPassword />} />
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
                    <Route path="/pay-pal-button" element={<PayPalButton />} />
                    <Route path="/thank-you" element={<ThankYou />} />
                    <Route path="/contact" element={<Contact />} />
                    <Route path="/notification" element={<Notification />} />
                    <Route path="/cards-carrusel" element={<CardsCarrusel />} />
                    <Route path="/sidebar" element={<Sidebar />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="/aside-categories" element={<AsideCategories />} />
                    <Route path="/aside-otherscategories" element={<AsideOthersCategories />} />
                    <Route path="/aside-post" element={<AsidePost />} />
                    <Route path="/breadcrumb" element={<Breadcrumb />} />
                    <Route path="/rejas-para-ventanas" element={<RejasParaVentanas />} />
                    <Route path="/vallados-metalicos-exteriores" element={<ValladosMetalicosExteriores />} />
                    <Route path="/puertas-peatonales-metalicas" element={<PuertasPeatonalesMetalicas />} />
                    <Route path="/puertas-correderas-interiores" element={<PuertasCorrederasInteriores />} />
                    <Route path="/puertas-correderas-exteriores" element={<PuertasCorrederasExteriores />} />
                    <Route path="/cerramientos-de-cocina-con-cristal" element={<CerramientoDeCocinaConCristal />} />
                    <Route path="/blogs" element={<BlogListPage />} />
                    <Route path="/medir-hueco-rejas-para-ventanas" element={<MedirHuecoRejasParaVentanas />} />
                    <Route path="/instalation-rejas-para-ventanas" element={<InstalationRejasParaVentanas />} />
                    <Route path="*" element={<Error404 />} />
                    <Route path="/cookies-esenciales" element={<PrivacyCookiesHome />} />
                    <Route path="/politica-privacidad" element={<PrivacyPolicy />} />
                    <Route path="/politica-cookies" element={<CookiesPolicy />} />
                    <Route path="/informacion-recogida" element={<InformationCollected />} />
                    <Route path="/cambios-politica-cookies" element={<ChangesInCookiePolicy />} />
                    <Route path="/politica-devolucion" element={<ReturnsPolicy />} />
                    <Route path="/license" element={<License />} />
                </Routes>
                <Footer />
            </div>
        </BrowserRouter>
    );
};

export default injectContext(Layout);

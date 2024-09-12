import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import injectContext from "./store/appContext.js";
// Custom components
import { Alert } from "./component/Alert.jsx";
import ScrollToTop from "./component/ScrollToTop.jsx";
import { BackendURL } from "./component/BackendURL.jsx";
import { Footer } from "./component/Footer.jsx";
import { MainNavbar } from "./component/MainNavbar.jsx";
import { BmrCalculator } from "./component/BmrCalculator.jsx";
import { Sidebar } from "./component/Sidebar.jsx";
import { FormTrainer } from "./component/FormTrainer.jsx";
import { BodyHomeMain } from "./component/BodyHomeMain.jsx";
import { BodyHomeSecondary } from "./component/BodyHomeSecondary.jsx";
// Custom pages
import { Home } from "./pages/Home.jsx";
import { Error404 } from "./pages/Error404.jsx";
import { Login } from "./pages/Login.jsx";
import { SignUp } from "./pages/SignUp.jsx";
import { Dashboard } from "./pages/Dashboard.jsx";
import { Trainers } from './pages/Trainers.jsx';
import { Exercise } from './pages/Exercise.jsx';
import { GenerateRecipes } from "./pages/GenerateRecipes.jsx";
import { GenerateRoutines } from "./pages/GenerateRoutines.jsx";
import { Profile } from "./pages/Profile.jsx";
import { Routines } from "./pages/Routines.jsx";
import { NutritionPlan } from "./pages/NutritionPlan.jsx";

// Create your first component
const Layout = () => {
    // The basename is used when your project is published in a subdirectory and not in the root of the domain
    // you can set the basename on the .env file located at the root of this project, E.g: BASENAME=/react-hello-webapp/
    const basename = process.env.BASENAME || "";
    if(!process.env.BACKEND_URL || process.env.BACKEND_URL == "") return <BackendURL/ >;

    return (
        <div className="d-flex flex-column min-vh-100">
            <BrowserRouter basename={basename}>
                <ScrollToTop>
                    <MainNavbar />
                    <Routes>
                        <Route element={<Home />} path="/" />
                        <Route element={<Error404/>} path='*'/>
                        <Route element={<BmrCalculator />} path="/bmr-calculator" />
                        <Route element={<Trainers />} path="/trainers" />
                        <Route element={<FormTrainer />} path="/become-a-trainer" />
                        <Route element={<Login />} path='/login' />
                        <Route element={<GenerateRecipes />} path="/generate-recipes" />
                        <Route element={<GenerateRoutines />} path="/generate-routines" />
                        <Route element={<Dashboard />} path='/dashboard' />
                        <Route element={<BodyHomeMain />} path='/body-home-main' />
                        <Route element={<BodyHomeSecondary />} path='/body-home-secondary' />
                        <Route element={<Exercise />} path="/exercises" />
                        <Route element={<Sidebar />} path='/Sidebar' />
                        <Route element={<Profile />} path='/Profile' />
                        <Route element={<Routines />} path='/routines' />
                        <Route element={<NutritionPlan />} path='/nutrition-plan' />
                    </Routes>
                    <Footer />
                </ScrollToTop>
            </BrowserRouter>
        </div>
    );
};

export default injectContext(Layout);


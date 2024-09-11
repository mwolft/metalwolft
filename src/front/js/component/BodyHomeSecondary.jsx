import React from "react";
import "../../styles/home.css";
import imageBodySecondary from "../../img/app-fit.jpg";
import { useNavigate } from "react-router-dom";

export const BodyHomeSecondary = () => {
    const navigate = useNavigate();
    const handleSignUp = () => {
        navigate("/login"); 
    };

    return (
        <div className="container pt-5 text-center">
            <div className="row">
                <div className="body-secondary col-12 col-sm-12 col-md-12 col-lg-6 col-xl-6">
                    <h2 className="my-4">Es fácil ser Fit con nuestra IA trAIner</h2>
                    <p>Podrás realizar rutinas de entrenamiento y planes de nutrición en base a tus necesidades</p>
                    <p className="d-flex justify-content-center">
                        <button className="btn btn-color-yellow btn-lg px-5 py-3 my-3" onClick={handleSignUp}>
                            Regístrate
                        </button>
                    </p>
                </div>
                <div className="col-12 col-sm-12 col-md-12 col-lg-6 col-xl-6 d-flex justify-content-center mb-5">
                    <img className="img-secondary img-fluid" src={imageBodySecondary} alt="" />
                </div>
            </div>
        </div>
    );
};


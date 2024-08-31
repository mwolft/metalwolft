import React from "react";
import fitnessImage from "../../img/fitness.jpg";
import "../../styles/home.css";
import { MainNavbar } from "../component/MainNavbar.jsx";

export const Home = () => {
    return (
        <header className="container-fluid d-flex align-items-start flex-column text-center background-image p-0" style={{backgroundImage: `url(${fitnessImage})`}}>
            <div className="row py-5 my-5 p-2 m-auto">
                <div className="col-lg-12 col-md-12">
                    <h1>ES FÁCIL SER FIT</h1>
                    <p>
                        <a href="#" className="btn btn-warning btn-lg px-5">Registrate</a>
                    </p>
                </div>
            </div>
        </header>
    );
};

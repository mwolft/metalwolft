import React from "react";
import { useNavigate } from "react-router-dom";

export const Breadcrumb = () => {
    const navigate = useNavigate();
    const handleSignUp = () => {
        navigate("/login");
    };

    return (
        <div className="container-fluid breadcrumb" style={{ marginTop: '65px' }}>
            <div className="row d-flex justify-content-center">
                <div className="col-11 py-3">
                    <div className="row d-flex align-items-center">
                        <div className="col-12 col-lg-9 col-xl-9">
                            <h1 className="h1-breadcrumb">Rejas para Ventanas Modernas | Sencillas | Sin obra | Envíos Gratuítos.</h1>
                        </div>
                        <div className="col-12 col-lg-3 col-xl-3">
                            <p className="p-breadcrumb">Inicio Rejas para ventanas</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

};


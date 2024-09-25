import React from "react";
import { Breadcrumb } from "../../component/Breadcrumb.jsx"
import { Product } from "../../component/Product.jsx";
import "../../../styles/categories.css";
import { useNavigate } from "react-router-dom";

export const RejasParaVentanas = () => {
    const navigate = useNavigate();
    const handleSignUp = () => {
        navigate("/login");
    };

    return (
        <>
            <Breadcrumb />
            <div className="container">
                <div className="row">
                    <div className="col-12 col-lg-3 col-xl-3 order-2 order-sm-2 order-md-2 order-lg-1 order-xl-1">
                        <h3 className="mt-5">Categorias</h3>
                        <ul>
                            <li>Rejas</li>
                            <li>Vallados</li>
                            <li>Correderas</li>
                            <li>Peatonales</li>
                            <li>Cerramientos</li>
                        </ul>
                    </div>
                    <div className="col-12 col-lg-9 col-xl-9 order-1 order-sm-1 order-md-1 order-lg-2 order-xl-2">
                        <Product />
                    </div>
                </div>
            </div>
        </>
    );

};


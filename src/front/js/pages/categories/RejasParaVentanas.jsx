import React from "react";
import { Breadcrumb } from "../../component/Breadcrumb.jsx"
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
            </div>
        </>
    );

};


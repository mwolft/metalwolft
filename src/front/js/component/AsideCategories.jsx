import React from "react";
import { useNavigate } from "react-router-dom";

export const AsideCategories = () => {
    const navigate = useNavigate();
    const handleSignUp = () => {
        navigate("/login");
    };

    return (
        <>
            <h3 className="mt-5">Categorias</h3>
            <ul>
                <li>Rejas</li>
                <li>Vallados</li>
                <li>Correderas</li>
                <li>Peatonales</li>
                <li>Cerramientos</li>
            </ul>
        </>
    );

};


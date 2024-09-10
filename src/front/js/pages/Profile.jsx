import React, { useContext, useEffect, useState } from "react";
import { Context } from "../store/appContext.js";
import "../../styles/profile.css";
import Button from 'react-bootstrap/Button';
import { Link, useNavigate } from "react-router-dom";
import { Sidebar } from "../component/Sidebar.jsx";

export const Profile = () => {
    const { store, actions } = useContext(Context);
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        weight: store.currentUser ? store.currentUser.weight || '' : '',
        height: store.currentUser ? store.currentUser.height || '' : '',
        age: store.currentUser ? store.currentUser.age || '' : '',
        sex: store.currentUser ? store.currentUser.sex || 'male' : 'male',
    });

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const handleSave = async () => {
        const updatedData = {
            height: formData.height,
            weight: formData.weight,
            age: formData.age,
            sex: formData.sex
        };
        const response = await actions.updateUserProfile(store.currentUser.id, updatedData);
        if (response.ok) {
            alert("Perfil actualizado correctamente.");
        } else {
            alert("Error al actualizar el perfil.");
        }
    };


    return (
        !store.currentUser ?
            navigate("/login")
            :
            <div className="wrapper bg-white" style={{ marginTop: '55px' }}>
                <Sidebar />
                <div id="content" className="m-auto">
                    <nav className="navbar navbar-expand-lg">
                        <div className="container-fluid">
                            <button type="button" id="sidebarCollapse" className="btn btn-light py-2">
                                <i className="fa-solid fa-align-left px-2"></i>
                                <span> Menu</span>
                            </button>
                        </div>
                    </nav>
                    <div className="row my-2">
                        <div className="d-flex flex-column col-12 col-sm-12 col-md-12 col-lg-5 col-xl-5">
                            <i className="fa-solid fa-user fa-8x py-2 px-2"></i>
                            <h1 className="h1-profile">{store.currentUser.firstname} {store.currentUser.lastname}</h1>
                            <i className="fa-solid fa-location-dot d-flex"><h6 className="mx-2"> Sevilla, España</h6></i>
                        </div>
                        <div className="col-12 col-sm-12 col-md-12 col-lg-5 col-xl-5">
                            <form>
                                <div className="mb-3">
                                    <div className="d-flex justify-content-between">
                                        <div className="flex-fill mr-2">
                                            <label className="form-label">Peso (kg):</label>
                                            <input type="number" name="weight" className="form-control"
                                                value={formData.weight}
                                                onChange={handleInputChange} />
                                        </div>
                                        <div className="flex-fill mx-2">
                                            <label className="form-label">Altura (cm):</label>
                                            <input type="number" name="height" className="form-control"
                                                value={formData.height}
                                                onChange={handleInputChange} />
                                        </div>
                                    </div>
                                    <div className="d-flex justify-content-between mt-3">
                                        <div className="flex-fill mr-2">
                                            <label className="form-label">Edad:</label>
                                            <input type="number" name="age" className="form-control"
                                                value={formData.age}
                                                onChange={handleInputChange} />
                                        </div>
                                        <div className="flex-fill mx-2">
                                            <label className="form-label">Sexo:</label>
                                            <select name="sex" className="form-control"
                                                value={formData.sex}
                                                onChange={handleInputChange}>
                                                <option value="male">Masculino</option>
                                                <option value="female">Femenino</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div className="d-flex flex-column justify-content-beetwen mt-3">
                                    <Button className="btn-profile btn-success text-white" 
                                    onClick={handleSave}>
                                        Actualizar perfil
                                    </Button>
                                    <Button className="btn-profile btn-primary mt-2 text-white">
                                        <Link to="/nutrition-plan" className="text-white text-decoration-none">
                                            Ir a plan nutricional
                                        </Link>
                                    </Button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
    );
};


import React, { useContext, useEffect, useState } from "react";
import { Context } from "../store/appContext.js";
import "../../styles/profile.css";
import Button from 'react-bootstrap/Button';
import { useNavigate } from "react-router-dom";

export const Profile = () => {
    const { store, actions } = useContext(Context);
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        weight: store.currentUser?.weight || '',
        height: store.currentUser?.height || '',
        age: store.currentUser?.age || '',
        sex: store.currentUser?.sex || 'male'
    });

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const handleSave = async (e) => {
        e.preventDefault(); 
        const response = await actions.updateUserProfile(store.currentUser.id, formData);
        if (response.ok) {
            alert("Perfil actualizado correctamente.");
        } else {
            alert("Error al actualizar el perfil.");
        }
    };

    // SIDEBAR
    useEffect(() => {
        const sidebarToggle = document.getElementById('sidebarCollapse');
        const sidebar = document.getElementById('sidebar');

        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });

        return () => {
            sidebarToggle.removeEventListener('click', () => {
                sidebar.classList.toggle('active');
            });
        };
    }, []);

    return (
        !store.currentUser ?
            navigate("/login")
            :
            <div className="wrapper bg-white" style={{ marginTop: '55px' }}>
                <nav id="sidebar" className="pt-5">
                    <ul className="list-unstyled components">
                        <li><a href="#"><i className="fa-solid fa-chart-line"></i> Dashboard</a></li>
                        <li><a href="#"><i className="fa-regular fa-user"></i> Datos Corporales</a></li>
                        <li><a href="#"><i className="fa-solid fa-clock-rotate-left"></i> Historial</a></li>
                    </ul>
                </nav>
                <div id="content" className="m-auto">
                    <nav className="navbar navbar-expand-lg navbar-dark">
                        <div className="container-fluid">
                            <button type="button" id="sidebarCollapse" className="btn btn-light py-2">
                                <i className="fa-solid fa-align-left px-2"></i>
                                <span> Menu</span>
                            </button>
                        </div>
                    </nav>
                    <div className="row">
                        <div className="col-12 col-sm-12 col-md-12 col-lg-6 d-flex align-items-center justify-content-center">
                            <div className="cards-dashboard-profile d-flex justify-content-evenly align-items-center" style={{ width: '100%', height: '98%' }}>
                                <form onSubmit={handleSave}>
                                    <h1 className="h1-profile text-center">{store.currentUser.firstname} {store.currentUser.lastname}</h1>
                                    <div className="mb-3">
                                        <div className="d-flex justify-content-between">
                                            <div className="flex-fill mr-2">
                                                <label className="form-label">Peso (kg):</label>
                                                <input type="number" name="weight" className="form-control" value={formData.weight} onChange={handleInputChange} />
                                            </div>
                                            <div className="flex-fill mx-2">
                                                <label className="form-label">Altura (cm):</label>
                                                <input type="number" name="height" className="form-control" value={formData.height} onChange={handleInputChange} />
                                            </div>
                                        </div>
                                        <div className="d-flex justify-content-between mt-3">
                                            <div className="flex-fill mr-2">
                                                <label className="form-label">Edad:</label>
                                                <input type="number" name="age" className="form-control" value={formData.age} onChange={handleInputChange} />
                                            </div>
                                            <div className="flex-fill mx-2">
                                                <label className="form-label">Sexo:</label>
                                                <select name="sex" className="form-control" value={formData.sex} onChange={handleInputChange}>
                                                    <option value="male">Masculino</option>
                                                    <option value="female">Femenino</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                    <Button type="submit" className="btn-profile btn-success mb-2 text-white">
                                        Actualizar
                                    </Button>
                                </form>
                            </div>
                        </div>
                        <div className="col-12 col-sm-12 col-md-12 col-lg-6">
                            <div className="row">
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard">
                                        <p className="p-profile-title">TASA METABÓLICA BASAL</p>
                                        <p className="p-profile-info">Cantidad de calorías que su cuerpo necesita para realizar funciones básicas en reposo.</p>
                                        <h3 className="h3-profile"><p className="p-profile py-0"> 895 KCAL</p></h3>
                                    </div>
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard">
                                        <p className="p-profile-title">POR ACTIVIDAD FÍSICA</p>
                                        <ul className="profile-list">
                                            <li>
                                                <b>Sedentario:</b> 5254 kcal
                                            </li>
                                            <li>
                                                <b>Ligeramente activo:</b> 5825 kcal
                                            </li>
                                            <li>
                                                Moderadamente activo: 2587 kcal
                                            </li>
                                            <li>
                                                <b>Muy activo:</b> 5646 kcal
                                            </li>
                                            <li>
                                                <b>Super atlético:</b> 5487 kcal
                                            </li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div className="row">
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard">
                                        <p className="p-profile-title">PROTEINAS</p>
                                        <h3 className="h3-profile">878<p className="p-profile py-0"> GR</p></h3>
                                        <i className="fa-solid fa-drumstick-bite fa-3x d-flex justify-content-center"></i>
                                    </div>
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard-dark">
                                        <p className="p-profile-title">CARBOHIDRATOS</p>
                                        <h3 className="h3-profile">564<p className="p-profile py-0"> GR</p></h3>
                                        <i className="fa-solid fa-utensils fa-3x d-flex justify-content-center"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="row">
                        <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-3">
                            <div className="cards-dashboard-dark">
                                <p className="p-profile-title">PLANES NUTRICIONALES</p>
                                <h3 className="h3-profile">0</h3>
                                <i className="fa-solid fa-calendar-days fa-3x d-flex justify-content-center"></i>
                            </div>
                        </div>
                        <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-3">
                            <div className="cards-dashboard">
                                <p className="p-profile-title">RUTINAS DE EJERCICIOS</p>
                                <h3 className="h3-profile">0</h3>
                                <i className="fa-solid fa-dumbbell fa-3x d-flex justify-content-center"></i>
                            </div>
                        </div>
                        <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-3">
                            <div className="cards-dashboard">
                                <p className="p-profile-title">GRASAS</p>
                                <h3 className="h3-profile">465<p className="p-profile py-0"> GR</p></h3>
                                <i className="fa-solid fa-droplet fa-3x d-flex justify-content-center"></i>
                            </div>
                        </div>
                        <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-3">
                            <div className="cards-dashboard">
                                <p className="p-profile-title">AGUA</p>
                                <h3 className="h3-profile">85<p className="p-profile py-0"> GR</p></h3>
                                <i className="fa-solid fa-droplet fa-3x d-flex justify-content-center"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
    );
};


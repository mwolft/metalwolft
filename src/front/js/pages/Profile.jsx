import React, { useContext, useEffect } from "react";
import { Context } from "../store/appContext.js";
import "../../styles/profile.css";
import Button from 'react-bootstrap/Button';

export const Profile = () => {
    const { store } = useContext(Context);

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
            <Home />
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
                                <i class="fa-solid fa-align-left px-2"></i>
                                <span> Menu</span>
                            </button>
                        </div>
                    </nav>
                    <h1 className="h1-profile text-center">{store.currentUser.firstname} {store.currentUser.lastname}</h1>
                    <div className="row">
                        <div className="col-12 col-sm-12 col-md-12 col-lg-6 d-flex align-items-center justify-content-center">
                            <div className="cards-dashboard d-flex flex-column justify-content-center align-items-center" style={{ width: '100%', height: '96%' }}>
                                <i className="fa-solid fa-user fa-8x py-2"></i>
                                <p className="p-profile">Peso: --kg</p>
                                <p className="p-profile">Altura: --cm</p>
                                <p className="p-profile">Edad: 31 años</p>
                                <p className="p-profile">IMC: --</p>
                                <Button className="btn-profile" variant="primary">Calcular IMC</Button>
                                <button data-bs-toggle="modal" data-bs-target="#updateProfile" type="button" className="btn-profile btn btn-link mt-1">
                                    <i className="fa-solid fa-rotate-right"></i> Actualizar perfil
                                </button>
                            </div>
                        </div>
                        <div className="modal fade" id="updateProfile" tabindex="-1" aria-labelledby="upgradeUser" aria-hidden="true">
                            <div className="modal-dialog">
                                <div className="modal-content">
                                    <div className="modal-header">
                                        <h5 className="modal-title">Actualizar perfil</h5>
                                        <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                    </div>
                                    <div className="modal-body">
                                        <form>
                                            <div className="mb-3">
                                                <label for="recipient-name" className="col-form-label">Peso:</label>
                                                <input type="text" className="form-control" id="recipient-name" />
                                            </div>
                                            <div className="mb-3">
                                                <label for="recipient-name" className="col-form-label">Altura:</label>
                                                <input type="text" className="form-control" id="recipient-name" />
                                            </div>
                                            <div className="mb-3">
                                                <label for="recipient-name" className="col-form-label">Edad:</label>
                                                <input type="text" className="form-control" id="recipient-name" />
                                            </div>
                                        </form>
                                    </div>
                                    <div className="modal-footer">
                                        <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                        <button type="button" className="btn btn-primary">Save changes</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="col-12 col-sm-12 col-md-12 col-lg-6">
                            <div className="row">
                                <div className="col-12">
                                    <div className="cards-dashboard">
                                        <p className="p-profile">DIETA OBJETIVO</p>
                                        <h3 className="h3-profile">2205<p className="p-profile py-0"> KCAL</p></h3>
                                        <i className="fa-solid fa-flag-checkered fa-3x d-flex justify-content-center"></i>
                                    </div>
                                </div>
                            </div>
                            <div className="row">
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard">
                                        <p className="p-profile">PROTEINAS RESTANTES</p>
                                        <h3 className="h3-profile">2205<p className="p-profile py-0"> GR</p></h3>
                                        <i className="fa-solid fa-drumstick-bite fa-3x d-flex justify-content-center"></i>
                                    </div>
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard-dark">
                                        <p className="p-profile">KCAL INGERIDAS</p>
                                        <h3 className="h3-profile">0<p className="p-profile py-0"> KCAL</p></h3>
                                        <i className="fa-solid fa-utensils fa-3x d-flex justify-content-center"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="row">
                        <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-3">
                            <div className="cards-dashboard-dark">
                                <p className="p-profile">PLANES NUTRICIONALES</p>
                                <h3 className="h3-profile">0</h3>
                                <i className="fa-solid fa-calendar-days fa-3x d-flex justify-content-center"></i>
                            </div>
                        </div>
                        <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-3">
                            <div className="cards-dashboard">
                                <p className="p-profile">RUTINAS DE EJERCICIOS</p>
                                <h3 className="h3-profile">0</h3>
                                <i className="fa-solid fa-dumbbell fa-3x d-flex justify-content-center"></i>
                            </div>
                        </div>
                        <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-3">
                            <div className="cards-dashboard-dark">
                                <p className="p-profile">CARBOHIDRATOS RESTANTES</p>
                                <h3 className="h3-profile">205<p className="p-profile py-0"> GR</p></h3>
                                <i className="fa-solid fa-bread-slice fa-3x d-flex justify-content-center"></i>
                            </div>
                        </div>
                        <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-3">
                            <div className="cards-dashboard">
                                <p className="p-profile">GRASAS RESTANTES</p>
                                <h3 className="h3-profile">85<p className="p-profile py-0"> GR</p></h3>
                                <i className="fa-solid fa-droplet fa-3x d-flex justify-content-center"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
    )
}


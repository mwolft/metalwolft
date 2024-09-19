import React, { useState, useEffect, useContext } from "react";
import { Context } from "../store/appContext.js";
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import { Sidebar } from "../component/Sidebar.jsx";
import "../../styles/profile.css";
import { useNavigate, Link } from "react-router-dom";
import Card from 'react-bootstrap/Card';


export const Profile = () => {
    const { store, actions } = useContext(Context);
    const [show, setShow] = useState(false); // visibilidad del modal de la actualización del perfil
    const [showAlert, setShowAlert] = useState(false); // visibilidad del modal del alert
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        firstname: store.currentUser ? store.currentUser.firstname || '' : '',
        lastname: store.currentUser ? store.currentUser.lastname || '' : '',
        phone: store.currentUser ? store.currentUser.phone || '' : '',
        location: store.currentUser ? store.currentUser.location || '' : '',
        weight: store.currentUser ? store.currentUser.weight || '' : '',
        height: store.currentUser ? store.currentUser.height || '' : '',
        age: store.currentUser ? store.currentUser.age || '' : '',
        gender: store.currentUser ? store.currentUser.gender || 'male' : 'male', // Valor predeterminado masculino
    });


    useEffect(() => {
        if (!store.currentUser.firstname || !store.currentUser.lastname) {
            setShow(true); // Si faltan datos, mostrar el modal
        }
    }, [store.currentUser]);


    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };


    const handleSave = async () => {
        const updatedData = {
            firstname: formData.firstname,
            lastname: formData.lastname,
            phone: formData.phone,
            location: formData.location,
            height: formData.height,
            weight: formData.weight,
            age: formData.age,
            sex: formData.sex
        };
        const response = await actions.updateUserProfile(store.currentUser.id, updatedData);
        if (response.ok) {
            setShow(false); // Cerrar el modal de edición
            setShowAlert(true); // Mostrar el modal de alerta
        } else {
            alert("Error al actualizar el perfil.");
        }
    };


    return (
        !store.currentUser ?
            navigate("/login")
            :
            <div className="wrapper bg-dark text-white" style={{ marginTop: '55px' }}>
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
                    <div className="row my-2 justify-content-center">
                        <div className="col-12 col-sm-12 col-md-8 col-lg-6 col-xl-5 border-warning">
                            <Card border="light" className="py-5">
                                <div className="d-flex flex-column align-items-center text-center">
                                    <i className="fa-solid fa-user fa-8x py-2 px-2"></i>
                                    <h1 className="h1-profile">{store.currentUser.firstname} {store.currentUser.lastname}</h1>
                                    <ul className="w-100" style={{ maxWidth: "300px", textAlign: "left" }}>
                                        <li className="li-profile d-flex align-items-center">
                                            <i className="fa-solid fa-location-dot me-2" style={{ width: "20px", textAlign: "center" }}></i>
                                            <span>Ubicación: {store.currentUser.location}</span>
                                        </li>
                                        <li className="li-profile d-flex align-items-center">
                                            <i className="fa-solid fa-arrows-up-down me-2" style={{ width: "20px", textAlign: "center" }}></i>
                                            <span>Altura: {store.currentUser.height} cm</span>
                                        </li>
                                        <li className="li-profile d-flex align-items-center">
                                            <i className="fa-solid fa-weight-scale me-2" style={{ width: "20px", textAlign: "center" }}></i>
                                            <span>Peso: {store.currentUser.weight} kg</span>
                                        </li>
                                        <li className="li-profile d-flex align-items-center">
                                            <i className="fa-solid fa-calendar-check me-2" style={{ width: "20px", textAlign: "center" }}></i>
                                            <span>Edad: {store.currentUser.age} años</span>
                                        </li>
                                    </ul>
                                    <Button className="btn btn-primary mt-4" onClick={() => setShow(true)}>
                                        Actualizar perfil
                                    </Button>
                                </div>
                            </Card>
                        </div>
                        <div className="col-12 col-sm-12 col-md-4 col-lg-4 col-xl-3">
                            <div className="d-flex flex-column align-items-center text-center mt-5">
                                <span>¿Eres entrenador?</span>
                                <Button className="mt-1" variant="link" as={Link} to="/form-trainer">
                                    Contáctanos
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
                {/* Modal de primer registro o actualizar el perfil*/}
                <Modal show={show} onHide={() => setShow(false)} backdrop="static" keyboard={false}>
                    <Modal.Header closeButton>
                        <Modal.Title>Completa o actualiza tu perfil</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        <form>
                            <div className="mb-3 row">
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <label className="form-label">Nombre:</label>
                                    <input type="text" name="firstname" className="form-control"
                                        value={formData.firstname}
                                        onChange={handleInputChange} />
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <label className="form-label">Apellidos:</label>
                                    <input type="text" name="lastname" className="form-control"
                                        value={formData.lastname}
                                        onChange={handleInputChange} />
                                </div>
                            </div>
                            <div className="mb-3 row">
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <label className="form-label">Teléfono:</label>
                                    <input type="tel" name="phone" className="form-control"
                                        value={formData.phone}
                                        onChange={handleInputChange} />
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <label className="form-label">Localización:</label>
                                    <input type="text" name="location" className="form-control"
                                        value={formData.location}
                                        onChange={handleInputChange} />
                                </div>
                            </div>
                            <div className="mb-3 row">
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <label className="form-label">Peso (kg):</label>
                                    <input type="number" name="weight" className="form-control"
                                        value={formData.weight}
                                        onChange={handleInputChange} />
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <label className="form-label">Altura (cm):</label>
                                    <input type="number" name="height" className="form-control"
                                        value={formData.height}
                                        onChange={handleInputChange} />
                                </div>
                            </div>
                            <div className="mb-3 row">
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <label className="form-label">Edad:</label>
                                    <input type="number" name="age" className="form-control"
                                        value={formData.age}
                                        onChange={handleInputChange} />
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <label className="form-label">Sexo:</label>
                                    <select name="sex" className="form-control"
                                        value={formData.sex}
                                        onChange={handleInputChange}>
                                        <option value="male">Masculino</option>
                                        <option value="female">Femenino</option>
                                    </select>
                                </div>
                            </div>
                        </form>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={() => setShow(false)}>
                            Cancelar
                        </Button>
                        <Button variant="primary" onClick={handleSave}>
                            Guardar
                        </Button>
                    </Modal.Footer>
                </Modal>
                {/* Modal del alert cuando completa o actualiza el perfil*/}
                <Modal show={showAlert} onHide={() => setShowAlert(false)} backdrop="static" keyboard={false}>
                    <Modal.Header closeButton>
                        <Modal.Title>Perfil actualizado correctamente</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>
                        <p>Obten un plan nutricional haciendo clic en el siguiente botón.</p>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="primary" as={Link} to="/nutrition-plan">
                            Ir al plan nutricional
                        </Button>
                    </Modal.Footer>
                </Modal>
            </div>
    );
};







import React, { useContext, useState, useRef } from "react";
import { Context } from "../store/appContext.js";
import "../../styles/profile.css";
import Button from 'react-bootstrap/Button';
import { Sidebar } from "../component/Sidebar.jsx";
import { Link, useNavigate } from "react-router-dom";


export const NutritionPlan = () => {
    const { store } = useContext(Context);
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        objective: 'maintenance',
        bmr: null,
        calories: null,
        selectedCalories: null,
        protein: null,
        carbs: null,
        fats: null
    });


    const macronutrientSectionRef = useRef(null);
    const infoSectionRef = useRef(null);
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };


    const calculateBMR = (e) => {
        e.preventDefault();  
        const { sex, age, height, weight } = store.currentUser;
        if (!age || !height || !weight) {
            alert("Por favor, ingresa todos los datos necesarios en el perfil.");
            return;
        }
        let calculatedBMR;
        const heightInCm = parseFloat(height);
        const weightInKg = parseFloat(weight);
        const ageValue = parseInt(age);
        if (sex === 'male') {
            calculatedBMR = 88.362 + (13.397 * weightInKg) + (4.799 * heightInCm) - (5.677 * ageValue);
        } else {
            calculatedBMR = 447.593 + (9.247 * weightInKg) + (3.098 * heightInCm) - (4.330 * ageValue);
        }
        const calorieNeeds = {
            BMR: calculatedBMR.toFixed(2),
            Sedentary: (calculatedBMR * 1.2).toFixed(0),
            "Lightly active": (calculatedBMR * 1.375).toFixed(0),
            "Moderately active": (calculatedBMR * 1.55).toFixed(0),
            "Highly active": (calculatedBMR * 1.725).toFixed(0),
            "Super athletic": (calculatedBMR * 1.9).toFixed(0)
        };
    

        setFormData({ ...formData, bmr: calorieNeeds.BMR, calories: calorieNeeds });

        
        setTimeout(() => {
            const position = infoSectionRef.current.getBoundingClientRect().top + window.scrollY - 50; 
            window.scrollTo({
                top: position,
                behavior: 'smooth'
            });
        }, 300);
    };
    

    const handleActivitySelection = (calories) => {
        const totalCalories = parseInt(calories);
        const protein = (totalCalories * 0.3 / 4).toFixed(2);
        const carbs = (totalCalories * 0.4 / 4).toFixed(2);
        const fats = (totalCalories * 0.3 / 9).toFixed(2);
        setFormData({
            ...formData,
            selectedCalories: totalCalories,
            protein,
            carbs,
            fats
        });
        macronutrientSectionRef.current.scrollIntoView({ behavior: 'smooth' });
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
                    <h1 className="h1-profile">Plan Nutricional</h1>
                    <p>Calcula tu Tasa Metabólica Basal y elige la cantidad de actividad que vas a realizar para obtener el porcentaje de macronutrientes recomendados</p>
                    <form onSubmit={calculateBMR}> 
                        <div className="mt-3">
                            <label className="form-label">Objetivo:</label>
                            <select
                                name="objective"
                                className="form-control"
                                value={formData.objective}
                                onChange={handleInputChange}>
                                <option value="maintenance">Mantenimiento</option>
                                <option value="weight_loss">Pérdida de peso</option>
                                <option value="muscle_gain">Ganancia muscular</option>
                            </select>
                        </div>
                        <Button ref={infoSectionRef} type="submit" className="text-white btn btn-outline-primary btn-sm mx-1 mt-3">
                            Calcular
                        </Button>
                    </form>
                    {formData.bmr && (
                        <div className="mt-4">
                            <div className="row">
                                <div className="col-12">
                                    <div className="alert alert-info" role="alert">
                                        <u>Elige la actividad física</u>&nbsp;que vas a realizar para obtener los macronutrientes recomendados para tu objetivo.
                                    </div>
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard">
                                        <p className="p-profile-title">TU TASA METABÓLICA BASAL:</p>
                                        <p className="p-profile-info">Cantidad de calorías que su cuerpo necesita para realizar funciones básicas en reposo, tales como respirar, parpadear, filtrar la sangre, regular la temperatura del cuerpo o sintetizar hormonas.</p>
                                        <h3 className="h3-profile">{formData.bmr} <p className="p-profile py-0"> KCAL</p></h3>
                                    </div>
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard">
                                        <p className="p-profile-title">ACTIVIDAD FÍSICA</p>
                                        <ul className="profile-list">
                                            <li className="d-flex justify-content-between">
                                                <b style={{ width: "33%", textAlign: "left" }} className="m-auto">Sedentario:</b>
                                                <b style={{ width: "33%", textAlign: "center" }} className="m-auto">{formData.calories.Sedentary} kcal</b>
                                                <a style={{ width: "33%", textAlign: "center" }} className="ml-2 choose-activity m-auto"
                                                    onClick={() => handleActivitySelection(formData.calories.Sedentary)}> Elegir
                                                </a>
                                            </li>
                                            <li className="d-flex justify-content-between">
                                                <b style={{ width: "33%", textAlign: "left" }} className="m-auto">Ligeramente:</b>
                                                <b style={{ width: "33%", textAlign: "center" }} className="m-auto">{formData.calories["Lightly active"]} kcal</b>
                                                <a style={{ width: "33%", textAlign: "center" }} className="ml-2 choose-activity m-auto"
                                                    onClick={() => handleActivitySelection(formData.calories["Lightly active"])}> Elegir
                                                </a>
                                            </li>
                                            <li className="d-flex justify-content-between">
                                                <b style={{ width: "33%", textAlign: "left" }} className="m-auto">Moderadamente:</b>
                                                <b style={{ width: "33%", textAlign: "center" }} className="m-auto">{formData.calories["Moderately active"]} kcal</b>
                                                <a style={{ width: "33%", textAlign: "center" }} className="ml-2 choose-activity m-auto"
                                                    onClick={() => handleActivitySelection(formData.calories["Moderately active"])}> Elegir
                                                </a>
                                            </li>
                                            <li className="d-flex justify-content-between">
                                                <b style={{ width: "33%", textAlign: "left" }} className="m-auto">Muy activo:</b>
                                                <b style={{ width: "33%", textAlign: "center" }} className="m-auto">{formData.calories["Highly active"]} kcal</b>
                                                <a style={{ width: "33%", textAlign: "center" }} className="ml-2 choose-activity m-auto"
                                                    onClick={() => handleActivitySelection(formData.calories["Highly active"])}> Elegir
                                                </a>
                                            </li>
                                            <li className="d-flex justify-content-between">
                                                <b style={{ width: "33%", textAlign: "left" }} className="m-auto">Atlético:</b>
                                                <b style={{ width: "33%", textAlign: "center" }} className="m-auto">{formData.calories["Super athletic"]} kcal</b>
                                                <a  ref={macronutrientSectionRef} style={{ width: "33%", textAlign: "center" }} className="ml-2 choose-activity m-auto"
                                                    onClick={() => handleActivitySelection(formData.calories["Super athletic"])}> Elegir
                                                </a>
                                            </li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div className="row mt-4">
                                <div className="col-12">
                                    <div className="alert alert-info" role="alert">
                                        Tus macronutrientes personalizados para potenciar tu rendimiento y lograr tus metas.
                                    </div>
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard">
                                        <p className="p-profile-title">PROTEINAS</p>
                                        <h3 className="h3-profile">{formData.protein} <p className="p-profile py-0"> GR</p></h3>
                                        <i className="fa-solid fa-drumstick-bite fa-3x d-flex justify-content-center"></i>
                                    </div>
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard">
                                        <p className="p-profile-title">CARBOHIDRATOS</p>
                                        <h3 className="h3-profile">{formData.carbs} <p className="p-profile py-0"> GR</p></h3>
                                        <i className="fa-solid fa-utensils fa-3x d-flex justify-content-center"></i>
                                    </div>
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard">
                                        <p className="p-profile-title">GRASAS</p>
                                        <h3 className="h3-profile">{formData.fats} <p className="p-profile py-0"> GR</p></h3>
                                        <i className="fa-solid fa-droplet fa-3x d-flex justify-content-center"></i>
                                    </div>
                                </div>
                                <div className="col-12 col-sm-12 col-md-6 col-lg-6 col-xl-6">
                                    <div className="cards-dashboard">
                                        <p className="p-profile-info">Obten un plan de ejercicios personalizados con nuestra TrAIner</p>
                                        <Link to="/generate-routines" className="btn btn-primary mt-2 text-white text-decoration-none">
                                            Crear
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
    );
};

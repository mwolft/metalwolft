import React, { useContext, useEffect, useState } from "react";
import { Context } from "../store/appContext.js";
import "../../styles/profile.css";
import Button from 'react-bootstrap/Button';
import { useNavigate } from "react-router-dom";
import { Sidebar } from "../component/Sidebar.jsx";

export const Routines = () => {
    const { store, actions } = useContext(Context);
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        weight: store.currentUser ? store.currentUser.weight || '' : '',
        height: store.currentUser ? store.currentUser.height || '' : '',
        age: store.currentUser ? store.currentUser.age || '' : '',
        sex: store.currentUser ? store.currentUser.sex || 'male' : 'male',
        objective: 'maintenance',  
        bmr: null,
        calories: null,
        selectedCalories: null,
        protein: null,
        carbs: null,
        fats: null
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
            sex: formData.sex,
            objective: formData.objective 
        };
        const response = await actions.updateUserProfile(store.currentUser.id, updatedData);
        if (response.ok) {
            alert("Perfil actualizado correctamente.");
        } else {
            alert("Error al actualizar el perfil.");
        }
    };

    const calculateBMR = () => {
        const { sex, age, height, weight } = formData;
        if (!age || !height || !weight) {
            alert("Por favor, ingresa todos los datos necesarios.");
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
    };


    return (
        !store.currentUser ?
            navigate("/login")
            :
            <div className="wrapper bg-white" style={{ marginTop: '55px' }}>
                <Sidebar/>
                <div id="content" className="m-auto">
                    <nav className="navbar navbar-expand-lg">
                        <div className="container-fluid">
                            <button type="button" id="sidebarCollapse" className="btn btn-light py-2">
                                <i className="fa-solid fa-align-left px-2"></i>
                                <span> Menu</span>
                            </button>
                        </div>
                    </nav>
                    <h1 className="h1-profile text-center">{store.currentUser.firstname} {store.currentUser.lastname}</h1>
                    <div className="row">
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
                    </div>
                </div>
            </div>
        </div>
    );
};
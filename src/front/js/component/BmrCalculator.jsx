import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const BmrCalculator = () => {
    const [sex, setSex] = useState('male');
    const [age, setAge] = useState('');
    const [height, setHeight] = useState('');
    const [weight, setWeight] = useState('');
    const [heightUnit, setHeightUnit] = useState('cm');
    const [weightUnit, setWeightUnit] = useState('kg');
    const navigate = useNavigate();
    const [bmr, setBmr] = useState(null);
    const [calories, setCalories] = useState(null);

    const handleConvert = () => {
        let heightInCm = heightUnit === 'feet' ? height * 30.48 : height;
        let weightInKg = weightUnit === 'lbs' ? weight * 0.453592 : weight;

        let calculatedBMR;

        if (sex === 'male') {
            calculatedBMR = 88.362 + (13.397 * weightInKg) + (4.799 * heightInCm) - (5.677 * age);
        } else {
            calculatedBMR = 447.593 + (9.247 * weightInKg) + (3.098 * heightInCm) - (4.330 * age);
        }

        setBmr(calculatedBMR.toFixed(2));

        const calorieNeeds = {
            BMR: calculatedBMR.toFixed(2),
            "Sedentario": (calculatedBMR * 1.2).toFixed(0),
            "Ligeramente activo": (calculatedBMR * 1.375).toFixed(0),
            "Moderadamente activo": (calculatedBMR * 1.55).toFixed(0),
            "Muy activo": (calculatedBMR * 1.725).toFixed(0),
            "Súper atlético": (calculatedBMR * 1.9).toFixed(0)
        };

        navigate('/profile', { state: { calorieNeeds } });
    };

    return (
        <div className="row mt-5">
            <div className="container mt-5">
                <div className="card p-4 bg-dark text-light">
                    <h2 className="mb-4 text-center text-warning">CALCULADORA BMR</h2>
                    <div className="d-flex justify-content-between mb-3">
                        <button
                            className={`btn ${sex === 'male' ? 'btn-warning' : 'btn-outline-warning'} flex-fill`}
                            onClick={() => setSex('male')}
                        >
                            Hombre
                        </button>
                        <button
                            className={`btn ${sex === 'female' ? 'btn-warning' : 'btn-outline-warning'} flex-fill ms-2`}
                            onClick={() => setSex('female')}
                        >
                            Mujer
                        </button>
                    </div>
                    <div className="form-group mb-3">
                        <label className="text-warning">Edad:</label>
                        <input
                            type="number"
                            className="form-control bg-dark text-light border-warning"
                            value={age}
                            onChange={(e) => setAge(e.target.value)}
                            placeholder="Introduce tu edad"
                        />
                    </div>
                    <div className="form-group mb-3">
                        <label className="text-warning">Altura:</label>
                        <div className="d-flex">
                            <input
                                type="number"
                                className="form-control bg-dark text-light border-warning"
                                value={height}
                                onChange={(e) => setHeight(e.target.value)}
                                placeholder="Introduce tu altura"
                            />
                            <div className="btn-group ml-2">
                                <button
                                    className={`btn ${heightUnit === 'cm' ? 'btn-warning' : 'btn-outline-warning'}`}
                                    onClick={() => setHeightUnit('cm')}
                                >
                                    cm
                                </button>
                                <button
                                    className={`btn ${heightUnit === 'feet' ? 'btn-warning' : 'btn-outline-warning'}`}
                                    onClick={() => setHeightUnit('feet')}
                                >
                                    Pies
                                </button>
                            </div>
                        </div>
                    </div>
                    <div className="form-group mb-3">
                        <label className="text-warning">Peso:</label>
                        <div className="d-flex">
                            <input
                                type="number"
                                className="form-control bg-dark text-light border-warning"
                                value={weight}
                                onChange={(e) => setWeight(e.target.value)}
                                placeholder="Introduce tu peso"
                            />
                            <div className="btn-group ml-2 ms-2">
                                <button
                                    className={`btn ${weightUnit === 'kg' ? 'btn-warning' : 'btn-outline-warning'}`}
                                    onClick={() => setWeightUnit('kg')}
                                >
                                    kg
                                </button>
                                <button
                                    className={`btn ${weightUnit === 'lbs' ? 'btn-warning' : 'btn-outline-warning'}`}
                                    onClick={() => setWeightUnit('lbs')}
                                >
                                    lbs
                                </button>
                            </div>
                        </div>
                    </div>
                    <button className="btn btn-warning btn-block mt-4" onClick={handleConvert}>
                        Convertir
                    </button>
                </div>
            </div>
        </div>
    );
};
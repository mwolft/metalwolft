import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const BmrCalculator = () => {
    const [sex, setSex] = useState('male');
    const [age, setAge] = useState('');
    const [height, setHeight] = useState('');
    const [weight, setWeight] = useState('');
    const [heightUnit, setHeightUnit] = useState('cm');
    const [weightUnit, setWeightUnit] = useState('kg');
    const [bmr, setBmr] = useState(null);
    const [calories, setCalories] = useState(null);
    const navigate = useNavigate();

    const handleAgeChange = (e) => {
        let inputAge = parseInt(e.target.value);
        if (inputAge > 90) inputAge = 90;
        if (inputAge < 1) inputAge = 1;
        setAge(inputAge);
    };

    const handleWeightChange = (e) => {
        let inputWeight = parseFloat(e.target.value);
        if (weightUnit === 'lbs') {
            const maxWeightInLbs = 500 * 2.20462;
            if (inputWeight > maxWeightInLbs) inputWeight = maxWeightInLbs;
            if (inputWeight < 1) inputWeight = 1;
        } else {
            if (inputWeight > 500) inputWeight = 500;
            if (inputWeight < 1) inputWeight = 1;
        }
        setWeight(inputWeight);
    };

    const handleHeightChange = (e) => {
        let inputHeight = parseFloat(e.target.value);
        if (heightUnit === 'feet') {
            if (inputHeight > 9.84) inputHeight = 9.84;
        } else {
            if (inputHeight > 300) inputHeight = 300;
        }
        if (inputHeight < 0) inputHeight = 0;
        setHeight(inputHeight);
    };

    const handleConvert = () => {
        if (height <= 0) {
            alert("Por favor, introduce una altura válida.");
            return;
        }

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

        setCalories(calorieNeeds);
    };

    return (
        <div className="container-fluid" style={{ backgroundColor: '#D3D3D3', minHeight: '100vh', paddingTop: '30px', paddingBottom: '30px' }}>
            <br />
            <div className="row justify-content-center mt-5">
                <div className="col-12 col-md-8 col-lg-6">
                    <div className="card p-4 bg-dark text-light">
                        
                        <h2 className="mb-5 text-center text-warning">CALCULADORA BMR</h2>
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
                                onChange={handleAgeChange}
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
                                    onChange={handleHeightChange}
                                    placeholder="Introduce tu altura"
                                    min="0"
                                />
                                <div className="btn-group ml-2 ms-2">
                                    <button
                                        className={`btn ${heightUnit === 'cm' ? 'btn-warning' : 'btn-outline-warning'}`}
                                        onClick={() => setHeightUnit('cm')}
                                        style={{ width: '75px' }}
                                    >
                                        cm
                                    </button>
                                    <button
                                        className={`btn ${heightUnit === 'feet' ? 'btn-warning' : 'btn-outline-warning'}`}
                                        onClick={() => setHeightUnit('feet')}
                                        style={{ width: '75px' }}
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
                                    onChange={handleWeightChange}
                                    placeholder="Introduce tu peso"
                                    min="0"
                                />
                                <div className="btn-group ml-2 ms-2">
                                    <button
                                        className={`btn ${weightUnit === 'kg' ? 'btn-warning' : 'btn-outline-warning'}`}
                                        onClick={() => setWeightUnit('kg')}
                                        style={{ width: '75px' }}
                                    >
                                        kg
                                    </button>
                                    <button
                                        className={`btn ${weightUnit === 'lbs' ? 'btn-warning' : 'btn-outline-warning'}`}
                                        onClick={() => setWeightUnit('lbs')}
                                        style={{ width: '75px' }}
                                    >
                                        lbs
                                    </button>
                                </div>
                            </div>
                        </div>
                        <button className="btn btn-warning btn-block mt-4" onClick={handleConvert}>
                            Convertir
                        </button>

                        {bmr && calories && (
                            <div className="mt-4">
                                <h4 className="text-warning text-center">Resultados:</h4>
                                <table className="table table-dark table-bordered text-center">
                                    <thead>
                                        <tr>
                                            <th>Tipo</th>
                                            <th>Calorías (kcal/día)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>BMR (Tasa Metabólica Basal)</td>
                                            <td>{bmr}</td>
                                        </tr>
                                        <tr>
                                            <td>Sedentario</td>
                                            <td>{calories["Sedentario"]}</td>
                                        </tr>
                                        <tr>
                                            <td>Ligeramente activo</td>
                                            <td>{calories["Ligeramente activo"]}</td>
                                        </tr>
                                        <tr>
                                            <td>Moderadamente activo</td>
                                            <td>{calories["Moderadamente activo"]}</td>
                                        </tr>
                                        <tr>
                                            <td>Muy activo</td>
                                            <td>{calories["Muy activo"]}</td>
                                        </tr>
                                        <tr>
                                            <td>Súper atlético</td>
                                            <td>{calories["Súper atlético"]}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
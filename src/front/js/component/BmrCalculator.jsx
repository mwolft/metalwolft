import React, { useState } from 'react';

export const BmrCalculator = () => {
    const [sex, setSex] = useState('male');
    const [age, setAge] = useState('');
    const [height, setHeight] = useState('');
    const [weight, setWeight] = useState('');
    const [heightUnit, setHeightUnit] = useState('cm');
    const [weightUnit, setWeightUnit] = useState('kg');
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
            Sedentary: (calculatedBMR * 1.2).toFixed(0),
            "Lightly active": (calculatedBMR * 1.375).toFixed(0),
            "Moderately active": (calculatedBMR * 1.55).toFixed(0),
            "Highly active": (calculatedBMR * 1.725).toFixed(0),
            "Super athletic": (calculatedBMR * 1.9).toFixed(0)
        };

        setCalories(calorieNeeds);
    };

    return (
        <div style={{ backgroundColor: '#d3d3d3', height: 'auto' }}>
            <div className="row">
                <div className="container mt-5"></div>
                <div className="container d-flex justify-content-center my-5">
                    <div className="card p-3" style={{ backgroundColor: '#FFFACD', color: 'black', maxWidth: '1200px', width: '100%' }}>
                        <h2 className="mb-4 text-center text-black">BMR Calculator</h2>
                        <div className="d-flex justify-content-between mb-3">
                            <button
                                className={`btn ${sex === 'male' ? 'btn-warning' : 'btn-outline-warning'} flex-fill me-2`}
                                onClick={() => setSex('male')}
                            >
                                Male
                            </button>
                            <button
                                className={`btn ${sex === 'female' ? 'btn-warning' : 'btn-outline-warning'} flex-fill`}
                                onClick={() => setSex('female')}
                            >
                                Female
                            </button>
                        </div>
                        <div className="form-group mb-3">
                            <label className="text-black">Age:</label>
                            <input
                                type="number"
                                className="form-control border-warning"
                                value={age}
                                onChange={(e) => setAge(e.target.value)}
                                placeholder="Enter your age"
                            />
                        </div>
                        <div className="form-group mb-3">
                            <label className="text-black">Height:</label>
                            <div className="d-flex">
                                <input
                                    type="number"
                                    className="form-control border-warning me-2"
                                    value={height}
                                    onChange={(e) => setHeight(e.target.value)}
                                    placeholder="Enter your height"
                                />
                                <div className="btn-group ml-2" style={{ width: '150px' }}> 
                                    <button
                                        className={`btn ${heightUnit === 'cm' ? 'btn-warning' : 'btn-outline-warning'} w-50`} 
                                        onClick={() => setHeightUnit('cm')}
                                    >
                                        cm
                                    </button>
                                    <button
                                        className={`btn ${heightUnit === 'feet' ? 'btn-warning' : 'btn-outline-warning'} w-50`}
                                        onClick={() => setHeightUnit('feet')}
                                    >
                                        Feet
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div className="form-group mb-3">
                            <label className="text-black">Weight:</label>
                            <div className="d-flex">
                                <input
                                    type="number"
                                    className="form-control border-warning me-2"
                                    value={weight}
                                    onChange={(e) => setWeight(e.target.value)}
                                    placeholder="Enter your weight"
                                />
                                <div className="btn-group ml-2" style={{ width: '150px' }}>
                                    <button
                                        className={`btn ${weightUnit === 'kg' ? 'btn-warning' : 'btn-outline-warning'} w-50`}
                                    >
                                        kg
                                    </button>
                                    <button
                                        className={`btn ${weightUnit === 'lbs' ? 'btn-warning' : 'btn-outline-warning'} w-50`}
                                        onClick={() => setWeightUnit('lbs')}
                                    >
                                        lbs
                                    </button>
                                </div>
                            </div>
                        </div>
                        <button className="btn btn-warning btn-block mt-4" onClick={handleConvert}>
                            Convert
                        </button>
                        {bmr && (
                            <div className="mt-4">
                                <h4 className="text-center text-black">Your BMR: {bmr} kcal/day</h4>
                                <table className="table mt-3 table-striped border-warning">
                                    <thead>
                                        <tr>
                                            <th className="text-black">Activity Level</th>
                                            <th className="text-black">Calories</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {Object.keys(calories).map((level, index) => (
                                            <tr key={index}>
                                                <td>{level}</td>
                                                <td>{calories[level]}</td>
                                            </tr>
                                        ))}
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
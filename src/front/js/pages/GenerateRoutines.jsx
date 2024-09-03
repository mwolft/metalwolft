import React, { useState, useContext } from 'react';
import { Context } from '../store/appContext';
import Select from 'react-select';

export const GenerateRoutines = () => {
    const { store, actions } = useContext(Context);
    const [routineData, setRoutineData] = useState({
        days: [],
        hours_per_day: '',
        target_muscles: [],
        level: ''
    });

    const daysOptions = [
        { value: "Monday", label: "Monday" },
        { value: "Tuesday", label: "Tuesday" },
        { value: "Wednesday", label: "Wednesday" },
        { value: "Thursday", label: "Thursday" },
        { value: "Friday", label: "Friday" },
        { value: "Saturday", label: "Saturday" },
        { value: "Sunday", label: "Sunday" }
    ];

    const muscles = [
        { value: "chest", label: "Chest" },
        { value: "back", label: "Back" },
        { value: "biceps", label: "Biceps" },
        { value: "triceps", label: "Triceps" },
        { value: "shoulders", label: "Shoulders" },
        { value: "legs", label: "Legs" }
    ];

    const levels = [
        { value: "beginner", label: "Beginner" },
        { value: "intermediate", label: "Intermediate" },
        { value: "advanced", label: "Advanced" }
    ];

    const handleGenerateRoutine = () => {
        actions.clearError();
        actions.generateRoutine({
            ...routineData,
            days: routineData.days.map(option => option.value),
            target_muscles: routineData.target_muscles.map(option => option.value)
        });
    };

    return (
        <div className="container my-5">
            <h2>Generate an Exercise Routine</h2>
            <div className="mb-3">
                <Select
                    isMulti
                    options={daysOptions}
                    value={routineData.days}
                    onChange={(selectedOptions) => setRoutineData({ ...routineData, days: selectedOptions })}
                    className="mb-2"
                    placeholder="Select days"
                />

                <input
                    type="text"
                    className="form-control mb-2"
                    placeholder="Hours per day"
                    value={routineData.hours_per_day}
                    onChange={(e) => setRoutineData({ ...routineData, hours_per_day: e.target.value })}
                />
                
                <Select
                    isMulti
                    options={muscles}
                    value={routineData.target_muscles}
                    onChange={(selectedOptions) => setRoutineData({ ...routineData, target_muscles: selectedOptions })}
                    className="mb-2"
                    placeholder="Select target muscles"
                />

                <Select
                    options={levels}
                    value={levels.find(option => option.value === routineData.level)}
                    onChange={(selectedOption) => setRoutineData({ ...routineData, level: selectedOption.value })}
                    className="mb-2"
                    placeholder="Select level"
                />
                
                <button onClick={handleGenerateRoutine} className="btn btn-primary mt-3">Generate Routine</button>
            </div>
            {store.generatedRoutine && (
                <div className="alert alert-success mt-3">
                    <h3>Generated Routine</h3>
                    <div className="routine-content" dangerouslySetInnerHTML={{ __html: formatRoutine(store.generatedRoutine) }} />
                </div>
            )}
            {store.error && (
                <div className="alert alert-danger mt-3">
                    {store.error}
                </div>
            )}
        </div>
    );
};

// Helper function to format the routine
const formatRoutine = (routine) => {
    return routine
        .replace(/\*\*(.*?)\*\*/g, '<h4>$1</h4>')  // Convert **Day 1: Back and Triceps** to <h4>Day 1: Back and Triceps</h4>
        .replace(/\*(.*?)\*/g, '<li>$1</li>')  // Convert * Warm-up (10 minutes): to <li>Warm-up (10 minutes):</li>
        .replace(/(\d+\.\s)/g, '<br /><strong>$1</strong>')  // Convert 1. Warm-up to <br /><strong>1. Warm-up</strong>
        .replace(/<br \/>/g, '')  // Remove extra <br />
        .replace(/-\s/g, '• ')  // Convert * to bullet points
        .replace(/\n/g, '<br />');  // Convert newlines to <br />
};
import React, { useEffect, useState, useMemo } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';

export const Exercise = () => {
  const [selectedMuscle, setSelectedMuscle] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch exercises when a muscle group is selected
  useEffect(() => {
    if (selectedMuscle) {
      fetchExercises(selectedMuscle);
    }
  }, [selectedMuscle]);

  const fetchExercises = async (muscleGroup) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${process.env.BACKEND_URL}/api/exercises?muscle_group=${muscleGroup}`, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch exercises for ${muscleGroup}. Status: ${response.status}`);
      }

      const data = await response.json();
      setExercises(data);

      const showErrorForMuscles = [
        'pecho', 'espalda', 'hombros', 'biceps', 'triceps',
        'cuadriceps', 'femorales', 'pantorrillas', 'gluteos'
      ];

      if (data.length === 0 && showErrorForMuscles.includes(muscleGroup)) {
        setError(`No exercises found for ${muscleGroup}.`);
      }
    } catch (error) {
      console.error('Error fetching exercises:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const muscleGroups = useMemo(() => [
    'pecho', 'espalda', 'hombros', 'biceps', 'triceps', 'piernas'
  ], []);

  // List of sub-categories for legs
  const legMuscleGroups = useMemo(() => [
    'cuadriceps', 'femorales', 'pantorrillas', 'gluteos'
  ], []);

  return (
    <div className="container-fluid" style={{ backgroundColor: '#D3D3D3', minHeight: '100vh', paddingTop: '50px', paddingBottom: '50px' }}>
      <br />
      <h2 className="text-center my-5 display-4">SELECCIONA UN GRUPO MUSCULAR</h2>
      <div className="d-flex justify-content-center flex-wrap mb-4">
        {muscleGroups.map(muscle => (
          <button
            key={muscle}
            className="btn btn-warning m-2 px-4 py-2"
            onClick={() => setSelectedMuscle(muscle)}
          >
            {muscle.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Sub-category for Legs */}
      {selectedMuscle === 'piernas' && (
        <div className="text-center mb-4">
          <h3 className="display-6">SELECCIONA LA SUB-CATEGORÍA</h3>
          <div className="d-flex justify-content-center flex-wrap">
            {legMuscleGroups.map(subMuscle => (
              <button
                key={subMuscle}
                className="btn btn-warning m-2 px-4 py-2"
                onClick={() => setSelectedMuscle(subMuscle)}
              >
                {subMuscle.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Display loading status */}
      {loading && <div className="text-center"><div className="spinner-border text-dark" role="status"><span className="sr-only">Loading...</span></div></div>}

      {/* Display error message for specified muscles */}
      {error && <p className="text-danger text-center">{error}</p>}

      {/* Display exercises if no error */}
      {!loading && !error && exercises.length > 0 && (
        <div className="container">
          <h3 className="text-center display-6">Ejercicios para {selectedMuscle === 'piernas' ? 'Piernas - ' : ''}{selectedMuscle.toUpperCase()}</h3>
          <div className="row">
            {exercises.map(exercise => (
              <div key={exercise.name} className="col-lg-4 col-md-6 col-sm-12 mb-4">
                <div className="card h-100 d-flex flex-column justify-content-between">
                  <div>
                    <img
                      src={exercise.image_url || '/path/to/placeholder.jpg'}
                      className="card-img-top img-fluid"  // Ensures responsiveness of image
                      alt={exercise.name}
                      style={{ height: '200px', objectFit: 'contain' }}  // Use 'contain' to prevent cutting the image
                    />
                  </div>
                  <div className="card-body d-flex flex-column justify-content-end">
                    <h5 className="card-title">{exercise.name}</h5>
                    <p className="card-text" style={{ fontSize: '1.1rem' }}> {/* Adjusted font size for the description */}
                      {exercise.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && !selectedMuscle && (
        <p className="text-center">CADA GRUPO MUSCULAR CONTIENE EJERCICIOS CON IMÁGENES EXPLICATIVAS.</p>
      )}
    </div>
  );
};
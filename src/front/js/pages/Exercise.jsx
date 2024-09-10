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

  // Function to fetch exercises for a specific muscle group
  const fetchExercises = async (muscleGroup) => {
    setLoading(true);
    setError(null); // Reset error before fetching
    try {
      const response = await fetch(`${process.env.BACKEND_URL}/api/exercises?muscle_group=${muscleGroup}`, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
      });

      // If response is not OK, throw an error
      if (!response.ok) {
        throw new Error(`Failed to fetch exercises for ${muscleGroup}. Status: ${response.status}`);
      }

      const data = await response.json();
      setExercises(data);

      // Only show an error for specific muscle groups and subcategories
      const showErrorForMuscles = [
        'chest', 'back', 'shoulders', 'biceps', 'triceps', 
        'quads', 'hamstrings', 'calves', 'glutes'
      ];
      
      if (data.length === 0 && showErrorForMuscles.includes(muscleGroup)) {
        setError(`No exercises found for ${muscleGroup}.`);
      }
    } catch (error) {
      console.error('Error fetching exercises:', error);
      setError(error.message); // Only set error for failed requests, not empty data
    } finally {
      setLoading(false);
    }
  };

  // List of main muscle groups
  const muscleGroups = useMemo(() => [
    'chest', 'back', 'shoulders', 'biceps', 'triceps', 'legs'
  ], []);

  // List of sub-categories for legs
  const legMuscleGroups = useMemo(() => [
    'quads', 'hamstrings', 'calves', 'glutes'
  ], []);

  return (
    <div className="container-fluid bg-secondary py-5">
      <h2 className="text-center mb-4 text-white">Select a Muscle Group</h2>
      <div className="d-flex justify-content-center flex-wrap mb-4">
        {muscleGroups.map(muscle => (
          <button 
            key={muscle} 
            className="btn btn-warning m-2" 
            onClick={() => setSelectedMuscle(muscle)}
          >
            {muscle.charAt(0).toUpperCase() + muscle.slice(1)}
          </button>
        ))}
      </div>

      {/* Sub-category for Legs */}
      {selectedMuscle === 'legs' && (
        <div className="text-center mb-4">
          <h3 className="text-white">Select a Leg Sub-Category</h3>
          <div className="d-flex justify-content-center flex-wrap">
            {legMuscleGroups.map(subMuscle => (
              <button 
                key={subMuscle} 
                className="btn btn-warning m-2" 
                onClick={() => setSelectedMuscle(subMuscle)}
              >
                {subMuscle.charAt(0).toUpperCase() + subMuscle.slice(1)}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Display loading status */}
      {loading && <div className="text-center"><div className="spinner-border text-light" role="status"><span className="sr-only">Loading...</span></div></div>}

      {/* Display error message for specified muscles */}
      {error && <p className="text-danger text-center">{error}</p>}

      {/* Display exercises if no error */}
      {!loading && !error && exercises.length > 0 && (
        <div className="container">
          <h3 className="text-center text-white">Exercises for {selectedMuscle === 'legs' ? 'Legs - ' : ''}{selectedMuscle.charAt(0).toUpperCase() + selectedMuscle.slice(1)}</h3>
          <div className="row">
            {exercises.map(exercise => (
              <div key={exercise.name} className="col-lg-4 col-md-6 col-sm-12 mb-4">
                <div className="card h-100">
                  <img src={exercise.image_url || '/path/to/placeholder.jpg'} className="card-img-top" alt={exercise.name} />
                  <div className="card-body">
                    <h5 className="card-title">{exercise.name}</h5>
                    <p className="card-text" style={{ fontSize: '0.9rem' }}>{exercise.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Message for when no muscle is selected */}
      {!loading && !selectedMuscle && (
        <p className="text-center text-white">Please select a muscle group to view exercises.</p>
      )}
    </div>
  );
};
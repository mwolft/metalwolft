const getState = ({ getStore, getActions, setStore }) => {
    return {
        store: {
            message: null,
            currentUser: null,
            isLoged: false,
            alert: { visible: false, back: 'danger', text: 'Mensaje del back' },
            generatedRecipe: null,
            recipeId: null,  // Added to store the generated recipe ID
            generatedRoutine: null,
            routineId: null,  // Added to store the generated routine ID
            favoriteRecipes: [],
            favoriteRoutines: [],
            error: null,
            loading: false
        },
        actions: {
            getMessage: async () => {
                const options = {
                    headers: { 'Content-Type': 'application/json' },
                    method: 'GET'
                };
                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/hello`, options);
                    if (!response.ok) throw new Error("Error loading message from backend");
                    const data = await response.json();
                    setStore({ message: data.message });
                    return data;
                } catch (error) {
                    setStore({ error: error.message });
                }
            },

			setCurrentUser: (user) => {
				setStore({ currentUser: user });
			},
			updateUserProfile: async (userId, updatedData) => {
                const store = getStore();
                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/users/${userId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}` 
                        },
                        body: JSON.stringify(updatedData)
                    });
                    if (!response.ok) throw new Error("Error al actualizar el perfil");

                    const data = await response.json();
                    setStore({ currentUser: data.results }); 
                    return { ok: true };
                } catch (error) {
                    setStore({ error: error.message });
                    return { ok: false };
                }
            },
			setIsLoged: (isLogin) => {
				if (isLogin) {
					setStore({ isLoged: true });
				} else {
					setStore({ isLoged: false });
					localStorage.removeItem("token");
					localStorage.removeItem("user");
				}
			},

            setAlert: (newAlert) => {
                setStore({ alert: newAlert });
            },

            // Generate an exercise routine
            generateRoutine: async (routineData) => {
                setStore({ loading: true, generatedRoutine: null, routineId: null, error: null });
                const url = `${process.env.BACKEND_URL}/api/generate-exercise-routine`;
                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                        body: JSON.stringify(routineData)
                    });
                    if (!response.ok) throw new Error('Registrate para poder acceder al trAIner');
                    const data = await response.json();
                    setStore({ generatedRoutine: data.generated_routine, routineId: data.routine_id, error: null, loading: false });
                } catch (error) {
                    setStore({ error: error.message, loading: false });
                }
            },

            // Generate a recipe
            generateRecipe: async (ingredientNames) => {
                if (!ingredientNames.trim()) {
                    setStore({ error: 'Tienes que agregar al menos un ingrediente', loading: false });
                    return;
                }
                setStore({ loading: true, generatedRecipe: null, recipeId: null, error: null });
                const url = `${process.env.BACKEND_URL}/api/generate-recipe?ingredient_names=${encodeURIComponent(ingredientNames)}`;
                try {
                    const response = await fetch(url, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                    });
                    if (!response.ok) throw new Error('Registrate para poder acceder al trAIner');
                    const data = await response.json();
                    setStore({ generatedRecipe: data.generated_recipe, recipeId: data.recipe_id, error: null, loading: false }); 
                } catch (error) {
                    setStore({ error: error.message, loading: false });
                }
            },

            // Add a recipe to favorites
            addFavoriteRecipe: async (recipeId) => {
                const url = `${process.env.BACKEND_URL}/api/favorite-recipe`;
                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('token')}`  // Send JWT token for authorization
                        },
                        body: JSON.stringify({ recipe_id: recipeId }),  // Ensure the body contains the recipe_id
                        mode: 'cors'  // Ensure mode is 'cors' for cross-origin requests
                    });
            
                    if (!response.ok) throw new Error('Failed to add recipe to favorites');
                    const data = await response.json();
                    setStore({ message: data.message });
            
                } catch (error) {
                    setStore({ error: error.message });
                }
            },

            // Add a routine to favorites
            addFavoriteRoutine: async (routineId) => {
                const url = `${process.env.BACKEND_URL}/api/favorite-routine`;
                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                        body: JSON.stringify({ routine_id: routineId })
                    });
                    if (!response.ok) throw new Error('Failed to add routine to favorites');
                    const data = await response.json();
                    setStore({ message: data.message });

                } catch (error) {
                    setStore({ error: error.message });
                }
            },

            // Fetch favorite recipes and routines
            fetchFavorites: async () => {
                const token = localStorage.getItem('token');
                if (!token) {
                    setStore({ error: "User not logged in" });
                    return;
                }

                const url = `${process.env.BACKEND_URL}/api/favorites`;
                try {
                    const response = await fetch(url, {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    if (!response.ok) throw new Error('Failed to fetch favorites');
                    const data = await response.json();
                    setStore({ favoriteRecipes: data.recipes, favoriteRoutines: data.routines });
                } catch (error) {
                    setStore({ error: error.message });
                }
            },

            // Remove a recipe from favorites
            deleteFavoriteRecipe: async (recipeId) => {
                const token = localStorage.getItem('token');
                if (!token) {
                    alert('Please log in to remove this recipe from your favorites');
                    return;
                }

                const url = `${process.env.BACKEND_URL}/api/favorite-recipe/${recipeId}`;
                try {
                    const response = await fetch(url, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    if (!response.ok) throw new Error('Failed to remove recipe from favorites');
                    const data = await response.json();
                    setStore({ message: data.message });

                    // Fetch updated favorites
                    getActions().fetchFavorites();
                } catch (error) {
                    setStore({ error: error.message });
                }
            },

            // Remove a routine from favorites
            deleteFavoriteRoutine: async (routineId) => {
                const token = localStorage.getItem('token');
                if (!token) {
                    alert('Please log in to remove this routine from your favorites');
                    return;
                }

                const url = `${process.env.BACKEND_URL}/api/favorite-routine/${routineId}`;
                try {
                    const response = await fetch(url, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    if (!response.ok) throw new Error('Failed to remove routine from favorites');
                    const data = await response.json();
                    setStore({ message: data.message });

                    // Fetch updated favorites
                    getActions().fetchFavorites();
                } catch (error) {
                    setStore({ error: error.message });
                }
            },

            // Clear errors
            clearError: () => {
                setStore({ error: null, loading: false });
            }
        }
    };
};

export default getState;
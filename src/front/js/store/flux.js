const getState = ({ getStore, getActions, setStore }) => {
	return {
		store: {
			message: null,
			currentUser: null,
			isLoged: false,
			alert: { visible: false, back: 'danger', text: 'Mensaje del back' },
			generatedRecipe: null,
			generatedRoutine: null,
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
					console.log(error);
				}
			},

			setCurrentUser: (user) => {
				setStore({ currentUser: user });
			},
			updateUserProfile: async (userId, updatedData) => {
                const store = getStore();
                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/users/${userId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}` 
                        },
                        body: JSON.stringify(updatedData)
                    });
                    if (!response.ok) throw new Error("Error al actualizar el perfil");

                    const data = await response.json();
                    setStore({ currentUser: data.user }); 
                    return { ok: true };
                } catch (error) {
                    console.error("Error en updateUserProfile: ", error);
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

			generateRoutine: async (routineData) => {
				setStore({ loading: true, generatedRoutine: null, error: null });
				const url = `${process.env.BACKEND_URL}/api/generate-exercise-routine`;
				try {
					const response = await fetch(url, {
						method: 'POST',
						headers: {
							'Content-Type': 'application/json',
						},
						body: JSON.stringify(routineData)
					});
					if (!response.ok) throw new Error('Failed to generate routine');
					const data = await response.json();
					setStore({ generatedRoutine: data.generated_routine, error: null, loading: false });
				} catch (error) {
					setStore({ error: error.message, loading: false });
				}
			},

			// Action to generate a recipe
			generateRecipe: async (ingredientNames) => {
				setStore({ loading: true, generatedRecipe: null, error: null });
				const url = `${process.env.BACKEND_URL}/api/generate-recipe?ingredient_names=${encodeURIComponent(ingredientNames)}`;
				try {
					const response = await fetch(url, {
						method: 'GET',
						headers: {
							'Content-Type': 'application/json',
						},
					});
					if (!response.ok) throw new Error('Failed to generate recipe');
					const data = await response.json();
					setStore({ generatedRecipe: data.generated_recipe, error: null, loading: false });
				} catch (error) {
					setStore({ error: error.message, loading: false });
				}
			},

			clearError: () => {
				setStore({ error: null, loading: false });
			}
		}
	};
};

export default getState;
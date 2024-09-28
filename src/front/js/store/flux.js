const getState = ({ getStore, getActions, setStore }) => {
    return {
        store: {
            message: null,
            currentUser: null,
            isLoged: false,
            isAdmin: false,  // Nuevo campo para indicar si el usuario es administrador
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
                setStore({
                    currentUser: user,
                    isAdmin: user?.is_admin || false // Actualizar el estado de administrador según el usuario
                });
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
                    setStore({ isLoged: false, isAdmin: false });  // Restablecer isAdmin al cerrar sesión
                    localStorage.removeItem("token");
                    localStorage.removeItem("user");
                }
            },

            setIsAdmin: (isAdmin) => {
                setStore({ isAdmin });
            },

            setAlert: (newAlert) => {
                setStore({ alert: newAlert });
            }
        }
    };
};

export default getState;

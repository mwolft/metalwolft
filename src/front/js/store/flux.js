const getState = ({ getStore, getActions, setStore }) => {
    return {
        store: {
            message: null,
            currentUser: null,
            isLoged: false,
            isAdmin: false,  // Campo para indicar si el usuario es administrador
            alert: { visible: false, back: 'danger', text: 'Mensaje del back' },
            generatedRecipe: null,
            recipeId: null,  // ID de receta generada
            generatedRoutine: null,
            routineId: null,  // ID de rutina generada
            favoriteRecipes: [],
            favoriteRoutines: [],
            error: null,
            loading: false,
            orders: [],  // Lista de órdenes
            orderDetails: [],  // Lista de detalles de órdenes
            products: []  // Lista de productos
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
                    isAdmin: user?.is_admin || false  // Actualizar el estado de administrador según el usuario
                });
            },
            updateUserProfile: async (userId, updatedData) => {
                const store = getStore(); // Corrección: Agregar esta línea para obtener el estado actual
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
                    setStore({ isLoged: false, isAdmin: false });
                    localStorage.removeItem("token");
                    localStorage.removeItem("user");
                }
            },
            setIsAdmin: (isAdmin) => {
                setStore({ isAdmin });
            },
            setAlert: (newAlert) => {
                setStore({ alert: newAlert });
            },
            fetchOrders: async () => {
                const store = getStore(); // Corrección: Agregar esta línea para obtener el estado actual
                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/orders`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        }
                    });
                    if (!response.ok) throw new Error("Error al obtener las órdenes");

                    const data = await response.json();
                    setStore({ orders: data });
                    return { ok: true };
                } catch (error) {
                    setStore({ error: error.message });
                    return { ok: false };
                }
            },
            fetchOrderDetails: async () => {
                const store = getStore(); // Corrección: Agregar esta línea para obtener el estado actual
                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/orderdetails`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        }
                    });
                    if (!response.ok) throw new Error("Error al obtener los detalles de las órdenes");

                    const data = await response.json();
                    setStore({ orderDetails: data });
                    return { ok: true };
                } catch (error) {
                    setStore({ error: error.message });
                    return { ok: false };
                }
            },
            fetchProducts: async () => {
                const store = getStore(); // Corrección: Agregar esta línea para obtener el estado actual
                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/products`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        }
                    });
                    if (!response.ok) throw new Error("Error al obtener productos");

                    const data = await response.json();
                    setStore({ products: data });
                } catch (error) {
                    setStore({ error: error.message });
                }
            }
        }
    };
};

export default getState;

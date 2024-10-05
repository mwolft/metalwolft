const getState = ({ getStore, getActions, setStore }) => {
    return {
        store: {
            message: null,
            currentUser: null,
            isLoged: false,
            isAdmin: false,  
            alert: { visible: false, back: 'danger', text: 'Mensaje del back' },
            error: null,
            loading: false,
            products: [],  
            favorites: [],
            orders: [],  
            orderDetails: [],
            cart: []
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
                    isAdmin: user?.is_admin || false
                });
                // Cargar los favoritos y el carrito del usuario al iniciar sesión
                getActions().loadFavorites();
                getActions().loadCart();
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
            clearCart: () => {
                setStore({ cart: [] });
            },
            setIsLoged: (isLogin) => {
                if (isLogin) {
                    setStore({ isLoged: true });
                } else {
                    setStore({ isLoged: false, isAdmin: false, favorites: [] }); // Resetear los favoritos al desloguearse
                    getActions().clearCart(); // Vaciar el carrito al cerrar sesión
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
                const store = getStore(); 
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
            },
            loadFavorites: async () => {
                const store = getStore();
                if (!store.isLoged) return; // Solo cargar si el usuario está logueado

                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/favorites`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        }
                    });
                    if (!response.ok) throw new Error("Error al cargar los favoritos");

                    const data = await response.json();
                    setStore({ favorites: data });
                } catch (error) {
                    console.error("Error al cargar los favoritos:", error);
                }
            },
            addFavorite: async (product) => {
                const store = getStore();
                if (!store.isLoged) {
                    console.error("Debe estar logueado para añadir favoritos");
                    return;
                }

                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/favorites`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        },
                        body: JSON.stringify({ product_id: product.id })
                    });

                    if (!response.ok) {
                        const data = await response.json();
                        console.error("Error al añadir a favoritos:", data.message);
                        return;
                    }

                    setStore({ favorites: [...store.favorites, product] });
                } catch (error) {
                    console.error("Error al añadir a favoritos:", error);
                }
            },
            removeFavorite: async (productId) => {
                const store = getStore();
                if (!store.isLoged) {
                    console.error("Debe estar logueado para eliminar favoritos");
                    return;
                }

                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/favorites/${productId}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        }
                    });

                    if (!response.ok) {
                        const data = await response.json();
                        console.error("Error al eliminar de favoritos:", data.message);
                        return;
                    }

                    setStore({ favorites: store.favorites.filter(product => product.id !== productId) });
                } catch (error) {
                    console.error("Error al eliminar de favoritos:", error);
                }
            },
            isFavorite: (product) => {
                const store = getStore();
                return store.favorites.some(favorite => favorite.id === product.id);
            },
            loadCart: async () => {
                const store = getStore();
                if (!store.isLoged) return; // Solo cargar si el usuario está logueado

                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/cart`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        }
                    });
                    if (!response.ok) throw new Error("Error al cargar el carrito");

                    const data = await response.json();
                    setStore({ cart: data });
                } catch (error) {
                    console.error("Error al cargar el carrito:", error);
                }
            },
            addToCart: async (product) => {
                const store = getStore();
                if (!store.isLoged) {
                    alert("Debe estar logueado para añadir productos al carrito");
                    return;
                }
                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/cart`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        },
                        body: JSON.stringify({ product_id: product.id })
                    });

                    if (!response.ok) {
                        const data = await response.json();
                        alert(data.message || "Error al añadir al carrito");
                        return;
                    }
                    setStore({ cart: [...store.cart, product] });
                    alert("Producto añadido al carrito");
                } catch (error) {
                    console.error("Error al añadir al carrito:", error);
                }
            },
            removeFromCart: async (productId) => {
                const store = getStore();
                if (!store.isLoged) {
                    alert("Debe estar logueado para eliminar productos del carrito");
                    return;
                }

                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/cart/${productId}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        }
                    });

                    if (!response.ok) {
                        const data = await response.json();
                        alert(data.message || "Error al eliminar del carrito");
                        return;
                    }

                    setStore({ cart: store.cart.filter(product => product.id !== productId) });
                    alert("Producto eliminado del carrito");
                } catch (error) {
                    console.error("Error al eliminar del carrito:", error);
                }
            }
        }
    };
};

export default getState;

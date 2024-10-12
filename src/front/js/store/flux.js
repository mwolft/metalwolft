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
            favoritesLoaded: false,
            orders: [],  
            orderDetails: [],
            cart: [],
            paymentCompleted: false
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
                    isAdmin: user?.is_admin || false,
                    isLoged: true
                });
                // Cargar favoritos cuando se establece el usuario actual
                getActions().loadFavorites();
                // Cargar el carrito del usuario cuando se establece el usuario actual
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
            setIsLoged: (isLogin) => {
                if (isLogin) {
                    setStore({ isLoged: true });
                } else {
                    console.log("Cerrando sesión y limpiando carrito"); // Verificar que se está ejecutando
                    setStore({ isLoged: false, isAdmin: false, favorites: [] }); // Resetear favoritos
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
            fetchProducts: async () => {
                const store = getStore();
                const token = localStorage.getItem("token");
            
                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/products`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            ...(token && { Authorization: `Bearer ${token}` }) // Incluir el token solo si está presente
                        }
                    });
                    if (!response.ok) throw new Error("Error al obtener productos");
            
                    const data = await response.json();
                    setStore({ products: data });
                } catch (error) {
                    setStore({ error: error.message });
                }
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
            
                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error("Error al cargar el carrito:", errorText);
                        throw new Error(`Error al cargar el carrito: ${errorText}`);
                    }
            
                    const data = await response.json();  // Obtener los productos con especificaciones
                    console.log("Datos del carrito recibidos del backend:", data);
                    setStore({ cart: data });  // Guardar los productos en el estado global
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
                        body: JSON.stringify({
                            product_id: product.product_id,
                            alto: product.alto,
                            ancho: product.ancho,
                            anclaje: product.anclaje,
                            color: product.color,
                            precio_total: product.precio_total
                        })
                    });
            
                    if (!response.ok) {
                        const data = await response.json();
                        alert(data.message || "Error al añadir al carrito");
                        return;
                    }
            
                    // Actualizar el carrito en el estado
                    const newProduct = await response.json();  // Obtener el producto añadido del backend
                    setStore({ cart: [...store.cart, newProduct] });
                } catch (error) {
                    console.error("Error al añadir al carrito:", error);
                }
            },                    
            removeFromCart: async (product) => {
                const store = getStore();
                if (!store.isLoged) {
                    alert("Debe estar logueado para eliminar productos del carrito");
                    return;
                }
            
                try {
                    if (!product.producto_id) {
                        console.error("Faltan especificaciones del producto");
                        alert("Faltan especificaciones para eliminar el producto del carrito");
                        return;
                    }
            
                    const response = await fetch(`${process.env.BACKEND_URL}/api/cart/${product.producto_id}`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        },
                        body: JSON.stringify({
                            alto: product.alto,
                            ancho: product.ancho,
                            anclaje: product.anclaje,
                            color: product.color,
                            precio_total: product.precio_total,
                            imagen: product.imagen
                        })
                    });
            
                    if (!response.ok) {
                        const data = await response.text();
                        console.error("Error al eliminar del carrito:", data);
                        alert("Error al eliminar del carrito");
                        return;
                    }
            
                    const data = await response.json();
                    setStore({ cart: data.updated_cart });
                } catch (error) {
                    console.error("Error al eliminar del carrito:", error);
                }
            },  
            clearCart: async () => {
                const store = getStore();
                if (!store.isLoged) return;
            
                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/cart/clear`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        }
                    });
            
                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error("Error al vaciar el carrito:", errorText);
                        throw new Error(`Error al vaciar el carrito: ${errorText}`);
                    }
            
                    // Si el backend responde correctamente, vacía el carrito también en el frontend
                    setStore({ cart: [], paymentCompleted: true });
                    localStorage.removeItem("cart");
                } catch (error) {
                    console.error("Error al vaciar el carrito:", error);
                }
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
            saveOrder: async () => {
                const store = getStore();
                const orderData = {
                    total_amount: store.cart.reduce((acc, product) => acc + product.precio_total, 0),
                    products: store.cart.map(product => ({
                        product_id: product.producto_id,
                        quantity: 1,
                        alto: product.alto,
                        ancho: product.ancho,
                        anclaje: product.anclaje,
                        color: product.color,
                        precio_total: product.precio_total
                    }))
                };
            
                // Agregar un console.log para ver qué datos se envían al backend
                console.log("Datos de la orden que se envían al backend:", orderData);
            
                try {
                    const response = await fetch(`${process.env.BACKEND_URL}/api/orders`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        },
                        body: JSON.stringify(orderData)
                    });
            
                    if (!response.ok) {
                        const errorData = await response.json();
                        console.error("Error al guardar el pedido:", errorData.message);
                        alert("Error al guardar el pedido.");
                        return { ok: false };
                    }
            
                    const data = await response.json();
                    return { ok: true, order: data.order };
                } catch (error) {
                    console.error("Error al guardar el pedido:", error);
                    alert("Error al guardar el pedido.");
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
            saveOrderDetails: async (orderId) => {
                const store = getStore();
                
                const orderDetailsData = store.cart.map(product => ({
                    order_id: orderId,
                    product_id: product.producto_id,
                    quantity: 1,
                    alto: product.alto,
                    ancho: product.ancho,
                    anclaje: product.anclaje,
                    color: product.color,
                    precio_total: product.precio_total
                }));
            
                // Agregar un console.log para ver los detalles de la orden
                console.log("Detalles del pedido enviados al backend:", orderDetailsData);
            
                try {
                    for (const detail of orderDetailsData) {
                        const response = await fetch(`${process.env.BACKEND_URL}/api/orderdetails`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                Authorization: `Bearer ${localStorage.getItem("token")}`
                            },
                            body: JSON.stringify(detail)
                        });
            
                        if (!response.ok) {
                            const errorData = await response.json();
                            console.error("Error al guardar el detalle del pedido:", errorData.message);
                            return { ok: false };
                        }
                    }
            
                    return { ok: true };
                } catch (error) {
                    console.error("Error al guardar los detalles del pedido:", error);
                    return { ok: false };
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
            setFavoritesLoaded: (loaded) => {
                setStore({ favoritesLoaded: loaded });
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
            }               
        }
    };
};

export default getState;

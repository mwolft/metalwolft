import { calcularEnvio } from '../../utils/shippingCalculator';


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
            paymentIntentId: null,
            idempotencyKey: null,
            paymentCompleted: false,
            posts: [],
            postsLoaded: false,
            recentPosts: [],
            subcategories: [],
            categories: [],
            otherCategories: [],
            currentPost: null,
            currentComments: [],
            commentsLoaded: false
        },
        actions: {
            loadPosts: async () => {
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });

                    if (!response.ok) throw new Error("Error loading posts");

                    const data = await response.json();
                    setStore({ posts: data, postsLoaded: true });
                } catch (error) {
                    console.error("Error fetching posts:", error);
                    setStore({ error: error.message });
                }
            },
            addPost: async (postData) => {
                const token = localStorage.getItem("token");
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${token}` // usuario autenticado
                        },
                        body: JSON.stringify(postData)
                    });

                    if (!response.ok) throw new Error("Error adding post");

                    const newPost = await response.json();
                    const store = getStore();
                    setStore({ posts: [...store.posts, newPost] });
                } catch (error) {
                    console.error("Error adding post:", error);
                    setStore({ error: error.message });
                }
            },
            fetchPost: async (postId) => {
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts/${postId}`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });

                    if (!response.ok) throw new Error("Error fetching post");

                    const postData = await response.json();
                    setStore({ currentPost: postData });
                    getActions().fetchComments(postData.id);
                } catch (error) {
                    console.error("Error fetching post:", error);
                    setStore({ error: error.message });
                }
            },
            getRecentPosts: async () => {
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts?limit=5`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    if (!response.ok) throw new Error("Error fetching recent posts");
                    const data = await response.json();
                    setStore({ recentPosts: data });
                    return data;
                } catch (error) {
                    console.error("Error fetching recent posts:", error);
                    return [];
                }
            },
            getOtherCategories: async (currentCategoryId) => {
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/categories`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    if (!response.ok) throw new Error("Error fetching categories");

                    const data = await response.json();
                    const otherCategories = data.filter(category => category.id !== currentCategoryId);
                    setStore({ otherCategories });
                    return otherCategories;
                } catch (error) {
                    console.error("Error fetching other categories:", error);
                    return [];
                }
            },
            navigateToCategory: (categoryId) => {
                window.location.href = `/category/${categoryId}`;
            },
            fetchComments: async (postId) => {
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts/${postId}/comments`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });

                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error(`Error fetching comments: ${response.status} - ${errorText}`);
                        throw new Error(`Error ${response.status}: ${response.statusText}`);
                    }

                    const commentsData = await response.json();
                    setStore({
                        currentComments: commentsData,
                        commentsLoaded: true
                    });
                } catch (error) {
                    console.error("Error fetching comments:", error);
                    setStore({
                        error: error.message,
                        commentsLoaded: false
                    });
                }
            },
            addComment: async (postId, commentContent) => {
                const token = localStorage.getItem("jwt");
                if (!token) {
                    console.error("No JWT token found");
                    return;
                }

                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts/${postId}/comments`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({ content: commentContent })
                    });

                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error(`Error posting comment: ${response.status} - ${errorText}`);
                        throw new Error(`Error ${response.status}: ${response.statusText}`);
                    }

                    const newComment = await response.json();
                    const store = getStore();
                    setStore({ currentComments: [...store.currentComments, newComment] });
                } catch (error) {
                    console.error("Error posting comment:", error);
                }
            },
            setCurrentUser: (user) => {
                setStore({
                    currentUser: user,
                    isAdmin: user?.is_admin || false,
                    isLoged: true
                });
                getActions().loadFavorites();
                getActions().loadCart();
            },
            updateUserProfile: async (userId, updatedData) => {
                const store = getStore();
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/users/${userId}`, {
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
                    setStore({ isLoged: false, isAdmin: false, favorites: [] });
                    getActions().clearCart();
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
            getCategories: async () => {
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/categories`, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    if (!response.ok) throw new Error("Error fetching categories");

                    const data = await response.json();
                    setStore({ categories: data });
                } catch (error) {
                    console.error("Error fetching categories:", error);
                    setStore({ error: error.message, categories: [] });
                }
            },
            fetchProducts: async (categoryId = null, subcategoryId = null) => {
                let url = `${process.env.REACT_APP_BACKEND_URL}/api/products`;

                const queryParams = new URLSearchParams();
                if (categoryId) queryParams.append('category_id', categoryId);
                if (subcategoryId) queryParams.append('subcategory_id', subcategoryId);

                if (queryParams.toString()) {
                    url += `?${queryParams.toString()}`;
                }

                try {
                    const response = await fetch(url, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });

                    if (!response.ok) throw new Error("Error fetching products");

                    const data = await response.json();
                    setStore({ products: data });
                } catch (error) {
                    console.error("Error fetching products:", error);
                    setStore({ error: error.message, products: [] });
                }
            },
            loadCart: async () => {
                const store = getStore();
                if (!store.isLoged) return;
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/cart`, {
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

                const existing = store.cart.find(item =>
                    item.producto_id === product.product_id &&
                    item.alto === product.alto &&
                    item.ancho === product.ancho &&
                    item.anclaje === product.anclaje &&
                    item.color === product.color
                );

                if (existing) {
                    // Si ya existe, actualizar cantidad
                    try {
                        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/cart/${existing.producto_id}`, {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json',
                                Authorization: `Bearer ${localStorage.getItem("token")}`
                            },
                            body: JSON.stringify({
                                alto: existing.alto,
                                ancho: existing.ancho,
                                anclaje: existing.anclaje,
                                color: existing.color,
                                quantity: (existing.quantity || 1) + 1 
                            })
                        });

                        if (!response.ok) {
                            const data = await response.json();
                            alert(data.message || "Error al actualizar el carrito");
                            return;
                        }

                        const updatedCart = await response.json();
                        setStore({ cart: updatedCart });
                    } catch (error) {
                        console.error("Error al actualizar el carrito:", error);
                    }

                } else {
                    // Si no existe, añadir nuevo
                    try {
                        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/cart`, {
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
                                precio_total: product.precio_total,
                                quantity: 1 
                            })
                        });

                        if (!response.ok) {
                            const data = await response.json();
                            alert(data.message || "Error al añadir al carrito");
                            return;
                        }

                        const newProduct = await response.json();
                        setStore({ cart: [...store.cart, newProduct] });
                    } catch (error) {
                        console.error("Error al añadir al carrito:", error);
                    }
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
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/cart/${product.producto_id}`, {
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
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/cart/clear`, {
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
                    setStore({ cart: [], paymentCompleted: true });
                    localStorage.removeItem("cart");
                } catch (error) {
                    console.error("Error al vaciar el carrito:", error);
                }
            },
            fetchOrders: async () => {
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/orders`, {
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
                    console.error("Error al obtener las órdenes:", error.message);
                    return { ok: false };
                }
            },
            saveOrder: async (orderData) => {
                const store = getStore();
                console.log("Payload orderData enviado:", orderData);
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/orders`, {
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
                        return { ok: false, error: errorData.message };
                    }

                    const data = await response.json();

                    // Actualizar el store con la nueva orden
                    setStore({ orders: [...store.orders, data.data] });
                    return { ok: true, order: data.data };
                } catch (error) {
                    console.error("Error al guardar el pedido:", error.message);
                    return { ok: false, error: error.message };
                }
            },
            fetchOrderDetails: async () => {
                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/orderdetails`, {
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
                    console.error("Error al obtener los detalles de las órdenes:", error.message);
                    return { ok: false };
                }
            },
            saveOrderDetails: async (orderId, formData) => {
                const store = getStore();
                const { products: enrichedCart } = calcularEnvio(store.cart);

                const orderDetailsData = enrichedCart.map(product => ({
                    order_id: orderId,
                    product_id: product.producto_id,
                    quantity: 1,
                    alto: product.alto,
                    ancho: product.ancho,
                    anclaje: product.anclaje,
                    color: product.color,
                    precio_total: product.precio_total,
                    shipping_type: product.shipping_type,
                    shipping_cost: product.shipping_cost,
                    firstname: formData.firstname,
                    lastname: formData.lastname,
                    shipping_address: formData.shipping_address,
                    shipping_city: formData.shipping_city,
                    shipping_postal_code: formData.shipping_postal_code,
                    billing_address: formData.billing_address,
                    billing_city: formData.billing_city,
                    billing_postal_code: formData.billing_postal_code,
                    CIF: formData.CIF
                }));

                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/orderdetails`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        },
                        body: JSON.stringify(orderDetailsData)
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        console.error("Error al guardar los detalles del pedido:", errorData.message);
                        return { ok: false };
                    }

                    const data = await response.json();
                    setStore({ orderDetails: [...store.orderDetails, ...data] });
                    return { ok: true };
                } catch (error) {
                    console.error("Error al guardar los detalles del pedido:", error);
                    return { ok: false };
                }
            },
            handlePaymentSuccess: async () => {
                const store = getStore();
                const actions = getActions();
                const { ok, order } = await actions.saveOrder();
                if (!ok) {
                    console.error("Error al guardar la orden.");
                    return;
                }
                const result = await actions.saveOrderDetails(order.id);
                if (!result.ok) {
                    console.error("Error al guardar los detalles de la orden.");
                    return;
                }
                actions.clearCart();
            },
            loadFavorites: async () => {
                const store = getStore();
                if (!store.isLoged) return;

                try {
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/favorites`, {
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
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/favorites`, {
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
                    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/favorites/${productId}`, {
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
            setPaymentIntentId: (paymentIntentId) => {
                setStore({ paymentIntentId });
            },
            setIdempotencyKey: (idempotencyKey) => {
                setStore({ idempotencyKey });
            }
        }
    };
};

export default getState;

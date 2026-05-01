import { authenticatedFetch } from '../../utils/authenticatedFetch';

const getStoredUserSnapshot = () => {
    try {
        const rawStoredUser = localStorage.getItem("user");
        if (!rawStoredUser || rawStoredUser === "undefined") return null;

        const parsedUser = JSON.parse(rawStoredUser);
        return parsedUser && typeof parsedUser === "object" ? parsedUser : null;
    } catch (error) {
        console.error("Error al leer el usuario persistido:", error);
        return null;
    }
};

const buildPersistedUser = (incomingUser, fallbackUser = null) => {
    if (!incomingUser || typeof incomingUser !== "object") {
        return null;
    }

    const safeFallback = fallbackUser && typeof fallbackUser === "object" ? fallbackUser : {};
    const resolvedIsAdmin =
        typeof incomingUser.is_admin === "boolean"
            ? incomingUser.is_admin
            : typeof safeFallback.is_admin === "boolean"
                ? safeFallback.is_admin
                : false;

    return {
        ...safeFallback,
        ...incomingUser,
        is_admin: resolvedIsAdmin
    };
};


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
            posts: [],
            postsLoaded: false,
            recentPosts: [],
            subcategories: [],
            categories: [],
            otherCategories: [],
            currentPost: null,
            currentComments: [],
            commentsLoaded: false,
            profile: null
        },
        actions: {
            authenticatedFetch: authenticatedFetch,
            setDiscountPercent: (value) => setStore({ discountPercent: value }),
            setDiscountCode: (code) => setStore({ discountCode: code }),
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
                const token = localStorage.getItem("token");
                if (!token) {
                    console.error("No se encontró el token de autenticación. El usuario debe estar logueado.");
                    return;
                }
                if (!commentContent || commentContent.trim() === "") {
                    console.warn("No se puede enviar un comentario vacío.");
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
                        console.error(`Error al publicar comentario: ${response.status} - ${errorText}`);
                        throw new Error(`Error ${response.status}: ${response.statusText}`);
                    }
                    const newComment = await response.json();
                    const store = getStore();
                    setStore({
                        currentComments: [...store.currentComments, newComment]
                    });

                    console.log("Comentario añadido con éxito:", newComment);

                } catch (error) {
                    console.error("Error en addComment:", error);
                    getActions().setAlert({
                        visible: true,
                        back: "danger",
                        text: "No se pudo publicar el comentario. Inténtalo de nuevo.",
                    });
                }
            },
            setCurrentUser: (user) => {
                const fallbackUser = getStore().currentUser || getStoredUserSnapshot();
                const nextUser = buildPersistedUser(user, fallbackUser);

                if (nextUser) {
                    localStorage.setItem("user", JSON.stringify(nextUser));
                } else {
                    localStorage.removeItem("user");
                }

                setStore({
                    currentUser: nextUser,
                    isAdmin: nextUser?.is_admin || false,
                    isLoged: Boolean(nextUser)
                });

                if (nextUser) {
                    getActions().loadFavorites();
                    getActions().loadCart();
                }
            },
            updateUserProfile: async (userId, updatedData) => {
                try {
                    const result = await authenticatedFetch(
                        `${process.env.REACT_APP_BACKEND_URL}/api/users/${userId}`,
                        {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(updatedData)
                        }
                    );

                    if (!result.ok) {
                        throw new Error(result.data?.message || "Error al actualizar el perfil");
                    }

                    getActions().setCurrentUser(result.data?.results || result.data);

                    return { ok: true };

                } catch (error) {
                    setStore({ error: error.message });
                    return { ok: false };
                }
            },
            fetchProfile: async () => {
                const actions = getActions();

                const result = await actions.authenticatedFetch(
                    `${process.env.REACT_APP_BACKEND_URL}/api/me`,
                    { method: "GET" },
                    actions,
                    setStore
                );

                console.log("RESULT /me:", result);

                if (!result.ok) {
                    console.log("NO OK:", result.status, result.data);
                    return null;
                }

                const user = result.data;
                console.log("USER DATA:", user);

                getActions().setCurrentUser(user);

                return user;
            },

            updateProfile: async (updatedProfile) => {
                const actions = getActions();

                const result = await actions.authenticatedFetch(
                    `${process.env.REACT_APP_BACKEND_URL}/api/me`,
                    {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(updatedProfile)
                    },
                    actions,
                    setStore
                );

                if (!result.ok) {
                    return false;
                }

                // Tras actualizar, lo normal es volver a pedir el perfil
                await actions.fetchProfile();

                return true;
            },
            setIsLoged: (isLogin) => {
                if (isLogin) {
                    setStore({ isLoged: true });
                } else {
                    setStore({ isLoged: false, isAdmin: false, currentUser: null, favorites: [] });
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
                const actions = getActions();

                if (!store.isLoged) return;

                try {
                    const result = await authenticatedFetch(
                        `${process.env.REACT_APP_BACKEND_URL}/api/cart`,
                        { method: "GET" },
                        actions,
                        setStore
                    );

                    if (!result.ok) {
                        console.error("Error al cargar carrito:", result.data?.message);
                        setStore({ cart: [] });
                        return;
                    }

                    setStore({ cart: Array.isArray(result.data) ? result.data : [] });

                } catch (error) {
                    console.error("Error en loadCart:", error);
                    setStore({ cart: [] });
                }
            },
            addToCart: async (product) => {
                const store = getStore();
                const actions = getActions();

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

                try {
                    if (existing) {
                        const result = await authenticatedFetch(
                            `${process.env.REACT_APP_BACKEND_URL}/api/cart/${existing.producto_id}`,
                            {
                                method: "PUT",
                                body: JSON.stringify({
                                    alto: existing.alto,
                                    ancho: existing.ancho,
                                    anclaje: existing.anclaje,
                                    color: existing.color,
                                    quantity: (existing.quantity || 1) + 1
                                })
                            },
                            actions,
                            setStore
                        );

                        if (!result.ok) {
                            console.error("Error actualizando carrito:", result.data?.message);
                            return;
                        }

                        setStore({ cart: Array.isArray(result.data) ? result.data : [] });

                    } else {
                        const result = await authenticatedFetch(
                            `${process.env.REACT_APP_BACKEND_URL}/api/cart`,
                            {
                                method: "POST",
                                body: JSON.stringify({
                                    product_id: product.product_id,
                                    alto: product.alto,
                                    ancho: product.ancho,
                                    anclaje: product.anclaje,
                                    color: product.color,
                                    precio_total: product.precio_total,
                                    quantity: 1
                                })
                            },
                            actions,
                            setStore
                        );

                        if (!result.ok) {
                            console.error("Error añadiendo al carrito:", result.data?.message);
                            return;
                        }

                        setStore({ cart: Array.isArray(result.data) ? result.data : [...store.cart] });
                    }

                } catch (error) {
                    console.error("Error al gestionar el carrito:", error);
                }
            },
            removeFromCart: async (product) => {
                const store = getStore();
                const actions = getActions();

                if (!store.isLoged) {
                    alert("Debe estar logueado para eliminar productos del carrito");
                    return;
                }

                if (!product.producto_id) return;

                try {
                    const result = await authenticatedFetch(
                        `${process.env.REACT_APP_BACKEND_URL}/api/cart/${product.producto_id}`,
                        {
                            method: "DELETE",
                            body: JSON.stringify({
                                alto: product.alto,
                                ancho: product.ancho,
                                anclaje: product.anclaje,
                                color: product.color,
                                precio_total: product.precio_total,
                                imagen: product.imagen
                            })
                        },
                        actions,
                        setStore
                    );

                    if (!result.ok) {
                        console.error("Error al eliminar del carrito:", result.data?.message);
                        return;
                    }

                    setStore({
                        cart: Array.isArray(result.data?.updated_cart)
                            ? result.data.updated_cart
                            : Array.isArray(result.data)
                                ? result.data
                                : []
                    });

                } catch (error) {
                    console.error("Error al eliminar del carrito:", error);
                }
            },
            clearCart: async () => {
                const store = getStore();
                const actions = getActions();

                if (!store.isLoged) return;

                try {
                    const result = await authenticatedFetch(
                        `${process.env.REACT_APP_BACKEND_URL}/api/cart/clear`,
                        { method: "POST" },
                        actions,
                        setStore
                    );

                    if (!result.ok) {
                        console.error("Error al vaciar el carrito:", result.data?.message);
                        return;
                    }

                    setStore({
                        cart: [],
                        paymentIntentId: null,
                        idempotencyKey: null
                    });
                    localStorage.removeItem("cart");

                } catch (error) {
                    console.error("Error al vaciar el carrito:", error);
                }
            },
            fetchOrders: async () => {
                const actions = getActions();

                const result = await actions.authenticatedFetch(
                    `${process.env.REACT_APP_BACKEND_URL}/api/orders`,
                    { method: 'GET' },
                    actions,
                    setStore
                );

                if (!result.ok) {
                    console.error("Error al cargar pedidos:", result.data?.message);
                    setStore({ orders: [] });
                    return { ok: false };
                }

                setStore({ orders: result.data || [] });

                return { ok: true };
            },
            saveOrder: async (orderData) => {
                const store = getStore();
                console.log("Payload orderData enviado:", orderData);
                try {
                    const result = await authenticatedFetch(
                        `${process.env.REACT_APP_BACKEND_URL}/api/orders`,
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(orderData)
                        }
                    );

                    if (!result.ok) {
                        console.error("Error al guardar el pedido:", result.data?.message);
                        return { ok: false, error: result.data?.message };
                    }

                    const data = result.data;

                    const nextOrders = store.orders.some((order) => order.id === data.data?.id)
                        ? store.orders
                        : [...store.orders, data.data];

                    setStore({ orders: nextOrders });
                    return { ok: true, order: data.data };
                } catch (error) {
                    console.error("Error al guardar el pedido:", error.message);
                    return { ok: false, error: error.message };
                }
            },
            fetchOrderDetails: async () => {
                try {
                    const result = await authenticatedFetch(
                        `${process.env.REACT_APP_BACKEND_URL}/api/orderdetails`,
                        {
                            method: 'GET',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        }
                    );

                    if (!result.ok) {
                        throw new Error(result.data?.message || "Error al obtener los detalles de las órdenes");
                    }

                    setStore({
                        orderDetails: Array.isArray(result.data) ? result.data : []
                    });

                    return { ok: true };

                } catch (error) {
                    setStore({ error: error.message });
                    console.error("Error al obtener los detalles de las órdenes:", error.message);
                    return { ok: false };
                }
            },
            loadFavorites: async () => {
                const store = getStore();
                const actions = getActions();

                if (!store.isLoged) return;

                try {
                    const result = await authenticatedFetch(
                        `${process.env.REACT_APP_BACKEND_URL}/api/favorites`,
                        { method: "GET" },
                        actions,
                        setStore
                    );

                    if (!result.ok) {
                        console.error("Error al cargar favoritos:", result.data?.message);
                        setStore({ favorites: [] });
                        return;
                    }

                    setStore({ favorites: result.data || [] });

                } catch (error) {
                    console.error("Error al cargar los favoritos:", error);
                    setStore({ favorites: [] });
                }
            },
            setFavoritesLoaded: (loaded) => {
                setStore({ favoritesLoaded: loaded });
            },
            addFavorite: async (product) => {
                const store = getStore();
                if (!store.isLoged) return;

                try {
                    const result = await authenticatedFetch(
                        `${process.env.REACT_APP_BACKEND_URL}/api/favorites`,
                        {
                            method: "POST",
                            body: JSON.stringify({ product_id: product.id }),
                        }
                    );

                    if (!result.ok) {
                        console.error("Error al añadir a favoritos:", result.data?.message);
                        return;
                    }

                    setStore({ favorites: [...store.favorites, product] });

                } catch (error) {
                    console.error("Error al añadir a favoritos:", error);
                }
            },
            removeFavorite: async (productId) => {
                const store = getStore();
                if (!store.isLoged) return;

                try {
                    const result = await authenticatedFetch(
                        `${process.env.REACT_APP_BACKEND_URL}/api/favorites/${productId}`,
                        { method: "DELETE" }
                    );

                    if (!result.ok) {
                        console.error("Error al eliminar de favoritos:", result.data?.message);
                        return;
                    }

                    setStore({
                        favorites: store.favorites.filter(
                            (product) => product.id !== productId
                        ),
                    });

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

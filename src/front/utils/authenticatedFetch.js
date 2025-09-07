export const authenticatedFetch = async (url, options = {}, getActions, setStore) => {
    const token = localStorage.getItem("token");

    const headers = {
        ...(options.headers || {}),
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
    };

    try {
        const response = await fetch(url, { ...options, headers });

        // Si el token ha expirado, cerrar sesión y redirigir
        if (response.status === 401) {
            const errorData = await response.json();

            if (errorData.msg === "Token has expired") {
                console.warn("Token expirado, cerrando sesión...");

                // Limpiar localStorage
                localStorage.removeItem("token");
                localStorage.removeItem("user");

                // Limpiar el store global
                if (setStore) {
                    setStore({ isLoged: false, isAdmin: false, cart: [], favorites: [] });
                }

                // Mostrar notificación (usando el sistema del flux)
                if (getActions && typeof getActions === "function") {
                    getActions().setAlert({
                        visible: true,
                        back: "danger",
                        text: "Tu sesión ha expirado. Por favor, vuelve a iniciar sesión."
                    });
                }

                // Redirigir al login
                window.location.href = "/login";
                return null;
            }
        }

        return response;
    } catch (error) {
        console.error("Error en authenticatedFetch:", error);
        throw error;
    }
};

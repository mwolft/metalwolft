export const authenticatedFetch = async (url, options = {}, getActions, setStore) => {
    const token = localStorage.getItem("token");

    const headers = {
        ...(options.headers || {}),
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
    };

    try {
        const response = await fetch(url, { ...options, headers });

        // 🔐 Token expirado
        if (response.status === 401) {
            let errorData = null;
            try {
                errorData = await response.json();
            } catch {}

            if (errorData?.msg === "Token has expired") {
                localStorage.removeItem("token");
                localStorage.removeItem("user");

                if (setStore) {
                    setStore({
                        isLoged: false,
                        isAdmin: false,
                        cart: [],
                        favorites: [],
                    });
                }

                if (getActions && typeof getActions === "function") {
                    getActions().setAlert({
                        visible: true,
                        back: "danger",
                        text: "Tu sesión ha expirado. Por favor, vuelve a iniciar sesión.",
                    });
                }

                window.location.href = "/login";
                return null;
            }
        }

        // 🔒 Sin contenido
        if (response.status === 204 || response.status === 304) {
            return null;
        }

        // 🔒 Solo parsear JSON real
        const contentType = response.headers.get("content-type") || "";
        if (!contentType.includes("application/json")) {
            console.warn("Respuesta no JSON ignorada:", response);
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error("Error en authenticatedFetch:", error);
        throw error;
    }
};

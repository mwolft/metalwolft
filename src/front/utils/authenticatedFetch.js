export const authenticatedFetch = async (url, options = {}, getActions, setStore) => {
    const token = localStorage.getItem("token");

    const headers = {
        ...(options.headers || {}),
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
    };

    try {
        const response = await fetch(url, { ...options, headers });

        let data = null;

        const contentType = response.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
            try {
                data = await response.json();
            } catch (e) {
                data = null;
            }
        }

        // 🔐 Token expirado
        if (response.status === 401 && data?.msg === "Token has expired") {
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

            return {
                ok: false,
                status: 401,
                data
            };
        }

        return {
            ok: response.ok,
            status: response.status,
            data
        };

    } catch (error) {
        console.error("Error en authenticatedFetch:", error);
        throw error;
    }
};
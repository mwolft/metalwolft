import React, { useState, useEffect } from "react";
import getState from "./flux.js";

// Inicializamos nuestro contexto, por defecto será null.
export const Context = React.createContext(null);

// Esta función inyecta el store global a cualquier vista/componente donde se necesite usar.
const injectContext = PassedComponent => {
    const StoreWrapper = props => {
        // Este será el valor que se pasa como contexto.
        const [state, setState] = useState(
            getState({
                getStore: () => state.store,
                getActions: () => state.actions,
                setStore: updatedStore =>
                    setState({
                        store: Object.assign(state.store, updatedStore),
                        actions: { ...state.actions }
                    })
            })
        );

        useEffect(() => {
            // Revisa si el usuario ya está logueado comprobando el localStorage.
            const storedUser = localStorage.getItem('user');
            const token = localStorage.getItem('token');

            // Parseamos solo si el token y el usuario son válidos.
            if (token && storedUser && storedUser !== 'undefined') {
                try {
                    const user = JSON.parse(storedUser);
                    if (user && typeof user === "object") {
                        state.actions.setIsLoged(true);
                        state.actions.setCurrentUser(user);
                        state.actions.setIsAdmin(user.is_admin);
                    }
                } catch (error) {
                    console.error("Error al parsear los datos del usuario desde localStorage:", error);
                }
            }
        }, []);

        return (
            <Context.Provider value={state}>
                <PassedComponent {...props} />
            </Context.Provider>
        );
    };
    return StoreWrapper;
};

export default injectContext;

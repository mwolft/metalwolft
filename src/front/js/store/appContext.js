import React, { useState, useEffect } from "react";
import getState from "./flux.js";

// Don't change, here is where we initialize our context, by default it's just going to be null.
export const Context = React.createContext(null);

// This function injects the global store to any view/component where you want to use it
const injectContext = PassedComponent => {
    const StoreWrapper = props => {
        // This will be passed as the context value
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
            state.actions.getMessage();  // Calling this function from the flux.js actions

            // Check if the user is already logged in by checking localStorage
            const storedUser = localStorage.getItem('user');
            const token = localStorage.getItem('token');

            console.log("Token from localStorage:", token);
            console.log("User from localStorage:", storedUser);

            // Parse only if token and user are valid
            if (token && storedUser && storedUser !== 'undefined') {
                try {
                    const user = JSON.parse(storedUser);
                    if (user && typeof user === "object") {
                        state.actions.setIsLoged(true);
                        state.actions.setCurrentUser(user);
                        state.actions.setIsAdmin(user.is_admin);
                    }
                } catch (error) {
                    console.error("Error parsing user data from localStorage:", error);
                }
            } else {
                console.warn("No valid user data found in localStorage or user is 'undefined'.");
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

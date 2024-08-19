import React, { useContext } from "react";
import { Context } from "../store/appContext.js";

export const Logout = () => {
    const { actions } = useContext(Context);
  
    const handleLogout = () => {
      localStorage.clear();
      actions.setIsLoged(false);
      actions.setCurrentUser(null);
    }
  
  
    return (
      <button onClick={handleLogout} className="btn btn-primary ms-2">Logout</button>
    )
  }
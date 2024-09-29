import React, { useEffect } from "react";
import { Admin } from "react-admin";
import jsonServerProvider from "ra-data-json-server";
import { useNavigate } from "react-router-dom";

const dataProvider = jsonServerProvider(process.env.REACT_APP_BACKEND_URL + "/api");

const AdminPanel = () => {
  const navigate = useNavigate();

  // Verificar si el usuario tiene acceso de administrador antes de cargar el panel de administración.
  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null;

    if (!token || !user || !user.is_admin) {
      navigate('/'); // Redirigir a la página de inicio si no está autenticado o no tiene privilegios de administrador
    }
  }, [navigate]);

  return (
    <Admin
      dataProvider={dataProvider}
      title="Admin Panel"
    >
    </Admin>
  );
};

export default AdminPanel;

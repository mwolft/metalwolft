import React, { useEffect, useState } from "react";
import { Admin, Resource } from "react-admin";
import jsonServerProvider from "ra-data-json-server";
import { fetchUtils } from 'ra-core'; // Importa utilidades para hacer fetch
import { useNavigate } from "react-router-dom";
import { UserList } from "../component/admin/users/users.js";
import { authProvider } from "../authProvider.js";

// Crear una función de cliente personalizado para agregar el token al header de cada solicitud
const httpClient = (url, options = {}) => {
  if (!options.headers) {
    options.headers = new Headers({ Accept: 'application/json' });
  }
  const token = localStorage.getItem('token');
  if (token) {
    options.headers.set('Authorization', `Bearer ${token}`);
  }
  return fetchUtils.fetchJson(url, options);
};

// Data Provider con cliente HTTP personalizado
const dataProvider = jsonServerProvider(process.env.REACT_APP_BACKEND_URL + "/api", httpClient);

const AdminPanel = () => {
  const navigate = useNavigate();
  const [hasAccess, setHasAccess] = useState(false);

  useEffect(() => {
    console.log("Checking admin access...");
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null;

    if (!token) {
      console.warn("Access denied. No token found. Redirecting to home.");
      navigate('/');
    } else if (!user || !user.is_admin) {
      console.warn("Access denied. User is not an admin. Redirecting to home.");
      navigate('/');
    } else {
      console.log("Admin access granted.");
      setHasAccess(true);
    }
  }, [navigate]);

  console.log("Rendering AdminPanel...");
  console.log("Data Provider URL:", process.env.REACT_APP_BACKEND_URL + "/api");

  // Mostrar un mensaje de carga mientras se verifica el acceso
  if (!hasAccess) {
    return <p>Verificando acceso de administrador...</p>;
  }

  return ( 
    <div style={{ marginTop: '100px' }}>
      <Admin
        dataProvider={dataProvider}
        authProvider={authProvider}
        title="Admin Panel"
        basename="/admin"
      >
        <Resource name="users" list={UserList} />
      </Admin>
    </div>
  );
};

export default AdminPanel;

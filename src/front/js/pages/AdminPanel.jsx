import React, { useEffect, useState } from "react";
import { Admin, Resource } from "react-admin";
import jsonServerProvider from "ra-data-json-server";
import { fetchUtils } from 'ra-core';
import { useNavigate } from "react-router-dom";
import { UserList } from "../component/admin/users/users.js";
import { ProductList } from "../component/admin/products/products.js";
import { OrderList } from "../component/admin/orders/orders.js";
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
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null;

    if (!token || !user || !user.is_admin) {
      navigate('/');
    } else {
      setHasAccess(true);
    }
  }, [navigate]);

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
        <Resource name="products" list={ProductList} />
        <Resource name="orders" list={OrderList} />
      </Admin>
    </div>
  );
};

export default AdminPanel;

import React, { useEffect, useState } from "react";
import { Admin, Resource, Layout } from "react-admin";
import jsonServerProvider from "ra-data-json-server";
import { fetchUtils } from 'ra-core';
import { useNavigate, useLocation } from "react-router-dom";
import { UserList, UserEdit, UserCreate } from "../component/admin/users/users.js";
import { ProductList, ProductEdit, ProductCreate } from "../component/admin/products/products.js";
import { OrderList, OrderEdit, OrderCreate } from "../component/admin/orders/orders.js";
import { ProductImagesList, ProductImagesEdit, ProductImagesCreate } from "../component/admin/products/productImages.js";
import { authProvider } from "../authProvider.js";
import { FaUser, FaBoxOpen, FaShoppingCart, FaImages } from 'react-icons/fa';
import '../../styles/admin-panel.css';

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

// Layout personalizado para mostrar un título dinámico
const CustomLayout = (props) => {
  const location = useLocation();
  let title = '';

  if (location.pathname.includes("/users")) {
    title = "Usuarios";
  } else if (location.pathname.includes("/products")) {
    title = "Productos";
  } else if (location.pathname.includes("/orders")) {
    title = "Pedidos";
  } else if (location.pathname.includes("/product_images")) {
    title = "Imágenes de Productos";
  }

  return (
    <div className="custom-layout">
      <div className="custom-header">
        <h4>{title}</h4>
      </div>
      <Layout {...props} />
    </div>
  );
};

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
    <div className="admin-box" style={{ marginTop: '85px', paddingBottom: '35px' }}>
      <div className="admin-header">
        <h3 className="text-center pt-1">PANEL DE ADMINISTRACIÓN</h3>
      </div>
      <div className="admin-body">
        <Admin
          dataProvider={dataProvider}
          authProvider={authProvider}
          title="Admin Panel"
          basename="/admin"
          layout={CustomLayout}
        >
          <Resource
            name="users"
            list={UserList}
            edit={UserEdit}
            create={UserCreate}
            icon={() => <FaUser size={24} />}
          />
          <Resource
            name="products"
            list={ProductList}
            edit={ProductEdit}
            create={ProductCreate}
            icon={() => <FaBoxOpen size={24} />}
          />
          <Resource
            name="orders"
            list={OrderList}
            edit={OrderEdit}
            create={OrderCreate}
            icon={() => <FaShoppingCart size={24} />}
          />
          <Resource
            name="product_images"
            list={ProductImagesList}
            edit={ProductImagesEdit}
            create={ProductImagesCreate}
            icon={() => <FaImages size={24} />}
          />
        </Admin>
      </div>
    </div>
  );
};

export default AdminPanel;

import React from "react";
import { Admin, Resource } from "react-admin";
import jsonServerProvider from "ra-data-json-server";
import { UserList, UserEdit, UserCreate } from "../component/admin/users/users.js";
import { ProductList, ProductEdit, ProductCreate } from "../component/admin/products/products.js";
import { OrderList, OrderEdit, OrderCreate } from "../component/admin/orders/orders.js";
import { useNavigate } from "react-router-dom";
import { authProvider } from "../authProvider.js";  // Asegúrate de tener el authProvider creado

const dataProvider = jsonServerProvider(process.env.REACT_APP_BACKEND_URL + "/api");

const AdminPanel = () => {
  const navigate = useNavigate();

  console.log("Data Provider URL:", process.env.REACT_APP_BACKEND_URL + "/api");

  return (
    <Admin
      dataProvider={dataProvider}
      authProvider={authProvider}
      title="Admin Panel"
      onNoAccess={() => navigate("/")} // Si no tiene acceso, redirige a home
    >
      <Resource name="users" list={UserList} edit={UserEdit} create={UserCreate} />
      <Resource name="products" list={ProductList} edit={ProductEdit} create={ProductCreate} />
      <Resource name="orders" list={OrderList} edit={OrderEdit} create={OrderCreate} />
    </Admin>
  );
};

export default AdminPanel;

import React, { useEffect, useState } from "react";
import { Admin, Resource, Layout } from "react-admin";
import dataProvider from '../../../../src/dataProvider.js'; 
import jsonServerProvider from "ra-data-json-server";
import { fetchUtils } from 'ra-core';
import { useNavigate } from "react-router-dom";
import { UserList, UserEdit, UserCreate } from "../component/admin/users/users.js";
import { ProductList, ProductEdit, ProductCreate } from "../component/admin/products/products.js";
import { OrderList, OrderEdit, OrderCreate } from "../component/admin/orders/orders.js";
import { ProductImagesList, ProductImagesEdit, ProductImagesCreate } from "../component/admin/products/productImages.js";
import { OrderDetailsList, OrderDetailsEdit, OrderDetailsCreate } from "../component/admin/orderDetails/orderDetails.js";
import { InvoiceList, InvoiceCreate, InvoiceEdit } from "../component/admin/invoices/invoices.js";
import { authProvider } from "../authProvider.js";
import { FaUser, FaBoxOpen, FaShoppingCart, FaImages, FaFileInvoice } from 'react-icons/fa';
import { TbListDetails } from "react-icons/tb";
import '../../styles/admin-panel.css';


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
    <div className="admin-box" style={{ marginTop: '65px', paddingBottom: '35px' }}>
      <div className="admin-header">
        <h3 className="text-center pt-2">PANEL DE ADMINISTRACIÓN</h3>
      </div>
      <div className="admin-body">
        <Admin
          dataProvider={dataProvider}
          authProvider={authProvider}
          title="Admin Panel"
          basename="/admin"
        >
          <Resource
            name="users"
            list={UserList}
            edit={UserEdit}
            create={UserCreate}
            icon={() => <FaUser size={19} />}
          />
          <Resource
            name="products"
            list={ProductList}
            edit={ProductEdit}
            create={ProductCreate}
            icon={() => <FaBoxOpen size={19} />}
          />
          <Resource
            name="orders"
            list={OrderList}
            edit={OrderEdit}
            create={OrderCreate}
            icon={() => <FaShoppingCart size={19} />}
          />
          <Resource
            name="product_images"
            list={ProductImagesList}
            edit={ProductImagesEdit}
            create={ProductImagesCreate}
            icon={() => <FaImages size={19} />}
          />
          <Resource
            name="orderdetails"
            list={OrderDetailsList}
            edit={OrderDetailsEdit}
            create={OrderDetailsCreate}
            icon={() => <TbListDetails size={19} />}
          />
          <Resource
            name="invoices"
            list={InvoiceList}
            edit={InvoiceEdit}
            create={InvoiceCreate}
            icon={() => <FaFileInvoice size={19} />} 
          />
        </Admin>
      </div>
    </div>
  );
};

export default AdminPanel;

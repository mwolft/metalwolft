import React, { useEffect, useState } from "react";
import { Admin, Resource } from "react-admin";
import dataProvider from '../../../../src/dataProvider.js';
import { useNavigate } from "react-router-dom";
import { UserList, UserEdit, UserCreate } from "../component/admin/users/users.js";
import { OrderList, OrderEdit, OrderCreate } from "../component/admin/orders/orders.js";
import { OrderDetailsList, OrderDetailsEdit, OrderDetailsCreate } from "../component/admin/orderDetails/orderDetails.js";
import { InvoiceList, InvoiceCreate, InvoiceEdit } from "../component/admin/invoices/invoices.js";
import { authProvider } from "../authProvider.js";
import { FaUser, FaShoppingCart, FaFileInvoice } from 'react-icons/fa';
import { TbListDetails } from "react-icons/tb";
import '../../styles/admin-panel.css';


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
    return <p className="admin-loading-state">Verificando acceso de administrador...</p>;
  }

  return (
    <div className="admin-box admin-panel-page">
      <div className="admin-header">
        <h3 className="admin-title">Panel de administracion</h3>
      </div>
      <div className="admin-body">
        <Admin
          dataProvider={dataProvider}
          authProvider={authProvider}
          title="Panel de Administración"
          basename="/admin"
        >
          <Resource
            name="users"
            list={UserList}
            edit={UserEdit}
            create={UserCreate}
            icon={() => <FaUser size={19} />}
            options={{ label: "Usuarios" }}
          />
          <Resource
            name="orders"
            list={OrderList}
            edit={OrderEdit}
            create={OrderCreate}
            icon={() => <FaShoppingCart size={19} />}
            options={{ label: "Pedidos" }}
          />
          <Resource
            name="orderdetails"
            list={OrderDetailsList}
            edit={OrderDetailsEdit}
            create={OrderDetailsCreate}
            icon={() => <TbListDetails size={19} />}
            options={{ label: "Detalles Pedido" }}
          />
          <Resource
            name="invoices"
            list={InvoiceList}
            edit={InvoiceEdit}
            create={InvoiceCreate}
            icon={() => <FaFileInvoice size={19} />}
            options={{ label: "Facturas" }}
          />
        </Admin>
      </div>
    </div>
  );
};

export default AdminPanel;

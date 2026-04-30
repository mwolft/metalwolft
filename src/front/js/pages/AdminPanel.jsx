import React, { useEffect, useState } from "react";
import { Admin, Layout, Resource } from "react-admin";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { FaFileInvoice, FaShoppingCart, FaUser } from "react-icons/fa";
import { TbListDetails } from "react-icons/tb";
import dataProvider from "../../../../src/dataProvider.js";
import { authProvider } from "../authProvider.js";
import { UserList, UserEdit, UserCreate } from "../component/admin/users/users.js";
import { OrderList, OrderEdit, OrderCreate } from "../component/admin/orders/orders.js";
import {
  OrderDetailsList,
  OrderDetailsEdit,
  OrderDetailsCreate,
} from "../component/admin/orderDetails/orderDetails.js";
import { InvoiceList, InvoiceCreate, InvoiceEdit } from "../component/admin/invoices/invoices.js";
import "../../styles/admin-panel.css";

const EmptyAdminMenu = () => null;
const EmptyAdminSidebar = () => null;

const AdminShellLayout = (props) => (
  <Layout {...props} menu={EmptyAdminMenu} sidebar={EmptyAdminSidebar} />
);

const adminNavItems = [
  { to: "/admin/users", label: "Usuarios", icon: <FaUser size={16} /> },
  { to: "/admin/orders", label: "Pedidos", icon: <FaShoppingCart size={16} /> },
  { to: "/admin/orderdetails", label: "Detalles Pedido", icon: <TbListDetails size={16} /> },
  { to: "/admin/invoices", label: "Facturas", icon: <FaFileInvoice size={16} /> },
];

const AdminResourceNav = () => (
  <nav className="admin-resource-nav" aria-label="Secciones del panel de administracion">
    {adminNavItems.map((item) => (
      <NavLink
        key={item.to}
        to={item.to}
        className={({ isActive }) =>
          `admin-resource-link${isActive ? " admin-resource-link--active" : ""}`
        }
      >
        {item.icon}
        <span>{item.label}</span>
      </NavLink>
    ))}
  </nav>
);

const AdminPanel = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [hasAccess, setHasAccess] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const user = localStorage.getItem("user")
      ? JSON.parse(localStorage.getItem("user"))
      : null;

    if (!token || !user || !user.is_admin) {
      navigate("/");
      return;
    }

    setHasAccess(true);

    if (location.pathname === "/admin" || location.pathname === "/admin/") {
      navigate("/admin/users", { replace: true });
    }
  }, [location.pathname, navigate]);

  if (!hasAccess) {
    return <p className="admin-loading-state">Verificando acceso de administrador...</p>;
  }

  return (
    <div className="admin-box admin-panel-page">
      <div className="admin-header">
        <h3 className="admin-title">Panel de administracion</h3>
      </div>
      <div className="admin-body">
        <AdminResourceNav />
        <Admin
          dataProvider={dataProvider}
          authProvider={authProvider}
          title="Panel de administracion"
          basename="/admin"
          layout={AdminShellLayout}
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

// src/components/admin/orders/orders.js
import React from "react";
import { List, Datagrid, TextField, NumberField, EditButton, DeleteButton } from "react-admin";

// Lista de pedidos: muestra todos los pedidos
export const OrderList = (props) => (
  <List {...props}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <TextField source="user_id" label="ID Usuario" />
      <NumberField source="total_amount" label="Total" />
      <TextField source="created_at" label="Fecha de Creación" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

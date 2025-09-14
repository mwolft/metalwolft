import React from "react";
import { List, Datagrid, TextField, NumberField, EditButton, DeleteButton, Edit, SimpleForm, TextInput, NumberInput, Create, DateField } from "react-admin";

// Lista de órdenes: muestra todas las órdenes
export const OrderList = (props) => (
  <List {...props} sort={{ field: 'id', order: 'DESC' }}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <TextField source="user_id" label="ID del Usuario" />
      <NumberField source="total_amount" label="Monto Total" />
      <DateField source="order_date" label="Fecha de Orden" />
      <TextField source="invoice_number" label="Número de Factura" />
      <TextField source="locator" label="Localizador" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
);


// Editar una orden existente
export const OrderEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <TextInput source="user_id" label="ID del Usuario" />
      <NumberInput source="total_amount" label="Monto Total" />
      <TextInput source="order_date" label="Fecha de Orden" />
      <TextInput source="invoice_number" label="Número de Factura" disabled />
      <TextInput source="locator" label="Localizador" disabled />
    </SimpleForm>
  </Edit>
);

// Crear una nueva orden
export const OrderCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <TextInput source="user_id" label="ID del Usuario" />
      <NumberInput source="total_amount" label="Monto Total" />
      <TextInput source="order_date" label="Fecha de Orden" />
      <TextInput source="invoice_number" label="Número de Factura" disabled />
      <TextInput source="locator" label="Localizador" disabled />
    </SimpleForm>
  </Create>
);

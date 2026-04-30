import React from "react";
import { List, Datagrid, TextField, NumberField, EditButton, DeleteButton, WrapperField, Edit, SimpleForm, TextInput, NumberInput, Create, DateField } from "react-admin";

const OrderActions = () => (
  <WrapperField label="Acciones">
    <div className="admin-action-group">
      <EditButton className="admin-ra-button admin-ra-button--secondary" />
      <DeleteButton className="admin-ra-button admin-ra-button--danger" />
    </div>
  </WrapperField>
);

// Lista de órdenes: muestra todas las órdenes
export const OrderList = (props) => (
  <List {...props} sort={{ field: 'id', order: 'DESC' }} className="admin-resource-list">
    <div className="admin-datagrid-scroll">
      <Datagrid>
      <TextField source="id" label="ID" />
      <NumberField source="total_amount" label="Monto Total" />
      <DateField source="order_date" label="Fecha de Orden" />
      <TextField source="invoice_number" label="Número de Factura" />
      <TextField source="locator" label="Localizador" />
        <OrderActions />
      </Datagrid>
    </div>
  </List>
);


// Editar una orden existente
export const OrderEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
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
      <NumberInput source="total_amount" label="Monto Total" />
      <TextInput source="order_date" label="Fecha de Orden" />
      <TextInput source="invoice_number" label="Número de Factura" disabled />
      <TextInput source="locator" label="Localizador" disabled />
    </SimpleForm>
  </Create>
);

import React from "react";
import { List, Datagrid, TextField, EditButton, DeleteButton, Edit, SimpleForm, TextInput, NumberInput, Create } from "react-admin";

// Lista de pedidos: muestra todos los pedidos
export const OrderList = (props) => (
  <List {...props}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <TextField source="user_id" label="ID Usuario" />
      <TextField source="total_amount" label="Monto Total" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

// Editar un pedido existente
export const OrderEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <TextInput source="user_id" label="ID Usuario" />
      <NumberInput source="total_amount" label="Monto Total" />
    </SimpleForm>
  </Edit>
);

// Crear un nuevo pedido
export const OrderCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <TextInput source="user_id" label="ID Usuario" />
      <NumberInput source="total_amount" label="Monto Total" />
    </SimpleForm>
  </Create>
);

import React from "react";
import { List, Datagrid, TextField, EmailField, BooleanField, EditButton, DeleteButton, Edit, SimpleForm, TextInput, BooleanInput, Create } from "react-admin";

// Lista de usuarios: muestra todos los usuarios
export const UserList = (props) => (
  <List {...props}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <TextField source="firstname" label="Nombre" />
      <TextField source="lastname" label="Apellido" />
      <EmailField source="email" label="Correo Electrónico" />
      <BooleanField source="is_admin" label="Administrador" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

// Editar un usuario existente
export const UserEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <TextInput source="firstname" label="Nombre" />
      <TextInput source="lastname" label="Apellido" />
      <TextInput source="email" label="Correo Electrónico" />
      <BooleanInput source="is_admin" label="Administrador" />
    </SimpleForm>
  </Edit>
);

// Crear un nuevo usuario
export const UserCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <TextInput source="firstname" label="Nombre" />
      <TextInput source="lastname" label="Apellido" />
      <TextInput source="email" label="Correo Electrónico" />
      <TextInput source="password" type="password" label="Contraseña" />
      <BooleanInput source="is_admin" label="Administrador" />
    </SimpleForm>
  </Create>
);

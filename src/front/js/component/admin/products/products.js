import React from "react";
import { List, Datagrid, TextField, NumberField, EditButton, DeleteButton, Edit, SimpleForm, TextInput, NumberInput, Create } from "react-admin";

// Lista de productos: muestra todos los productos
export const ProductList = (props) => (
  <List {...props}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <TextField source="nombre" label="Nombre" />
      <TextField source="descripcion" label="Descripción" />
      <NumberField source="precio" label="Precio" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

// Editar un producto existente
export const ProductEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <TextInput source="nombre" label="Nombre" />
      <TextInput source="descripcion" label="Descripción" />
      <NumberInput source="precio" label="Precio" />
    </SimpleForm>
  </Edit>
);

// Crear un nuevo producto
export const ProductCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <TextInput source="nombre" label="Nombre" />
      <TextInput source="descripcion" label="Descripción" />
      <NumberInput source="precio" label="Precio" />
    </SimpleForm>
  </Create>
);


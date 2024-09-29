import React from "react";
import { List, Datagrid, TextField, EditButton, DeleteButton, Edit, SimpleForm, TextInput, Create, NumberInput } from "react-admin";

// Lista de productos: muestra todos los productos
export const ProductList = (props) => (
  <List {...props}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <TextField source="nombre" label="Nombre" />
      <TextField source="descripcion" label="Descripción" />
      <TextField source="precio" label="Precio" />
      <TextField source="stock" label="Stock" />
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
      <NumberInput source="stock" label="Stock" />
      <TextInput source="alto" label="Alto" />
      <TextInput source="ancho" label="Ancho" />
      <TextInput source="anclaje" label="Anclaje" />
      <TextInput source="color" label="Color" />
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
      <NumberInput source="stock" label="Stock" />
      <TextInput source="alto" label="Alto" />
      <TextInput source="ancho" label="Ancho" />
      <TextInput source="anclaje" label="Anclaje" />
      <TextInput source="color" label="Color" />
    </SimpleForm>
  </Create>
);

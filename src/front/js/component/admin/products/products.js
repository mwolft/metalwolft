import React from "react";
import { List, Datagrid, TextField, NumberField, EditButton, DeleteButton, Edit, SimpleForm, TextInput, ImageField, Create, ImageInput } from "react-admin";

// Lista de productos: muestra todos los productos
export const ProductList = (props) => (
  <List {...props}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <TextField source="nombre" label="Nombre" />
      <TextField source="descripcion" label="Descripción" />
      <NumberField source="precio" label="Precio" />
      <TextField source="categoria_id" label="Categoría" />
      <ImageField source="imagen" label="Imagen Principal" />
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
      <TextInput source="precio" label="Precio" />
      <TextInput source="categoria_id" label="Categoría" />
      <ImageInput source="imagen" label="Actualizar Imagen Principal" accept="image/*">
        <ImageField source="src" title="title" />
      </ImageInput>
    </SimpleForm>
  </Edit>
);

// Crear un nuevo producto
export const ProductCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <TextInput source="nombre" label="Nombre" />
      <TextInput source="descripcion" label="Descripción" />
      <TextInput source="precio" label="Precio" />
      <TextInput source="categoria_id" label="Categoría" />
      <ImageInput source="imagen" label="Subir Imagen Principal" accept="image/*">
        <ImageField source="src" title="title" />
      </ImageInput>
    </SimpleForm>
  </Create>
);

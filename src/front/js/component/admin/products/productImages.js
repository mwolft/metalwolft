import React from "react";
import { List, Datagrid, ImageField, TextField, EditButton, DeleteButton, Edit, SimpleForm, TextInput, ImageInput, Create } from "react-admin";

// Lista de imágenes del producto: muestra todas las imágenes
export const ProductImages = (props) => (
  <List {...props}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <TextField source="product_id" label="Producto ID" />
      <ImageField source="image_url" label="Imagen" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

// Editar una imagen del producto existente
export const ProductImageEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <TextInput disabled source="product_id" label="Producto ID" />
      <ImageInput source="image" label="Subir nueva imagen" accept="image/*">
        <ImageField source="src" title="title" />
      </ImageInput>
    </SimpleForm>
  </Edit>
);

// Crear una nueva imagen para un producto
export const ProductImageCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <TextInput source="product_id" label="Producto ID" />
      <ImageInput source="image" label="Subir imagen" accept="image/*">
        <ImageField source="src" title="title" />
      </ImageInput>
    </SimpleForm>
  </Create>
);

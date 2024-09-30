// ProductImages.js
import React from "react";
import { List, Datagrid, TextField, ReferenceField, ImageField, EditButton, DeleteButton, Edit, SimpleForm, TextInput, ReferenceInput, SelectInput, Create } from "react-admin";

// Lista de imágenes de productos
export const ProductImagesList = (props) => (
  <List {...props}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <ReferenceField source="product_id" reference="products" label="Producto">
        <TextField source="nombre" />
      </ReferenceField>
      <ImageField source="image_url" label="Imagen" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

// Editar una imagen de producto existente
export const ProductImagesEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <ReferenceInput source="product_id" reference="products" label="Producto">
        <SelectInput optionText="nombre" />
      </ReferenceInput>
      <TextInput source="image_url" label="URL de la Imagen" />
    </SimpleForm>
  </Edit>
);

// Crear una nueva imagen de producto
export const ProductImagesCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <ReferenceInput source="product_id" reference="products" label="Producto">
        <SelectInput optionText="nombre" />
      </ReferenceInput>
      <TextInput source="image_url" label="URL de la Imagen" />
    </SimpleForm>
  </Create>
);

// src/components/admin/products/products.js
import React from "react";
import { List, Datagrid, TextField, NumberField, EditButton, DeleteButton } from "react-admin";

// Lista de productos: muestra todos los productos
export const ProductList = (props) => (
  <List {...props}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <TextField source="nombre" label="Nombre" />
      <TextField source="descripcion" label="Descripción" />
      <NumberField source="precio" label="Precio" />
      <NumberField source="stock" label="Stock" />
      <TextField source="alto" label="Alto" />
      <TextField source="ancho" label="Ancho" />
      <TextField source="anclaje" label="Anclaje" />
      <TextField source="color" label="Color" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

import React from "react";
import { List, Datagrid, TextField, NumberField, EditButton, DeleteButton, Edit, SimpleForm, TextInput, NumberInput, Create, ReferenceField, ReferenceInput, SelectInput } from "react-admin";

// Lista de detalles de órdenes: muestra todos los detalles de órdenes
export const OrderDetailsList = (props) => (
  <List {...props}>
    <Datagrid>
      <TextField source="id" label="ID" />
      <ReferenceField source="order_id" reference="orders" label="Número de Orden">
        <TextField source="id" />
      </ReferenceField>
      <ReferenceField source="product_id" reference="products" label="Producto">
        <TextField source="nombre" />
      </ReferenceField>
      <NumberField source="quantity" label="Cantidad" />
      <NumberField source="alto" label="Alto" />
      <NumberField source="ancho" label="Ancho" />
      <TextField source="anclaje" label="Anclaje" />
      <TextField source="color" label="Color" />
      <EditButton />
      <DeleteButton />
    </Datagrid>
  </List>
);

// Editar un detalle de orden existente
export const OrderDetailsEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <ReferenceInput source="order_id" reference="orders" label="Número de Orden">
        <SelectInput optionText="id" />
      </ReferenceInput>
      <ReferenceInput source="product_id" reference="products" label="Producto">
        <SelectInput optionText="nombre" />
      </ReferenceInput>
      <NumberInput source="quantity" label="Cantidad" />
      <NumberInput source="alto" label="Alto" />
      <NumberInput source="ancho" label="Ancho" />
      <TextInput source="anclaje" label="Anclaje" />
      <TextInput source="color" label="Color" />
    </SimpleForm>
  </Edit>
);

// Crear un nuevo detalle de orden
export const OrderDetailsCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <ReferenceInput source="order_id" reference="orders" label="Número de Orden">
        <SelectInput optionText="id" />
      </ReferenceInput>
      <ReferenceInput source="product_id" reference="products" label="Producto">
        <SelectInput optionText="nombre" />
      </ReferenceInput>
      <NumberInput source="quantity" label="Cantidad" />
      <NumberInput source="alto" label="Alto" />
      <NumberInput source="ancho" label="Ancho" />
      <TextInput source="anclaje" label="Anclaje" />
      <TextInput source="color" label="Color" />
    </SimpleForm>
  </Create>
);
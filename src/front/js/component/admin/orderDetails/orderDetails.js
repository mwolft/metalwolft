import React from "react";
import {
  List,
  TextField,
  NumberField,
  EditButton,
  DeleteButton,
  Edit,
  SimpleForm,
  TextInput,
  NumberInput,
  Create,
  ReferenceField,
  ReferenceInput,
  SelectInput,
  useListContext,
  RecordContextProvider,
} from "react-admin";

const getOrderDetailRecords = (data, ids) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(ids) && data) {
    return ids.map((id) => data[id]).filter(Boolean);
  }

  return Object.values(data || {});
};

const OrderDetailsListTable = () => {
  const { data, ids, isLoading, isPending } = useListContext();
  const records = getOrderDetailRecords(data, ids);

  if (isLoading || isPending) {
    return <p className="admin-native-empty">Cargando detalles de pedido...</p>;
  }

  if (!records.length) {
    return <p className="admin-native-empty">No hay detalles de pedido para mostrar.</p>;
  }

  return (
    <div className="admin-native-scroll admin-native-scroll--order-details">
      <table className="admin-native-table admin-native-table--order-details">
        <thead>
          <tr>
            <th>Nº</th>
            <th>Producto</th>
            <th>Cantidad</th>
            <th>Alto</th>
            <th>Ancho</th>
            <th>Anclaje</th>
            <th>Color</th>
            <th>Precio Total</th>
            <th>Localizador</th>
            <th>N factura</th>
            <th>Nombre</th>
            <th>Apellido</th>
            <th>Direccion de Facturacion</th>
            <th>Ciudad de Facturacion</th>
            <th>Codigo Postal de Facturacion</th>
            <th>CIF</th>
            <th>Direccion de Envio</th>
            <th>Ciudad de Envio</th>
            <th>Codigo Postal de Envio</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <RecordContextProvider key={record.id} value={record}>
              <tr>
                <td>
                  <ReferenceField source="order_id" reference="orders">
                    <TextField source="id" />
                  </ReferenceField>
                </td>
                <td>
                  <ReferenceField source="product_id" reference="products">
                    <TextField source="nombre" />
                  </ReferenceField>
                </td>
                <td><NumberField source="quantity" /></td>
                <td><NumberField source="alto" /></td>
                <td><NumberField source="ancho" /></td>
                <td><TextField source="anclaje" /></td>
                <td><TextField source="color" /></td>
                <td><NumberField source="precio_total" /></td>
                <td><TextField source="locator" /></td>
                <td><TextField source="invoice_number" /></td>
                <td><TextField source="firstname" /></td>
                <td><TextField source="lastname" /></td>
                <td><TextField source="billing_address" /></td>
                <td><TextField source="billing_city" /></td>
                <td><TextField source="billing_postal_code" /></td>
                <td><TextField source="CIF" /></td>
                <td><TextField source="shipping_address" /></td>
                <td><TextField source="shipping_city" /></td>
                <td><TextField source="shipping_postal_code" /></td>
                <td>
                  <div className="admin-action-group">
                    <EditButton className="admin-ra-button admin-ra-button--secondary" />
                    <DeleteButton className="admin-ra-button admin-ra-button--danger" />
                  </div>
                </td>
              </tr>
            </RecordContextProvider>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export const OrderDetailsList = (props) => (
  <List {...props} className="admin-resource-list">
    <OrderDetailsListTable />
  </List>
);

export const OrderDetailsEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <ReferenceInput source="order_id" reference="orders" label="Numero de Orden">
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
      <NumberInput source="precio_total" label="Precio Total" />
      <TextInput source="firstname" label="Nombre" />
      <TextInput source="lastname" label="Apellido" />
      <TextInput source="shipping_address" label="Direccion de Envio" />
      <TextInput source="shipping_city" label="Ciudad de Envio" />
      <TextInput source="shipping_postal_code" label="Codigo Postal de Envio" />
      <TextInput source="billing_address" label="Direccion de Facturacion" />
      <TextInput source="billing_city" label="Ciudad de Facturacion" />
      <TextInput source="billing_postal_code" label="Codigo Postal de Facturacion" />
      <TextInput source="CIF" label="CIF" />
    </SimpleForm>
  </Edit>
);

export const OrderDetailsCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <ReferenceInput source="order_id" reference="orders" label="Numero de Orden">
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
      <NumberInput source="precio_total" label="Precio Total" />
      <TextInput source="firstname" label="Nombre" />
      <TextInput source="lastname" label="Apellido" />
      <TextInput source="shipping_address" label="Direccion de Envio" />
      <TextInput source="shipping_city" label="Ciudad de Envio" />
      <TextInput source="shipping_postal_code" label="Codigo Postal de Envio" />
      <TextInput source="billing_address" label="Direccion de Facturacion" />
      <TextInput source="billing_city" label="Ciudad de Facturacion" />
      <TextInput source="billing_postal_code" label="Codigo Postal de Facturacion" />
      <TextInput source="CIF" label="CIF" />
    </SimpleForm>
  </Create>
);

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
  DateField,
  useListContext,
  RecordContextProvider,
} from "react-admin";

const getOrderRecords = (data, ids) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(ids) && data) {
    return ids.map((id) => data[id]).filter(Boolean);
  }

  return Object.values(data || {});
};

const OrderListTable = () => {
  const { data, ids, isLoading, isPending } = useListContext();
  const records = getOrderRecords(data, ids);

  if (isLoading || isPending) {
    return <p className="admin-native-empty">Cargando pedidos...</p>;
  }

  if (!records.length) {
    return <p className="admin-native-empty">No hay pedidos para mostrar.</p>;
  }

  return (
    <div className="admin-native-scroll">
      <table className="admin-native-table admin-native-table--orders">
        <thead>
          <tr>
            <th>ID</th>
            <th>Monto Total</th>
            <th>Fecha de Orden</th>
            <th>Número de Factura</th>
            <th>Localizador</th>
            <th>Estado del Pedido</th>
            <th className="admin-cell-note">Nota de Entrega</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <RecordContextProvider key={record.id} value={record}>
              <tr>
                <td><TextField source="id" /></td>
                <td><NumberField source="total_amount" /></td>
                <td><DateField source="order_date" /></td>
                <td><TextField source="invoice_number" /></td>
                <td><TextField source="locator" /></td>
                <td><TextField source="order_status" /></td>
                <td className="admin-cell-note"><TextField source="estimated_delivery_note" /></td>
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

// Lista de órdenes: muestra todas las órdenes
export const OrderList = (props) => (
  <List {...props} sort={{ field: "id", order: "DESC" }} className="admin-resource-list">
    <OrderListTable />
  </List>
);

// Editar una orden existente
export const OrderEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <NumberInput source="total_amount" label="Monto Total" />
      <TextInput source="order_date" label="Fecha de Orden" />
      <TextInput source="invoice_number" label="Número de Factura" disabled />
      <TextInput source="locator" label="Localizador" disabled />
    </SimpleForm>
  </Edit>
);

// Crear una nueva orden
export const OrderCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <NumberInput source="total_amount" label="Monto Total" />
      <TextInput source="order_date" label="Fecha de Orden" />
      <TextInput source="invoice_number" label="Número de Factura" disabled />
      <TextInput source="locator" label="Localizador" disabled />
    </SimpleForm>
  </Create>
);

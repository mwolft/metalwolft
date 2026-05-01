import React from "react";
import {
  List,
  TextField,
  NumberField,
  DateField,
  EditButton,
  DeleteButton,
  Edit,
  SimpleForm,
  TextInput,
  NumberInput,
  DateInput,
  SelectInput,
  Create,
  useListContext,
  RecordContextProvider,
} from "react-admin";

const ORDER_STATUS_CHOICES = [
  { id: "pendiente", name: "Pendiente" },
  { id: "fabricacion", name: "En fabricacion" },
  { id: "pintura", name: "En pintura" },
  { id: "embalaje", name: "En embalaje" },
  { id: "enviado", name: "Enviado" },
  { id: "entregado", name: "Entregado" },
];

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
            <th>Monto total</th>
            <th>Fecha de pedido</th>
            <th>Numero de factura</th>
            <th>Localizador</th>
            <th>Estado del pedido</th>
            <th className="admin-cell-note">Nota de entrega</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <RecordContextProvider key={record.id} value={record}>
              <tr>
                <td>
                  <TextField source="id" />
                </td>
                <td>
                  <NumberField source="total_amount" />
                </td>
                <td>
                  <DateField source="order_date" />
                </td>
                <td>
                  <TextField source="invoice_number" />
                </td>
                <td>
                  <TextField source="locator" />
                </td>
                <td>
                  <TextField source="order_status" />
                </td>
                <td className="admin-cell-note">
                  <TextField source="estimated_delivery_note" />
                </td>
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

export const OrderList = (props) => (
  <List {...props} sort={{ field: "id", order: "DESC" }} className="admin-resource-list">
    <OrderListTable />
  </List>
);

export const OrderEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" fullWidth />
      <NumberInput disabled source="total_amount" label="Monto total" fullWidth />
      <TextInput disabled source="order_date" label="Fecha de pedido" fullWidth />
      <TextInput disabled source="invoice_number" label="Numero de factura" fullWidth />
      <TextInput disabled source="locator" label="Localizador" fullWidth />

      <h4 className="admin-form-section-title">Gestion operativa</h4>

      <SelectInput
        source="order_status"
        label="Estado del pedido"
        choices={ORDER_STATUS_CHOICES}
        fullWidth
        defaultValue="pendiente"
      />
      <DateInput
        source="estimated_delivery_at"
        label="Fecha estimada de entrega"
        fullWidth
      />
      <TextInput
        source="estimated_delivery_note"
        label="Nota de entrega"
        multiline
        minRows={3}
        fullWidth
      />
    </SimpleForm>
  </Edit>
);

export const OrderCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <NumberInput source="total_amount" label="Monto total" />
      <TextInput source="order_date" label="Fecha de pedido" />
      <TextInput source="invoice_number" label="Numero de factura" disabled />
      <TextInput source="locator" label="Localizador" disabled />
    </SimpleForm>
  </Create>
);

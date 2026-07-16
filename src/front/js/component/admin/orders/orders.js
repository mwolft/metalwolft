import React, { useState } from "react";
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
  useRecordContext,
  useNotify,
  useRefresh,
} from "react-admin";
import { FaFileAlt, FaFileInvoice } from "react-icons/fa";

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

const getBackendUrl = () => process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";

const getAdminToken = () => localStorage.getItem("token");

const WorkOrderButton = () => {
  const record = useRecordContext();

  const handleDownload = async () => {
    if (!record?.id) {
      alert("No se encontro informacion para este pedido.");
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      alert("Debes iniciar sesion para descargar el parte de trabajo.");
      return;
    }

    const backendUrl = process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";

    try {
      const response = await fetch(`${backendUrl}/api/admin/work-order/${record.id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error("No tienes permiso para descargar este parte de trabajo.");
        }

        if (response.status === 404) {
          throw new Error("No se encontro el pedido solicitado.");
        }

        const data = await response.json().catch(() => null);
        throw new Error(data?.message || data?.error || "No se pudo descargar el parte de trabajo.");
      }

      const blob = await response.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const fallbackName = `parte-trabajo-${record.locator || record.id}.pdf`;
      const contentDisposition = response.headers.get("Content-Disposition") || "";
      const matchedFilename = contentDisposition.match(/filename="?([^"]+)"?/i);

      link.href = objectUrl;
      link.download = matchedFilename?.[1] || fallbackName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(objectUrl);
    } catch (error) {
      alert(error.message || "No se pudo descargar el parte de trabajo.");
    }
  };

  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        handleDownload();
      }}
      className="admin-action-button admin-action-button--primary"
    >
      <FaFileAlt /> Parte de trabajo
    </button>
  );
};

const IssueInvoiceButton = () => {
  const record = useRecordContext();
  const notify = useNotify();
  const refresh = useRefresh();
  const [isIssuing, setIsIssuing] = useState(false);

  const handleIssueInvoice = async () => {
    if (isIssuing) {
      return;
    }

    if (!record?.id) {
      notify("No se encontro informacion para este pedido.", { type: "warning" });
      return;
    }

    if (record.invoice_number) {
      notify(`Este pedido ya tiene factura ${record.invoice_number}.`, { type: "info" });
      return;
    }

    const confirmed = window.confirm(
      `Emitir una factura ordinaria para el pedido ${record.locator || record.id}?`
    );

    if (!confirmed) {
      return;
    }

    const token = getAdminToken();
    if (!token) {
      notify("Debes iniciar sesion para emitir facturas.", { type: "warning" });
      return;
    }

    setIsIssuing(true);

    try {
      const response = await fetch(`${getBackendUrl()}/api/admin/orders/${record.id}/issue-invoice`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.message || data?.error || "No se pudo emitir la factura.");
      }

      notify(`Factura ${data?.invoice_number || ""} emitida correctamente.`, { type: "success" });
      refresh();
    } catch (error) {
      notify(error.message || "No se pudo emitir la factura.", { type: "error" });
    } finally {
      setIsIssuing(false);
    }
  };

  if (record?.invoice_number) {
    return null;
  }

  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        handleIssueInvoice();
      }}
      disabled={isIssuing}
      className="admin-action-button admin-action-button--success"
    >
      <FaFileInvoice /> {isIssuing ? "Emitiendo..." : "Emitir factura"}
    </button>
  );
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
                    <WorkOrderButton />
                    <IssueInvoiceButton />
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
      <div className="admin-action-group admin-action-group--form">
        <IssueInvoiceButton />
      </div>

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

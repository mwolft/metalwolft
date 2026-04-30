import React from "react";
import {
  List,
  TextField,
  DateField,
  NumberField,
  Create,
  SimpleForm,
  TextInput,
  NumberInput,
  ArrayInput,
  SimpleFormIterator,
  Edit,
  useRecordContext,
  useRefresh,
  useListContext,
  RecordContextProvider,
} from "react-admin";
import { FaDownload, FaSyncAlt } from "react-icons/fa";

const DownloadButton = () => {
  const record = useRecordContext();

  const handleDownload = async () => {
    if (!record) {
      alert("No se encontró información para esta factura.");
      return;
    }

    if (!record.pdf_path) {
      alert("No se encontró el archivo PDF para esta factura.");
      return;
    }

    const backendUrl = process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";
    const downloadUrl = record.pdf_path?.startsWith("http")
      ? record.pdf_path
      : `${backendUrl}${record.pdf_path}`;
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Debes iniciar sesión para descargar la factura.");
      return;
    }

    try {
      const response = await fetch(downloadUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("No se pudo descargar la factura.");
      }

      const blob = await response.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      const filename = record.pdf_path.split("/").pop() || `${record.invoice_number}.pdf`;
      const link = document.createElement("a");

      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(objectUrl);
    } catch (error) {
      alert(error.message || "No se pudo descargar la factura.");
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
      <FaDownload /> Descargar
    </button>
  );
};

const RegenerateButton = () => {
  const record = useRecordContext();
  const refresh = useRefresh();

  const handleRegenerate = async () => {
    if (!record) {
      alert("No se encontró información para esta factura.");
      return;
    }

    if (!record.order_id) {
      alert("Solo se pueden regenerar facturas asociadas a pedidos.");
      return;
    }

    const confirmed = window.confirm(
      `¿Seguro que quieres regenerar manualmente el PDF de la factura ${record.invoice_number}?`
    );

    if (!confirmed) {
      return;
    }

    const backendUrl = process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Debes iniciar sesión para regenerar la factura.");
      return;
    }

    try {
      const response = await fetch(
        `${backendUrl}/api/invoices/${record.id}/regenerate-pdf`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.message || "No se pudo regenerar la factura.");
      }

      alert(data?.message || "Factura regenerada correctamente.");
      refresh();
    } catch (error) {
      alert(error.message || "No se pudo regenerar la factura.");
    }
  };

  if (!record?.order_id) {
    return null;
  }

  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        handleRegenerate();
      }}
      className="admin-action-button admin-action-button--danger"
    >
      <FaSyncAlt /> Regenerar PDF
    </button>
  );
};

const getInvoiceRecords = (data, ids) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(ids) && data) {
    return ids.map((id) => data[id]).filter(Boolean);
  }

  return Object.values(data || {});
};

const InvoiceListTable = () => {
  const { data, ids, isLoading, isPending } = useListContext();
  const records = getInvoiceRecords(data, ids);

  if (isLoading || isPending) {
    return <p className="admin-native-empty">Cargando facturas...</p>;
  }

  if (!records.length) {
    return <p className="admin-native-empty">No hay facturas para mostrar.</p>;
  }

  return (
    <div className="admin-native-scroll">
      <table className="admin-native-table admin-native-table--invoices">
        <thead>
          <tr>
            <th>Número de Factura</th>
            <th>Cliente</th>
            <th>Teléfono</th>
            <th>Total</th>
            <th>Fecha</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <RecordContextProvider key={record.id} value={record}>
              <tr>
                <td><TextField source="invoice_number" /></td>
                <td><TextField source="client_name" /></td>
                <td><TextField source="client_phone" /></td>
                <td><NumberField source="amount" options={{ style: "currency", currency: "EUR" }} /></td>
                <td><DateField source="created_at" /></td>
                <td>
                  <div className="admin-action-group">
                    <DownloadButton />
                    <RegenerateButton />
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

export const InvoiceList = (props) => (
  <List {...props} title="Facturas" className="admin-resource-list">
    <InvoiceListTable />
  </List>
);

export const InvoiceCreate = (props) => (
  <Create {...props} title="Crear Factura Manual">
    <SimpleForm>
      <TextInput source="client_name" label="Nombre del Cliente" />
      <TextInput source="client_address" label="Dirección del Cliente" />
      <TextInput source="client_cif" label="CIF del Cliente" />
      <TextInput source="client_phone" label="Teléfono" />
      <NumberInput source="amount" label="Monto Total (€)" />
      <ArrayInput source="order_details" label="Detalles del Pedido">
        <SimpleFormIterator>
          <TextInput source="product" label="Producto" />
          <NumberInput source="quantity" label="Cantidad" />
          <NumberInput source="price" label="Precio Unitario (€)" />
        </SimpleFormIterator>
      </ArrayInput>
    </SimpleForm>
  </Create>
);

export const InvoiceEdit = (props) => (
  <Edit {...props} title="Editar Factura">
    <SimpleForm>
      <TextInput source="client_name" label="Nombre del Cliente" />
      <TextInput source="client_address" label="Dirección del Cliente" />
      <TextInput source="client_cif" label="CIF del Cliente" />
      <TextInput source="client_phone" label="Teléfono" />
      <NumberInput source="amount" label="Monto Total (€)" />
      <ArrayInput source="order_details" label="Detalles del Pedido">
        <SimpleFormIterator>
          <TextInput source="product" label="Producto" />
          <NumberInput source="quantity" label="Cantidad" />
          <NumberInput source="price" label="Precio Unitario (€)" />
        </SimpleFormIterator>
      </ArrayInput>
      <TextField source="pdf_path" label="Ruta del PDF" />
      <div className="admin-action-group admin-action-group--form">
        <DownloadButton />
        <RegenerateButton />
      </div>
    </SimpleForm>
  </Edit>
);

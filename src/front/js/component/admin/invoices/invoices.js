import React from "react";
import {
  List,
  Datagrid,
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
} from "react-admin";
import { FaDownload, FaSyncAlt } from "react-icons/fa";

const buttonBaseStyle = {
  color: "#FFF",
  padding: "5px 10px",
  border: "none",
  borderRadius: "4px",
  cursor: "pointer",
};

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
    const downloadUrl = record.pdf_path?.startsWith('http')
      ? record.pdf_path
      : `${backendUrl}${record.pdf_path}`;
    const token = localStorage.getItem("token");

    if (!token) {
      alert("Debes iniciar sesiÃ³n para descargar la factura.");
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
      style={{
        ...buttonBaseStyle,
        backgroundColor: "#007BFF",
      }}
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
      style={{
        ...buttonBaseStyle,
        backgroundColor: "#dc3545",
      }}
    >
      <FaSyncAlt /> Regenerar PDF
    </button>
  );
};

const InvoiceActions = () => (
  <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
    <DownloadButton />
    <RegenerateButton />
  </div>
);

export const InvoiceList = (props) => (
  <List {...props} title="Facturas">
    <Datagrid rowClick="edit">
      <TextField source="invoice_number" label="Número de Factura" />
      <TextField source="client_name" label="Cliente" />
      <TextField source="client_phone" label="Teléfono" />
      <NumberField source="amount" label="Total" options={{ style: "currency", currency: "EUR" }} />
      <DateField source="created_at" label="Fecha" />
      <TextField source="pdf_path" label="Ruta del PDF" />
      <InvoiceActions />
    </Datagrid>
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
      <DownloadButton />
      <RegenerateButton />
    </SimpleForm>
  </Edit>
);

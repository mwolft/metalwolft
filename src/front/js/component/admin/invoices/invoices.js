import React from "react";
import {
  List,
  Datagrid,
  TextField,
  DateField,
  NumberField,
  Button,
  Create,
  SimpleForm,
  TextInput,
  NumberInput,
  ArrayInput,
  SimpleFormIterator,
  Edit,
} from "react-admin";
import { FaDownload } from "react-icons/fa";

// Botón de descarga para el PDF de la factura
const DownloadButton = ({ record }) => {
  const handleDownload = () => {
    if (!record || !record.pdf_path) {
        alert("No se encontró el archivo PDF para esta factura.");
        return;
    }

    const backendUrl = process.env.REACT_APP_BACKEND_URL || "http://localhost:3001"; // Cambia según tu configuración
    const downloadUrl = `${backendUrl}${record.pdf_path}`;
    console.log("Descargando desde:", downloadUrl);

    window.open(downloadUrl, "_blank");
};


  return (
    <button
      onClick={handleDownload}
      style={{
        backgroundColor: "#007BFF",
        color: "#FFF",
        padding: "5px 10px",
        border: "none",
        borderRadius: "4px",
        cursor: "pointer",
      }}
    >
      <FaDownload /> Descargar
    </button>
  );
};

// Listado de facturas
export const InvoiceList = (props) => (
  <List {...props} title="Facturas">
    <Datagrid rowClick="edit">
      <TextField source="invoice_number" label="Número de Factura" />
      <TextField source="client_name" label="Cliente" />
      <NumberField source="amount" label="Total" options={{ style: "currency", currency: "EUR" }} />
      <DateField source="created_at" label="Fecha" />
      <TextField source="pdf_path" label="Ruta del PDF" />
      {/* El botón recibe el record automáticamente */}
      <DownloadButton />
    </Datagrid>
  </List>
);

// Crear nueva factura manual
export const InvoiceCreate = (props) => (
  <Create {...props} title="Crear Factura Manual">
    <SimpleForm>
      <TextInput source="client_name" label="Nombre del Cliente" />
      <TextInput source="client_address" label="Dirección del Cliente" />
      <TextInput source="client_cif" label="CIF del Cliente" />
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

// Editar factura existente
export const InvoiceEdit = (props) => (
  <Edit {...props} title="Editar Factura">
    <SimpleForm>
      <TextInput source="client_name" label="Nombre del Cliente" />
      <TextInput source="client_address" label="Dirección del Cliente" />
      <TextInput source="client_cif" label="CIF del Cliente" />
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
    </SimpleForm>
  </Edit>
);

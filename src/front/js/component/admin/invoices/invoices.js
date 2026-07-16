import React, { useState } from "react";
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
  useNotify,
  RecordContextProvider,
} from "react-admin";
import { FaBook, FaDownload, FaEnvelope, FaFilePdf } from "react-icons/fa";

const getBackendUrl = () => process.env.REACT_APP_BACKEND_URL || "http://localhost:3001";

const getAdminToken = () => localStorage.getItem("token");

const readActionError = async (response, fallbackMessage) => {
  const data = await response.json().catch(() => null);
  return data?.message || data?.error || fallbackMessage;
};

const AdminStatusChip = ({ children, tone = "neutral" }) => (
  <span className={`admin-status-chip admin-status-chip--${tone}`}>{children}</span>
);

const DownloadButton = () => {
  const record = useRecordContext();

  const handleDownload = async () => {
    if (!record) {
      alert("No se encontro informacion para esta factura.");
      return;
    }

    if (!record.pdf_path) {
      alert("No se encontro el archivo PDF para esta factura.");
      return;
    }

    const backendUrl = getBackendUrl();
    const downloadUrl = record.pdf_path?.startsWith("http")
      ? record.pdf_path
      : `${backendUrl}${record.pdf_path}`;
    const token = getAdminToken();

    if (!token) {
      alert("Debes iniciar sesion para descargar la factura.");
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

const InvoicePdfActionButton = () => {
  const record = useRecordContext();
  const notify = useNotify();
  const refresh = useRefresh();
  const [isLoading, setIsLoading] = useState(false);
  const hasPdf = Boolean(record?.pdf_available);

  const handlePdfAction = async () => {
    if (isLoading) return;

    if (!record?.id) {
      notify("No se encontro informacion para esta factura.", { type: "warning" });
      return;
    }

    if (hasPdf) {
      const confirmed = window.confirm(
        `Regenerar el PDF de la factura ${record.invoice_number}?`
      );
      if (!confirmed) return;
    }

    const token = getAdminToken();
    if (!token) {
      notify("Debes iniciar sesion para gestionar facturas.", { type: "warning" });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `${getBackendUrl()}/api/admin/invoices/${record.id}/generate-pdf`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ regenerate: hasPdf }),
        }
      );

      if (!response.ok) {
        throw new Error(await readActionError(response, "No se pudo generar el PDF."));
      }

      notify(hasPdf ? "PDF regenerado correctamente." : "PDF generado correctamente.", {
        type: "success",
      });
      refresh();
    } catch (error) {
      notify(error.message || "No se pudo generar el PDF.", { type: "error" });
    } finally {
      setIsLoading(false);
    }
  };

  if (!record?.invoice_number) return null;

  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        handlePdfAction();
      }}
      disabled={isLoading}
      className={hasPdf ? "admin-action-button admin-action-button--danger" : "admin-action-button admin-action-button--primary"}
    >
      <FaFilePdf /> {isLoading ? "Procesando..." : hasPdf ? "Regenerar PDF" : "Generar PDF"}
    </button>
  );
};

const RecordAccountingButton = () => {
  const record = useRecordContext();
  const notify = useNotify();
  const refresh = useRefresh();
  const [isLoading, setIsLoading] = useState(false);

  const handleRecordAccounting = async () => {
    if (isLoading) return;

    if (!record?.id) {
      notify("No se encontro informacion para esta factura.", { type: "warning" });
      return;
    }

    const token = getAdminToken();
    if (!token) {
      notify("Debes iniciar sesion para registrar contabilidad.", { type: "warning" });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `${getBackendUrl()}/api/admin/invoices/${record.id}/record-accounting`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(await readActionError(response, "No se pudo registrar la contabilidad."));
      }

      notify("Registro contable creado correctamente.", { type: "success" });
      refresh();
    } catch (error) {
      notify(error.message || "No se pudo registrar la contabilidad.", { type: "error" });
    } finally {
      setIsLoading(false);
    }
  };

  if (record?.accounting_entry_status) {
    return (
      <AdminStatusChip tone="success">
        Contabilidad: {record.accounting_entry_status}
      </AdminStatusChip>
    );
  }

  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        handleRecordAccounting();
      }}
      disabled={isLoading}
      className="admin-action-button admin-action-button--secondary"
    >
      <FaBook /> {isLoading ? "Registrando..." : "Registrar contabilidad"}
    </button>
  );
};

const SendInvoiceEmailButton = () => {
  const record = useRecordContext();
  const notify = useNotify();
  const refresh = useRefresh();
  const [isLoading, setIsLoading] = useState(false);

  const handleSendEmail = async () => {
    if (isLoading) return;

    if (!record?.id) {
      notify("No se encontro informacion para esta factura.", { type: "warning" });
      return;
    }

    if (!record.pdf_available) {
      notify("Genera el PDF antes de enviar la factura por email.", { type: "warning" });
      return;
    }

    const confirmed = window.confirm(`Enviar por email la factura ${record.invoice_number}?`);
    if (!confirmed) return;

    const token = getAdminToken();
    if (!token) {
      notify("Debes iniciar sesion para enviar facturas.", { type: "warning" });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `${getBackendUrl()}/api/admin/invoices/${record.id}/send-email`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(await readActionError(response, "No se pudo enviar la factura por email."));
      }

      notify("Factura enviada por email correctamente.", { type: "success" });
      refresh();
    } catch (error) {
      notify(error.message || "No se pudo enviar la factura por email.", { type: "error" });
    } finally {
      setIsLoading(false);
    }
  };

  if (record?.email_status === "sent") {
    return <AdminStatusChip tone="success">Email enviado</AdminStatusChip>;
  }

  if (!record?.pdf_available) {
    return (
      <button
        type="button"
        disabled
        className="admin-action-button admin-action-button--secondary"
      >
        <FaEnvelope /> PDF requerido
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        handleSendEmail();
      }}
      disabled={isLoading}
      className="admin-action-button admin-action-button--success"
    >
      <FaEnvelope /> {isLoading ? "Enviando..." : "Enviar email"}
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
            <th>Numero de Factura</th>
            <th>Cliente</th>
            <th>Telefono</th>
            <th>Total</th>
            <th>Fecha</th>
            <th>PDF</th>
            <th>Contabilidad</th>
            <th>Email</th>
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
                  <AdminStatusChip tone={record.pdf_available ? "success" : "warning"}>
                    {record.pdf_available ? "Generado" : "Pendiente"}
                  </AdminStatusChip>
                </td>
                <td>
                  <AdminStatusChip tone={record.accounting_entry_status ? "success" : "warning"}>
                    {record.accounting_entry_status || "Pendiente"}
                  </AdminStatusChip>
                </td>
                <td>
                  <AdminStatusChip tone={record.email_status === "sent" ? "success" : "warning"}>
                    {record.email_status === "sent" ? "Enviado" : "Pendiente"}
                  </AdminStatusChip>
                </td>
                <td>
                  <div className="admin-action-group">
                    <DownloadButton />
                    <InvoicePdfActionButton />
                    <RecordAccountingButton />
                    <SendInvoiceEmailButton />
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
  <List {...props} title="Facturas" sort={{ field: "id", order: "DESC" }} className="admin-resource-list">
    <InvoiceListTable />
  </List>
);

export const InvoiceCreate = (props) => (
  <Create {...props} title="Crear Factura Manual">
    <SimpleForm>
      <TextInput source="client_name" label="Nombre del Cliente" />
      <TextInput source="client_address" label="Direccion del Cliente" />
      <TextInput source="client_cif" label="CIF del Cliente" />
      <TextInput source="client_phone" label="Telefono" />
      <NumberInput source="amount" label="Monto Total (EUR)" />
      <ArrayInput source="order_details" label="Detalles del Pedido">
        <SimpleFormIterator>
          <TextInput source="product" label="Producto" />
          <NumberInput source="quantity" label="Cantidad" />
          <NumberInput source="price" label="Precio Unitario (EUR)" />
        </SimpleFormIterator>
      </ArrayInput>
    </SimpleForm>
  </Create>
);

export const InvoiceEdit = (props) => (
  <Edit {...props} title="Editar Factura">
    <SimpleForm>
      <TextInput source="client_name" label="Nombre del Cliente" />
      <TextInput source="client_address" label="Direccion del Cliente" />
      <TextInput source="client_cif" label="CIF del Cliente" />
      <TextInput source="client_phone" label="Telefono" />
      <NumberInput source="amount" label="Monto Total (EUR)" />
      <ArrayInput source="order_details" label="Detalles del Pedido">
        <SimpleFormIterator>
          <TextInput source="product" label="Producto" />
          <NumberInput source="quantity" label="Cantidad" />
          <NumberInput source="price" label="Precio Unitario (EUR)" />
        </SimpleFormIterator>
      </ArrayInput>
      <TextField source="pdf_path" label="Ruta del PDF" />
      <TextField source="invoice_type" label="Tipo fiscal" />
      <TextField source="email_status" label="Estado email" />
      <TextField source="accounting_entry_status" label="Estado contable" />
      <div className="admin-action-group admin-action-group--form">
        <DownloadButton />
        <InvoicePdfActionButton />
        <RecordAccountingButton />
        <SendInvoiceEmailButton />
      </div>
    </SimpleForm>
  </Edit>
);

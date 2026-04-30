import React, { useState } from "react";
import {
  List,
  Datagrid,
  TextField,
  EmailField,
  BooleanField,
  EditButton,
  DeleteButton,
  Edit,
  SimpleForm,
  TextInput,
  BooleanInput,
  Create,
  useRecordContext,
  useRefresh
} from "react-admin";

const SendCartReminderButton = () => {
  const record = useRecordContext();
  const refresh = useRefresh();
  const [isSending, setIsSending] = useState(false);

  if (!record?.id || record?.is_admin || !record?.has_active_cart) {
    return null;
  }

  const handleSendReminder = async (event) => {
    event.stopPropagation();

    const confirmed = window.confirm(
      `¿Seguro que quieres enviar un recordatorio de carrito al usuario ${record.email || record.id}?`
    );

    if (!confirmed) {
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      alert("Debes iniciar sesión como administrador para enviar recordatorios.");
      return;
    }

    setIsSending(true);

    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/admin/cart-reminders/${record.id}/send`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = await response.json().catch(() => null);
      const message = data?.message || "No se pudo procesar el recordatorio.";

      if (response.status === 200) {
        alert(message);
        refresh();
        return;
      }

      if (response.status === 400 || response.status === 403 || response.status === 409) {
        alert(message);
        return;
      }

      throw new Error(message);
    } catch (error) {
      alert(error.message || "No se pudo enviar el recordatorio del carrito.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleSendReminder}
      disabled={isSending}
      style={{
        border: "1px solid #0d6efd",
        background: "#ffffff",
        color: "#0d6efd",
        borderRadius: "6px",
        padding: "6px 10px",
        fontSize: "0.85rem",
        cursor: isSending ? "not-allowed" : "pointer"
      }}
    >
      {isSending ? "Enviando..." : "Enviar recordatorio carrito"}
    </button>
  );
};

// Lista de usuarios: muestra todos los usuarios
export const UserList = (props) => (
  <List
    {...props}
    sort={{ field: "id", order: "DESC" }}
  >
    <div style={{ overflowX: "auto", width: "100%" }}>
      <Datagrid>
        <TextField source="id" label="ID" sortable={false} />
        <TextField source="firstname" label="Nombre" />
        <TextField source="lastname" label="Apellido" />
        <EmailField source="email" label="Correo Electrónico" />
        <BooleanField source="is_admin" label="Administrador" />
        <SendCartReminderButton />
        <EditButton />
        <DeleteButton />
      </Datagrid>
    </div>
  </List>
);

// Editar un usuario existente
export const UserEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <TextInput source="firstname" label="Nombre" />
      <TextInput source="lastname" label="Apellido" />
      <TextInput source="email" label="Correo Electrónico" />
      <BooleanInput source="is_admin" label="Administrador" />
    </SimpleForm>
  </Edit>
);

// Crear un nuevo usuario
export const UserCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <TextInput source="firstname" label="Nombre" />
      <TextInput source="lastname" label="Apellido" />
      <TextInput source="email" label="Correo Electrónico" />
      <TextInput source="password" type="password" label="Contraseña" />
      <BooleanInput source="is_admin" label="Administrador" />
    </SimpleForm>
  </Create>
);

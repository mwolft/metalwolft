import React, { useState } from "react";
import { FaPaperPlane } from "react-icons/fa";
import {
  List,
  Datagrid,
  TextField,
  EmailField,
  BooleanField,
  EditButton,
  DeleteButton,
  WrapperField,
  Edit,
  SimpleForm,
  TextInput,
  BooleanInput,
  Create,
  useRecordContext,
  useRefresh
} from "react-admin";

const userDatagridSx = {
  minWidth: 1100,
  width: "max-content",
  "& .RaDatagrid-table": {
    minWidth: 1100,
    width: "max-content",
    tableLayout: "auto",
  },
  "& .MuiTable-root": {
    minWidth: 1100,
    width: "max-content",
    tableLayout: "auto",
  },
  "& .MuiTableCell-root": {
    whiteSpace: "nowrap",
  },
};

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
      className="admin-action-button admin-action-button--secondary admin-action-button--compact"
      title="Enviar recordatorio de carrito"
    >
      <FaPaperPlane />
      {isSending ? "Enviando..." : "Recordatorio"}
    </button>
  );
};

const UserActions = () => (
  <WrapperField label="Acciones">
    <div className="admin-action-group">
      <SendCartReminderButton />
      <EditButton className="admin-ra-button admin-ra-button--secondary" />
      <DeleteButton className="admin-ra-button admin-ra-button--danger" />
    </div>
  </WrapperField>
);

// Lista de usuarios: muestra todos los usuarios
export const UserList = (props) => (
  <List
    {...props}
    sort={{ field: "id", order: "DESC" }}
    className="admin-resource-list"
  >
    <div className="admin-table-scroll">
      <Datagrid sx={userDatagridSx}>
        <TextField source="id" label="ID" sortable={false} />
        <TextField source="firstname" label="Nombre" />
        <TextField source="lastname" label="Apellido" />
        <EmailField source="email" label="Correo Electrónico" />
        <BooleanField source="is_admin" label="Administrador" />
        <UserActions />
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

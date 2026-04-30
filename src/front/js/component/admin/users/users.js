import React, { useState } from "react";
import { FaPaperPlane } from "react-icons/fa";
import {
  List,
  EditButton,
  DeleteButton,
  Edit,
  SimpleForm,
  TextInput,
  BooleanInput,
  Create,
  useRecordContext,
  useRefresh,
  useListContext,
  RecordContextProvider,
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
      `Â¿Seguro que quieres enviar un recordatorio de carrito al usuario ${record.email || record.id}?`
    );

    if (!confirmed) {
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      alert("Debes iniciar sesiÃ³n como administrador para enviar recordatorios.");
      return;
    }

    setIsSending(true);

    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/admin/cart-reminders/${record.id}/send`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
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

const getUserRecords = (data, ids) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(ids) && data) {
    return ids.map((id) => data[id]).filter(Boolean);
  }

  return Object.values(data || {});
};

const UserListTable = () => {
  const { data, ids, isLoading } = useListContext();
  const records = getUserRecords(data, ids);

  if (isLoading) {
    return <p className="admin-native-empty">Cargando usuarios...</p>;
  }

  if (!records.length) {
    return <p className="admin-native-empty">No hay usuarios para mostrar.</p>;
  }

  return (
    <div className="admin-native-scroll">
      <table className="admin-native-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Apellido</th>
            <th>Correo ElectrÃ³nico</th>
            <th>Administrador</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <RecordContextProvider key={record.id} value={record}>
              <tr>
                <td>{record.id}</td>
                <td>{record.firstname || "-"}</td>
                <td>{record.lastname || "-"}</td>
                <td>{record.email || "-"}</td>
                <td>{record.is_admin ? "SÃ­" : "No"}</td>
                <td>
                  <div className="admin-action-group">
                    <SendCartReminderButton />
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

// Lista de usuarios: muestra todos los usuarios
export const UserList = (props) => (
  <List
    {...props}
    sort={{ field: "id", order: "DESC" }}
    className="admin-resource-list"
  >
    <UserListTable />
  </List>
);

// Editar un usuario existente
export const UserEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <TextInput source="firstname" label="Nombre" />
      <TextInput source="lastname" label="Apellido" />
      <TextInput source="email" label="Correo ElectrÃ³nico" />
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
      <TextInput source="email" label="Correo ElectrÃ³nico" />
      <TextInput source="password" type="password" label="ContraseÃ±a" />
      <BooleanInput source="is_admin" label="Administrador" />
    </SimpleForm>
  </Create>
);

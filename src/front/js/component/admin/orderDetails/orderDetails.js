import React, { useMemo, useState } from "react";
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
  ReferenceField,
  ReferenceInput,
  SelectInput,
  useListContext,
  RecordContextProvider,
} from "react-admin";

const getOrderDetailRecords = (data, ids) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(ids) && data) {
    return ids.map((id) => data[id]).filter(Boolean);
  }

  return Object.values(data || {});
};

const formatEstimatedDeliveryDate = (value) => {
  if (!value) {
    return "-";
  }

  const [year, month, day] = String(value).split("-");
  if (year && month && day) {
    return `${day}/${month}/${year}`;
  }

  return value;
};

const getEstimatedDeliveryDateKey = (value) => {
  if (!value) {
    return null;
  }

  return String(value).slice(0, 10);
};

const formatMonthLabel = (date) =>
  new Intl.DateTimeFormat("es-ES", {
    month: "long",
    year: "numeric",
  }).format(date);

const WEEKDAY_LABELS = ["L", "M", "X", "J", "V", "S", "D"];

const buildMonthDays = (date) => {
  const year = date.getFullYear();
  const month = date.getMonth();
  const firstDay = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const startOffset = (firstDay.getDay() + 6) % 7;
  const calendarCells = [];

  for (let index = 0; index < startOffset; index += 1) {
    calendarCells.push({ key: `empty-start-${index}`, isEmpty: true });
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const isoKey = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    calendarCells.push({
      key: isoKey,
      isoKey,
      dayNumber: day,
      isEmpty: false,
    });
  }

  while (calendarCells.length % 7 !== 0) {
    calendarCells.push({
      key: `empty-end-${calendarCells.length}`,
      isEmpty: true,
    });
  }

  return calendarCells;
};

const OrderDetailsMiniCalendar = ({ records, selectedDate, onSelectDate }) => {
  const currentMonth = useMemo(() => new Date(), []);
  const monthDays = useMemo(() => buildMonthDays(currentMonth), [currentMonth]);

  const deliveryCounts = useMemo(() => {
    const ordersByDate = records.reduce((accumulator, record) => {
      const dateKey = getEstimatedDeliveryDateKey(record.estimated_delivery_at);
      if (!dateKey || !record.order_id) {
        return accumulator;
      }

      if (!accumulator[dateKey]) {
        accumulator[dateKey] = new Set();
      }

      accumulator[dateKey].add(record.order_id);
      return accumulator;
    }, {});

    return Object.fromEntries(
      Object.entries(ordersByDate).map(([dateKey, orderIds]) => [dateKey, orderIds.size])
    );
  }, [records]);

  const hasDeliveriesInMonth = monthDays.some(
    (day) => !day.isEmpty && deliveryCounts[day.isoKey]
  );

  return (
    <aside className="admin-order-details-calendar-panel">
      <div className="admin-order-details-calendar-card">
        <div className="admin-order-details-calendar-header">
          <div>
            <p className="admin-order-details-calendar-eyebrow">Entregas</p>
            <h3 className="admin-order-details-calendar-title">
              {formatMonthLabel(currentMonth)}
            </h3>
          </div>
          {selectedDate ? (
            <button
              type="button"
              className="admin-action-button admin-action-button--compact admin-action-button--secondary"
              onClick={() => onSelectDate(null)}
            >
              Limpiar
            </button>
          ) : null}
        </div>

        <div className="admin-order-details-calendar-weekdays" aria-hidden="true">
          {WEEKDAY_LABELS.map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>

        <div className="admin-order-details-calendar-grid">
          {monthDays.map((day) => {
            if (day.isEmpty) {
              return (
                <span
                  key={day.key}
                  className="admin-order-details-calendar-day admin-order-details-calendar-day--empty"
                  aria-hidden="true"
                />
              );
            }

            const count = deliveryCounts[day.isoKey] || 0;
            const isActive = count > 0;
            const isSelected = selectedDate === day.isoKey;

            return (
              <button
                key={day.key}
                type="button"
                className={[
                  "admin-order-details-calendar-day",
                  isActive ? "admin-order-details-calendar-day--active" : "",
                  isSelected ? "admin-order-details-calendar-day--selected" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => onSelectDate(isSelected || !isActive ? null : day.isoKey)}
                disabled={!isActive}
                aria-pressed={isSelected}
                title={
                  isActive
                    ? `${count} pedido${count === 1 ? "" : "s"} con entrega estimada`
                    : "Sin entregas estimadas"
                }
              >
                <span>{day.dayNumber}</span>
                {isActive ? (
                  <span className="admin-order-details-calendar-count">{count}</span>
                ) : null}
              </button>
            );
          })}
        </div>

        <p className="admin-order-details-calendar-help">
          {selectedDate
            ? `Filas destacadas para ${formatEstimatedDeliveryDate(selectedDate)}.`
            : hasDeliveriesInMonth
              ? "Pulsa un día marcado para destacar sus líneas en la tabla."
              : "No hay entregas estimadas en el mes actual dentro de esta página."}
        </p>
      </div>
    </aside>
  );
};

const OrderDetailsListTable = () => {
  const { data, ids, isLoading, isPending } = useListContext();
  const records = getOrderDetailRecords(data, ids);
  const [selectedDate, setSelectedDate] = useState(null);

  if (isLoading || isPending) {
    return <p className="admin-native-empty">Cargando detalles de pedido...</p>;
  }

  if (!records.length) {
    return <p className="admin-native-empty">No hay detalles de pedido para mostrar.</p>;
  }

  return (
    <div className="admin-order-details-layout">
      <OrderDetailsMiniCalendar
        records={records}
        selectedDate={selectedDate}
        onSelectDate={setSelectedDate}
      />

      <div className="admin-order-details-table-panel">
        <div className="admin-native-scroll admin-native-scroll--order-details">
          <table className="admin-native-table admin-native-table--order-details">
            <thead>
              <tr>
                <th>Nº</th>
                <th>Producto</th>
                <th>Cantidad</th>
                <th>FECHA ENTREGA</th>
                <th>Alto</th>
                <th>Ancho</th>
                <th>Anclaje</th>
                <th>Color</th>
                <th>Precio Total</th>
                <th>Localizador</th>
                <th>N factura</th>
                <th>Nombre</th>
                <th>Apellido</th>
                <th>Direccion de Facturacion</th>
                <th>Ciudad de Facturacion</th>
                <th>Codigo Postal de Facturacion</th>
                <th>CIF</th>
                <th>Direccion de Envio</th>
                <th>Ciudad de Envio</th>
                <th>Codigo Postal de Envio</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => {
                const recordDate = getEstimatedDeliveryDateKey(record.estimated_delivery_at);
                const isSelected = selectedDate && recordDate === selectedDate;

                return (
                  <RecordContextProvider key={record.id} value={record}>
                    <tr className={isSelected ? "admin-order-details-row--selected" : ""}>
                      <td>
                        <ReferenceField source="order_id" reference="orders">
                          <TextField source="id" />
                        </ReferenceField>
                      </td>
                      <td>
                        <ReferenceField source="product_id" reference="products">
                          <TextField source="nombre" />
                        </ReferenceField>
                      </td>
                      <td><NumberField source="quantity" /></td>
                      <td>{formatEstimatedDeliveryDate(record.estimated_delivery_at)}</td>
                      <td><NumberField source="alto" /></td>
                      <td><NumberField source="ancho" /></td>
                      <td><TextField source="anclaje" /></td>
                      <td><TextField source="color" /></td>
                      <td><NumberField source="precio_total" /></td>
                      <td><TextField source="locator" /></td>
                      <td><TextField source="invoice_number" /></td>
                      <td><TextField source="firstname" /></td>
                      <td><TextField source="lastname" /></td>
                      <td><TextField source="billing_address" /></td>
                      <td><TextField source="billing_city" /></td>
                      <td><TextField source="billing_postal_code" /></td>
                      <td><TextField source="CIF" /></td>
                      <td><TextField source="shipping_address" /></td>
                      <td><TextField source="shipping_city" /></td>
                      <td><TextField source="shipping_postal_code" /></td>
                      <td>
                        <div className="admin-action-group">
                          <EditButton className="admin-ra-button admin-ra-button--secondary" />
                          <DeleteButton className="admin-ra-button admin-ra-button--danger" />
                        </div>
                      </td>
                    </tr>
                  </RecordContextProvider>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export const OrderDetailsList = (props) => (
  <List {...props} perPage={20} className="admin-resource-list">
    <OrderDetailsListTable />
  </List>
);

export const OrderDetailsEdit = (props) => (
  <Edit {...props}>
    <SimpleForm>
      <TextInput disabled source="id" label="ID" />
      <ReferenceInput source="order_id" reference="orders" label="Numero de Orden">
        <SelectInput optionText="id" />
      </ReferenceInput>
      <ReferenceInput source="product_id" reference="products" label="Producto">
        <SelectInput optionText="nombre" />
      </ReferenceInput>
      <NumberInput source="quantity" label="Cantidad" />
      <NumberInput source="alto" label="Alto" />
      <NumberInput source="ancho" label="Ancho" />
      <TextInput source="anclaje" label="Anclaje" />
      <TextInput source="color" label="Color" />
      <NumberInput source="precio_total" label="Precio Total" />
      <TextInput source="firstname" label="Nombre" />
      <TextInput source="lastname" label="Apellido" />
      <TextInput source="shipping_address" label="Direccion de Envio" />
      <TextInput source="shipping_city" label="Ciudad de Envio" />
      <TextInput source="shipping_postal_code" label="Codigo Postal de Envio" />
      <TextInput source="billing_address" label="Direccion de Facturacion" />
      <TextInput source="billing_city" label="Ciudad de Facturacion" />
      <TextInput source="billing_postal_code" label="Codigo Postal de Facturacion" />
      <TextInput source="CIF" label="CIF" />
    </SimpleForm>
  </Edit>
);

export const OrderDetailsCreate = (props) => (
  <Create {...props}>
    <SimpleForm>
      <ReferenceInput source="order_id" reference="orders" label="Numero de Orden">
        <SelectInput optionText="id" />
      </ReferenceInput>
      <ReferenceInput source="product_id" reference="products" label="Producto">
        <SelectInput optionText="nombre" />
      </ReferenceInput>
      <NumberInput source="quantity" label="Cantidad" />
      <NumberInput source="alto" label="Alto" />
      <NumberInput source="ancho" label="Ancho" />
      <TextInput source="anclaje" label="Anclaje" />
      <TextInput source="color" label="Color" />
      <NumberInput source="precio_total" label="Precio Total" />
      <TextInput source="firstname" label="Nombre" />
      <TextInput source="lastname" label="Apellido" />
      <TextInput source="shipping_address" label="Direccion de Envio" />
      <TextInput source="shipping_city" label="Ciudad de Envio" />
      <TextInput source="shipping_postal_code" label="Codigo Postal de Envio" />
      <TextInput source="billing_address" label="Direccion de Facturacion" />
      <TextInput source="billing_city" label="Ciudad de Facturacion" />
      <TextInput source="billing_postal_code" label="Codigo Postal de Facturacion" />
      <TextInput source="CIF" label="CIF" />
    </SimpleForm>
  </Create>
);

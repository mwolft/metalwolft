import {
  formatCivilDateEs,
  type DeliveryEstimate as DeliveryEstimateData
} from "@/lib/delivery-estimate";

type DeliveryEstimateProps = {
  estimate: DeliveryEstimateData;
};

export function DeliveryEstimate({ estimate }: DeliveryEstimateProps) {
  const startDate = formatCivilDateEs(estimate.start_date);
  const endDate = formatCivilDateEs(estimate.end_date);

  if (!startDate || !endDate) {
    return null;
  }

  return (
    <aside className="mw-delivery-estimate" aria-label="Previsión orientativa de entrega">
      <p>
        <strong>Previsión orientativa para pedidos realizados hoy:</strong> entrega entre el{" "}
        <time dateTime={estimate.start_date}>{startDate}</time> y el{" "}
        <time dateTime={estimate.end_date}>{endDate}</time>. El plazo puede variar según la
        configuración y el destino.
      </p>
    </aside>
  );
}

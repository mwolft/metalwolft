import {
  formatCivilDateEs,
  type DeliveryEstimate as DeliveryEstimateData
} from "@/lib/delivery-estimate";

type DeliveryEstimateProps = {
  estimate: DeliveryEstimateData | null;
  variant?: "default" | "banner" | "compact";
};

export function DeliveryEstimate({
  estimate,
  variant = "default"
}: DeliveryEstimateProps) {
  if (!estimate) {
    return null;
  }

  const startDate = formatCivilDateEs(estimate.start_date);
  const endDate = formatCivilDateEs(estimate.end_date);

  if (!startDate || !endDate) {
    return null;
  }

  const dates = (
    <>
      <time dateTime={estimate.start_date}>{startDate}</time> y el{" "}
      <time dateTime={estimate.end_date}>{endDate}</time>
    </>
  );

  return (
    <aside
      className={`mw-delivery-estimate mw-delivery-estimate--${variant}`}
      aria-label="Previsión orientativa de entrega"
    >
      {variant === "banner" ? (
        <>
          <p>
            <strong>Previsión orientativa para pedidos realizados hoy:</strong> entrega entre el{" "}
            {dates}.
          </p>
          <p className="mw-delivery-estimate__detail">
            Los plazos pueden variar según el modelo, la configuración y el destino.
          </p>
        </>
      ) : variant === "compact" ? (
        <>
          <p>
            <strong>Entrega orientativa entre el {dates}.</strong>
          </p>
          <p className="mw-delivery-estimate__detail">
            Puede variar según la configuración y el destino.
          </p>
        </>
      ) : (
        <p>
          <strong>Previsión orientativa para pedidos realizados hoy:</strong> entrega entre el{" "}
          {dates}. El plazo puede variar según la configuración y el destino.
        </p>
      )}
    </aside>
  );
}

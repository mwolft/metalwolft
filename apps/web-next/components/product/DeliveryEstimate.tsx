import Image from "next/image";
import Link from "next/link";
import {
  formatCivilDateEs,
  formatCivilDateRangeEs,
  type DeliveryEstimate as DeliveryEstimateData
} from "@/lib/delivery-estimate";

type DeliveryEstimateProps = {
  estimate: DeliveryEstimateData | null;
  variant?: "default" | "banner" | "category" | "compact";
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
  const dateRange = formatCivilDateRangeEs(estimate.start_date, estimate.end_date);

  if (!startDate || !endDate || !dateRange) {
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
      {variant === "category" ? (
        <div className="mw-delivery-estimate__category-layout">
          <Image
            src="/icons/plazos-de-entrega.webp"
            alt=""
            width={80}
            height={80}
            className="mw-delivery-estimate__icon"
          />
          <h2 className="mw-delivery-estimate__title">
            Entrega estimada para pedidos realizados hoy
          </h2>
          <p className="mw-delivery-estimate__range">
            <strong>{dateRange}</strong>
          </p>
          <p className="mw-delivery-estimate__description">
            Previsión calculada según la carga actual del taller. Puede ampliarse en pedidos de
            grandes dimensiones o para determinados destinos.
          </p>
          <Link
            href="/plazos-entrega-rejas-a-medida"
            className="mw-delivery-estimate__link"
            aria-label="Leer más sobre cómo calculamos los plazos de entrega"
          >
            Leer más
          </Link>
        </div>
      ) : variant === "banner" ? (
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

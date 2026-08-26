"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearSession, getToken } from "@/lib/auth-client";
import { useAuthSession } from "@/hooks/useAuthSession";
import {
  DesignServiceClientError,
  getDesignServiceConfirmation,
  type DesignServiceConfirmation
} from "@/lib/design-service-client";

function formatCurrency(value: string, currency: string) {
  return new Intl.NumberFormat("es-ES", { style: "currency", currency }).format(Number(value));
}

function loginHref(id: number) {
  return `/login?next=${encodeURIComponent(`/diseno-previo/confirmado?design_request_id=${id}`)}`;
}

export function DesignServiceConfirmationView({ designRequestId }: { designRequestId: number | null }) {
  const router = useRouter();
  const { isAuthenticated, isReady } = useAuthSession();
  const [confirmation, setConfirmation] = useState<DesignServiceConfirmation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isReady || designRequestId === null || !isAuthenticated) return;
    const token = getToken();
    if (!token) {
      clearSession();
      router.replace(loginHref(designRequestId));
      return;
    }
    let timer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;
    const load = async () => {
      try {
        const next = await getDesignServiceConfirmation(token, designRequestId);
        if (cancelled) return;
        setConfirmation(next);
        setError(null);
        if (!next.order && next.checkout_status !== "payment_failed" && next.checkout_status !== "canceled") {
          timer = setTimeout(load, 2500);
        }
      } catch (requestError) {
        if (cancelled) return;
        if (requestError instanceof DesignServiceClientError && requestError.kind === "authentication") {
          clearSession();
          router.replace(loginHref(designRequestId));
          return;
        }
        setError("No hemos podido comprobar el estado del pago. Inténtalo de nuevo en unos segundos.");
      }
    };
    void load();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [designRequestId, isAuthenticated, isReady, router]);

  if (designRequestId === null) {
    return <section className="mw-section mw-design-checkout-state"><h1>Solicitud no válida</h1><Link className="mw-button mw-button--secondary" href="/diseno-previo">Volver al diseño previo</Link></section>;
  }
  if (!isReady || !isAuthenticated || (!confirmation && !error)) {
    return <section className="mw-section mw-design-checkout-state" aria-live="polite"><h1>Confirmando tu pago</h1><p>Estamos comprobando la solicitud de diseño.</p></section>;
  }
  if (error || !confirmation) {
    return <section className="mw-section mw-design-checkout-state"><h1>No hemos podido confirmar la solicitud</h1><p>{error}</p><Link className="mw-button mw-button--secondary" href={`/diseno-previo/checkout?design_request_id=${designRequestId}`}>Volver al pago</Link></section>;
  }
  if (confirmation.checkout_status === "payment_failed" || confirmation.checkout_status === "canceled") {
    return <section className="mw-section mw-design-checkout-state"><h1>El pago no se ha completado</h1><p>Tu solicitud sigue pendiente de pago. Puedes intentarlo de nuevo cuando quieras.</p><Link className="mw-button mw-button--secondary" href={`/diseno-previo/checkout?design_request_id=${designRequestId}`}>Volver al pago</Link></section>;
  }
  if (!confirmation.order) {
    return <section className="mw-section mw-design-checkout-state" aria-live="polite"><h1>Estamos confirmando el pago</h1><p>El proveedor ha recibido la operación. Actualizaremos esta página automáticamente cuando la solicitud quede confirmada.</p></section>;
  }
  return (
    <section className="mw-design-checkout mw-design-confirmation" aria-labelledby="design-confirmation-title">
      <p className="mw-eyebrow">Pago confirmado</p>
      <h1 className="mw-title mw-title--compact" id="design-confirmation-title">Solicitud recibida</h1>
      <p className="mw-lead">Hemos recibido el pago y ya podemos preparar tu diseño.</p>
      <div className="mw-design-checkout__panel">
        <p><strong>Referencia:</strong> {confirmation.reference}</p>
        <ul className="mw-design-checkout__items">
          {confirmation.items.map((item) => <li key={`${item.product_name}-${item.width_cm}-${item.height_cm}`}><strong>{item.product_name}</strong><span>{item.width_cm} × {item.height_cm} cm</span></li>)}
        </ul>
        <p><strong>Total:</strong> {formatCurrency(confirmation.total_amount, confirmation.currency)}</p>
        <p><strong>Entrega estimada:</strong> {confirmation.lead_time_hours} h</p>
        <p>Enviaremos el diseño terminado al correo asociado a tu cuenta cuando esté listo.</p>
      </div>
      <Link className="mw-button mw-button--secondary" href="/mi-cuenta">Ver mis pedidos</Link>
    </section>
  );
}

"use client";

import Link from "next/link";
import { useAuthSession } from "@/hooks/useAuthSession";

function customerName(user: ReturnType<typeof useAuthSession>["user"]) {
  const fullName = [user?.firstname, user?.lastname]
    .filter((part): part is string => Boolean(part && part.trim()))
    .join(" ");

  return fullName || user?.email || "tu cuenta";
}

export function AccountOverview() {
  const { user } = useAuthSession();

  return (
    <section className="mw-account-card" aria-labelledby="account-overview-title">
      <p className="mw-note">Resumen</p>
      <h2 id="account-overview-title">Hola, {customerName(user)}</h2>
      <p>
        Desde aquí puedes consultar el historial de pedidos hechos con tu cuenta de
        MetalWolft. El detalle de cada pedido quedará preparado para la siguiente fase.
      </p>
      <div className="mw-actions">
        <Link className="mw-button mw-button--primary" href="/mi-cuenta/pedidos">
          Ver mis pedidos
        </Link>
        <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
          Seguir comprando
        </Link>
      </div>
    </section>
  );
}

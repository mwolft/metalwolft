"use client";

import Link from "next/link";

export function CartPaymentPlaceholder() {
  return (
    <section className="mw-cart-state">
      <p className="mw-eyebrow">Pago</p>
      <h2 className="mw-title mw-title--compact">El pago todavia no esta disponible.</h2>
      <p className="mw-lead">
        Esta fase se activara cuando integremos el pago seguro en Next.
      </p>
      <div className="mw-actions">
        <Link className="mw-button mw-button--primary" href="/cart?step=details">
          Volver a datos
        </Link>
        <Link className="mw-button mw-button--secondary" href="/cart">
          Volver al carrito
        </Link>
      </div>
    </section>
  );
}

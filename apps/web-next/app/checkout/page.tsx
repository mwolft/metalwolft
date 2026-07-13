import Link from "next/link";
import type { Metadata } from "next";
import { CheckoutView } from "@/components/checkout/CheckoutView";
import { PageContainer } from "@/components/layout/PageContainer";

export const metadata: Metadata = {
  title: "Checkout | MetalWolft",
  description: "Completa tus datos para revisar el pedido de rejas para ventanas a medida.",
  alternates: {
    canonical: "/checkout"
  },
  robots: {
    index: false,
    follow: false
  }
};

export default function CheckoutPage() {
  return (
    <div className="mw-page">
      <PageContainer>
        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <Link href="/cart">Carrito</Link>
          <span>/</span>
          <span aria-current="page">Checkout</span>
        </nav>

        <section className="mw-section mw-cart-intro">
          <p className="mw-eyebrow">Checkout</p>
          <h1 className="mw-title mw-title--compact">Finalizar pedido</h1>
          <p className="mw-lead">
            Revisa tus datos, confirma la direccion de entrega y consulta el total
            calculado por MetalWolft antes de pasar al pago.
          </p>
        </section>

        <CheckoutView />
      </PageContainer>
    </div>
  );
}

import Link from "next/link";
import type { Metadata } from "next";
import { CartView } from "@/components/cart/CartView";
import { PageContainer } from "@/components/layout/PageContainer";

export const metadata: Metadata = {
  title: "Carrito | MetalWolft",
  description: "Revisa las rejas para ventanas configuradas en tu carrito de MetalWolft.",
  alternates: {
    canonical: "/cart"
  },
  robots: {
    index: false,
    follow: false
  }
};

export default function CartPage() {
  return (
    <div className="mw-page">
      <PageContainer>
        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <span aria-current="page">Carrito</span>
        </nav>

        <section className="mw-section mw-cart-intro">
          <p className="mw-eyebrow">Carrito</p>
          <h1 className="mw-title mw-title--compact">Tu carrito</h1>
          <p className="mw-lead">
            Revisa las rejas configuradas, ajusta cantidades y continúa comprando
            cuando lo necesites.
          </p>
        </section>

        <CartView />
      </PageContainer>
    </div>
  );
}

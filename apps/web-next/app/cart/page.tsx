import Link from "next/link";
import type { Metadata } from "next";
import { Suspense } from "react";
import { CartFlow } from "@/components/cart/CartFlow";
import { PageContainer } from "@/components/layout/PageContainer";
import { DeliveryEstimate } from "@/components/product/DeliveryEstimate";
import { fetchDeliveryEstimate } from "@/lib/delivery-estimate";

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

export default async function CartPage() {
  const deliveryEstimate = await fetchDeliveryEstimate();

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

        <Suspense fallback={<div className="mw-cart-state">Cargando carrito...</div>}>
          <CartFlow
            deliveryEstimate={
              <DeliveryEstimate estimate={deliveryEstimate} variant="compact" />
            }
          />
        </Suspense>
      </PageContainer>
    </div>
  );
}

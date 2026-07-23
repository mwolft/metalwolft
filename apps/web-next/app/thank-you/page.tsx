import type { Metadata } from "next";
import { Suspense } from "react";
import { PageContainer } from "@/components/layout/PageContainer";
import { ThankYouStatus } from "@/components/cart/ThankYouStatus";
import { MetalSpinner } from "@/components/ui/MetalSpinner";

export const metadata: Metadata = {
  title: "Estado del pedido | MetalWolft",
  description: "Consulta el estado de confirmación de tu pedido en MetalWolft.",
  robots: {
    index: false,
    follow: false
  }
};

export default function ThankYouPage() {
  return (
    <div className="mw-thank-you-page">
      <PageContainer>
        <Suspense
          fallback={
            <div className="mw-thank-you-fallback">
              <MetalSpinner variant="page" label="Comprobando pedido" />
            </div>
          }
        >
          <ThankYouStatus />
        </Suspense>
      </PageContainer>
    </div>
  );
}

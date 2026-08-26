import type { Metadata } from "next";
import Link from "next/link";
import { DesignServiceCheckoutView } from "@/components/design-service/DesignServiceCheckoutView";
import { PageContainer } from "@/components/layout/PageContainer";

export const metadata: Metadata = {
  title: "Preparar compra de diseño previo | MetalWolft",
  robots: { index: false, follow: false }
};

type DesignServiceCheckoutPageProps = {
  searchParams: Promise<{ design_request_id?: string | string[] }>;
};

function parseDesignRequestId(value: string | string[] | undefined) {
  const raw = Array.isArray(value) ? value[0] : value;
  const parsed = Number(raw);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

export default async function DesignServiceCheckoutPage({ searchParams }: DesignServiceCheckoutPageProps) {
  const { design_request_id } = await searchParams;
  const designRequestId = parseDesignRequestId(design_request_id);

  return (
    <div className="mw-page">
      <PageContainer>
        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <Link href="/diseno-previo">Diseño previo</Link>
          <span>/</span>
          <span aria-current="page">Preparar compra</span>
        </nav>
        <DesignServiceCheckoutView designRequestId={designRequestId} />
      </PageContainer>
    </div>
  );
}

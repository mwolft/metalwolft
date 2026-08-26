import type { Metadata } from "next";
import Link from "next/link";
import { DesignServiceConfirmationView } from "@/components/design-service/DesignServiceConfirmationView";
import { PageContainer } from "@/components/layout/PageContainer";

export const metadata: Metadata = {
  title: "Solicitud de diseño confirmada | MetalWolft",
  robots: { index: false, follow: false }
};

type PageProps = { searchParams: Promise<{ design_request_id?: string | string[] }> };

function parseId(value: string | string[] | undefined) {
  const raw = Array.isArray(value) ? value[0] : value;
  const parsed = Number(raw);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

export default async function DesignServiceConfirmationPage({ searchParams }: PageProps) {
  const { design_request_id } = await searchParams;
  return (
    <div className="mw-page"><PageContainer>
      <nav className="mw-breadcrumbs" aria-label="Breadcrumb"><Link href="/">Inicio</Link><span>/</span><Link href="/diseno-previo">Diseño previo</Link><span>/</span><span aria-current="page">Confirmación</span></nav>
      <DesignServiceConfirmationView designRequestId={parseId(design_request_id)} />
    </PageContainer></div>
  );
}

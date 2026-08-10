import type { Metadata } from "next";
import Link from "next/link";
import { IssueReportForm } from "@/components/contact/IssueReportForm";
import { PageContainer } from "@/components/layout/PageContainer";

const PATH = "/formulario-incidencias";

export const metadata: Metadata = {
  title: "Formulario de incidencias | MetalWolft",
  description:
    "Comunica una incidencia de pintura, medidas, transporte o embalaje de tu pedido de MetalWolft.",
  alternates: { canonical: PATH },
  robots: { index: false, follow: false }
};

export default function IssueReportPage() {
  return (
    <div className="mw-page">
      <PageContainer>
        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <Link href="/politica-devolucion">Devoluciones y garantías</Link>
          <span>/</span>
          <span aria-current="page">Formulario de incidencias</span>
        </nav>

        <section className="mw-hero mw-hero--compact">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Revisión de incidencias</p>
            <h1 className="mw-title mw-title--compact">Formulario de incidencias</h1>
            <p className="mw-lead">
              Indícanos qué ha ocurrido con tu pedido y adjunta imágenes si ayudan a
              revisar el caso. Te responderemos tras analizar la información.
            </p>
          </div>
        </section>

        <section className="mw-section" aria-labelledby="issue-report-form-title">
          <h2 id="issue-report-form-title">Cuéntanos qué ha ocurrido</h2>
          <p>
            Para localizar el pedido y revisar la incidencia, necesitamos tu nombre,
            correo electrónico, número de pedido y el tipo de incidencia.
          </p>
          <IssueReportForm />
        </section>
      </PageContainer>
    </div>
  );
}

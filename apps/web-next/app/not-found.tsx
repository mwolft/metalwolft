import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { buildMetadata } from "@/lib/metadata";

export const metadata = buildMetadata({
  title: "Página no encontrada",
  description:
    "La URL solicitada no existe en la shell pública SEO de MetalWolft.",
  path: "/404"
});

export default function NotFoundPage() {
  return (
    <div className="mw-page mw-empty">
      <PageContainer>
        <section className="mw-section">
          <p className="mw-eyebrow">404</p>
          <h1 className="mw-title mw-title--compact">Página no encontrada</h1>
          <p className="mw-lead">
            Esta shell pública todavía está en construcción. Puedes volver al
            inicio o entrar en la landing principal de rejas para ventanas.
          </p>
          <div className="mw-actions">
            <Link className="mw-button mw-button--primary" href="/">
              Volver al inicio
            </Link>
            <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
              Ir a rejas para ventanas
            </Link>
          </div>
        </section>
      </PageContainer>
    </div>
  );
}

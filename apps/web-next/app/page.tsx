import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { JsonLd } from "@/components/seo/JsonLd";
import { buildMetadata, absoluteUrl, siteConfig } from "@/lib/metadata";

export const metadata = buildMetadata({
  title: "Rejas para ventanas a medida",
  description:
    "Front público SEO de MetalWolft enfocado en rejas para ventanas a medida, instalación sin obra y fabricación bajo pedido.",
  path: "/"
});

export default function HomePage() {
  return (
    <div className="mw-page">
      <PageContainer>
        <JsonLd
          data={{
            "@context": "https://schema.org",
            "@type": "WebPage",
            name: "Rejas para ventanas a medida",
            url: absoluteUrl("/"),
            description:
              "Front público SEO de MetalWolft enfocado en rejas para ventanas a medida, instalación sin obra y fabricación bajo pedido.",
            isPartOf: {
              "@type": "WebSite",
              name: siteConfig.name,
              url: siteConfig.siteUrl
            }
          }}
        />

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Fase 1 SEO pública</p>
            <h1 className="mw-title">Rejas para ventanas a medida</h1>
            <p className="mw-lead">
              Este shell Next.js nace para mejorar el renderizado inicial, la
              indexabilidad y la estructura SEO de MetalWolft sin tocar todavía
              checkout, pagos ni la lógica transaccional del stack actual.
            </p>
            <div className="mw-actions">
              <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
                Ver rejas para ventanas
              </Link>
            </div>
          </div>

          <aside className="mw-panel" aria-label="Resumen de alcance">
            <p className="mw-note">Validación inicial</p>
            <h2>Qué cubre esta fase</h2>
            <ul className="mw-list">
              <li>HTML inicial orientado a SEO.</li>
              <li>Metadata base con canonical y Open Graph.</li>
              <li>Robots y sitemap propios del frontend público.</li>
              <li>Separación total respecto al backend transaccional.</li>
            </ul>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Base preparada para migración progresiva</h2>
          <p>
            La siguiente ola podrá incorporar la landing principal de{" "}
            <strong>rejas para ventanas</strong>, fichas dinámicas de producto y,
            más adelante, blog y guías de apoyo para posicionar búsquedas con
            intención comercial e informacional.
          </p>
        </section>
      </PageContainer>
    </div>
  );
}

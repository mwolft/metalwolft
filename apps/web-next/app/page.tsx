import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { JsonLd } from "@/components/seo/JsonLd";
import { buildMetadata, absoluteUrl, siteConfig } from "@/lib/metadata";

export const metadata = buildMetadata({
  title: "Rejas para ventanas a medida",
  description:
    "Rejas para ventanas a medida fabricadas por MetalWolft, con soluciones metalicas seguras, instalacion sin obra y envio directo desde taller.",
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
              "Rejas para ventanas a medida fabricadas por MetalWolft, con soluciones metalicas seguras, instalacion sin obra y envio directo desde taller.",
            isPartOf: {
              "@type": "WebSite",
              name: siteConfig.name,
              url: siteConfig.siteUrl
            }
          }}
        />

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Fabricacion a medida</p>
            <h1 className="mw-title">Rejas para ventanas a medida</h1>
            <p className="mw-lead">
              Fabricamos rejas metalicas para ventanas con enfoque en seguridad,
              medidas a medida y montaje limpio. Aqui puedes descubrir modelos
              pensados para vivienda, comparar acabados y acceder al catalogo
              principal de rejas para ventanas.
            </p>
            <div className="mw-actions">
              <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
                Ver rejas para ventanas
              </Link>
            </div>
          </div>

          <aside className="mw-panel" aria-label="Puntos clave">
            <p className="mw-note">Puntos clave</p>
            <h2>Que encontrara aqui</h2>
            <ul className="mw-list">
              <li>Rejas para ventanas fabricadas a medida.</li>
              <li>Soluciones de instalacion sin obra.</li>
              <li>Modelos metalicos con foco en seguridad.</li>
              <li>Acceso directo al catalogo y a las guias utiles.</li>
            </ul>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Rejas metalicas para proteger la vivienda</h2>
          <p>
            Si buscas una reja fija, abatible o una opcion pensada para una
            instalacion sin obra, esta puerta de entrada te ayuda a llegar
            rapido a la categoria principal y a las fichas de producto con
            informacion clara sobre fabricacion, medicion del hueco y envio
            desde taller.
          </p>
        </section>
      </PageContainer>
    </div>
  );
}

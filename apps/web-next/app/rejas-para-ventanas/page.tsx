import { PageContainer } from "@/components/layout/PageContainer";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import { JsonLd } from "@/components/seo/JsonLd";
import { buildMetadata, absoluteUrl } from "@/lib/metadata";

export const metadata = buildMetadata({
  title: "Rejas para ventanas",
  description:
    "Landing SEO inicial para rejas para ventanas a medida, con foco en instalación sin obra, fabricación bajo pedido y envío directo de fábrica.",
  path: "/rejas-para-ventanas"
});

export default function RejasParaVentanasPage() {
  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd
          items={[
            { name: "Inicio", path: "/" },
            { name: "Rejas para ventanas", path: "/rejas-para-ventanas" }
          ]}
        />
        <JsonLd
          data={{
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            name: "Rejas para ventanas",
            url: absoluteUrl("/rejas-para-ventanas"),
            description:
              "Landing SEO inicial para rejas para ventanas a medida, con foco en instalación sin obra, fabricación bajo pedido y envío directo de fábrica."
          }}
        />

        <div className="mw-breadcrumbs" aria-label="Breadcrumb">
          <span>Inicio</span>
          <span>/</span>
          <span>Rejas para ventanas</span>
        </div>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Landing principal</p>
            <h1 className="mw-title mw-title--compact">Rejas para ventanas</h1>
            <p className="mw-lead">
              Esta versión inicial sirve para validar la migración SEO del
              escaparate público: contenido visible desde servidor, metadata
              limpia y una base preparada para crecer sin tocar la lógica de
              pedido ni el backend transaccional.
            </p>
          </div>

          <aside className="mw-panel" aria-label="Puntos clave">
            <p className="mw-note">Base SEO</p>
            <h2>Enfoque de la fase</h2>
            <ul className="mw-list">
              <li>Priorizar la keyword “rejas para ventanas”.</li>
              <li>Preparar arquitectura para categorías y producto dinámico.</li>
              <li>Separar contenido comercial público de la app privada.</li>
            </ul>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Rejas para ventanas a medida</h2>
          <p>
            El objetivo de esta página es convertirse en la pieza principal para
            posicionar el escaparate de MetalWolft sobre búsquedas transaccionales
            relacionadas con fabricación a medida, seguridad y personalización.
          </p>
        </section>

        <section className="mw-section">
          <h2>Rejas para ventanas sin obra</h2>
          <p>
            La siguiente iteración podrá desplegar contenido más profundo sobre
            instalación sin obra, medición del hueco y selección del sistema de
            anclaje, manteniendo una experiencia inicial más ligera y mejor para
            indexación.
          </p>
        </section>

        <section className="mw-section">
          <h2>Fabricación y envío</h2>
          <p>
            Esta base también deja preparada la estructura para incorporar más
            adelante contenido sobre tiempos de fabricación, catálogo y entrega,
            sin mezclar todavía lógica de checkout, pagos o cuenta de usuario.
          </p>
          <h3>Enlaces internos previstos</h3>
          <ul className="mw-list">
            <li>Guía para medir el hueco.</li>
            <li>Instalación sin obra.</li>
            <li>Plazos de entrega.</li>
          </ul>
        </section>
      </PageContainer>
    </div>
  );
}

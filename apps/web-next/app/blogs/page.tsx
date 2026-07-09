import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import { JsonLd } from "@/components/seo/JsonLd";
import {
  blogArticles,
  buildBlogIndexJsonLd,
  buildBlogIndexMetadata,
  buildBlogItemListJsonLd
} from "@/lib/blog";

export const metadata = buildBlogIndexMetadata();

export default function BlogIndexPage() {
  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd
          items={[
            { name: "Inicio", path: "/" },
            { name: "Blog", path: "/blogs" }
          ]}
        />
        <JsonLd data={buildBlogIndexJsonLd()} />
        <JsonLd data={buildBlogItemListJsonLd()} />

        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <span aria-current="page">Blog</span>
        </nav>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Guías de ayuda</p>
            <h1 className="mw-title mw-title--compact">Blog sobre rejas para ventanas</h1>
            <p className="mw-lead">
              Reunimos las guías principales para ayudarte a medir bien el hueco,
              entender la instalación sin obra y comparar estilos de rejas para
              ventanas antes de elegir un modelo a medida.
            </p>
            <div className="mw-actions">
              <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
                Ver catálogo principal
              </Link>
            </div>
          </div>

          <aside className="mw-panel" aria-label="Resumen del blog">
            <p className="mw-note">Contenido</p>
            <h2>Qué cubren estas guías</h2>
            <ul className="mw-list">
              <li>Medición correcta del hueco antes de fabricar.</li>
              <li>Instalación sin obra paso a paso.</li>
              <li>Diferencias entre sistemas y acabados.</li>
              <li>Ideas de diseño para viviendas actuales.</li>
            </ul>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Guías principales</h2>
          <p>
            Estas páginas ya viven dentro del shell público de Next y sirven
            como base SEO para resolver dudas frecuentes antes de pedir unas
            rejas para ventanas a medida.
          </p>

          <div className="mw-article-grid">
            {blogArticles.map((article) => (
              <article className="mw-article-card" key={article.slug}>
                <Link href={`/${article.slug}`} aria-label={article.title}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={article.image} alt={article.imageAlt} />
                </Link>
                <div className="mw-article-card__body">
                  <p className="mw-card__meta">
                    <span>{article.topic}</span>
                    <span>{article.readingTime}</span>
                  </p>
                  <h2>
                    <Link href={`/${article.slug}`}>{article.title}</Link>
                  </h2>
                  <p>{article.excerpt}</p>
                  <div className="mw-actions">
                    <Link className="mw-button mw-button--secondary" href={`/${article.slug}`}>
                      Leer guía
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="mw-section">
          <h2>Cómo aprovechar estas guías antes de pedir tu reja</h2>
          <p>
            Lo ideal es empezar por la medición del hueco, continuar con la
            instalación sin obra si buscas un montaje limpio y terminar en la
            categoría principal para comparar modelos reales, acabados y tipos
            de apertura.
          </p>
          <div className="mw-actions">
            <Link className="mw-button mw-button--secondary" href="/medir-hueco-rejas-para-ventanas">
              Empezar por la medición
            </Link>
            <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas-modernas">
              Ver ideas de diseño
            </Link>
          </div>
        </section>
      </PageContainer>
    </div>
  );
}

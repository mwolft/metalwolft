import type { ReactNode } from "react";
import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import { JsonLd } from "@/components/seo/JsonLd";
import { buildBlogArticleJsonLd, type BlogArticle } from "@/lib/blog";

type BlogArticleShellProps = {
  article: BlogArticle;
  eyebrow?: string;
  keyPoints: string[];
  heroMedia?: ReactNode;
  children: ReactNode;
};

export function BlogArticleShell({
  article,
  eyebrow = "Guía práctica",
  keyPoints,
  heroMedia,
  children
}: BlogArticleShellProps) {
  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd
          items={[
            { name: "Inicio", path: "/" },
            { name: "Blog", path: "/blogs" },
            { name: article.title, path: `/${article.slug}` }
          ]}
        />
        <JsonLd data={buildBlogArticleJsonLd(article)} />

        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <Link href="/blogs">Blog</Link>
          <span>/</span>
          <span aria-current="page">{article.title}</span>
        </nav>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">{eyebrow}</p>
            <p className="mw-article-meta">
              <span>{article.topic}</span>
              <span>Lectura {article.readingTime}</span>
            </p>
            <h1 className="mw-title mw-title--compact">{article.title}</h1>
            <p className="mw-lead">{article.description}</p>
            <div className="mw-actions">
              <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
                Ver rejas para ventanas
              </Link>
              <Link className="mw-button mw-button--secondary" href="/blogs">
                Volver al blog
              </Link>
            </div>
          </div>

          <aside className="mw-panel" aria-label="Puntos clave del artículo">
            <p className="mw-note">Puntos clave</p>
            <h2>Qué vas a encontrar</h2>
            <ul className="mw-list">
              {keyPoints.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </aside>
        </section>

        {heroMedia ? <section className="mw-section mw-article-media">{heroMedia}</section> : null}

        {children}
      </PageContainer>
    </div>
  );
}

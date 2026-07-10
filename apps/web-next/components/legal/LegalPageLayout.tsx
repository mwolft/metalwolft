import type { ReactNode } from "react";
import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import type { LegalLink } from "@/lib/legal";

type LegalPageLayoutProps = {
  path: string;
  title: string;
  eyebrow: string;
  description: string;
  summaryTitle: string;
  summaryItems: string[];
  relatedLinks: LegalLink[];
  children: ReactNode;
};

export function LegalPageLayout({
  path,
  title,
  eyebrow,
  description,
  summaryTitle,
  summaryItems,
  relatedLinks,
  children
}: LegalPageLayoutProps) {
  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd
          items={[
            { name: "Inicio", path: "/" },
            { name: title, path }
          ]}
        />

        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <span aria-current="page">{title}</span>
        </nav>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">{eyebrow}</p>
            <h1 className="mw-title mw-title--compact">{title}</h1>
            <p className="mw-lead">{description}</p>
          </div>

          <aside className="mw-panel" aria-label={`Resumen de ${title}`}>
            <p className="mw-note">Resumen</p>
            <h2>{summaryTitle}</h2>
            <ul className="mw-list">
              {summaryItems.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </aside>
        </section>

        {children}

        <section className="mw-section">
          <h2>Enlaces relacionados</h2>
          <ul className="mw-list">
            {relatedLinks.map((link) => (
              <li key={link.href}>
                <Link href={link.href}>{link.label}</Link>
              </li>
            ))}
          </ul>
        </section>
      </PageContainer>
    </div>
  );
}

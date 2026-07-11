import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { contactDetails, contactLinks } from "@/lib/contact";
import { legalFooterLinks } from "@/lib/legal";
import { footerCatalogLinks, footerGuideLinks } from "@/lib/navigation";

export function SiteFooter() {
  return (
    <footer className="mw-footer">
      <PageContainer>
        <div className="mw-footer__grid">
          <div className="mw-footer__brand">
            <p className="mw-footer__eyebrow">MetalWolft</p>
            <p className="mw-footer__title">Rejas para ventanas a medida</p>
            <p className="mw-footer__copy">
              Fabricamos rejas para ventanas a medida con atención directa desde taller,
              guías claras para medir bien y una compra más enfocada en lo que realmente
              necesita la vivienda.
            </p>
          </div>

          <nav className="mw-footer__section" aria-label="Catálogo de rejas">
            <p className="mw-footer__section-title">Catálogo</p>
            <div className="mw-footer__links">
              {footerCatalogLinks.map((link) => (
                <Link href={link.href} key={link.href}>
                  {link.label}
                </Link>
              ))}
            </div>
          </nav>

          <nav className="mw-footer__section" aria-label="Guías de ayuda">
            <p className="mw-footer__section-title">Guías</p>
            <div className="mw-footer__links">
              {footerGuideLinks.map((link) => (
                <Link href={link.href} key={link.href}>
                  {link.label}
                </Link>
              ))}
            </div>
          </nav>

          <div className="mw-footer__section">
            <p className="mw-footer__section-title">Contacto</p>
            <div className="mw-footer__links">
              <Link href="/contact">Hablar con MetalWolft</Link>
              <a href={contactLinks.phone}>{contactDetails.phoneDisplay}</a>
              <a href={contactLinks.email}>{contactDetails.email}</a>
              <a href={contactLinks.whatsapp} rel="noopener noreferrer" target="_blank">
                WhatsApp
              </a>
            </div>
          </div>

          <nav className="mw-footer__section" aria-label="Enlaces legales">
            <p className="mw-footer__section-title">Legales</p>
            <div className="mw-footer__links">
              {legalFooterLinks.map((link) => (
                <Link href={link.href} key={link.href}>
                  {link.label}
                </Link>
              ))}
            </div>
          </nav>
        </div>
      </PageContainer>
    </footer>
  );
}

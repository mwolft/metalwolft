import Image from "next/image";
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
            <div className="mw-footer__brand-location">
              <svg
                aria-hidden="true"
                className="mw-footer__brand-location-icon"
                fill="none"
                focusable="false"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0" />
                <circle cx="12" cy="10" r="3" />
              </svg>
              <div>
                <address>
                  <span>Carretera de Porzuna, km 1,8</span>
                  <span>13005 Ciudad Real · España</span>
                </address>
                <a
                  aria-label="Ver ubicación de MetalWolft en Google Maps"
                  className="mw-footer__map-preview"
                  href="https://maps.app.goo.gl/jG5SvHQvDozB4puc7"
                  rel="noopener noreferrer"
                  target="_blank"
                >
                  <Image
                    src="/metalwolft-location-map.jpg"
                    alt=""
                    width={880}
                    height={495}
                    sizes="(max-width: 640px) 100vw, 440px"
                  />
                </a>
              </div>
            </div>
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

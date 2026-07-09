import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { contactDetails, contactLinks } from "@/lib/contact";

export function SiteFooter() {
  return (
    <footer className="mw-footer">
      <PageContainer>
        <div className="mw-footer__grid">
          <div className="mw-footer__brand">
            <p className="mw-footer__title">MetalWolft</p>
            <p className="mw-footer__copy">
              Rejas para ventanas a medida, atención directa y ayuda para medir,
              instalar y pedir presupuesto con más claridad.
            </p>
          </div>

          <div className="mw-footer__inner">
            <p className="mw-footer__title">Enlaces</p>
            <div className="mw-footer__links">
              <Link href="/">Inicio</Link>
              <Link href="/rejas-para-ventanas">Rejas para ventanas</Link>
              <Link href="/blogs">Blog</Link>
              <Link href="/contact">Contacto</Link>
            </div>
          </div>

          <div className="mw-footer__inner">
            <p className="mw-footer__title">Ayuda rápida</p>
            <div className="mw-footer__links">
              <Link href="/contact">Formulario de contacto</Link>
              <a href={contactLinks.phone}>{contactDetails.phoneDisplay}</a>
              <a href={contactLinks.email}>{contactDetails.email}</a>
              <a href={contactLinks.whatsapp} rel="noopener noreferrer" target="_blank">
                WhatsApp
              </a>
            </div>
          </div>
        </div>
      </PageContainer>
    </footer>
  );
}
